from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db
from typing import List

router = APIRouter(prefix="/api/pick-stats", tags=["pick-stats"])

@router.get("/", response_model=List[schemas.PickStat])
async def get_pick_stats(db: AsyncSession = Depends(get_db)):
    """Get all pick stats with computed win rate"""
    return await crud.get_pick_stats(db)

@router.post("/", response_model=schemas.PickStat)
async def create_pick_stat(
    pick_stat: schemas.PickStatCreate, db: AsyncSession = Depends(get_db)
):
    """Create new champion for tracking pick stats"""
    return await crud.create_pick_stat(db, pick_stat)

@router.patch("/{id}/win", response_model=schemas.PickStat)
async def add_win(id: int, db: AsyncSession = Depends(get_db)):
    """Increment both games and wins for a champion"""
    result = await crud.add_win(db, id)
    if not result:
        raise HTTPException(status_code=404, detail="Pick stat not found")
    return result

@router.patch("/{id}/loss", response_model=schemas.PickStat)
async def add_loss(id: int, db: AsyncSession = Depends(get_db)):
    """Increment only games for a champion (loss)"""
    result = await crud.add_loss(db, id)
    if not result:
        raise HTTPException(status_code=404, detail="Pick stat not found")
    return result

@router.patch("/{id}/champion", response_model=schemas.PickStat)
async def update_champion_name(
    id: int,
    data: schemas.PickStatChampionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update champion name for a pick stat"""
    try:
        stat = await crud.update_pick_stat_champion(db, id, data.champion_name)
        # Compute win_rate
        stat.win_rate = (
            (stat.first_pick_wins / stat.first_pick_games * 100)
            if stat.first_pick_games > 0 else 0.0
        )
        return stat
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{id}", response_model=schemas.PickStat)
async def update_pick_stat(
    id: int,
    data: schemas.PickStatUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update wins and/or losses for a pick stat"""
    result = await crud.update_pick_stat(db, id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Pick stat not found")
    return result

@router.delete("/{id}")
async def delete_pick_stat(id: int, db: AsyncSession = Depends(get_db)):
    """Delete a pick stat by ID"""
    success = await crud.delete_pick_stat(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Pick stat not found")
    return {"message": "Pick stat deleted successfully"}
