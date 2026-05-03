"""Async client for the Riot Games API (regional EUW endpoints).

The eligibility decision (does this match count toward weekly accountability?)
deliberately lives in services.match_eligibility -- this module only fetches
and parses Riot data.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

import httpx


RIOT_API_BASE = "https://europe.api.riotgames.com"
DEFAULT_TIMEOUT = 15.0


@dataclass
class RiotMatchData:
    """Parsed match data for a single player in a single game."""
    riot_match_id: str
    champion_name: str
    won: bool
    kills: int
    deaths: int
    assists: int
    cs: int
    vision_score: int
    gold_earned: int
    damage_to_champions: int
    game_duration_seconds: int
    team_position: str
    game_start_time: datetime
    queue_id: int
    team_puuids: List[str] = field(default_factory=list)


class RiotAPIClient:
    """Async client for Riot Games API.

    A new httpx.AsyncClient is created per request -- avoids connection issues
    in long-running processes and is fine for our low-volume sync flow.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("RIOT_API_KEY is not configured")
        self.api_key = api_key
        self.headers = {"X-Riot-Token": api_key}

    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        """Resolve a Riot ID (gameName#tagLine) to a stable PUUID.

        PUUIDs never change for an account -- callers should cache the result.
        Raises httpx.HTTPStatusError on 401/403 (bad key), 404 (not found),
        429 (rate limited).
        """
        url = f"{RIOT_API_BASE}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["puuid"]

    async def get_match_ids(
        self,
        puuid: str,
        start_time: int,
        count: int = 100,
        queue: int = 420,
    ) -> List[str]:
        """Return ranked solo match IDs for a player since start_time (epoch SECONDS)."""
        url = f"{RIOT_API_BASE}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"queue": queue, "startTime": start_time, "count": count}
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_match_detail(self, match_id: str, puuid: str) -> RiotMatchData:
        """Fetch a match and project just this player's stats + their teammates' PUUIDs."""
        url = f"{RIOT_API_BASE}/lol/match/v5/matches/{match_id}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

        info = data["info"]
        participant = next((p for p in info["participants"] if p["puuid"] == puuid), None)
        if participant is None:
            raise ValueError(f"Player {puuid} not found in match {match_id}")

        my_team_id = participant["teamId"]
        team_puuids = [
            p["puuid"]
            for p in info["participants"]
            if p["teamId"] == my_team_id and p["puuid"] != puuid
        ]

        return RiotMatchData(
            riot_match_id=match_id,
            champion_name=participant["championName"],
            won=bool(participant["win"]),
            kills=participant.get("kills", 0),
            deaths=participant.get("deaths", 0),
            assists=participant.get("assists", 0),
            cs=participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0),
            vision_score=participant.get("visionScore", 0),
            gold_earned=participant.get("goldEarned", 0),
            damage_to_champions=participant.get("totalDamageDealtToChampions", 0),
            game_duration_seconds=info.get("gameDuration", 0),
            team_position=participant.get("teamPosition", "") or "",
            # gameStartTimestamp is epoch MILLISECONDS -> divide by 1000.
            game_start_time=datetime.fromtimestamp(info["gameStartTimestamp"] / 1000),
            queue_id=info.get("queueId", 0),
            team_puuids=team_puuids,
        )

    async def get_all_match_ids_paginated(
        self,
        puuid: str,
        queue: int = 420,
        known_match_ids: Optional[set] = None,
    ) -> List[str]:
        """Paginate through match IDs for a player with no start_time filter.

        Stops early when an entire page consists only of IDs already present in
        known_match_ids -- avoids fetching all 30 pages when only a few new games
        exist after the initial full sync.

        Returns only IDs not present in known_match_ids.
        """
        new_ids: List[str] = []
        start = 0
        count = 100
        while True:
            url = f"{RIOT_API_BASE}/lol/match/v5/matches/by-puuid/{puuid}/ids"
            params = {"queue": queue, "start": start, "count": count}
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                page = response.json()
            if known_match_ids:
                page_new = [mid for mid in page if mid not in known_match_ids]
                new_ids.extend(page_new)
                # Riot returns newest-first; if every ID on this page is already
                # known we have reached previously-synced history -- stop.
                if len(page_new) == 0:
                    break
            else:
                new_ids.extend(page)
            if len(page) < count:
                break
            start += count
        return new_ids

    async def fetch_player_games(
        self,
        puuid: str,
        since_date: date,
        queue: int = 420,
        known_match_ids: set = None,
    ) -> List[RiotMatchData]:
        """Fetch all matches for a player since since_date, with rate limiting between detail calls.

        known_match_ids: set of riot_match_ids already in the DB. Detail calls are skipped for
        these -- only the match IDs list call is made, so repeat syncs are near-instant.
        """
        # Match-V5 startTime expects epoch SECONDS, NOT milliseconds.
        start_epoch = int(datetime.combine(since_date, datetime.min.time()).timestamp())

        all_match_ids = await self.get_match_ids(puuid, start_time=start_epoch, queue=queue)

        if known_match_ids:
            new_match_ids = [mid for mid in all_match_ids if mid not in known_match_ids]
        else:
            new_match_ids = all_match_ids

        games: List[RiotMatchData] = []
        for match_id in new_match_ids:
            game = await self.get_match_detail(match_id, puuid)
            games.append(game)
        return games

    async def fetch_all_player_games(
        self,
        puuid: str,
        known_match_ids: Optional[set] = None,
        queue: int = 420,
        rate_limit_delay: float = 1.2,
    ) -> List[RiotMatchData]:
        """Fetch full match history for a player with no date limit.

        Paginates through all available match IDs, skips any already stored in
        known_match_ids, then fetches details with rate_limit_delay seconds
        between calls to stay within the 100 requests / 2 minute rate limit.
        """
        new_match_ids = await self.get_all_match_ids_paginated(
            puuid, queue=queue, known_match_ids=known_match_ids
        )

        games: List[RiotMatchData] = []
        for i, match_id in enumerate(new_match_ids):
            if i > 0:
                await asyncio.sleep(rate_limit_delay)
            game = await self.get_match_detail(match_id, puuid)
            games.append(game)
        return games
