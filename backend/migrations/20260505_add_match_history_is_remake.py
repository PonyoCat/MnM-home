"""Add is_remake column to match_history and backfill from duration heuristic.

Backfill rule: any synced match with game_duration_seconds < 300 (5 min) is
treated as a remake. In ranked solo/duo there is a structural dead zone between
~3:30 (early-surrender threshold) and 15:00 (/ff threshold), so duration < 5
min is safe -- normal stomps cannot end that fast.

Also clears any weekly_champions rows that point to a now-flagged remake so
accountability stops counting them.
"""
import asyncio
from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS match_history "
                "ADD COLUMN IF NOT EXISTS is_remake BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )

        await conn.execute(
            text(
                """
                UPDATE match_history
                SET is_remake = TRUE
                WHERE is_remake = FALSE
                  AND game_duration_seconds < 300
                """
            )
        )

        # Drop weekly_champions rows whose underlying match is now flagged as remake.
        await conn.execute(
            text(
                """
                DELETE FROM weekly_champions wc
                USING match_history mh
                WHERE wc.riot_match_id IS NOT NULL
                  AND wc.riot_match_id = mh.riot_match_id
                  AND wc.player_name = mh.player_name
                  AND mh.is_remake = TRUE
                """
            )
        )

    print("Migration complete: match_history.is_remake added and backfilled.")


if __name__ == "__main__":
    asyncio.run(run())
