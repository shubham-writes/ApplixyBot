import httpx
import asyncio
import urllib.parse
import re

async def run():
    # Try DuckDuckGo HTML search
    query = 'site:boards.greenhouse.io OR site:jobs.lever.co "frontend developer" remote'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        
        # very basic regex to grab result URLs
        matches = re.findall(r'href="(https://boards\.greenhouse\.io/[^"]+|https://jobs\.lever\.co/[^"]+)"', r.text)
        
        # DDG obscures URLs in a redirect parameter, e.g. //duckduckgo.com/l/?uddg=https...
        hidden = re.findall(r'uddg=([^&]+)', r.text)
        
        print("Explicit Matches:", list(set(matches)))
        print("Hidden Matches:", [urllib.parse.unquote(u) for u in set(hidden) if 'greenhouse' in urllib.parse.unquote(u) or 'lever' in urllib.parse.unquote(u)])

if __name__ == '__main__':
    asyncio.run(run())
