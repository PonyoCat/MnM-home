from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db
from datetime import date
from typing import List

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
