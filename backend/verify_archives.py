"""
Script to verify session review archives in the database.
Directly queries the session_review_archives table to check data integrity.
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import SessionReviewArchive


async def verify_archives():
    """Query and display all archives from the database"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SessionReviewArchive)
                .order_by(SessionReviewArchive.archived_at.desc())
            )
            archives = result.scalars().all()

            print(f"\n{'='*60}")
            print(f"DATABASE VERIFICATION: Session Review Archives")
            print(f"{'='*60}\n")
            print(f"Found {len(archives)} archive(s) in database:\n")

            if len(archives) == 0:
                print("  (No archives found - database is empty)")
                print("\nThis is expected if you haven't archived any sessions yet.")
            else:
                for i, archive in enumerate(archives, 1):
                    print(f"Archive #{i}:")
                    print(f"  ID: {archive.id}")
                    print(f"  Title: {archive.title}")
                    print(f"  Archived At: {archive.archived_at}")
                    print(f"  Original Date: {archive.original_date}")
                    print(f"  Notes Preview: {archive.notes[:80]}{'...' if len(archive.notes) > 80 else ''}")
                    print()

            print(f"{'='*60}")
            print("Verification complete!\n")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR: Failed to verify archives")
        print(f"{'='*60}\n")
        print(f"Error details: {e}")
        print("\nPossible causes:")
        print("  1. Database connection failed (check DATABASE_URL in .env)")
        print("  2. Table doesn't exist (run: python init_db.py)")
        print("  3. Database credentials are incorrect")
        print(f"\n{'='*60}\n")
        raise


if __name__ == "__main__":
    asyncio.run(verify_archives())
