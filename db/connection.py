"""
Database connection pool management using asyncpg.
"""
import asyncpg
from pathlib import Path
from loguru import logger
from config import settings


_pool: asyncpg.Pool | None = None


async def init_db() -> asyncpg.Pool:
    """Initialize the database connection pool and run schema."""
    global _pool

    if _pool is not None:
        return _pool

    logger.info("Connecting to PostgreSQL...")
    _pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=2,
        max_size=10,
        command_timeout=30,
        max_inactive_connection_lifetime=300,
        statement_cache_size=0,
    )

    # Run schema on first boot
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    async with _pool.acquire() as conn:
        await conn.execute(schema_sql)
        
        # Soft migrations for new columns
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS experience_level TEXT DEFAULT '0';")
            await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_required INT NULL;")
            await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_type TEXT DEFAULT 'full-time';")
            await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS duration TEXT;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS ats_checks_today INT DEFAULT 0;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS ats_checks_reset DATE DEFAULT CURRENT_DATE;")
        except Exception as e:
            logger.warning(f"Failed to apply DB migrations: {e}")

        # Trial & pricing migrations
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMPTZ;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT FALSE;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_early_adopter BOOLEAN DEFAULT FALSE;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS joined_at TIMESTAMPTZ DEFAULT NOW();")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pricing_config (
                    id                   SERIAL PRIMARY KEY,
                    early_adopter_price  INT DEFAULT 199,
                    regular_price        INT DEFAULT 499,
                    early_adopter_slots  INT DEFAULT 200,
                    slots_filled         INT DEFAULT 0,
                    early_adopter_active BOOLEAN DEFAULT TRUE,
                    launch_date          TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            await conn.execute("""
                INSERT INTO pricing_config (
                    early_adopter_price, regular_price, early_adopter_slots,
                    slots_filled, early_adopter_active, launch_date
                )
                SELECT 199, 499, 200, 0, TRUE, NOW()
                WHERE NOT EXISTS (SELECT 1 FROM pricing_config);
            """)
        except Exception as e:
            logger.warning(f"Failed to apply trial/pricing migrations: {e}")

    logger.info("Database initialized successfully.")
    return _pool


def get_pool() -> asyncpg.Pool:
    """Get the active connection pool. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return _pool


async def close_db():
    """Gracefully close the database pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed.")
