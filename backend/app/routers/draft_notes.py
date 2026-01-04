from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/draft-notes", tags=["draft-notes"])

@router.get("/", response_model=schemas.DraftNote)
async def get_draft_notes(db: AsyncSession = Depends(get_db)):
    """Get current draft notes"""
    return await crud.get_draft_note(db)

@router.put("/", response_model=schemas.DraftNote)
async def update_draft_notes(
    draft_note: schemas.DraftNoteUpdate, db: AsyncSession = Depends(get_db)
):
    """Update draft notes"""
    return await crud.update_draft_note(db, draft_note.notes)
