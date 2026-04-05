import httpx
import asyncio

async def run():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Get from Arbeitnow via api
        print("Testing Arbeitnow API...")
        r = await client.get('https://www.arbeitnow.com/api/job-board-api')
        job = r.json()['data'][0]
        url = job['url']
        print(f"Arbeitnow URL: {url}")
        r2 = await client.get(url)
        print(f"Final URL after following redirects: {r2.url}")
        
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Remotive
        print("Testing Remotive API...")
        r = await client.get('https://remotive.com/api/remote-jobs?category=software-dev&limit=1')
        job = r.json().get('jobs', [{}])[0]
        url = job.get('url')
        if url:
             r2 = await client.get(url)
             print(f"Remotive Final URL: {r2.url}")

if __name__ == '__main__':
    asyncio.run(run())
