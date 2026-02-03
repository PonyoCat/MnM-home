from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from .. import crud, database

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)

@router.get("/weekly-trends")
async def get_weekly_trends(
    start_date: date,
    end_date: date,
    player_name: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db)
):
    """Get aggregated weekly data for trends"""
    return await crud.get_weekly_trends(db, start_date, end_date, player_name)

@router.get("/practice-vs-winrate")
async def get_practice_vs_winrate(
    db: AsyncSession = Depends(database.get_db)
):
    """Get practice volume vs win rate data"""
    return await crud.get_practice_vs_winrate_data(db)

@router.get("/pool-coverage")
async def get_pool_coverage(
    week_start: date,
    db: AsyncSession = Depends(database.get_db)
):
    """Get champion pool coverage stats for a specific week"""
    return await crud.get_pool_coverage(db, week_start)
