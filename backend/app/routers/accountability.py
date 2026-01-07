from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/accountability", tags=["accountability"])

@router.get("/check", response_model=List[schemas.PlayerAccountability])
async def get_accountability_check(
    week_start: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if each player has played at least 1 game on all their champions.
    Returns accountability status for all players.
    """
    week_start_date = None
    if week_start:
        try:
            week_start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    return await crud.get_accountability_check(db, week_start_date)

@router.get("/debug")
async def get_accountability_debug_data(
    db: AsyncSession = Depends(get_db)
):
    """
    Get raw database data for accountability debugging.
    Returns champion pools and weekly champions for current week.
    """
    return await crud.get_accountability_debug_data(db)
