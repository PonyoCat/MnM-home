from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/clash-dates", tags=["clash-dates"])


@router.get("/", response_model=schemas.ClashDates)
async def get_clash_dates(db: AsyncSession = Depends(get_db)):
    """Get current clash dates"""
    return await crud.get_clash_dates(db)


@router.put("/", response_model=schemas.ClashDates)
async def update_clash_dates(
    data: schemas.ClashDatesUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update clash dates"""
    return await crud.update_clash_dates(db, data.date1, data.date2)
