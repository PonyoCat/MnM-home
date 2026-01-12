from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db
from datetime import date
from typing import List, Optional

router = APIRouter(prefix="/api/weekly-champions", tags=["weekly-champions"])

@router.get("/", response_model=List[schemas.WeeklyChampion])
async def get_weekly_champions(
    week_start: date = Query(..., description="Week start date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Get all weekly champions for a specific week"""
    return await crud.get_weekly_champions(db, week_start)

@router.post("/", response_model=schemas.WeeklyChampion)
async def upsert_weekly_champion(
    champion: schemas.WeeklyChampionCreate, db: AsyncSession = Depends(get_db)
):
    """Create or update weekly champion played status"""
    return await crud.upsert_weekly_champion(db, champion)

@router.delete("/", status_code=204)
async def delete_champion(
    player_name: str = Query(..., description="Player name"),
    champion_name: str = Query(..., description="Champion name"),
    week_start: date = Query(..., description="Week start date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Delete all instances of a champion for a player in a specific week"""
    await crud.delete_weekly_champion(db, player_name, champion_name, week_start)
    return None

@router.delete("/instance", status_code=204)
async def delete_one_champion_instance(
    player_name: str = Query(..., description="Player name"),
    champion_name: str = Query(..., description="Champion name"),
    week_start: date = Query(..., description="Week start date (YYYY-MM-DD)"),
    played: bool = Query(True, description="Whether to delete a played or unplayed instance"),
    db: AsyncSession = Depends(get_db)
):
    """Delete ONE instance of a champion for a player in a specific week"""
    await crud.delete_one_weekly_champion_instance(db, player_name, champion_name, week_start, played)
    return None

@router.post("/archive", response_model=List[schemas.WeeklyChampionArchive])
async def archive_week(
    week_start: date = Query(..., description="Week start date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Archive weekly champion stats for a specific week"""
    return await crud.archive_weekly_champions(db, week_start)

@router.post("/archive-current-week", response_model=List[schemas.WeeklyChampionArchive])
async def archive_current_week(db: AsyncSession = Depends(get_db)):
    """
    Archive the current week's champion stats and reset the data.
    Automatically calculates the week start (Wednesday) for the current week.
    This endpoint is designed to be called by scheduled jobs.
    """
    from datetime import datetime, timedelta

    # Get current date
    today = datetime.now().date()

    # Calculate the Wednesday of the current week
    # weekday() returns 0=Monday, 1=Tuesday, 2=Wednesday, 6=Sunday
    # Calculate days back to Wednesday (weekday 2)
    days_back = (today.weekday() - 2 + 7) % 7
    week_start = today - timedelta(days=days_back)

    return await crud.archive_weekly_champions(db, week_start)

@router.get("/archives", response_model=List[schemas.WeeklyChampionArchive])
async def get_archives(
    player_name: Optional[str] = Query(None, description="Filter by player name"),
    db: AsyncSession = Depends(get_db)
):
    """Get weekly champion archives, optionally filtered by player"""
    return await crud.get_weekly_champion_archives(db, player_name)
