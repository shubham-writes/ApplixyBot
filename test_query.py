import asyncio
from db.connection import init_db
from db.jobs import get_matching_jobs, count_matching_jobs
from db.users import get_user

async def run():
    await init_db()
    telegram_id = 5187310177
    user = await get_user(telegram_id)
    if not user:
        print("User not found.")
        return
        
    skills = user.get("skills", [])
    location = user.get("location_pref", "remote")
    print(f"User skills: {skills}")
    print(f"User location: {location}")
    
    count = await count_matching_jobs(skills, location)
    print(f"Count: {count}")
    
    jobs = await get_matching_jobs(skills, location, limit=5)
    print(f"Jobs returned: {len(jobs)}")
    for j in jobs:
        print(j['title'])
        
if __name__ == "__main__":
    asyncio.run(run())
