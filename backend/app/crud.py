import asyncio
import logging
import os
import time as _time
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, List, Optional, Set

import httpx
from sqlalchemy import desc, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas
from .database import AsyncSessionLocal
from .services import match_eligibility
from .services.charting import invalidate_chart_cache
from .services.riot_api import RiotAPIClient, RiotMatchData

logger = logging.getLogger(__name__)

# Display-form champion names that map to a different Riot Match-V5 championName.
# Riot uses Data Dragon IDs; for most champs those collapse to the same alphanumeric
# lowercase key as the display name (Kai'Sa -> "kaisa" both sides), but a few are
# renamed entirely and need an explicit alias.
_CHAMPION_NAME_ALIASES = {
    "wukong": "monkeyking",
    "nunuwillump": "nunu",
    "renataglasc": "renata",
}


def _normalize_champion_name(name: Any) -> str:
    """Canonical key for cross-source champion-name comparison.

    The match_history table stores Riot's championName (e.g. "Kaisa", "MonkeyKing");
    champion_pools stores whatever the user typed (e.g. "Kai'sa", "Wukong"). This
    function maps both forms to the same key so accountability/coverage lookups
    join correctly. Display strings are unchanged -- only the lookup key is normalized.
    """
    if not name:
        return ""
    text = str(name)
    key = "".join(ch.lower() for ch in text if ch.isalnum())
    return _CHAMPION_NAME_ALIASES.get(key, key)


# Hour (local time) at which the week resets on the configured weekday.
WEEK_RESET_HOUR = 16

WEEK_START_CACHE_TTL_SECONDS = 60


@dataclass
class _WeekStartCacheEntry:
    value: date
    expires_at: float


_week_start_cache: dict[date, _WeekStartCacheEntry] = {}


def _invalidate_week_start_cache() -> None:
    _week_start_cache.clear()


def _get_week_start(target_date: Optional[date] = None) -> date:
    """Return active week label for a target date using Python weekday numbering."""
    return _get_week_start_for_weekday(target_date=target_date, week_start_weekday=3)


def _get_week_start_for_weekday(
    target_date: Optional[date] = None,
    week_start_weekday: int = 3,
) -> date:
    """Return active week label for the configured reset weekday.

    Reset happens at WEEK_RESET_HOUR (16:00) on the configured weekday.

    When target_date is None (real-time lookup), time-of-day is considered:
    - If today IS the reset weekday and the clock has passed WEEK_RESET_HOUR,
      today is the start of the new week.
    - Otherwise today still belongs to the outgoing week.

    When target_date is explicitly provided (historical/date-only query), the
    old end-of-day convention is preserved: the reset weekday belongs to the
    outgoing week (reference = target_date - 1 day).

    Example with Thursday=3 and WEEK_RESET_HOUR=16:
    - Thursday 09:00 -> previous Thursday (outgoing week)
    - Thursday 17:00 -> this Thursday (new week)
    - Friday (any time) -> this Thursday (new week)
    """
    if target_date is None:
        now = datetime.now()
        today = now.date()
        if today.weekday() == week_start_weekday and now.hour >= WEEK_RESET_HOUR:
            # Past the reset cutoff on the reset weekday: new week has started.
            reference_date = today
        else:
            # Before the cutoff (or any other day): outgoing week still active.
            reference_date = today - timedelta(days=1)
    else:
        # Historical date-only query: model end-of-day convention with subtraction.
        reference_date = target_date - timedelta(days=1)
    days_back = (reference_date.weekday() - week_start_weekday + 7) % 7
    return reference_date - timedelta(days=days_back)


async def get_week_start_weekday_for_date(
    db: AsyncSession,
    target_date: Optional[date] = None,
) -> int:
    """Resolve configured week-start weekday for a given target date."""
    resolved_target_date = target_date or datetime.now().date()
    try:
        result = await db.execute(
            select(models.WeekResetConfig).where(
                models.WeekResetConfig.effective_from_date <= resolved_target_date,
                or_(
                    models.WeekResetConfig.effective_to_date.is_(None),
                    models.WeekResetConfig.effective_to_date >= resolved_target_date,
                ),
            ).order_by(models.WeekResetConfig.effective_from_date.desc())
        )
        version = result.scalars().first()
    except SQLAlchemyError:
        await db.rollback()
        version = None
    if version:
        return version.week_start_weekday
    # Fallback keeps existing behavior if table/rows are not present yet.
    return 3


async def get_configured_week_start(
    db: AsyncSession,
    target_date: Optional[date] = None,
) -> date:
    """Return week start for a target date based on database-configured rules.

    Handles config transitions: if the computed week start predates the active
    rule's effective_from_date, the date falls in the pre-rule overlap period.
    The prior rule's week start is returned instead, eliminating ghost weeks at
    config boundaries.
    """
    resolved_target_date = target_date or datetime.now().date()
    cache_key = resolved_target_date
    entry = _week_start_cache.get(cache_key)
    if entry and _time.monotonic() < entry.expires_at:
        return entry.value
    try:
        result = await db.execute(
            select(models.WeekResetConfig).where(
                models.WeekResetConfig.effective_from_date <= resolved_target_date,
                or_(
                    models.WeekResetConfig.effective_to_date.is_(None),
                    models.WeekResetConfig.effective_to_date >= resolved_target_date,
                ),
            ).order_by(models.WeekResetConfig.effective_from_date.desc())
        )
        rule = result.scalars().first()
    except SQLAlchemyError:
        await db.rollback()
        rule = None
    weekday = rule.week_start_weekday if rule else 3
    week_start = _get_week_start_for_weekday(
        target_date=target_date,  # Preserve None for real-time time-aware lookup.
        week_start_weekday=weekday,
    )
    # If the computed week start predates this rule's own effective_from_date, the
    # target falls in the gap before the new rule's first natural week boundary.
    # Fall back to the prior rule by recursing with the day before effective_from_date.
    if rule and week_start < rule.effective_from_date:
        return await get_configured_week_start(
            db, rule.effective_from_date - timedelta(days=1)
        )
    _week_start_cache[cache_key] = _WeekStartCacheEntry(
        value=week_start,
        expires_at=_time.monotonic() + WEEK_START_CACHE_TTL_SECONDS,
    )
    return week_start


def _get_week_start_for_datetime(
    dt: datetime,
    week_start_weekday: int,
    reset_hour: int = WEEK_RESET_HOUR,
) -> date:
    """Return week label for an absolute moment in time.

    Mirrors the real-time path of _get_week_start_for_weekday: applies the
    reset_hour cutoff to dt's clock instead of `now`. dt is treated naively
    against the server clock (Render runs UTC; Riot's gameStartTimestamp is
    epoch ms which datetime.fromtimestamp produces as naive local = UTC there).
    """
    dt_date = dt.date()
    if dt_date.weekday() == week_start_weekday and dt.hour >= reset_hour:
        reference_date = dt_date
    else:
        reference_date = dt_date - timedelta(days=1)
    days_back = (reference_date.weekday() - week_start_weekday + 7) % 7
    return reference_date - timedelta(days=days_back)


async def get_configured_week_start_for_datetime(
    db: AsyncSession,
    dt: datetime,
) -> date:
    """Return the week label for an exact moment, using DB-configured rules.

    Used so each persisted game can be filed against the week active at the
    moment it was played, regardless of when the sync run captures it. If the
    weekday or reset hour ever changes, this stays correct because it shares
    the same config source as get_configured_week_start.
    """
    target_date = dt.date()
    weekday = await get_week_start_weekday_for_date(db, target_date)
    week_start = _get_week_start_for_datetime(dt, weekday)
    try:
        result = await db.execute(
            select(models.WeekResetConfig).where(
                models.WeekResetConfig.effective_from_date <= target_date,
                or_(
                    models.WeekResetConfig.effective_to_date.is_(None),
                    models.WeekResetConfig.effective_to_date >= target_date,
                ),
            ).order_by(models.WeekResetConfig.effective_from_date.desc())
        )
        rule = result.scalars().first()
    except SQLAlchemyError:
        await db.rollback()
        rule = None
    # Pre-rule overlap fallback: if the natural week boundary lands before this
    # rule existed, fall back to the prior rule's week boundary (mirrors
    # get_configured_week_start's recursion).
    if rule and week_start < rule.effective_from_date:
        return await get_configured_week_start(
            db, rule.effective_from_date - timedelta(days=1)
        )
    return week_start


# Session Review CRUD
async def get_session_review(db: AsyncSession) -> models.SessionReview:
    """Get the single session review record"""
    result = await db.execute(select(models.SessionReview))
    return result.scalars().first()

async def update_session_review(db: AsyncSession, notes: str) -> models.SessionReview:
    """Update session review notes"""
    review = await get_session_review(db)

    if review:
        # Update existing record
        review.notes = notes
    else:
        # Create if doesn't exist
        review = models.SessionReview(notes=notes)
        db.add(review)

    await db.commit()
    await db.refresh(review)
    return review

# Weekly Champion CRUD
async def get_weekly_champions(db: AsyncSession, week_start: date) -> List[models.WeeklyChampion]:
    """Get all weekly champions for a specific week"""
    result = await db.execute(
        select(models.WeeklyChampion).where(
        models.WeeklyChampion.week_start_date == week_start
        )
    )
    return result.scalars().all()

async def upsert_weekly_champion(
    db: AsyncSession, champion_data: schemas.WeeklyChampionCreate
) -> models.WeeklyChampion:
    """Create a new played=true weekly champion record"""
    champion = models.WeeklyChampion(**champion_data.model_dump())
    db.add(champion)

    await db.commit()
    await db.refresh(champion)
    return champion

# Draft Note CRUD
async def get_draft_note(db: AsyncSession) -> models.DraftNote:
    """Get the single draft note record"""
    result = await db.execute(select(models.DraftNote))
    return result.scalars().first()

async def update_draft_note(db: AsyncSession, notes: str) -> models.DraftNote:
    """Update draft note"""
    draft_note = await get_draft_note(db)

    if draft_note:
        # Update existing record
        draft_note.notes = notes
    else:
        # Create if doesn't exist
        draft_note = models.DraftNote(notes=notes)
        db.add(draft_note)

    await db.commit()
    await db.refresh(draft_note)
    return draft_note

# Pick Stats CRUD
async def get_pick_stats(db: AsyncSession) -> List[models.PickStat]:
    """Get all pick stats with computed win rate"""
    result = await db.execute(select(models.PickStat))
    stats = list(result.scalars().all())

    # Compute win_rate for each stat
    for stat in stats:
        stat.win_rate = (
            round((stat.first_pick_wins / stat.first_pick_games) * 100, 1)
            if stat.first_pick_games > 0
            else 0.0
        )

    return stats

async def create_pick_stat(db: AsyncSession, champion_data: schemas.PickStatCreate) -> models.PickStat:
    """Create new pick stat for a champion"""
    pick_stat = models.PickStat(**champion_data.dict())
    db.add(pick_stat)
    await db.commit()
    await db.refresh(pick_stat)
    pick_stat.win_rate = 0.0
    return pick_stat

async def add_win(db: AsyncSession, pick_stat_id: int) -> models.PickStat:
    """Increment both games and wins for a champion"""
    result = await db.execute(select(models.PickStat).where(models.PickStat.id == pick_stat_id))
    pick_stat = result.scalars().first()

    if pick_stat:
        pick_stat.first_pick_games += 1
        pick_stat.first_pick_wins += 1
        await db.commit()
        await db.refresh(pick_stat)
        pick_stat.win_rate = round((pick_stat.first_pick_wins / pick_stat.first_pick_games) * 100, 1)

    return pick_stat

async def add_loss(db: AsyncSession, pick_stat_id: int) -> models.PickStat:
    """Increment only games for a champion (loss)"""
    result = await db.execute(select(models.PickStat).where(models.PickStat.id == pick_stat_id))
    pick_stat = result.scalars().first()

    if pick_stat:
        pick_stat.first_pick_games += 1
        await db.commit()
        await db.refresh(pick_stat)
        pick_stat.win_rate = (
            round((pick_stat.first_pick_wins / pick_stat.first_pick_games) * 100, 1)
            if pick_stat.first_pick_games > 0
            else 0.0
        )

    return pick_stat

async def delete_pick_stat(db: AsyncSession, pick_stat_id: int) -> bool:
    """Delete a pick stat by ID"""
    result = await db.execute(select(models.PickStat).where(models.PickStat.id == pick_stat_id))
    pick_stat = result.scalars().first()

    if pick_stat:
        await db.delete(pick_stat)
        await db.commit()
        return True

    return False

async def update_pick_stat(
    db: AsyncSession,
    pick_stat_id: int,
    update_data: schemas.PickStatUpdate
) -> Optional[models.PickStat]:
    """Update wins and/or losses for a pick stat"""
    result = await db.execute(select(models.PickStat).where(models.PickStat.id == pick_stat_id))
    pick_stat = result.scalars().first()

    if not pick_stat:
        return None

    # Update fields if provided
    if update_data.first_pick_games is not None:
        pick_stat.first_pick_games = update_data.first_pick_games
    if update_data.first_pick_wins is not None:
        pick_stat.first_pick_wins = update_data.first_pick_wins

    await db.commit()
    await db.refresh(pick_stat)

    # Compute win_rate
    pick_stat.win_rate = (
        round((pick_stat.first_pick_wins / pick_stat.first_pick_games) * 100, 1)
        if pick_stat.first_pick_games > 0
        else 0.0
    )

    return pick_stat

# Session Review Archive CRUD
async def create_session_review_archive(
    db: AsyncSession,
    title: str,
    notes: str,
    original_date: date = None
) -> models.SessionReviewArchive:
    """Create a new session review archive"""
    archive = models.SessionReviewArchive(
        title=title,
        notes=notes,
        original_date=original_date
    )
    db.add(archive)
    await db.commit()
    await db.refresh(archive)
    return archive

async def get_session_review_archives(db: AsyncSession) -> List[models.SessionReviewArchive]:
    """Get all session review archives, ordered by archived_at DESC"""
    result = await db.execute(
        select(models.SessionReviewArchive)
        .order_by(models.SessionReviewArchive.archived_at.desc())
    )
    return list(result.scalars().all())

async def get_session_review_archive_by_id(
    db: AsyncSession,
    archive_id: int
) -> models.SessionReviewArchive:
    """Get a single archive by ID"""
    result = await db.execute(
        select(models.SessionReviewArchive)
        .where(models.SessionReviewArchive.id == archive_id)
    )
    return result.scalars().first()

async def update_session_review_archive(
    db: AsyncSession,
    archive_id: int,
    title: str = None,
    notes: str = None
) -> models.SessionReviewArchive:
    """Update an existing archive"""
    archive = await get_session_review_archive_by_id(db, archive_id)

    if archive:
        if title is not None:
            archive.title = title
        if notes is not None:
            archive.notes = notes

        await db.commit()
        await db.refresh(archive)

    return archive

async def _flag_match_user_excluded(
    db: AsyncSession,
    player_name: str,
    riot_match_id: Optional[str],
) -> None:
    """If the row was synced, flag the corresponding match_history row user_excluded=True.

    The flag is sticky -- subsequent re-syncs see it and skip re-creating the weekly_champions row.
    """
    if not riot_match_id:
        return
    result = await db.execute(
        select(models.MatchHistory).where(
            models.MatchHistory.player_name == player_name,
            models.MatchHistory.riot_match_id == riot_match_id,
        )
    )
    match = result.scalar_one_or_none()
    if match is not None:
        match.user_excluded = True


async def delete_weekly_champion(
    db: AsyncSession,
    player_name: str,
    champion_name: str,
    week_start: date
) -> bool:
    """Delete ALL instances of a champion for a player in a specific week.

    Synced rows (riot_match_id IS NOT NULL) also flip match_history.user_excluded=True
    so a re-sync does not resurrect them.
    """
    result = await db.execute(
        select(models.WeeklyChampion).where(
            models.WeeklyChampion.player_name == player_name,
            models.WeeklyChampion.champion_name == champion_name,
            models.WeeklyChampion.week_start_date == week_start
        )
    )
    champions = list(result.scalars().all())

    for champ in champions:
        await _flag_match_user_excluded(db, champ.player_name, champ.riot_match_id)
        await db.delete(champ)

    await db.commit()
    return len(champions) > 0

async def delete_one_weekly_champion_instance(
    db: AsyncSession,
    player_name: str,
    champion_name: str,
    week_start: date,
    played: bool = True
) -> bool:
    """Delete ONE instance of a champion for a player in a specific week.

    If the deleted row was synced (riot_match_id IS NOT NULL), also flip
    match_history.user_excluded=True so re-syncs do not resurrect it.
    """
    result = await db.execute(
        select(models.WeeklyChampion).where(
            models.WeeklyChampion.player_name == player_name,
            models.WeeklyChampion.champion_name == champion_name,
            models.WeeklyChampion.week_start_date == week_start,
            models.WeeklyChampion.played == played
        ).limit(1)
    )
    champion = result.scalars().first()

    if champion:
        await _flag_match_user_excluded(db, champion.player_name, champion.riot_match_id)
        await db.delete(champion)
        await db.commit()
        return True

    return False

# Champion Pool CRUD
async def get_champion_pools(
    db: AsyncSession,
    player_name: Optional[str] = None,
    week_start: Optional[date] = None
) -> List[models.ChampionPool]:
    """Get champion pools, optionally filtered by player"""
    target_week_start = week_start or await get_configured_week_start(db)

    query = select(models.ChampionPool).order_by(
        models.ChampionPool.player_name,
        models.ChampionPool.champion_name
    ).where(
        models.ChampionPool.effective_from_week <= target_week_start,
        or_(
            models.ChampionPool.effective_to_week.is_(None),
            models.ChampionPool.effective_to_week >= target_week_start,
        ),
    )

    if player_name:
        query = query.where(models.ChampionPool.player_name == player_name)

    result = await db.execute(query)
    return list(result.scalars().all())

async def create_champion_pool(
    db: AsyncSession,
    pool_data: schemas.ChampionPoolCreate
) -> models.ChampionPool:
    """Create new champion pool entry"""
    current_week_start = await get_configured_week_start(db)

    existing_result = await db.execute(
        select(models.ChampionPool).where(
            models.ChampionPool.player_name == pool_data.player_name,
            models.ChampionPool.champion_name == pool_data.champion_name,
            models.ChampionPool.effective_to_week.is_(None),
        )
    )
    if existing_result.scalars().first():
        raise ValueError("Champion already exists in active pool for this player")

    pool = models.ChampionPool(
        **pool_data.model_dump(),
        effective_from_week=current_week_start,
        effective_to_week=None,
    )
    db.add(pool)
    await db.commit()
    await db.refresh(pool)
    return pool

async def update_champion_pool(
    db: AsyncSession,
    pool_id: int,
    pool_data: schemas.ChampionPoolUpdate
) -> Optional[models.ChampionPool]:
    """Update champion pool entry with week-based versioning."""
    result = await db.execute(
        select(models.ChampionPool).where(models.ChampionPool.id == pool_id)
    )
    pool = result.scalars().first()

    if not pool:
        return pool

    current_week_start = await get_configured_week_start(db)
    new_champion_name = (
        pool_data.champion_name
        if pool_data.champion_name is not None
        else pool.champion_name
    )
    new_description = (
        pool_data.description
        if pool_data.description is not None
        else pool.description
    )
    new_pick_priority = (
        pool_data.pick_priority
        if pool_data.pick_priority is not None
        else pool.pick_priority
    )
    new_disabled = (
        pool_data.disabled
        if pool_data.disabled is not None
        else pool.disabled
    )

    structural_change = (
        new_champion_name != pool.champion_name
        or new_disabled != pool.disabled
    )

    # Description/priority-only edits can stay in-place.
    if not structural_change:
        pool.description = new_description
        pool.pick_priority = new_pick_priority
        await db.commit()
        await db.refresh(pool)
        return pool

    existing_result = await db.execute(
        select(models.ChampionPool).where(
            models.ChampionPool.player_name == pool.player_name,
            models.ChampionPool.champion_name == new_champion_name,
            models.ChampionPool.effective_to_week.is_(None),
            models.ChampionPool.id != pool.id,
        )
    )
    if existing_result.scalars().first():
        raise ValueError("Champion already exists in active pool for this player")

    # If this version already started this week, update in-place.
    if pool.effective_from_week >= current_week_start:
        pool.champion_name = new_champion_name
        pool.description = new_description
        pool.pick_priority = new_pick_priority
        pool.disabled = new_disabled
        await db.commit()
        await db.refresh(pool)
        return pool

    # Close old version at the end of previous week and create the new active version.
    pool.effective_to_week = current_week_start - timedelta(days=7)
    versioned_pool = models.ChampionPool(
        player_name=pool.player_name,
        champion_name=new_champion_name,
        description=new_description,
        pick_priority=new_pick_priority,
        disabled=new_disabled,
        effective_from_week=current_week_start,
        effective_to_week=None,
    )
    db.add(versioned_pool)
    await db.commit()
    await db.refresh(versioned_pool)

    return versioned_pool

async def delete_champion_pool(
    db: AsyncSession,
    pool_id: int
) -> bool:
    """Delete champion pool entry with week-based versioning."""
    result = await db.execute(
        select(models.ChampionPool).where(models.ChampionPool.id == pool_id)
    )
    pool = result.scalars().first()

    if pool:
        current_week_start = await get_configured_week_start(db)
        if pool.effective_from_week >= current_week_start:
            await db.delete(pool)
        else:
            pool.effective_to_week = current_week_start - timedelta(days=7)
        await db.commit()
        return True

    return False

# Weekly Message CRUD
async def get_weekly_message(db: AsyncSession) -> models.WeeklyMessage:
    """Get the single weekly message record"""
    result = await db.execute(select(models.WeeklyMessage).where(models.WeeklyMessage.id == 1))
    message = result.scalar_one_or_none()
    if not message:
        # Create initial row if doesn't exist
        message = models.WeeklyMessage(id=1, message="")
        db.add(message)
        await db.commit()
        await db.refresh(message)
    return message

async def update_weekly_message(db: AsyncSession, message: str) -> models.WeeklyMessage:
    """Update weekly message"""
    weekly_message = await get_weekly_message(db)
    weekly_message.message = message
    await db.commit()
    await db.refresh(weekly_message)
    return weekly_message

# Pick Stats - Edit Champion Name
async def update_pick_stat_champion(
    db: AsyncSession,
    stat_id: int,
    new_champion_name: str
) -> models.PickStat:
    """Update champion name for a pick stat"""
    result = await db.execute(
        select(models.PickStat).where(models.PickStat.id == stat_id)
    )
    stat = result.scalar_one_or_none()
    if not stat:
        raise ValueError("Pick stat not found")

    # Check if new name already exists (different champion)
    check_result = await db.execute(
        select(models.PickStat)
        .where(models.PickStat.champion_name == new_champion_name)
        .where(models.PickStat.id != stat_id)
    )
    if check_result.scalar_one_or_none():
        raise ValueError("Champion name already exists")

    stat.champion_name = new_champion_name
    await db.commit()
    await db.refresh(stat)
    return stat

# Accountability Check CRUD
async def get_accountability_check(
    db: AsyncSession,
    week_start: Optional[date] = None
) -> List[dict]:
    """
    Check if each player has played at least 1 game on all their champions for a given week.
    Returns accountability status for all 5 players.
    Uses two bulk queries instead of per-player/per-champion queries to avoid N+1 overhead.
    """
    # Calculate target week start using configured week-boundary rules if not provided
    target_week_start = week_start or await get_configured_week_start(db)

    # IMPORTANT: Always return all 5 players
    PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

    # Bulk query 1: all active champion pool entries for the target week
    pools_result = await db.execute(
        select(models.ChampionPool).where(
            models.ChampionPool.disabled.is_(False),
            models.ChampionPool.effective_from_week <= target_week_start,
            or_(
                models.ChampionPool.effective_to_week.is_(None),
                models.ChampionPool.effective_to_week >= target_week_start,
            ),
        )
    )
    all_pool_entries = pools_result.scalars().all()

    # Build lookup: {player_name: [champion_name, ...]}
    pool_by_player: dict[str, list[str]] = {p: [] for p in PLAYERS}
    for entry in all_pool_entries:
        if entry.player_name in pool_by_player:
            pool_by_player[entry.player_name].append(entry.champion_name)

    # Bulk query 2: all played weekly_champions rows for the target week
    weekly_result = await db.execute(
        select(models.WeeklyChampion).where(
            models.WeeklyChampion.week_start_date == target_week_start,
            models.WeeklyChampion.played.is_(True),
        )
    )
    all_weekly = weekly_result.scalars().all()

    # Build lookup: {(player_name, normalized_champion_key): game_count}.
    # Normalize both sides because match_history holds Riot IDs ("Kaisa") while
    # champion_pools holds user-typed display names ("Kai'sa") -- exact-string
    # comparison would silently miss those games.
    played_counts: dict[tuple[str, str], int] = {}
    for row in all_weekly:
        key = (row.player_name, _normalize_champion_name(row.champion_name))
        played_counts[key] = played_counts.get(key, 0) + 1

    # Assemble results in Python — no more per-champion DB round-trips
    accountability_data = []

    for player in PLAYERS:
        champions = pool_by_player[player]

        if not champions:
            accountability_data.append({
                "player_name": player,
                "all_champions_played": False,
                "missing_champions": [],
                "total_champions": 0,
                "champions_played": 0,
                "champion_details": [],
            })
            continue

        missing_champions = []
        champion_details = []

        for champion_name in champions:
            games_played = played_counts.get(
                (player, _normalize_champion_name(champion_name)), 0
            )
            has_played = games_played > 0

            if not has_played:
                missing_champions.append(champion_name)

            champion_details.append({
                "champion_name": champion_name,
                "has_played": has_played,
                "games_played": games_played,
            })

        all_champions_played = len(missing_champions) == 0

        accountability_data.append({
            "player_name": player,
            "all_champions_played": all_champions_played,
            "missing_champions": missing_champions,
            "total_champions": len(champions),
            "champions_played": len(champions) - len(missing_champions),
            "champion_details": champion_details,
        })

    return accountability_data

async def get_accountability_debug_data(db: AsyncSession) -> dict:
    """
    Get raw database data for accountability debugging.
    Returns champion pools and weekly champions for current week.
    """
    # Calculate current week start using configured week-boundary rules
    week_start = await get_configured_week_start(db)

    # Get all champion pool entries
    pools_result = await db.execute(
        select(models.ChampionPool).order_by(
            models.ChampionPool.player_name,
            models.ChampionPool.champion_name
        )
    )
    champion_pools = pools_result.scalars().all()

    # Get all weekly champions for current week
    weekly_result = await db.execute(
        select(models.WeeklyChampion).where(
            models.WeeklyChampion.week_start_date == week_start
        ).order_by(
            models.WeeklyChampion.player_name,
            models.WeeklyChampion.champion_name
        )
    )
    weekly_champions = weekly_result.scalars().all()

    return {
        "week_start": week_start.isoformat(),
        "champion_pools": [
            {
                "id": p.id,
                "player_name": p.player_name,
                "champion_name": p.champion_name,
                "description": p.description,
                "pick_priority": p.pick_priority,
                "effective_from_week": p.effective_from_week.isoformat(),
                "effective_to_week": p.effective_to_week.isoformat() if p.effective_to_week else None,
            }
            for p in champion_pools
        ],
        "weekly_champions": [
            {
                "id": w.id,
                "player_name": w.player_name,
                "champion_name": w.champion_name,
                "played": w.played,
                "week_start_date": w.week_start_date.isoformat()
            }
            for w in weekly_champions
        ]
    }


# Week Boundary Config CRUD
async def list_week_reset_configs(
    db: AsyncSession,
) -> List[models.WeekResetConfig]:
    """Return all week-reset configs ordered by effective start date descending."""
    result = await db.execute(
        select(models.WeekResetConfig).order_by(
            models.WeekResetConfig.effective_from_date.desc()
        )
    )
    return list(result.scalars().all())


async def get_current_week_config(
    db: AsyncSession,
    target_date: Optional[date] = None,
) -> dict:
    """Return resolved week-start config for a target date."""
    resolved_target_date = target_date or datetime.now().date()
    week_start_date = await get_configured_week_start(
        db=db,
        target_date=resolved_target_date,
    )
    # Derive weekday from the resolved date so transition weeks report the correct day.
    week_start_weekday = week_start_date.weekday()
    weekday_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    return {
        "target_date": resolved_target_date,
        "week_start_date": week_start_date,
        "week_start_weekday": week_start_weekday,
        "week_start_day_name": weekday_names[week_start_weekday],
    }


# Analytics CRUD
async def get_weekly_trends(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    player_name: Optional[str] = None
) -> List[dict]:
    """Get weekly played-game counts grouped by week and player."""
    query = select(models.WeeklyChampion).where(
        models.WeeklyChampion.week_start_date >= start_date,
        models.WeeklyChampion.week_start_date <= end_date,
        models.WeeklyChampion.played.is_(True)
    )

    if player_name:
        query = query.where(models.WeeklyChampion.player_name == player_name)

    result = await db.execute(query)
    rows = result.scalars().all()

    trend_map: dict[tuple[date, str], int] = {}
    for row in rows:
        key = (row.week_start_date, row.player_name)
        trend_map[key] = trend_map.get(key, 0) + 1

    return [
        {
            "week_start_date": week_start,
            "player_name": player,
            "games_played": games_played,
        }
        for (week_start, player), games_played in sorted(trend_map.items(), key=lambda item: (item[0][0], item[0][1]))
    ]


async def get_practice_vs_winrate_data(db: AsyncSession) -> List[dict]:
    """
    Combine weekly champion data (practice volume) and pick stats (win rate).
    Returns list of champions with both metrics.
    """
    weekly_result = await db.execute(
        select(models.WeeklyChampion).where(models.WeeklyChampion.played.is_(True))
    )
    weekly_rows = weekly_result.scalars().all()

    practice_map: dict[str, int] = {}
    for row in weekly_rows:
        practice_map[row.champion_name] = practice_map.get(row.champion_name, 0) + 1

    # Get pick stats
    stats_result = await db.execute(select(models.PickStat))
    stats = list(stats_result.scalars().all())

    # Combine
    combined_data = []
    all_champions = set(practice_map.keys()) | set(s.champion_name for s in stats)

    stat_map = {s.champion_name: s for s in stats}

    for champ_name in all_champions:
        practice_count = practice_map.get(champ_name, 0)
        stat = stat_map.get(champ_name)

        if stat:
            win_rate = (
                round((stat.first_pick_wins / stat.first_pick_games) * 100, 1)
                if stat.first_pick_games > 0
                else 0.0
            )
            games_played = stat.first_pick_games
            wins = stat.first_pick_wins
        else:
            win_rate = 0.0
            games_played = 0
            wins = 0

        combined_data.append({
            "champion_name": champ_name,
            "total_practice_games": practice_count,
            "pick_stat_games": games_played,
            "pick_stat_wins": wins,
            "win_rate": win_rate
        })

    return combined_data


# Fine CRUD (Bødekasse)
async def get_fines(db: AsyncSession) -> List[models.Fine]:
    """Get all fines ordered by creation date (newest first)"""
    result = await db.execute(
        select(models.Fine).order_by(models.Fine.created_at.desc())
    )
    return list(result.scalars().all())


async def get_fines_summary(db: AsyncSession) -> List[dict]:
    """Get all fines grouped by player with totals"""
    # Get all fines
    result = await db.execute(
        select(models.Fine).order_by(models.Fine.created_at.desc())
    )
    fines = list(result.scalars().all())

    # Group by player
    from collections import defaultdict
    player_fines = defaultdict(list)
    for fine in fines:
        player_fines[fine.player_name].append(fine)

    # Build summary for each player that has fines
    summaries = []
    for player_name, player_fine_list in player_fines.items():
        total_amount = sum(f.amount for f in player_fine_list)
        summaries.append({
            "player_name": player_name,
            "total_amount": total_amount,
            "fines": player_fine_list
        })

    # Sort by player name for consistent ordering
    summaries.sort(key=lambda x: x["player_name"])

    return summaries


async def create_fine(
    db: AsyncSession,
    fine_data: schemas.FineCreate
) -> models.Fine:
    """Create a new fine"""
    fine = models.Fine(**fine_data.model_dump())
    db.add(fine)
    await db.commit()
    await db.refresh(fine)
    return fine


async def delete_fine(db: AsyncSession, fine_id: int) -> bool:
    """Delete a fine by ID"""
    result = await db.execute(
        select(models.Fine).where(models.Fine.id == fine_id)
    )
    fine = result.scalars().first()

    if fine:
        await db.delete(fine)
        await db.commit()
        return True

    return False


async def get_pool_coverage(
    db: AsyncSession,
    week_start: date
) -> List[dict]:
    """
    Calculate what percentage of their champion pool each player has played this week.
    """
    # 1. Get all pools
    pools_result = await db.execute(
        select(models.ChampionPool).where(
            models.ChampionPool.effective_from_week <= week_start,
            or_(
                models.ChampionPool.effective_to_week.is_(None),
                models.ChampionPool.effective_to_week >= week_start,
            ),
        )
    )
    pools = list(pools_result.scalars().all())
    
    player_stats = {} # player -> {pool_size, played_count, played_champs_set}
    
    # Initialize players
    for p in pools:
        if p.player_name not in player_stats:
            player_stats[p.player_name] = {
                "pool_size": 0,
                "played_count": 0,
                "played_unique": 0,
                "pool_champs": set(),
                "played_champs": set()
            }
        player_stats[p.player_name]["pool_size"] += 1
        player_stats[p.player_name]["pool_champs"].add(_normalize_champion_name(p.champion_name))

    qry = select(models.WeeklyChampion).where(
        models.WeeklyChampion.week_start_date == week_start,
        models.WeeklyChampion.played.is_(True)
    )
    res = await db.execute(qry)
    played_rows = res.scalars().all()

    for row in played_rows:
        if row.player_name in player_stats:
            player_stats[row.player_name]["played_champs"].add(_normalize_champion_name(row.champion_name))

    # Calculate coverage
    results = []
    for player, data in player_stats.items():
        # Intersection of pool champs and played champs
        played_from_pool = data["pool_champs"].intersection(data["played_champs"])
        
        coverage_pct = 0.0
        if data["pool_size"] > 0:
            coverage_pct = round((len(played_from_pool) / data["pool_size"]) * 100, 1)
            
        results.append({
            "player_name": player,
            "pool_size": data["pool_size"],
            "unique_champions_played": len(data["played_champs"]),
            "pool_champions_played": len(played_from_pool),
            "coverage_percent": coverage_pct
        })

    return results


# Clash Dates CRUD
async def get_clash_dates(db: AsyncSession) -> models.ClashDates:
    """Get the clash dates (singleton record)"""
    result = await db.execute(select(models.ClashDates).where(models.ClashDates.id == 1))
    clash_dates = result.scalar_one_or_none()
    if not clash_dates:
        # Create initial row if doesn't exist
        clash_dates = models.ClashDates(id=1, date1=None, date2=None)
        db.add(clash_dates)
        await db.commit()
        await db.refresh(clash_dates)
    return clash_dates


async def update_clash_dates(
    db: AsyncSession,
    date1: Optional[date],
    date2: Optional[date]
) -> models.ClashDates:
    """Update clash dates"""
    clash_dates = await get_clash_dates(db)
    clash_dates.date1 = date1
    clash_dates.date2 = date2
    await db.commit()
    await db.refresh(clash_dates)
    return clash_dates

# --- Player CRUD -------------------------------------------------------------


async def get_players(db: AsyncSession) -> List[models.Player]:
    """Return all roster players ordered by id (insertion order)."""
    result = await db.execute(select(models.Player).order_by(models.Player.id))
    return list(result.scalars().all())


async def get_player_names(db: AsyncSession) -> List[str]:
    """Return list of roster player names (legacy helper)."""
    result = await db.execute(
        select(models.Player.player_name).order_by(models.Player.id)
    )
    return list(result.scalars().all())


async def get_player_by_name(
    db: AsyncSession, player_name: str
) -> Optional[models.Player]:
    """Return the Player row whose player_name matches (case-sensitive)."""
    result = await db.execute(
        select(models.Player).where(models.Player.player_name == player_name)
    )
    return result.scalar_one_or_none()


async def update_player(
    db: AsyncSession,
    player_name: str,
    update_data: schemas.PlayerUpdate,
) -> Optional[models.Player]:
    """Update riot_id/region for a player. Clears cached PUUID if riot_id changes."""
    player = await get_player_by_name(db, player_name)
    if not player:
        return None

    if update_data.riot_id is not None and update_data.riot_id != player.riot_id:
        player.riot_id = update_data.riot_id or None
        # Clear cached PUUID -- it's tied to the previous Riot ID account.
        player.puuid = None
    if update_data.region is not None:
        player.region = update_data.region

    await db.commit()
    await db.refresh(player)
    return player


# --- Match History CRUD ------------------------------------------------------


async def get_match_history(
    db: AsyncSession,
    player_name: str,
    week_start: Optional[date] = None,
) -> List[models.MatchHistory]:
    """Return match history rows for a player, optionally filtered to a single week."""
    query = select(models.MatchHistory).where(
        models.MatchHistory.player_name == player_name
    )
    if week_start is not None:
        query = query.where(models.MatchHistory.week_start_date == week_start)
    query = query.order_by(models.MatchHistory.game_start_time.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def exclude_match(
    db: AsyncSession,
    match_id: int,
    player_name: str,
) -> bool:
    """Mark a match as user-excluded and remove any linked weekly_champions entry.

    Sets user_excluded=True so re-syncs do not resurrect it, then deletes the
    associated weekly_champions row (if one exists) so it no longer counts toward
    accountability.
    """
    result = await db.execute(
        select(models.MatchHistory).where(
            models.MatchHistory.id == match_id,
            models.MatchHistory.player_name == player_name,
        )
    )
    match = result.scalar_one_or_none()
    if match is None:
        return False

    match.user_excluded = True

    if match.riot_match_id:
        wc_result = await db.execute(
            select(models.WeeklyChampion).where(
                models.WeeklyChampion.player_name == player_name,
                models.WeeklyChampion.riot_match_id == match.riot_match_id,
            )
        )
        wc = wc_result.scalar_one_or_none()
        if wc is not None:
            await db.delete(wc)

    await db.commit()
    return True


async def get_match_history_for_week(
    db: AsyncSession,
    player_name: str,
    week_start: date,
) -> List[models.MatchHistory]:
    """Return all match_history rows for a player in a given week."""
    return await get_match_history(db, player_name=player_name, week_start=week_start)


async def get_existing_match_ids(
    db: AsyncSession,
    player_name: str,
) -> Set[str]:
    """Return the set of all riot_match_ids already stored for a player.

    Spans every week. The unique constraint uq_player_match is week-agnostic,
    so dedup must be too -- otherwise a game stored under one week label can be
    re-fetched and re-INSERTed under a different label, hitting the constraint
    and rolling back the whole player's sync.
    """
    result = await db.execute(
        select(models.MatchHistory.riot_match_id).where(
            models.MatchHistory.player_name == player_name,
        )
    )
    return set(result.scalars().all())


async def weekly_champions_row_exists(
    db: AsyncSession,
    player_name: str,
    riot_match_id: str,
) -> bool:
    """True if a weekly_champions row already references this riot_match_id for the player."""
    result = await db.execute(
        select(models.WeeklyChampion.id).where(
            models.WeeklyChampion.player_name == player_name,
            models.WeeklyChampion.riot_match_id == riot_match_id,
        )
    )
    return result.first() is not None


# --- Excluded Friends CRUD ---------------------------------------------------


async def get_excluded_friends(
    db: AsyncSession,
    player_name: str,
) -> List[models.ExcludedFriend]:
    """Return the excluded-friends list owned by the given roster player."""
    result = await db.execute(
        select(models.ExcludedFriend)
        .where(models.ExcludedFriend.player_name == player_name)
        .order_by(models.ExcludedFriend.id)
    )
    return list(result.scalars().all())


async def add_excluded_friend(
    db: AsyncSession,
    player_name: str,
    riot_id: str,
    region: str = "euw",
) -> models.ExcludedFriend:
    """Add a friend whose presence on the player's team excludes the match.

    PUUID resolution is intentionally lazy -- a mistyped Riot ID should not fail
    the form submission, just sit unresolved until the next sync.
    """
    friend = models.ExcludedFriend(
        player_name=player_name,
        riot_id=riot_id.strip(),
        region=region,
    )
    db.add(friend)
    await db.commit()
    await db.refresh(friend)
    return friend


async def remove_excluded_friend(
    db: AsyncSession,
    player_name: str,
    friend_id: int,
) -> bool:
    """Remove an excluded-friend row (scoped to its owning player)."""
    result = await db.execute(
        select(models.ExcludedFriend).where(
            models.ExcludedFriend.id == friend_id,
            models.ExcludedFriend.player_name == player_name,
        )
    )
    friend = result.scalar_one_or_none()
    if not friend:
        return False
    await db.delete(friend)
    await db.commit()
    return True


async def get_all_excluded_friends_global(
    db: AsyncSession,
) -> List[models.ExcludedFriend]:
    """Return all global excluded-friend rows (one per riot_id)."""
    result = await db.execute(
        select(models.ExcludedFriend).order_by(models.ExcludedFriend.riot_id)
    )
    return list(result.scalars().all())


async def add_excluded_friend_global(
    db: AsyncSession,
    riot_id: str,
    region: str = "euw",
) -> models.ExcludedFriend:
    """Add a global excluded friend (one row, not tied to any roster player)."""
    friend = models.ExcludedFriend(
        player_name="global",
        riot_id=riot_id.strip(),
        region=region,
    )
    db.add(friend)
    await db.commit()
    await db.refresh(friend)
    return friend


async def remove_excluded_friend_by_id(
    db: AsyncSession,
    friend_id: int,
) -> bool:
    """Remove a global excluded-friend row by id."""
    friend = await db.get(models.ExcludedFriend, friend_id)
    if not friend:
        return False
    await db.delete(friend)
    await db.commit()
    return True


# --- Sync Run CRUD -----------------------------------------------------------


async def get_last_successful_sync(db: AsyncSession) -> Optional[datetime]:
    """Return finished_at of the most recent successful sync_runs row (or None)."""
    result = await db.execute(
        select(models.SyncRun.finished_at)
        .where(models.SyncRun.status == "success")
        .where(models.SyncRun.finished_at.is_not(None))
        .order_by(desc(models.SyncRun.finished_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


# --- Sync Flow ---------------------------------------------------------------


async def exclude_synced_weekly_champion(
    db: AsyncSession, weekly_id: int
) -> bool:
    """Delete a weekly_champions row and (if synced) flag the match as user_excluded.

    The sticky flag means a subsequent re-sync will not resurrect the row.
    """
    row = await db.get(models.WeeklyChampion, weekly_id)
    if row is None:
        return False
    riot_match_id = row.riot_match_id
    player_name = row.player_name
    await db.delete(row)

    if riot_match_id:
        result = await db.execute(
            select(models.MatchHistory).where(
                models.MatchHistory.player_name == player_name,
                models.MatchHistory.riot_match_id == riot_match_id,
            )
        )
        match = result.scalar_one_or_none()
        if match is not None:
            match.user_excluded = True

    await db.commit()
    return True


async def sync_player_games(
    db: AsyncSession,
    player_name: str,
    week_start: Optional[date] = None,
    riot_client: Optional[RiotAPIClient] = None,
) -> schemas.SyncResult:
    """Fetch games from Riot API, persist match_history, create weekly_champions for eligible games.

    Eligibility (queue + premade exclusion + user override) is delegated to
    services.match_eligibility -- this function only orchestrates fetch+persist.
    """
    player = await get_player_by_name(db, player_name)
    if not player:
        raise ValueError(f"Player {player_name} not found")
    if not player.riot_id:
        raise ValueError(f"Player {player_name} has no riot_id set")

    target_week_start = week_start or await get_configured_week_start(db)

    _own_client = riot_client is None
    if _own_client:
        api_key = os.getenv("RIOT_API_KEY")
        if not api_key:
            raise ValueError("RIOT_API_KEY is not configured on the server")
        riot_client = RiotAPIClient(api_key=api_key)
        await riot_client.__aenter__()

    # 1. Resolve & cache the roster player's PUUID.
    if not player.puuid:
        if "#" not in player.riot_id:
            raise ValueError(
                f"Player {player_name} riot_id must be in 'Name#Tag' format"
            )
        game_name, tag_line = player.riot_id.split("#", 1)
        player.puuid = await riot_client.get_puuid(game_name.strip(), tag_line.strip())
        await db.commit()
    puuid = player.puuid

    # 2. Resolve & cache excluded-friend PUUIDs (lazy, one Account-V1 call per friend, first time only).
    excluded_friends = await get_all_excluded_friends_global(db)
    for friend in excluded_friends:
        if friend.puuid:
            continue
        if "#" not in friend.riot_id:
            continue
        try:
            fg, ft = friend.riot_id.split("#", 1)
            friend.puuid = await riot_client.get_puuid(fg.strip(), ft.strip())
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Could not resolve excluded friend %s for %s: %s",
                friend.riot_id, player_name, exc,
            )
        except Exception as exc:  # noqa: BLE001 -- never fail sync over one bad friend
            logger.warning(
                "Unexpected error resolving excluded friend %s for %s: %s",
                friend.riot_id, player_name, exc,
            )
    await db.commit()
    excluded_puuids = frozenset(f.puuid for f in excluded_friends if f.puuid)

    # 3. Load known match IDs from DB so we can skip fetching their details.
    #    Cross-week: a game played close to the reset cutoff can be stored under
    #    the previous week's label. The unique constraint is week-agnostic, so
    #    the dedup set must span all weeks for this player.
    known_ids = await get_existing_match_ids(db, player_name)

    # 4. Fetch only new games from Riot API (detail calls skipped for known IDs).
    games: List[RiotMatchData] = await riot_client.fetch_player_games(
        puuid, since_date=target_week_start, known_match_ids=known_ids
    )

    # 5. Load full existing match_history for dedup + user_excluded re-evaluation.
    existing_matches = await get_match_history_for_week(db, player_name, target_week_start)
    existing_by_id = {m.riot_match_id: m for m in existing_matches}

    games_synced = 0
    games_excluded = 0
    games_already_present = 0

    for game in games:
        existing = existing_by_id.get(game.riot_match_id)

        if existing is None:
            # Derive week_start from when the game was played, not from the
            # sync run's target_week_start. A game finishing seconds before the
            # reset cutoff but synced seconds after must still land in the
            # outgoing week.
            game_week_start = await get_configured_week_start_for_datetime(
                db, game.game_start_time
            )
            existing = models.MatchHistory(
                player_name=player_name,
                riot_match_id=game.riot_match_id,
                champion_name=game.champion_name,
                won=game.won,
                kills=game.kills,
                deaths=game.deaths,
                assists=game.assists,
                cs=game.cs,
                vision_score=game.vision_score,
                gold_earned=game.gold_earned,
                damage_to_champions=game.damage_to_champions,
                game_duration_seconds=game.game_duration_seconds,
                team_position=game.team_position,
                game_start_time=game.game_start_time,
                week_start_date=game_week_start,
                queue_id=game.queue_id,
                team_puuids=list(game.team_puuids),
                user_excluded=False,
                is_remake=game.is_remake,
            )
            db.add(existing)
            existing_by_id[game.riot_match_id] = existing

        verdict = match_eligibility.evaluate_match(
            queue_id=game.queue_id,
            team_puuids=game.team_puuids,
            excluded_puuids=excluded_puuids,
            user_excluded=bool(existing.user_excluded),
            is_remake=bool(existing.is_remake),
        )

        if not verdict.counts:
            games_excluded += 1
            continue

        # Flush pending inserts so the existence check below sees them.
        await db.flush()

        if await weekly_champions_row_exists(
            db, player_name=player_name, riot_match_id=game.riot_match_id
        ):
            games_already_present += 1
            continue

        db.add(
            models.WeeklyChampion(
                player_name=player_name,
                champion_name=game.champion_name,
                played=True,
                week_start_date=target_week_start,
                won=game.won,
                riot_match_id=game.riot_match_id,
            )
        )
        games_synced += 1

    # Retroactive exclusion: remove weekly_champions rows for any previously-synced
    # games that now involve an excluded friend (handles friends added after initial sync).
    if excluded_puuids:
        await db.flush()
        all_week_matches = await get_match_history_for_week(db, player_name, target_week_start)
        for match in all_week_matches:
            if match.user_excluded:
                continue
            if not (set(match.team_puuids or []) & excluded_puuids):
                continue
            match.user_excluded = True
            wc_retro = await db.execute(
                select(models.WeeklyChampion).where(
                    models.WeeklyChampion.player_name == player_name,
                    models.WeeklyChampion.riot_match_id == match.riot_match_id,
                )
            )
            wc_row = wc_retro.scalar_one_or_none()
            if wc_row is not None:
                await db.delete(wc_row)

    await db.commit()

    if _own_client:
        await riot_client.__aexit__(None, None, None)
    return schemas.SyncResult(
        player_name=player_name,
        games_synced=games_synced,
        games_excluded=games_excluded,
        games_already_present=games_already_present,
        total_games_found=len(games),
        message=(
            f"Synced {games_synced} new games "
            f"({games_excluded} excluded by eligibility, "
            f"{games_already_present} already present, "
            f"{len(games)} total found this week)"
        ),
    )


async def sync_all_players(
    db: AsyncSession,
    trigger: str = "manual",
    week_start: Optional[date] = None,
) -> schemas.SyncAllResult:
    """Run sync_player_games for every roster player with a riot_id set.

    Persists a sync_runs row for the run. Failures of individual player syncs
    are isolated -- the rest of the players still sync, and the failed player
    is recorded in failed_players.
    """
    started_at = datetime.now(timezone.utc)
    run = models.SyncRun(
        started_at=started_at,
        trigger=trigger,
        status="running",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    players = await get_players(db)
    eligible_players = [p for p in players if p.riot_id]

    api_key = os.getenv("RIOT_API_KEY")
    _client_ctx = RiotAPIClient(api_key=api_key) if api_key else nullcontext(None)

    per_player: List[schemas.SyncResult] = []
    failed_players: List[str] = []

    async with _client_ctx as riot_client:
        async def _sync_one(player_name: str) -> schemas.SyncResult:
            """Sync a single player using a dedicated DB session."""
            async with AsyncSessionLocal() as player_db:
                return await sync_player_games(
                    player_db,
                    player_name=player_name,
                    week_start=week_start,
                    riot_client=riot_client,
                )

        raw_results = await asyncio.gather(
            *[_sync_one(p.player_name) for p in eligible_players],
            return_exceptions=True,
        )

    for player, result in zip(eligible_players, raw_results):
        if isinstance(result, Exception):
            logger.exception("Sync failed for %s: %s", player.player_name, result)
            failed_players.append(player.player_name)
            per_player.append(
                schemas.SyncResult(
                    player_name=player.player_name,
                    games_synced=0,
                    games_excluded=0,
                    games_already_present=0,
                    total_games_found=0,
                    message=f"Failed: {result}",
                )
            )
        else:
            per_player.append(result)

    finished_at = datetime.now(timezone.utc)
    total_games_synced = sum(r.games_synced for r in per_player)
    total_games_excluded = sum(r.games_excluded for r in per_player)
    total_games_already_present = sum(r.games_already_present for r in per_player)
    total_games_found = sum(r.total_games_found for r in per_player)

    if failed_players and len(failed_players) == len(eligible_players):
        status = "failed"
    elif failed_players:
        status = "partial"
    else:
        status = "success"

    summary = schemas.SyncAllResult(
        trigger=trigger,
        started_at=started_at,
        finished_at=finished_at,
        per_player=per_player,
        total_games_synced=total_games_synced,
        total_games_excluded=total_games_excluded,
        total_games_already_present=total_games_already_present,
        total_games_found=total_games_found,
        failed_players=failed_players,
        message=(
            f"{trigger} sync: {total_games_synced} games synced across "
            f"{len(eligible_players) - len(failed_players)} players"
            + (f", {len(failed_players)} failed" if failed_players else "")
        ),
    )

    run.finished_at = finished_at
    run.status = status
    run.summary = summary.model_dump(mode="json")
    await db.commit()
    invalidate_chart_cache()

    return summary


async def full_sync_player_games(
    db: AsyncSession,
    player_name: str,
    riot_client: Optional[RiotAPIClient] = None,
) -> schemas.SyncResult:
    """Fetch the full ranked match history for a player with no date limit.

    Paginates through all available match IDs, skips any already stored in the
    database, then fetches details with rate limiting between calls to respect
    the 100 requests / 2 minute Riot API rate limit.
    """
    player = await get_player_by_name(db, player_name)
    if not player:
        raise ValueError(f"Player {player_name} not found")
    if not player.riot_id:
        raise ValueError(f"Player {player_name} has no riot_id set")

    _own_client = riot_client is None
    if _own_client:
        api_key = os.getenv("RIOT_API_KEY")
        if not api_key:
            raise ValueError("RIOT_API_KEY is not configured on the server")
        riot_client = RiotAPIClient(api_key=api_key)
        await riot_client.__aenter__()

    # 1. Resolve & cache PUUID.
    if not player.puuid:
        if "#" not in player.riot_id:
            raise ValueError(
                f"Player {player_name} riot_id must be in 'Name#Tag' format"
            )
        game_name, tag_line = player.riot_id.split("#", 1)
        player.puuid = await riot_client.get_puuid(game_name.strip(), tag_line.strip())
        await db.commit()
    puuid = player.puuid

    # 2. Resolve & cache excluded-friend PUUIDs.
    excluded_friends = await get_all_excluded_friends_global(db)
    for friend in excluded_friends:
        if friend.puuid or "#" not in friend.riot_id:
            continue
        try:
            fg, ft = friend.riot_id.split("#", 1)
            friend.puuid = await riot_client.get_puuid(fg.strip(), ft.strip())
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not resolve excluded friend %s for %s: %s",
                friend.riot_id, player_name, exc,
            )
    await db.commit()
    excluded_puuids = frozenset(f.puuid for f in excluded_friends if f.puuid)

    # 3. Load ALL known match IDs from DB (across every week, not just current).
    all_known_result = await db.execute(
        select(models.MatchHistory.riot_match_id).where(
            models.MatchHistory.player_name == player_name
        )
    )
    known_ids: Set[str] = set(all_known_result.scalars().all())

    # 4. Fetch all new games from Riot API with rate limiting.
    games: List[RiotMatchData] = await riot_client.fetch_all_player_games(
        puuid, known_match_ids=known_ids
    )

    if not games:
        if _own_client:
            await riot_client.__aexit__(None, None, None)
        return schemas.SyncResult(
            player_name=player_name,
            games_synced=0,
            games_excluded=0,
            games_already_present=0,
            total_games_found=len(known_ids),
            message=f"No new games found (all {len(known_ids)} already synced)",
        )

    # 5. Pre-compute week_start for each unique game date (batch to avoid N+1 queries).
    unique_dates = {g.game_start_time.date() for g in games}
    week_start_cache: dict[date, date] = {}
    for d in unique_dates:
        week_start_cache[d] = await get_configured_week_start(db, target_date=d)

    # 6. Load existing match_history for dedup.
    existing_result = await db.execute(
        select(models.MatchHistory).where(
            models.MatchHistory.player_name == player_name
        )
    )
    existing_by_id = {m.riot_match_id: m for m in existing_result.scalars().all()}

    games_synced = 0
    games_excluded = 0
    games_already_present = 0

    for game in games:
        game_week_start = week_start_cache[game.game_start_time.date()]
        existing = existing_by_id.get(game.riot_match_id)

        if existing is None:
            existing = models.MatchHistory(
                player_name=player_name,
                riot_match_id=game.riot_match_id,
                champion_name=game.champion_name,
                won=game.won,
                kills=game.kills,
                deaths=game.deaths,
                assists=game.assists,
                cs=game.cs,
                vision_score=game.vision_score,
                gold_earned=game.gold_earned,
                damage_to_champions=game.damage_to_champions,
                game_duration_seconds=game.game_duration_seconds,
                team_position=game.team_position,
                game_start_time=game.game_start_time,
                week_start_date=game_week_start,
                queue_id=game.queue_id,
                team_puuids=list(game.team_puuids),
                user_excluded=False,
                is_remake=game.is_remake,
            )
            db.add(existing)
            existing_by_id[game.riot_match_id] = existing

        verdict = match_eligibility.evaluate_match(
            queue_id=game.queue_id,
            team_puuids=game.team_puuids,
            excluded_puuids=excluded_puuids,
            user_excluded=bool(existing.user_excluded),
            is_remake=bool(existing.is_remake),
        )

        if not verdict.counts:
            games_excluded += 1
            continue

        await db.flush()

        if await weekly_champions_row_exists(
            db, player_name=player_name, riot_match_id=game.riot_match_id
        ):
            games_already_present += 1
            continue

        db.add(
            models.WeeklyChampion(
                player_name=player_name,
                champion_name=game.champion_name,
                played=True,
                week_start_date=game_week_start,
                won=game.won,
                riot_match_id=game.riot_match_id,
            )
        )
        games_synced += 1

    # Retroactive exclusion: remove weekly_champions rows for any previously-synced
    # games that now involve an excluded friend (handles friends added after initial sync).
    if excluded_puuids:
        await db.flush()
        all_match_result = await db.execute(
            select(models.MatchHistory).where(
                models.MatchHistory.player_name == player_name,
                models.MatchHistory.user_excluded.is_(False),
            )
        )
        all_matches = list(all_match_result.scalars().all())
        for match in all_matches:
            if not (set(match.team_puuids or []) & excluded_puuids):
                continue
            match.user_excluded = True
            wc_retro = await db.execute(
                select(models.WeeklyChampion).where(
                    models.WeeklyChampion.player_name == player_name,
                    models.WeeklyChampion.riot_match_id == match.riot_match_id,
                )
            )
            wc_row = wc_retro.scalar_one_or_none()
            if wc_row is not None:
                await db.delete(wc_row)

    await db.commit()

    if _own_client:
        await riot_client.__aexit__(None, None, None)
    return schemas.SyncResult(
        player_name=player_name,
        games_synced=games_synced,
        games_excluded=games_excluded,
        games_already_present=games_already_present,
        total_games_found=len(games) + len(known_ids),
        message=(
            f"Full sync: {games_synced} new games synced "
            f"({games_excluded} excluded, {games_already_present} already present, "
            f"{len(games)} new from Riot API)"
        ),
    )


async def full_sync_all_players(
    db: AsyncSession,
    trigger: str = "full_manual",
    run_id: Optional[int] = None,
) -> schemas.SyncAllResult:
    """Run full_sync_player_games sequentially for every roster player with a riot_id.

    Sequential execution (instead of asyncio.gather) is deliberate: the full
    history fetch issues many detail calls per player and must respect the
    100 requests / 2 minute Riot API rate limit across all players combined.

    Writes incremental progress to sync_runs.progress after each player so that
    the status polling endpoint can surface live updates.

    If run_id is provided (pre-created by the background-task endpoint), reuses
    that row instead of creating a new one.
    """
    started_at = datetime.now(timezone.utc)

    if run_id is not None:
        result = await db.execute(
            select(models.SyncRun).where(models.SyncRun.id == run_id)
        )
        run = result.scalar_one()
    else:
        run = models.SyncRun(
            started_at=started_at,
            trigger=trigger,
            status="running",
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

    players = await get_players(db)
    eligible_players = [p for p in players if p.riot_id]

    api_key = os.getenv("RIOT_API_KEY")
    _client_ctx = RiotAPIClient(api_key=api_key) if api_key else nullcontext(None)

    per_player: List[schemas.SyncResult] = []
    failed_players: List[str] = []
    games_synced_so_far = 0
    games_found_so_far = 0
    completed_players: List[str] = []

    # On restart recovery: skip players already completed in a previous run.
    existing_progress = run.progress or {}
    completed_players = list(existing_progress.get("completed_players", []))
    skipped = set(completed_players)

    async with _client_ctx as riot_client:
        for idx, player in enumerate(eligible_players):
            if player.player_name in skipped:
                logger.info("Full sync: skipping already-completed player %s", player.player_name)
                continue

            # Write progress before starting this player so polling sees who's active.
            run.progress = schemas.FullSyncProgress(
                players_total=len(eligible_players),
                players_done=len(completed_players),
                current_player=player.player_name,
                games_synced_so_far=games_synced_so_far,
                games_found_so_far=games_found_so_far,
                completed_players=completed_players,
            ).model_dump()
            await db.commit()

            try:
                async with AsyncSessionLocal() as player_db:
                    result = await full_sync_player_games(
                        player_db,
                        player_name=player.player_name,
                        riot_client=riot_client,
                    )
                per_player.append(result)
                games_synced_so_far += result.games_synced
                games_found_so_far += result.total_games_found
                completed_players.append(player.player_name)
            except Exception as exc:
                logger.exception("Full sync failed for %s: %s", player.player_name, exc)
                failed_players.append(player.player_name)
                per_player.append(
                    schemas.SyncResult(
                        player_name=player.player_name,
                        games_synced=0,
                        games_excluded=0,
                        games_already_present=0,
                        total_games_found=0,
                        message=f"Failed: {exc}",
                    )
                )

    finished_at = datetime.now(timezone.utc)
    total_games_synced = sum(r.games_synced for r in per_player)
    total_games_excluded = sum(r.games_excluded for r in per_player)
    total_games_already_present = sum(r.games_already_present for r in per_player)
    total_games_found = sum(r.total_games_found for r in per_player)

    if failed_players and len(failed_players) == len(eligible_players):
        final_status = "failed"
    elif failed_players:
        final_status = "partial"
    else:
        final_status = "success"

    summary = schemas.SyncAllResult(
        trigger=trigger,
        started_at=started_at,
        finished_at=finished_at,
        per_player=per_player,
        total_games_synced=total_games_synced,
        total_games_excluded=total_games_excluded,
        total_games_already_present=total_games_already_present,
        total_games_found=total_games_found,
        failed_players=failed_players,
        message=(
            f"Full sync: {total_games_synced} games synced across "
            f"{len(eligible_players) - len(failed_players)} players"
            + (f", {len(failed_players)} failed" if failed_players else "")
        ),
    )

    run.finished_at = finished_at
    run.status = final_status
    run.summary = summary.model_dump(mode="json")
    run.progress = schemas.FullSyncProgress(
        players_total=len(eligible_players),
        players_done=len(eligible_players),
        current_player=None,
        games_synced_so_far=total_games_synced,
        games_found_so_far=total_games_found,
    ).model_dump()
    await db.commit()
    invalidate_chart_cache()

    return summary


async def get_full_sync_status(db: AsyncSession, run_id: int) -> Optional[schemas.FullSyncStatus]:
    """Return the current status of a full sync run by its ID."""
    result = await db.execute(
        select(models.SyncRun).where(models.SyncRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None

    progress = None
    if run.progress:
        progress = schemas.FullSyncProgress(**run.progress)

    result_data = None
    if run.summary and run.status in ("success", "partial", "failed"):
        result_data = schemas.SyncAllResult(**run.summary)

    return schemas.FullSyncStatus(
        run_id=run.id,
        status=run.status,
        progress=progress,
        result=result_data,
    )


async def get_running_full_sync(db: AsyncSession) -> Optional[schemas.FullSyncStatus]:
    """Return the FullSyncStatus of any currently running full_manual sync run, or None."""
    result = await db.execute(
        select(models.SyncRun).where(
            models.SyncRun.trigger == "full_manual",
            models.SyncRun.status == "running",
        )
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None
    progress = schemas.FullSyncProgress(**run.progress) if run.progress else None
    return schemas.FullSyncStatus(run_id=run.id, status=run.status, progress=progress)


async def create_full_sync_run(db: AsyncSession) -> int:
    """Create a new SyncRun row for a full sync and return its id."""
    run = models.SyncRun(
        started_at=datetime.now(timezone.utc),
        trigger="full_manual",
        status="running",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run.id


async def mark_full_sync_run_failed(db: AsyncSession, run_id: int, reason: str) -> None:
    """Mark a SyncRun row as failed with a reason message."""
    result = await db.execute(
        select(models.SyncRun).where(models.SyncRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        return
    run.status = "failed"
    run.finished_at = datetime.now(timezone.utc)
    run.summary = {"message": reason}
    await db.commit()
