import asyncio
from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS weekly_champions "
                "ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ"
            )
        )
        await conn.execute(
            text(
                "UPDATE weekly_champions "
                "SET archived_at = NULL "
                "WHERE archived_at IS NULL"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_weekly_champions_archived_at ON weekly_champions (archived_at)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_weekly_champions_week_start_player_champion_archived_at "
                "ON weekly_champions (week_start_date, player_name, champion_name, archived_at)"
            )
        )
    print("Migration complete: archived_at column added to weekly_champions.")


if __name__ == "__main__":
    asyncio.run(run())
