from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas
from ..database import get_db
from typing import List

router = APIRouter(prefix="/api/session-review", tags=["session-review"])

@router.get("/", response_model=schemas.SessionReview)
async def get_session_review(db: AsyncSession = Depends(get_db)):
    """Get current session review notes"""
    return await crud.get_session_review(db)

@router.put("/", response_model=schemas.SessionReview)
async def update_session_review(
    review: schemas.SessionReviewUpdate, db: AsyncSession = Depends(get_db)
):
    """Update session review notes"""
    return await crud.update_session_review(db, review.notes)

@router.post("/archive", response_model=schemas.SessionReviewArchive)
async def create_archive(
    archive: schemas.SessionReviewArchiveCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new session review archive"""
    try:
        print(f"[ARCHIVE] Creating archive: title='{archive.title}', notes_length={len(archive.notes)}, date={archive.original_date}")
        result = await crud.create_session_review_archive(
            db,
            archive.title,
            archive.notes,
            archive.original_date
        )
        print(f"[ARCHIVE] Archive created successfully: id={result.id}, archived_at={result.archived_at}")
        return result
    except Exception as e:
        print(f"[ARCHIVE] ERROR creating archive: {e}")
        raise

@router.get("/archives", response_model=List[schemas.SessionReviewArchive])
async def get_archives(db: AsyncSession = Depends(get_db)):
    """Get all session review archives"""
    try:
        print("[ARCHIVE] Fetching all archives...")
        archives = await crud.get_session_review_archives(db)
        print(f"[ARCHIVE] Found {len(archives)} archive(s)")
        return archives
    except Exception as e:
        print(f"[ARCHIVE] ERROR fetching archives: {e}")
        raise

@router.get("/archives/{archive_id}", response_model=schemas.SessionReviewArchive)
async def get_archive(archive_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single session review archive by ID"""
    return await crud.get_session_review_archive_by_id(db, archive_id)

@router.patch("/archives/{archive_id}", response_model=schemas.SessionReviewArchive)
async def update_archive(
    archive_id: int,
    archive: schemas.SessionReviewArchiveUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing session review archive"""
    return await crud.update_session_review_archive(
        db,
        archive_id,
        archive.title,
        archive.notes
    )
