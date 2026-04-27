import asyncio
from db.connection import get_pool, init_db

async def test():
    await init_db()
    pool = get_pool()
    config = await pool.fetchrow('SELECT * FROM pricing_config LIMIT 1')
    print('CONFIG:', config)

asyncio.run(test())
