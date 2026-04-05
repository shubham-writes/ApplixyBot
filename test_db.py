import asyncio
from db.connection import get_pool, init_db

async def run():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as c:
        rows = await c.fetch('SELECT title, skills, location FROM jobs WHERE is_active=TRUE LIMIT 10;')
        for r in rows:
            print(dict(r))

if __name__ == "__main__":
    asyncio.run(run())
