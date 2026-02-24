import asyncio
from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS week_reset_configs (
                    id SERIAL PRIMARY KEY,
                    week_start_weekday INTEGER NOT NULL,
                    effective_from_date DATE NOT NULL,
                    effective_to_date DATE NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    CONSTRAINT ck_week_reset_configs_weekday_range
                        CHECK (week_start_weekday >= 0 AND week_start_weekday <= 6),
                    CONSTRAINT ck_week_reset_configs_effective_range
                        CHECK (effective_to_date IS NULL OR effective_to_date >= effective_from_date)
                )
                """
            )
        )

        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_week_reset_configs_effective_range "
                "ON week_reset_configs (effective_from_date, effective_to_date)"
            )
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_week_reset_configs_active_unique "
                "ON week_reset_configs ((1)) "
                "WHERE effective_to_date IS NULL"
            )
        )

        # Seed historical transition only when table is empty.
        await conn.execute(
            text(
                """
                INSERT INTO week_reset_configs (
                    week_start_weekday,
                    effective_from_date,
                    effective_to_date
                )
                SELECT 2, DATE '1900-01-01', DATE '2026-02-25'
                WHERE NOT EXISTS (
                    SELECT 1 FROM week_reset_configs
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                INSERT INTO week_reset_configs (
                    week_start_weekday,
                    effective_from_date,
                    effective_to_date
                )
                SELECT 3, DATE '2026-02-26', NULL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM week_reset_configs
                    WHERE effective_to_date IS NULL
                )
                """
            )
        )

    print("Migration complete: week_reset_configs table created and seeded.")


if __name__ == "__main__":
    asyncio.run(run())
