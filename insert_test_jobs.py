import asyncio
from db.connection import get_pool, init_db

async def run():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as c:
        # Insert a Greenhouse job
        await c.execute("""
            INSERT INTO jobs (url_hash, title, company, url, location, skills, source, portal_type, is_active)
            VALUES ('hash_greenhouse', 'Senior React Engineer (Test)', 'GreenhouseInc', 'https://boards.greenhouse.io/test/jobs/1234', 'Remote', '{"react", "nextjs"}', 'manual', 'greenhouse', TRUE)
            ON CONFLICT DO NOTHING
        """)
        # Insert a Lever job
        await c.execute("""
            INSERT INTO jobs (url_hash, title, company, url, location, skills, source, portal_type, is_active)
            VALUES ('hash_lever', 'Frontend Dev (Test)', 'LeverCorp', 'https://jobs.lever.co/test/5678', 'Remote', '{"react", "typescript"}', 'manual', 'lever', TRUE)
            ON CONFLICT DO NOTHING
        """)
        print("Test auto-apply jobs inserted!")

if __name__ == '__main__':
    asyncio.run(run())
