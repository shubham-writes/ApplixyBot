import asyncio
from db.connection import init_db, get_pool

async def run():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as c:
        total = await c.fetchval('SELECT COUNT(*) FROM jobs')
        ats_ready = await c.fetchval("SELECT COUNT(*) FROM jobs WHERE portal_type != 'other'")
        greenhouse = await c.fetchval("SELECT COUNT(*) FROM jobs WHERE portal_type = 'greenhouse'")
        print(f"Total jobs: {total}")
        print(f"Auto-apply ready: {ats_ready}")
        print(f"  Greenhouse: {greenhouse}")
        
        rows = await c.fetch("SELECT title, company, url, portal_type FROM jobs WHERE portal_type = 'greenhouse' LIMIT 5")
        print("\nSample Greenhouse jobs:")
        for r in rows:
            print(f"  {r['title']} at {r['company']}")
            print(f"  URL: {r['url']}")
            print()

if __name__ == '__main__':
    asyncio.run(run())
