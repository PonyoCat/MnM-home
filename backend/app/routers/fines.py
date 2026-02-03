from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/fines", tags=["fines"])


@router.get("/", response_model=List[schemas.PlayerFinesSummary])
async def get_fines_summary(db: AsyncSession = Depends(get_db)):
    """Get all fines grouped by player with totals"""
    return await crud.get_fines_summary(db)


@router.post("/", response_model=schemas.Fine)
async def create_fine(
    fine_data: schemas.FineCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new fine"""
    return await crud.create_fine(db, fine_data)


@router.delete("/{fine_id}")
async def delete_fine(
    fine_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a fine by ID"""
    success = await crud.delete_fine(db, fine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fine not found")
    return {"status": "deleted"}
