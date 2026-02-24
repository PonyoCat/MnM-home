import asyncio
from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS week_boundary_versions "
                "RENAME TO week_reset_configs"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS week_reset_configs "
                "RENAME CONSTRAINT ck_week_boundary_versions_weekday_range "
                "TO ck_week_reset_configs_weekday_range"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE IF EXISTS week_reset_configs "
                "RENAME CONSTRAINT ck_week_boundary_versions_effective_range "
                "TO ck_week_reset_configs_effective_range"
            )
        )
        await conn.execute(
            text(
                "ALTER INDEX IF EXISTS ix_week_boundary_versions_effective_range "
                "RENAME TO ix_week_reset_configs_effective_range"
            )
        )
        await conn.execute(
            text(
                "ALTER INDEX IF EXISTS ix_week_boundary_versions_active_unique "
                "RENAME TO ix_week_reset_configs_active_unique"
            )
        )
        await conn.execute(
            text(
                "ALTER INDEX IF EXISTS week_boundary_versions_pkey "
                "RENAME TO week_reset_configs_pkey"
            )
        )
        await conn.execute(
            text(
                "ALTER SEQUENCE IF EXISTS week_boundary_versions_id_seq "
                "RENAME TO week_reset_configs_id_seq"
            )
        )

    print("Migration complete: week_boundary_versions renamed to week_reset_configs.")


if __name__ == "__main__":
    asyncio.run(run())
