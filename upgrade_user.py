import asyncio
from db.connection import get_pool, init_db

async def run():
    await init_db()
    pool = get_pool()
    telegram_id = 5187310177  # User's known telegram_id from previous queries
    async with pool.acquire() as c:
        await c.execute(f"UPDATE users SET plan = 'premium' WHERE telegram_id = {telegram_id};")
        print("Successfully upgraded user to Premium!")

if __name__ == '__main__':
    asyncio.run(run())
