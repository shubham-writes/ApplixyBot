import asyncio
from db.connection import init_db, get_pool, close_db

async def run():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as c:
        with open('db/schema.sql', 'r') as f:
            await c.execute(f.read())
    await close_db()

asyncio.run(run())
print('Done')
