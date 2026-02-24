from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from typing import List, Optional
from datetime import date, datetime, timedelta


def _get_week_start(target_date: Optional[date] = None) -> date:
    """Return week start for a target date using Python weekday numbering."""
    return _get_week_start_for_weekday(target_date=target_date, week_start_weekday=3)


def _get_week_start_for_weekday(
    target_date: Optional[date] = None,
    week_start_weekday: int = 3,
) -> date:
    """Return the configured week start for the target date."""
    if target_date is None:
        target_date = datetime.now().date()
    days_back = (target_date.weekday() - week_start_weekday + 7) % 7
    return target_date - timedelta(days=days_back)


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
    """Return week start for a target date based on database-configured rules."""
    resolved_target_date = target_date or datetime.now().date()
    week_start_weekday = await get_week_start_weekday_for_date(
        db=db,
        target_date=resolved_target_date,
    )
    return _get_week_start_for_weekday(
        target_date=resolved_target_date,
        week_start_weekday=week_start_weekday,
    )

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
    champion = models.WeeklyChampion(**champion_data.dict())
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

async def delete_weekly_champion(
    db: AsyncSession,
    player_name: str,
    champion_name: str,
    week_start: date
) -> bool:
    """Delete ALL instances of a champion for a player in a specific week"""
    result = await db.execute(
        select(models.WeeklyChampion).where(
            models.WeeklyChampion.player_name == player_name,
            models.WeeklyChampion.champion_name == champion_name,
            models.WeeklyChampion.week_start_date == week_start
        )
    )
    champions = list(result.scalars().all())

    for champ in champions:
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
    """Delete ONE instance of a champion for a player in a specific week"""
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
    """
    # Calculate target week start using configured week-boundary rules if not provided
    target_week_start = week_start or await get_configured_week_start(db)

    # IMPORTANT: Always return all 5 players
    PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

    accountability_data = []

    for player in PLAYERS:
        # Get all active (non-disabled) champions in this player's pool
        champions_result = await db.execute(
            select(models.ChampionPool).where(
                models.ChampionPool.player_name == player,
                models.ChampionPool.disabled.is_(False),
                models.ChampionPool.effective_from_week <= target_week_start,
                or_(
                    models.ChampionPool.effective_to_week.is_(None),
                    models.ChampionPool.effective_to_week >= target_week_start,
                ),
            )
        )
        champions = list(champions_result.scalars().all())

        # If no champion pool entries, show 0/0
        if not champions:
            accountability_data.append({
                "player_name": player,
                "all_champions_played": False,
                "missing_champions": [],
                "total_champions": 0,
                "champions_played": 0,
                "champion_details": []  # New field for detailed status
            })
            continue

        # Check each champion for weekly games
        missing_champions = []
        champion_details = []

        for champ in champions:
            # CORRECT: Check weekly_champions table for current week
            conditions = [
                models.WeeklyChampion.player_name == player,
                models.WeeklyChampion.champion_name == champ.champion_name,
                models.WeeklyChampion.week_start_date == target_week_start,
                models.WeeklyChampion.played.is_(True),  # Only count played games
            ]

            weekly_result = await db.execute(select(models.WeeklyChampion).where(*conditions))
            weekly_games = list(weekly_result.scalars().all())

            # Has played if at least 1 game this week
            has_played = len(weekly_games) > 0

            if not has_played:
                missing_champions.append(champ.champion_name)

            # Add detailed status for UI expansion
            champion_details.append({
                "champion_name": champ.champion_name,
                "has_played": has_played,
                "games_played": len(weekly_games)
            })

        # Player is accountable if no missing champions
        all_champions_played = len(missing_champions) == 0

        accountability_data.append({
            "player_name": player,
            "all_champions_played": all_champions_played,
            "missing_champions": missing_champions,
            "total_champions": len(champions),
            "champions_played": len(champions) - len(missing_champions),
            "champion_details": champion_details  # New field
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
    week_start_weekday = await get_week_start_weekday_for_date(
        db=db,
        target_date=resolved_target_date,
    )
    week_start_date = _get_week_start_for_weekday(
        target_date=resolved_target_date,
        week_start_weekday=week_start_weekday,
    )
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
        player_stats[p.player_name]["pool_champs"].add(p.champion_name)

    qry = select(models.WeeklyChampion).where(
        models.WeeklyChampion.week_start_date == week_start,
        models.WeeklyChampion.played.is_(True)
    )
    res = await db.execute(qry)
    played_rows = res.scalars().all()

    for row in played_rows:
        if row.player_name in player_stats:
            player_stats[row.player_name]["played_champs"].add(row.champion_name)

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
