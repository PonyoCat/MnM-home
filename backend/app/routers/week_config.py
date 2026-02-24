from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/week-config", tags=["week-config"])


@router.get("/current", response_model=schemas.CurrentWeekConfig)
async def get_current_week_config(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get resolved week-start settings for a target date."""
    return await crud.get_current_week_config(db, target_date)


@router.get("/versions", response_model=List[schemas.WeekBoundaryVersion])
async def get_week_boundary_versions(
    db: AsyncSession = Depends(get_db),
):
    """Get all week-boundary configuration versions."""
    return await crud.list_week_reset_configs(db)
