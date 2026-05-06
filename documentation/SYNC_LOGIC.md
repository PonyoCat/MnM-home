# Riot Sync Logic

Reference for how the dashboard pulls match data from the Riot Match-v5 API, persists it, and decides what counts toward weekly accountability.

Source files:
- [backend/app/services/riot_api.py](../backend/app/services/riot_api.py) — HTTP client, pagination, retry
- [backend/app/services/match_eligibility.py](../backend/app/services/match_eligibility.py) — pure eligibility decision
- [backend/app/crud.py](../backend/app/crud.py) — sync orchestration (`sync_player_games`, `sync_all_players`, `full_sync_player_games`, `full_sync_all_players`)
- [backend/app/routers/players.py](../backend/app/routers/players.py) — endpoint surface and lock handling

---

## 1. Riot Match-v5 hard limits (read this first)

These constraints come from the API itself. Code cannot work around them.

### 1.1 ~1000-match cap per PUUID — GLOBAL, not per-queue

The endpoint `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` returns at most ~990–1000 IDs per PUUID before paginating into empty pages. The cap is on the player's underlying match index. The `queue=` parameter filters within that already-capped window — it does NOT unlock additional history.

Implication: if a player's last 1000 games are 800 ARAM + 200 ranked solo, calling with `queue=420` returns 200 IDs. Earlier ranked solo games are gone — no parameter brings them back.

Sources:
- [Riot dev-relations issue #517](https://github.com/RiotGames/developer-relations/issues/517) — closed by Riot as "working as intended"
- [Riot dev-relations issue #957](https://github.com/RiotGames/developer-relations/issues/957) — cap fires under 2 years too
- Wrapper libraries (RiotWatcher, Cassiopeia) treat `queue` as a post-filter, not a separate index

### 1.2 No documented depth difference between dev and production keys

`RGAPI-` dev keys differ from production keys only on rate limits, expiration, and access to RSO/Tournament endpoints. Match-v5 history depth is identical.

### 1.3 `startTime` omission

Without `startTime`, the API returns the player's most-recent matches working backward (newest-first), paginated by `start`/`count`. There is no implicit time floor beyond the ~1000-match cap. This is the correct call shape for full-history sync.

### 1.4 Practical consequence for our team

Today's count: 2432 games in DB across 5 players. Earliest game per player ranges 2025-05-14 (Hans) to 2025-09-04 (Sinus). Team formed 2025-03-30.

| Player | Ranked solo in DB | Earliest |
|--------|-------------------|----------|
| Mikkel | 599 | 2025-08-17 |
| Hans   | 579 | 2025-05-14 |
| Alex   | 574 | 2025-07-10 |
| Sinus  | 465 | 2025-09-04 |
| Elias  | 215 | 2025-08-13 |

None at 1000 cap on ranked solo, but the GLOBAL index could be near 1000 for high-volume players. Elias's 215 ranked solo with earliest 2025-08-13 is the most likely cap-victim — heavy non-ranked play could have pushed older ranked games out of the index.

To verify whether the global cap is biting for a given player, page `by-puuid/{puuid}/ids` WITHOUT a `queue` filter and check whether the count lands near 990. If it does, older ranked games are permanently inaccessible.

---

## 2. Sync types

Three distinct flows. All share the same eligibility rules and DB writes; they differ in how they choose which match IDs to fetch.

### 2.1 Weekly sync — `sync_player_games`

- **Trigger**: scheduler every 30 min (APScheduler `CronTrigger(minute="*/30")`), or `POST /api/players/sync-all`
- **Window**: from current week's Thursday-16:00 to now
- **API call**: `get_match_ids(puuid, startTime=epoch_seconds_of_week_start, queue=420, count=100)` — single page
- **Dedup**: skip detail calls for any IDs already in `match_history` for this week
- **Cost**: ≤1 IDs call + N detail calls per player (typically <20 detail calls per week per player)

### 2.2 Full historical sync — `full_sync_player_games`

- **Trigger**: `POST /api/players/full-sync` (background task, returns `run_id`)
- **Window**: no date filter — back as far as Riot will return (~1000 matches global cap)
- **API call**: `get_all_match_ids_paginated(puuid, queue=420)` — pages start=0,100,200... until a page returns <100 IDs
- **Dedup**: skip detail calls for ANY ID already in `match_history` for this player (across all weeks)
- **Cost**: up to ~10 IDs calls + only-the-new detail calls. After first run, repeat full syncs are nearly free (0 detail calls if Riot has nothing new).

### 2.3 Critical: full sync does NOT pass `known_match_ids` to the paginator

`fetch_all_player_games` calls `get_all_match_ids_paginated(puuid, queue=420)` with no `known_match_ids`. It applies the dedup AFTER pagination completes.

Why: `get_all_match_ids_paginated` has an early-stop heuristic — when an entire page consists only of already-known IDs, it bails. That heuristic is correct for incremental weekly sync, but breaks full sync after the first weekly sync has stored the most-recent 100 IDs. The paginator would bail on page 0 and never reach older history.

Pending diff in [backend/app/services/riot_api.py:232-271](../backend/app/services/riot_api.py#L232-L271) makes this explicit and adds a docstring explaining the trap. Keep it.

---

## 3. Pagination logic

```python
async def get_all_match_ids_paginated(puuid, queue=420, known_match_ids=None):
    new_ids, start, count = [], 0, 100
    while True:
        page = GET .../ids?queue={queue}&start={start}&count={count}
        if known_match_ids:
            page_new = [mid for mid in page if mid not in known_match_ids]
            new_ids.extend(page_new)
            if len(page_new) == 0: break   # early-stop: incremental mode
        else:
            new_ids.extend(page)
        if len(page) < count: break        # natural end of history
        start += count
    return new_ids
```

Two exit conditions:
1. **Natural end**: `len(page) < count` — Riot ran out of matches (or hit the ~1000 cap)
2. **Early-stop**: every ID on the page is already known (only used when `known_match_ids` is passed)

Riot has not been observed to return partial intermediate pages. If they ever did, the loop would terminate prematurely and miss history. Acceptable risk — empirical behavior is full pages until the end.

---

## 4. Eligibility rules

Decided per-match in [backend/app/services/match_eligibility.py](../backend/app/services/match_eligibility.py). Pure function: same inputs → same verdict, no DB or HTTP.

A match counts toward weekly accountability iff ALL hold:
- `queue_id` is in `COUNTING_QUEUE_IDS` (currently `{420}`)
- No PUUID on the player's team is in the global excluded-friends set
- `user_excluded` flag on the `match_history` row is `False`

To add Flex/Clash to accountability later, add the queue IDs to `COUNTING_QUEUE_IDS` — callers don't change.

Eligibility is re-evaluated every sync. If a friend is added to the excluded list AFTER a match was synced, the retroactive-exclusion block flips `user_excluded=True` on existing `match_history` rows and deletes the corresponding `weekly_champions` row.

---

## 5. Concurrency and locking

- Single shared `asyncio.Lock` on `app.state.sync_lock` (see [backend/app/main.py](../backend/app/main.py))
- Manual sync (`/sync-all`) and scheduled sync share the lock
- Whichever arrives second is rejected: manual returns 409, scheduled silently logs and skips
- Full sync uses the SAME lock. A weekly sync cannot start while a full sync is running, and vice versa.
- Inside a sync, per-player work runs concurrently via `asyncio.gather` with each player getting its own DB session
- Per-player detail calls are bounded by `asyncio.Semaphore(concurrency=5)` to stay under Riot rate limits

---

## 6. Rate limits and retry

- Riot dev key: ~20 req/sec, ~100 req/2 min — easy to hit during full sync
- Client retries on 429 up to `MAX_RETRIES=8` times, sleeping for the `Retry-After` header value (default 120 s if header is missing)
- All other non-2xx raise immediately
- `httpx.AsyncClient` reused across the whole sync via async context manager — saves TLS handshakes

---

## 7. Startup recovery

If the server restarts mid-full-sync, the `lifespan` hook in [backend/app/main.py](../backend/app/main.py) finds the orphaned `sync_runs` row (status=`running`, trigger=`full_manual`) and resumes it. Progress is polled via `GET /api/players/full-sync/status/{run_id}`.

---

## 8. Data writes per sync

For each fetched match:

1. Upsert into `match_history` (unique on `player_name, riot_match_id`). Stores champion, KDA, CS, gold, damage, vision, duration, queue_id, team_puuids, user_excluded flag.
2. Run eligibility verdict.
3. If `verdict.counts` and no `weekly_champions` row exists for `(player_name, riot_match_id)`, insert one with the correct `week_start_date` for that game's date.
4. Retroactive exclusion pass at end of sync: any existing `match_history` rows that now share an excluded PUUID get `user_excluded=True` and their `weekly_champions` row deleted.

---

## 9. Things that look like bugs but aren't

| Symptom | Explanation |
|---------|-------------|
| Full sync returns "0 new games, 2432 found" on second run | Correct — every ID is already known, dedup skipped all detail calls |
| Player's earliest game is months after team formed | Either (a) didn't play queue 420 before then, or (b) global ~1000 cap pushed older ranked games off the index. Not a code bug. |
| Manual sync returns 409 right after scheduled sync ran | Lock is held — wait for the other run to finish |
| `total_games_found` in full sync result includes already-known games | Intentional — it's `len(new) + len(known)` so the user sees total history size |

---

## 10. Things that ARE bugs to watch for

- Don't pass `known_match_ids` to `get_all_match_ids_paginated` from `fetch_all_player_games`. Early-stop will kill old-history fetches once weekly sync stores the most recent page.
- Don't forget to register `/excluded-friends` routes BEFORE `/{player_name}` in [backend/app/routers/players.py](../backend/app/routers/players.py) — FastAPI matches in registration order and the catch-all wins otherwise.
- Don't mix `startTime` units. Match-v5 expects epoch SECONDS (not milliseconds). `gameStartTimestamp` from match detail comes back in milliseconds and needs `/1000` for `datetime.fromtimestamp`.
