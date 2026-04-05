import asyncio
import os
from db.connection import get_pool, init_db
from services.job_scraper import scrape_all_sources
from db.jobs import upsert_jobs

async def run_scraper():
    await init_db()
    jobs = await scrape_all_sources()
    if jobs:
        inserted = await upsert_jobs(jobs)
        print(f"Scraped and inserted {inserted} fresh jobs!")
    else:
        print("No jobs found to insert.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
