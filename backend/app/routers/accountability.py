from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/accountability", tags=["accountability"])

@router.get("/check", response_model=List[schemas.PlayerAccountability])
async def get_accountability_check(
    db: AsyncSession = Depends(get_db)
):
    """
    Check if each player has played at least 1 game on all their champions.
    Returns accountability status for all players.
    """
    return await crud.get_accountability_check(db)
