import asyncio
from db.connection import init_db, get_pool

async def main():
    await init_db()
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT title, skills, experience_required FROM jobs WHERE title ILIKE '%credit limit%' LIMIT 3"
        )
        for r in rows:
            print(f"TITLE: {r['title']}")
            print(f"SKILLS: {list(r['skills'])}")
            print(f"EXP: {r['experience_required']}")
        
        total = await conn.fetchval("SELECT COUNT(*) FROM jobs")
        with_exp = await conn.fetchval("SELECT COUNT(*) FROM jobs WHERE experience_required IS NOT NULL")
        avg_skills = await conn.fetchval("SELECT AVG(array_length(skills, 1)) FROM jobs WHERE array_length(skills, 1) > 0")
        print(f"TOTAL: {total}")
        print(f"WITH_EXP: {with_exp}")
        print(f"AVG_SKILLS: {avg_skills}")

if __name__ == "__main__":
    asyncio.run(main())
