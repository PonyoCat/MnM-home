from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/champion-pool", tags=["champion-pool"])

@router.get("/", response_model=List[schemas.ChampionPool])
async def get_champion_pools(
    player_name: Optional[str] = None,
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get champion pools, optionally filtered by player name"""
    return await crud.get_champion_pools(db, player_name, week_start)

@router.post("/", response_model=schemas.ChampionPool)
async def create_champion_pool(
    pool: schemas.ChampionPoolCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new champion pool entry"""
    try:
        return await crud.create_champion_pool(db, pool)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.patch("/{id}", response_model=schemas.ChampionPool)
async def update_champion_pool(
    id: int,
    pool: schemas.ChampionPoolUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update champion pool entry"""
    try:
        result = await crud.update_champion_pool(db, id, pool)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Champion pool entry not found")
    return result

@router.delete("/{id}")
async def delete_champion_pool(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete champion pool entry"""
    success = await crud.delete_champion_pool(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Champion pool entry not found")
    return {"message": "Champion pool entry deleted successfully"}
