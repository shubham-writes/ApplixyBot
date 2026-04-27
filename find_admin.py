import asyncio
import os
from db.connection import init_db, close_db, get_pool

async def run():
    await init_db()
    pool = get_pool()
    rows = await pool.fetch("SELECT telegram_id, username, first_name FROM users WHERE username ILIKE $1", '%Planetbreaker%')
    for row in rows:
        print(f"ID: {row['telegram_id']}, Username: {row['username']}, First Name: {row['first_name']}")
    if not rows:
        print("NOT_FOUND")
    await close_db()

if __name__ == "__main__":
    asyncio.run(run())
