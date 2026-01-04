import asyncio
from app.database import engine, Base
from app.models import SessionReview, DraftNote, WeeklyChampion, PickStat, SessionReviewArchive, WeeklyChampionArchive
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal

async def init_db():
    """Initialize database tables and insert initial data"""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully!")

    # Insert initial rows for session_reviews and draft_notes
    async with AsyncSessionLocal() as session:
        # Check if session review already exists
        result = await session.execute(select(SessionReview))
        if not result.scalars().first():
            session_review = SessionReview(notes="Add your session notes here...")
            session.add(session_review)
            print("Initial session review created")

        # Check if draft note already exists
        result = await session.execute(select(DraftNote))
        if not result.scalars().first():
            draft_note = DraftNote(notes="Add your draft strategy notes here...")
            session.add(draft_note)
            print("Initial draft note created")

        await session.commit()

    print("Database initialization complete!")

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
