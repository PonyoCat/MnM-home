from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/weekly-message", tags=["weekly-message"])

@router.get("/", response_model=schemas.WeeklyMessage)
async def get_weekly_message(db: AsyncSession = Depends(get_db)):
    """Get current weekly message"""
    return await crud.get_weekly_message(db)

@router.put("/", response_model=schemas.WeeklyMessage)
async def update_weekly_message(
    data: schemas.WeeklyMessageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update weekly message"""
    return await crud.update_weekly_message(db, data.message)
