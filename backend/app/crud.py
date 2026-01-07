from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from typing import List, Optional
from datetime import date, datetime, timedelta


def _get_week_start(target_date: Optional[date] = None) -> date:
    """Return the Monday of the target date's week."""
    if target_date is None:
        target_date = datetime.now().date()
    return target_date - timedelta(days=target_date.weekday())

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
    current_week_start = _get_week_start()
    query = select(models.WeeklyChampion).where(
        models.WeeklyChampion.week_start_date == week_start
    )

    # Active weeks should ignore archived rows; historical weeks return all records
    if week_start >= current_week_start:
        query = query.where(models.WeeklyChampion.archived_at.is_(None))

    result = await db.execute(query)
    return result.scalars().all()

async def upsert_weekly_champion(
    db: AsyncSession, champion_data: schemas.WeeklyChampionCreate
) -> models.WeeklyChampion:
    """Create a new weekly champion record or update to unplayed if setting played=false"""
    # If setting played=false, try to update an existing played=true record first
    if not champion_data.played:
        result = await db.execute(
            select(models.WeeklyChampion).where(
                models.WeeklyChampion.player_name == champion_data.player_name,
                models.WeeklyChampion.champion_name == champion_data.champion_name,
                models.WeeklyChampion.week_start_date == champion_data.week_start_date,
                models.WeeklyChampion.played == True,
                models.WeeklyChampion.archived_at.is_(None)
            ).limit(1)
        )
        champion = result.scalars().first()

        if champion:
            # Update existing record to played=false
            champion.played = False
            await db.commit()
            await db.refresh(champion)
            return champion

        # If no played record exists, check if an unplayed record exists
        result = await db.execute(
            select(models.WeeklyChampion).where(
                models.WeeklyChampion.player_name == champion_data.player_name,
                models.WeeklyChampion.champion_name == champion_data.champion_name,
                models.WeeklyChampion.week_start_date == champion_data.week_start_date,
                models.WeeklyChampion.played == False,
                models.WeeklyChampion.archived_at.is_(None)
            ).limit(1)
        )
        existing_unplayed = result.scalars().first()

        if existing_unplayed:
            # Already have an unplayed record, just return it
            return existing_unplayed

    # Create a new record for played=true or if no record exists yet
    champion = models.WeeklyChampion(**champion_data.dict(), archived_at=None)
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

# Weekly Champion Archive CRUD
async def archive_weekly_champions(
    db: AsyncSession,
    week_start: date
) -> List[models.WeeklyChampionArchive]:
    """
    Archive all champions for a specific week and preserve champions with reset counts.
    Aggregates play counts per player/champion combination, saves to archive,
    marks the week's rows as archived, then recreates unique champion entries
    with played=False for the next week. This ensures champions persist week-to-week
    with play counts reset to 0 without deleting historical rows.
    """
    # Get all active champions for this week
    champions_result = await db.execute(
        select(models.WeeklyChampion).where(
            models.WeeklyChampion.week_start_date == week_start,
            models.WeeklyChampion.archived_at.is_(None)
        )
    )
    champions = list(champions_result.scalars().all())

    # Group by player and champion, count plays
    from collections import defaultdict
    aggregated = defaultdict(int)

    for champ in champions:
        if champ.played:
            key = (champ.player_name, champ.champion_name)
            aggregated[key] += 1

    # Calculate week end date (Sunday)
    week_end = week_start + timedelta(days=6)

    # Create archive records
    archives = []
    for (player, champion), count in aggregated.items():
        archive = models.WeeklyChampionArchive(
            player_name=player,
            champion_name=champion,
            times_played=count,
            week_start_date=week_start,
            week_end_date=week_end
        )
        db.add(archive)
        archives.append(archive)

    await db.commit()

    # Refresh all archives
    for archive in archives:
        await db.refresh(archive)

    # Extract unique player/champion combinations to preserve
    unique_combinations = set()
    for champ in champions:
        unique_combinations.add((champ.player_name, champ.champion_name))

    # Calculate next Monday (next week's start date)
    next_week_start = week_start + timedelta(days=7)

    # Mark all weekly champion records for this week as archived (non-destructive reset)
    await db.execute(
        update(models.WeeklyChampion)
        .where(
            models.WeeklyChampion.week_start_date == week_start,
            models.WeeklyChampion.archived_at.is_(None)
        )
        .values(archived_at=func.now())
    )
    await db.commit()

    # Recreate records with played=False for next week
    for player, champion in unique_combinations:
        new_record = models.WeeklyChampion(
            player_name=player,
            champion_name=champion,
            played=False,  # Reset to 0 plays
            week_start_date=next_week_start,  # Move to next week
            archived_at=None
        )
        db.add(new_record)

    await db.commit()

    return archives

async def get_weekly_champion_archives(
    db: AsyncSession,
    player_name: str = None
) -> List[models.WeeklyChampionArchive]:
    """Get weekly champion archives, optionally filtered by player"""
    query = select(models.WeeklyChampionArchive).order_by(
        models.WeeklyChampionArchive.week_start_date.desc()
    )

    if player_name:
        query = query.where(models.WeeklyChampionArchive.player_name == player_name)

    result = await db.execute(query)
    return list(result.scalars().all())

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
            models.WeeklyChampion.week_start_date == week_start,
            models.WeeklyChampion.archived_at.is_(None)
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
            models.WeeklyChampion.played == played,
            models.WeeklyChampion.archived_at.is_(None)
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
    player_name: str = None
) -> List[models.ChampionPool]:
    """Get champion pools, optionally filtered by player"""
    query = select(models.ChampionPool).order_by(
        models.ChampionPool.player_name,
        models.ChampionPool.champion_name
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
    pool = models.ChampionPool(**pool_data.model_dump())
    db.add(pool)
    await db.commit()
    await db.refresh(pool)
    return pool

async def update_champion_pool(
    db: AsyncSession,
    pool_id: int,
    pool_data: schemas.ChampionPoolUpdate
) -> models.ChampionPool:
    """Update champion pool entry"""
    result = await db.execute(
        select(models.ChampionPool).where(models.ChampionPool.id == pool_id)
    )
    pool = result.scalars().first()

    if pool:
        # Update only provided fields
        if pool_data.champion_name is not None:
            pool.champion_name = pool_data.champion_name
        if pool_data.description is not None:
            pool.description = pool_data.description
        if pool_data.pick_priority is not None:
            pool.pick_priority = pool_data.pick_priority

        await db.commit()
        await db.refresh(pool)

    return pool

async def delete_champion_pool(
    db: AsyncSession,
    pool_id: int
) -> bool:
    """Delete champion pool entry"""
    result = await db.execute(
        select(models.ChampionPool).where(models.ChampionPool.id == pool_id)
    )
    pool = result.scalars().first()

    if pool:
        await db.delete(pool)
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
    # Calculate target week start (Monday) if not provided
    current_week_start = _get_week_start()
    target_week_start = week_start or current_week_start

    # IMPORTANT: Always return all 5 players
    PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

    accountability_data = []

    for player in PLAYERS:
        # Get all champions in this player's pool
        champions_result = await db.execute(
            select(models.ChampionPool).where(
                models.ChampionPool.player_name == player
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
                models.WeeklyChampion.played == True  # Only count played games
            ]

            # For the active/current week, exclude archived rows
            if target_week_start >= current_week_start:
                conditions.append(models.WeeklyChampion.archived_at.is_(None))

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
    # Calculate current week start
    week_start = _get_week_start()

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
            models.WeeklyChampion.week_start_date == week_start,
            models.WeeklyChampion.archived_at.is_(None)
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
                "pick_priority": p.pick_priority
            }
            for p in champion_pools
        ],
        "weekly_champions": [
            {
                "id": w.id,
                "player_name": w.player_name,
                "champion_name": w.champion_name,
                "played": w.played,
                "week_start_date": w.week_start_date.isoformat(),
                "archived_at": w.archived_at.isoformat() if w.archived_at else None
            }
            for w in weekly_champions
        ]
    }
