import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.get('https://arbeitnow.com/api/job-board-api')
        jobs = r.json().get('data', [])
        if jobs:
            print("Arbeitnow keys:", list(jobs[0].keys()))

        r = await client.get('https://www.indeed.com/rss', params={"q": "frontend developer", "l": "remote"}, headers={"User-Agent": "Mozilla/5.0"})
        print("Indeed RSS has raw feed urls inside <link>")

if __name__ == '__main__':
    asyncio.run(run())
