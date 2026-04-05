from loguru import logger
from db.connection import get_pool
from datetime import datetime
import json

async def add_application(telegram_id: int, job_id: int) -> bool:
    """Add a job to applications. Return True if added, False if already exists."""
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            # Check if already tracked
            existing = await conn.fetchval(
                "SELECT id FROM applications WHERE telegram_id = $1 AND job_id = $2",
                telegram_id, job_id
            )
            if existing:
                return False

            # Insert the application
            app_id = await conn.fetchval(
                """
                INSERT INTO applications (telegram_id, job_id, status)
                VALUES ($1, $2, 'applied')
                RETURNING id
                """,
                telegram_id,
                job_id
            )

            # Schedule a follow-up reminder 3 days from now
            try:
                await conn.execute(
                    """
                    INSERT INTO reminders (telegram_id, application_id, remind_at, reminder_type)
                    VALUES ($1, $2, NOW() + INTERVAL '3 days', 'followup')
                    """,
                    telegram_id,
                    app_id
                )
            except Exception as e:
                logger.warning(f"Could not create reminder (non-critical): {e}")

            return True
        except Exception as e:
            logger.error(f"Error adding application: {e}")
            return False

async def get_applications(telegram_id: int, limit: int = 10, offset: int = 0) -> list[dict]:
    """Get active applications for a user with job details."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT a.id as app_id, a.status, a.applied_at,
                   j.id as job_id, j.title, j.company, j.location, j.url
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.telegram_id = $1
            ORDER BY a.applied_at DESC
            LIMIT $2 OFFSET $3
            """,
            telegram_id, limit, offset
        )
        return [dict(r) for r in rows]

async def count_applications(telegram_id: int) -> int:
    """Total applications count."""
    pool = get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval(
            "SELECT count(*) FROM applications WHERE telegram_id = $1",
            telegram_id
        )
        return val or 0

async def get_weekly_stats(telegram_id: int) -> dict:
    """Get statistics for the past 7 days."""
    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            """
            SELECT count(*) FROM applications 
            WHERE telegram_id = $1 
            AND applied_at >= NOW() - INTERVAL '7 days'
            """,
            telegram_id
        )
        return {"weekly_apps": count or 0}

async def update_application_status(telegram_id: int, app_id: int, new_status: str) -> bool:
    """Update status of a tracked application."""
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE applications SET status = $1 WHERE id = $2 AND telegram_id = $3",
            new_status, app_id, telegram_id
        )
        return result == "UPDATE 1"

async def get_application_by_id(telegram_id: int, app_id: int) -> dict | None:
    """Get a specific application for managing."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT a.id as app_id, a.status, a.applied_at,
                   j.id as job_id, j.title, j.company, j.location, j.url
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.telegram_id = $1 AND a.id = $2
            """,
            telegram_id, app_id
        )
        return dict(row) if row else None
