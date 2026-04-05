import asyncio
from db.connection import get_pool, init_db

async def run():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as c:
        rows = await c.fetch("SELECT id, title, portal_type, url FROM jobs WHERE portal_type != 'other' LIMIT 5")
        if not rows:
            print("No auto-apply jobs found!")
        for r in rows:
            print(dict(r))

if __name__ == '__main__':
    asyncio.run(run())
