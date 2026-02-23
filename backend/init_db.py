import asyncio
from app.database import engine, Base
from app.models import SessionReview, DraftNote, WeeklyChampion, PickStat, SessionReviewArchive, WeeklyMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal

async def init_db():
    """Initialize database tables and insert initial data"""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully!")
    print("\nTables created:")
    print("  - session_reviews")
    print("  - weekly_champions")
    print("  - draft_notes")
    print("  - pick_stats")
    print("  - session_review_archives")
    print("  - weekly_messages")

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

        # Check if weekly message already exists
        result = await session.execute(select(WeeklyMessage).where(WeeklyMessage.id == 1))
        if not result.scalars().first():
            weekly_message = WeeklyMessage(id=1, message="")
            session.add(weekly_message)
            print("Initial weekly message created")

        await session.commit()

    print("Database initialization complete!")

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
