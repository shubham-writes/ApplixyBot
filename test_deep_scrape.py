import httpx
import asyncio
import re

async def run():
    async with httpx.AsyncClient() as client:
        # Remotive
        print("Testing Remotive API...")
        r = await client.get('https://remotive.com/api/remote-jobs?category=software-dev&limit=1')
        job = r.json().get('jobs', [{}])[0]
        url = job.get('url')
        print(f"Aggregator URL: {url}")
        
        # Fetch the HTML
        html_resp = await client.get(url)
        html = html_resp.text
        
        # Try to find the apply link (usually contains something like class="apply" or text="Apply")
        # In remotive, the apply button is often a link with class containing 'apply' or going to /job/.../apply
        matches = re.findall(r'href=["\']([^"\']+/apply)[\'"]', html)
        if matches:
            apply_link = matches[0]
            if not apply_link.startswith('http'):
                apply_link = 'https://remotive.com' + apply_link
            print(f"Apply redirect link found: {apply_link}")
            
            # Now follow THAT link to see where it goes
            final_resp = await client.get(apply_link, follow_redirects=True)
            print(f"Final true destination: {final_resp.url}")
        else:
            print("No apply link found via Regex.")

if __name__ == '__main__':
    asyncio.run(run())
