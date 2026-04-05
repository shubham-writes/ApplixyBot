import asyncio
from db.connection import init_db
from services.job_scraper import scrape_all_sources
from db.jobs import upsert_jobs

async def run():
    await init_db()
    jobs = await scrape_all_sources()
    await upsert_jobs(jobs)
    print("Scraped and inserted!")

if __name__ == '__main__':
    asyncio.run(run())
