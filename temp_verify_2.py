import asyncio
from db.connection import init_db, get_pool

async def main():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as conn:
        print("--- Next.js Skill Check ---")
        rows = await conn.fetch("SELECT title, skills FROM jobs WHERE 'next.js' = ANY(skills) LIMIT 2")
        for r in rows:
            print(f"Title: {r['title']} | Skills: {r['skills']}")
            
        print("\n--- Internships / Contracts ---")
        rows = await conn.fetch("SELECT title, job_type, duration, salary FROM jobs WHERE job_type != 'full-time' LIMIT 3")
        for r in rows:
            print(f"Title: {r['title']} | Type: {r['job_type']} | Duration: {r['duration']} | Salary: {r['salary']}")
            
        print("\n--- Fallback Salary Extraction ---")
        rows = await conn.fetch("SELECT title, salary FROM jobs WHERE salary IS NOT NULL AND source = 'greenhouse' LIMIT 3")
        for r in rows:
            print(f"Title: {r['title']} | Salary: {r['salary']}")

if __name__ == "__main__":
    asyncio.run(main())
