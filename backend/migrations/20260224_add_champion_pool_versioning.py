import asyncio
from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS champion_pools "
                "ADD COLUMN IF NOT EXISTS effective_from_week DATE"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS champion_pools "
                "ADD COLUMN IF NOT EXISTS effective_to_week DATE"
            )
        )

        await conn.execute(
            text(
                """
                UPDATE champion_pools
                SET effective_from_week = COALESCE(
                    effective_from_week,
                    (
                        SELECT COALESCE(
                            MIN(week_start_date),
                            (
                                CURRENT_DATE
                                - ((EXTRACT(DOW FROM CURRENT_DATE)::int - 4 + 7) % 7)
                            )::date
                        )
                        FROM weekly_champions
                    )
                )
                """
            )
        )

        await conn.execute(
            text(
                "ALTER TABLE champion_pools "
                "ALTER COLUMN effective_from_week SET NOT NULL"
            )
        )

        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'ck_champion_pools_effective_range'
                    ) THEN
                        ALTER TABLE champion_pools
                        ADD CONSTRAINT ck_champion_pools_effective_range
                        CHECK (
                            effective_to_week IS NULL
                            OR effective_to_week >= effective_from_week
                        );
                    END IF;
                END $$;
                """
            )
        )

        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_champion_pools_effective_from_week ON champion_pools (effective_from_week)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_champion_pools_effective_to_week ON champion_pools (effective_to_week)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_champion_pools_player_effective_range "
                "ON champion_pools (player_name, effective_from_week, effective_to_week)"
            )
        )
        await conn.execute(
            text(
                """
                WITH duplicate_active_rows AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_name, champion_name
                            ORDER BY id
                        ) AS row_num
                    FROM champion_pools
                    WHERE effective_to_week IS NULL
                )
                DELETE FROM champion_pools cp
                USING duplicate_active_rows d
                WHERE cp.id = d.id
                  AND d.row_num > 1
                """
            )
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_champion_pools_active_player_champion_unique "
                "ON champion_pools (player_name, champion_name) "
                "WHERE effective_to_week IS NULL"
            )
        )

    print("Migration complete: champion_pools now supports week-based versioning.")


if __name__ == "__main__":
    asyncio.run(run())
