import asyncio
from db.connection import init_db, get_pool

async def main():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("UPDATE users SET plan = 'free' WHERE plan = 'premium'")
        print('Rows updated (premium -> free):', res)
        res = await conn.execute("UPDATE users SET plan = 'free' WHERE plan = 'proplus'")
        print('Rows updated (proplus -> free):', res)

    print("Success")

if __name__ == "__main__":
    asyncio.run(main())
