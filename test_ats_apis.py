import httpx
import asyncio

# Well-known tech companies with public Greenhouse boards
GREENHOUSE_COMPANIES = [
    "stripe", "airbnb", "cloudflare", "figma", "notion", 
    "square", "twitch", "hashicorp", "datadog", "gitlab",
    "cockroachlabs", "snyk", "vercel", "supabase", "netlify",
    "chainguard", "samsara", "airtable", "gusto", "plaid",
]

# Well-known tech companies with public Lever boards
LEVER_COMPANIES = [
    "netflix", "vimeo", "postman", "auth0", "yelp",
    "shopify", "stitchfix", "lyft", "lever", "grammarly",
]

async def test_greenhouse():
    print("=== GREENHOUSE API TEST ===")
    found = 0
    async with httpx.AsyncClient(timeout=15) as client:
        for company in GREENHOUSE_COMPANIES[:5]:
            try:
                resp = await client.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs")
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    frontend = [j for j in jobs if any(kw in j.get("title","").lower() for kw in ["frontend", "front-end", "react", "ui engineer", "web developer"])]
                    if frontend:
                        print(f"  {company}: {len(frontend)} frontend jobs (of {len(jobs)} total)")
                        j = frontend[0]
                        print(f"    Example: {j['title']}")
                        print(f"    URL: {j['absolute_url']}")
                        found += len(frontend)
                else:
                    print(f"  {company}: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  {company}: Error - {e}")
    print(f"\nTotal Greenhouse frontend jobs found: {found}\n")

async def test_lever():
    print("=== LEVER API TEST ===")
    found = 0
    async with httpx.AsyncClient(timeout=15) as client:
        for company in LEVER_COMPANIES[:5]:
            try:
                resp = await client.get(f"https://api.lever.co/v0/postings/{company}?mode=json")
                if resp.status_code == 200:
                    jobs = resp.json()
                    frontend = [j for j in jobs if any(kw in j.get("text","").lower() for kw in ["frontend", "front-end", "react", "ui engineer", "web developer"])]
                    if frontend:
                        print(f"  {company}: {len(frontend)} frontend jobs (of {len(jobs)} total)")
                        j = frontend[0]
                        print(f"    Example: {j['text']}")
                        print(f"    URL: {j['hostedUrl']}")
                        found += len(frontend)
                else:
                    print(f"  {company}: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  {company}: Error - {e}")
    print(f"\nTotal Lever frontend jobs found: {found}")

async def main():
    await test_greenhouse()
    await test_lever()

asyncio.run(main())
