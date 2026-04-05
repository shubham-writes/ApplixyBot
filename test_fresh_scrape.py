import asyncio
from db.connection import init_db, get_pool
from services.job_scraper import scrape_all_sources
from db.jobs import upsert_jobs

async def run():
    await init_db()
    pool = get_pool()
    
    # Wipe old jobs
    async with pool.acquire() as c:
        await c.execute('TRUNCATE jobs CASCADE;')
        print('Old jobs wiped!')
    
    # Scrape fresh
    jobs = await scrape_all_sources()
    await upsert_jobs(jobs)
    
    # Count auto-apply ready jobs
    async with pool.acquire() as c:
        total = await c.fetchval('SELECT COUNT(*) FROM jobs')
        ats_ready = await c.fetchval("SELECT COUNT(*) FROM jobs WHERE portal_type != 'other'")
        greenhouse = await c.fetchval("SELECT COUNT(*) FROM jobs WHERE portal_type = 'greenhouse'")
        print(f"\nTotal jobs: {total}")
        print(f"Auto-apply ready: {ats_ready}")
        print(f"  Greenhouse: {greenhouse}")
        
        # Show a few examples
        rows = await c.fetch("SELECT title, company, url, portal_type FROM jobs WHERE portal_type = 'greenhouse' LIMIT 3")
        for r in rows:
            print(f"  -> {r['title']} at {r['company']}")
            print(f"     URL: {r['url']}")

if __name__ == '__main__':
    asyncio.run(run())
