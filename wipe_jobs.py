import asyncio
from db.connection import get_pool, init_db

async def run():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as c:
        await c.execute('TRUNCATE jobs CASCADE;')
        print('Jobs wiped!')

if __name__ == '__main__':
    asyncio.run(run())
