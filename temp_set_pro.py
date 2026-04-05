import asyncio
from db.connection import init_db, get_pool

async def main():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id, first_name, username FROM users")
        if not users:
            print("No users found.")
            return
        for u in users:
            print(f"Upgrading user: {dict(u)}")
            await conn.execute("UPDATE users SET plan = 'pro' WHERE telegram_id = $1", u["telegram_id"])
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
