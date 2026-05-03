from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/week-config", tags=["week-config"])


@router.get("/current", response_model=schemas.CurrentWeekConfig)
async def get_current_week_config(
    response: Response,
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get resolved week-start settings for a target date."""
    response.headers["Cache-Control"] = "max-age=60, stale-while-revalidate=30"
    return await crud.get_current_week_config(db, target_date)


@router.get("/versions", response_model=List[schemas.WeekBoundaryVersion])
async def get_week_boundary_versions(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Get all week-boundary configuration versions."""
    response.headers["Cache-Control"] = "max-age=300, stale-while-revalidate=60"
    return await crud.list_week_reset_configs(db)
