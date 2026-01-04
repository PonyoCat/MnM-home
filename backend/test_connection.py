"""
Quick script to test database connection
"""
import asyncio
from app.database import engine

async def test_connection():
    """Test if we can connect to the database"""
    try:
        async with engine.connect() as conn:
            print("SUCCESS: Connected to Neon database!")
            return True
    except Exception as e:
        print(f"ERROR: Could not connect to database")
        print(f"Details: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
