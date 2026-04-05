"""
Job scraper — aggregates frontend jobs from 5 free sources.
Runs every 2 hours via APScheduler.
"""
import re
import hashlib
from datetime import datetime, timezone
import httpx
import feedparser
from loguru import logger

# ──────────────────────────────────────────────
# Skill detection patterns
# ──────────────────────────────────────────────
SKILL_PATTERNS = {
    # Frontend Core
    "javascript": r"\bjavascript\b|\bjs\b",
    "typescript": r"\btypescript\b",
    "react": r"\breact\.js\b|\breactjs\b|\breact(?!\s+(?:to|fast|quickly|with|against|in|on|accordingly|positively))\b",
    "vue": r"\bvue(?:\.?js)?\b",
    "angular": r"\bangular(?:js)?\b",
    "next.js": r"\bnext\.js\b|\bnextjs\b|\bnext\sjs\b",
    "svelte": r"\bsvelte\b",
    "react native": r"\breact[\s-]native\b",
    
    # Markup & Styling
    "html": r"\bhtml5?\b",
    "css": r"\bcss3?\b",
    "tailwind": r"\btailwind(?:\s?css)?\b",
    "sass": r"\bsass\b|\bscss\b",
    
    # Backend & Runtime
    "node": r"\bnode(?:\.?js)?\b",
    "python": r"\bpython\b",
    "java": r"\bjava\b(?!script)",
    "kotlin": r"\bkotlin\b",
    "go": r"\bgolang\b|\bgo\s+lang\b|\bgo\b(?=\s+(?:application|developer|engineer|service|backend|micro))",
    "ruby": r"\bruby\b",
    "rust": r"\brustlang\b|\brust\b",
    "php": r"\bphp\b",
    "c#": r"\bc#\b|\.net\b",
    "swift": r"\bswift\b",
    "elixir": r"\belixir\b",
    
    # Databases
    "postgresql": r"\bpostgres(?:ql)?\b",
    "mysql": r"\bmysql\b",
    "mongodb": r"\bmongo(?:db)?\b",
    "redis": r"\bredis\b",
    "dynamodb": r"\bdynamo\s?db\b",
    "sql": r"\bsql\b(?!ite)",
    
    # APIs & Data
    "graphql": r"\bgraphql\b",
    "rest": r"\brest(?:ful)?\s*api\b|\brest\b",
    "grpc": r"\bgrpc\b",
    "kafka": r"\bkafka\b",
    "rabbitmq": r"\brabbitmq\b",
    
    # Cloud & DevOps
    "aws": r"\baws\b|\bamazon\s+web\s+services\b",
    "gcp": r"\bgcp\b|\bgoogle\s+cloud\b",
    "azure": r"\bazure\b",
    "docker": r"\bdocker\b",
    "kubernetes": r"\bkubernetes\b|\bk8s\b",
    "terraform": r"\bterraform\b",
    "ci/cd": r"\bci/?cd\b|\bcontinuous\s+(?:integration|delivery|deployment)\b",
    "github actions": r"\bgithub\s+actions\b",
    
    # Tools & Design
    "git": r"\bgit(?:hub|lab)?\b",
    "figma": r"\bfigma\b",
    "webpack": r"\bwebpack\b",
    "vite": r"\bvite\b",
    "storybook": r"\bstorybook\b",
    "jest": r"\bjest\b",
    "cypress": r"\bcypress\b",
    "playwright": r"\bplaywright\b",
}


def extract_skills(text: str) -> list[str]:
    """Extract skill tags from job title + description text."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for skill, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def extract_experience(text: str) -> int | None:
    """Extract required years of experience from job text.
    Finds ALL mentions and returns the highest (most relevant) value.
    """
    if not text:
        return None
    text_lower = text.lower()
    
    patterns = [
        r"(\d+)\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"(\d+)\s*to\s*\d+\s*years?\s+of\s+experience",
        r"(\d+)\+?\s*years?\s+experience",
        r"minimum\s+(?:of\s+)?(\d+)\s*years?",
        r"at\s+least\s+(\d+)\s*years?",
    ]
    
    all_values = []
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower):
            try:
                val = int(match.group(1))
                if val <= 20:  # sanity check: ignore absurd values
                    all_values.append(val)
            except ValueError:
                pass
    
    return max(all_values) if all_values else None


def extract_job_type(text: str, title: str = "") -> str:
    """Extract job type (full-time, internship, contract) from text and title."""
    combined = f"{title} {text}".lower()
    
    if re.search(r"\b(?:intern|internship)\b", combined):
        return "internship"
    if re.search(r"\b(?:contract|contractor|freelance)\b", combined):
        return "contract"
    if re.search(r"\b(?:part-time|part time)\b", combined):
        return "part-time"
        
    return "full-time"


def extract_internship_duration(text: str) -> str | None:
    """Extract duration for internships (e.g. '6 months')."""
    if not text:
        return None
    text_lower = text.lower()
    
    patterns = [
        r"duration(?:.*?)(?:is\s+)?(\d+\s*(?:months?|weeks?))",
        r"(\d+\s*(?:months?|weeks?))\s*(?:internship|contract)",
        r"(?:internship|contract)(?:.*?)for\s+(\d+\s*(?:months?|weeks?))"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1).strip()
            
    return None


def extract_salary(text: str) -> str | None:
    """Extract raw salary strings like $100k - $120k or ₹8 LPA if not provided by API."""
    if not text:
        return None
    
    patterns = [
        r"(?:\$|usd\s*)?\d+(?:,\d{3})*(?:k)?\s*(?:-|to)\s*(?:\$|usd\s*)?\d+(?:,\d{3})*(?:k)?\b",
        r"(?:₹|inr\s*)?\d+(?:\.\d+)?\s*(?:lpa|lakhs?)(?:\s*(?:-|to)\s*(?:₹|inr\s*)?\d+(?:\.\d+)?\s*(?:lpa|lakhs?))?\b",
        r"(?:₹|inr\s*)?\d+(?:,\d{3})*(?:\s*/\s*mo(?:nth)?|\s*per\s*month)",
        r"(?:\$|usd\s*)?\d+(?:,\d{3})*(?:\s*/\s*mo(?:nth)?|\s*per\s*month)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(0).strip().title()
            
    return None


def detect_portal_type(url: str) -> str:
    """Detect if a job URL is from a supported auto-apply portal."""
    if not url:
        return "other"
    url_lower = url.lower()
    if "boards.greenhouse.io" in url_lower or "greenhouse.io" in url_lower:
        return "greenhouse"
    if "jobs.lever.co" in url_lower or "lever.co" in url_lower:
        return "lever"
    if "apply.workable.com" in url_lower or "workable.com" in url_lower:
        return "workable"
    return "other"


import os

def load_allowed_titles() -> set[str]:
    """Load strict job titles from Job_titles.txt"""
    allowed = set()
    filepath = os.path.join(os.path.dirname(__file__), "Job_titles.txt")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("🔹"):
                    allowed.add(line.rstrip(",").lower().strip())
    return allowed

ALLOWED_TITLES = load_allowed_titles()

def hash_url(url: str) -> str:
    """MD5 hash for dedup."""
    return hashlib.md5(url.strip().lower().encode()).hexdigest()


def _normalize_job(
    title: str,
    company: str | None,
    url: str,
    location: str | None,
    salary: str | None,
    source: str,
    posted_at: datetime | None = None,
    extra_text: str = "",
) -> dict | None:
    """Normalize a job into a standard dict format. Returns None if filtered out."""
    
    # ── Strict Filtering ──
    title_clean = title.lower() if title else ""
    
    # Strict title match: Title must contain one of the allowed titles
    if ALLOWED_TITLES:
        if not any(allowed in title_clean for allowed in ALLOWED_TITLES):
            return None
            
    full_text = f"{title} {extra_text}"
    exp_req = extract_experience(full_text)
    
    # Strict Experience match: Filter out >= 5 years
    if exp_req is not None and exp_req >= 5:
        return None
    
    final_salary = salary.strip() if salary else extract_salary(full_text)
    job_type = extract_job_type(extra_text, title)
    
    return {
        "title": title.strip() if title else "Untitled",
        "company": company.strip() if company else None,
        "url": url.strip(),
        "url_hash": hash_url(url),
        "location": location.strip() if location else None,
        "salary": final_salary,
        "job_type": job_type,
        "duration": extract_internship_duration(full_text) if job_type == "internship" else None,
        "skills": extract_skills(full_text),
        "experience_required": exp_req,
        "source": source,
        "portal_type": detect_portal_type(url),
        "posted_at": posted_at,
    }


# ──────────────────────────────────────────────
# Individual scrapers
# ──────────────────────────────────────────────

async def scrape_remotive() -> list[dict]:
    """Scrape Remotive API — free, no auth, JSON response."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://remotive.com/api/remote-jobs",
                params={"category": "software-dev", "limit": 250},
            )
            resp.raise_for_status()
            data = resp.json()

            for job in data.get("jobs", []):
                title = job.get("title", "")
                # Filter for frontend-related jobs
                full_text = f"{title} {job.get('description', '')}".lower()
                if not any(
                    kw in full_text
                    for kw in ["frontend", "front-end", "front end", "react", "vue", "angular", "next.js", "svelte", "ui developer", "ui engineer"]
                ):
                    continue

                posted = None
                if job.get("publication_date"):
                    try:
                        posted = datetime.fromisoformat(
                            job["publication_date"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

                jobs.append(
                    _normalize_job(
                        title=title,
                        company=job.get("company_name"),
                        url=job.get("url", ""),
                        location=job.get("candidate_required_location", "Remote"),
                        salary=job.get("salary"),
                        source="remotive",
                        posted_at=posted,
                        extra_text=job.get("description", ""),
                    )
                )

        logger.info(f"Remotive: scraped {len(jobs)} frontend jobs")
    except Exception as e:
        logger.error(f"Remotive scraper failed: {e}")
    return jobs


async def scrape_weworkremotely() -> list[dict]:
    """Scrape WeWorkRemotely RSS feed — programming jobs."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://weworkremotely.com/categories/remote-programming-jobs.rss"
            )
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:100]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}".lower()

            if not any(
                kw in full_text
                for kw in ["frontend", "front-end", "react", "vue", "angular", "next.js", "svelte", "typescript", "javascript", "ui"]
            ):
                continue

            posted = None
            if entry.get("published_parsed"):
                try:
                    posted = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Extract company from title (usually "Company: Role")
            company = None
            if ":" in title:
                company = title.split(":")[0].strip()
                title = title.split(":", 1)[1].strip()

            jobs.append(
                _normalize_job(
                    title=title,
                    company=company,
                    url=entry.get("link", ""),
                    location="Remote",
                    salary=None,
                    source="wwr",
                    posted_at=posted,
                    extra_text=summary,
                )
            )

        logger.info(f"WeWorkRemotely: scraped {len(jobs)} frontend jobs")
    except Exception as e:
        logger.error(f"WeWorkRemotely scraper failed: {e}")
    return jobs


async def scrape_indeed_rss() -> list[dict]:
    """Scrape Indeed RSS feed for frontend developer jobs."""
    jobs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            resp = await client.get(
                "https://www.indeed.com/rss",
                params={"q": "frontend developer", "l": "remote"},
            )
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:100]:
            posted = None
            if entry.get("published_parsed"):
                try:
                    posted = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            jobs.append(
                _normalize_job(
                    title=entry.get("title", ""),
                    company=entry.get("source", {}).get("value") if hasattr(entry.get("source", {}), "get") else None,
                    url=entry.get("link", ""),
                    location="Remote",
                    salary=None,
                    source="indeed",
                    posted_at=posted,
                    extra_text=entry.get("summary", ""),
                )
            )

        logger.info(f"Indeed RSS: scraped {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"Indeed RSS scraper failed: {e}")
    return jobs


async def scrape_arbeitnow() -> list[dict]:
    """Scrape Arbeitnow API — free, no auth, JSON."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get("https://www.arbeitnow.com/api/job-board-api")
            resp.raise_for_status()
            data = resp.json()

            for job in data.get("data", [])[:150]:
                title = job.get("title", "")
                description = job.get("description", "")
                full_text = f"{title} {description}".lower()

                if not any(
                    kw in full_text
                    for kw in ["frontend", "front-end", "react", "vue", "angular", "next.js", "svelte", "typescript", "javascript"]
                ):
                    continue

                posted = None
                if job.get("created_at"):
                    try:
                        posted = datetime.fromtimestamp(
                            job["created_at"], tz=timezone.utc
                        )
                    except (ValueError, TypeError, OSError):
                        pass

                jobs.append(
                    _normalize_job(
                        title=title,
                        company=job.get("company_name"),
                        url=job.get("url", ""),
                        location=job.get("location", ""),
                        salary=None,
                        source="arbeitnow",
                        posted_at=posted,
                        extra_text=description,
                    )
                )

        logger.info(f"Arbeitnow: scraped {len(jobs)} frontend jobs")
    except Exception as e:
        logger.error(f"Arbeitnow scraper failed: {e}")
    return jobs


async def scrape_jobicy() -> list[dict]:
    """Scrape Jobicy RSS/feed — remote-friendly dev jobs."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://jobicy.com/",
                params={"feed": "job_feed", "job_categories": "dev"},
            )
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:100]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}".lower()

            if not any(
                kw in full_text
                for kw in ["frontend", "front-end", "react", "vue", "angular", "next.js", "svelte", "typescript"]
            ):
                continue

            posted = None
            if entry.get("published_parsed"):
                try:
                    posted = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            jobs.append(
                _normalize_job(
                    title=title,
                    company=None,
                    url=entry.get("link", ""),
                    location="Remote",
                    salary=None,
                    source="jobicy",
                    posted_at=posted,
                    extra_text=summary,
                )
            )

        logger.info(f"Jobicy: scraped {len(jobs)} frontend jobs")
    except Exception as e:
        logger.error(f"Jobicy scraper failed: {e}")
    return jobs


# ──────────────────────────────────────────────
# Greenhouse Direct API Scraper (AUTO-APPLY READY)
# ──────────────────────────────────────────────

# Companies with public Greenhouse job boards
GREENHOUSE_COMPANIES = [
    "stripe", "airbnb", "cloudflare", "figma", "square",
    "twitch", "hashicorp", "datadog", "gitlab", "cockroachlabs",
    "snyk", "vercel", "netlify", "chainguard", "samsara",
    "airtable", "gusto", "plaid", "sourcegraph", "webflow",
    "benchling", "retool", "brex", "ramp", "rippling",
    "ironclad", "launchdarkly", "stytch", "persona", "vanta",
]

# Frontend-related keywords
FRONTEND_KEYWORDS = [
    "frontend", "front-end", "front end", "react", "vue",
    "angular", "ui engineer", "web developer", "web engineer",
    "javascript engineer", "typescript", "next.js", "nextjs",
]


async def scrape_greenhouse_boards() -> list[dict]:
    """Scrape frontend jobs directly from Greenhouse public API.
    These jobs have native greenhouse.io URLs = auto-apply ready!
    """
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for company in GREENHOUSE_COMPANIES:
                try:
                    resp = await client.get(
                        f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
                        params={"content": "true"},
                    )
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    for job in data.get("jobs", []):
                        title = job.get("title", "")
                        title_lower = title.lower()

                        # Filter for frontend-related roles
                        if not any(kw in title_lower for kw in FRONTEND_KEYWORDS):
                            # Also check content/description
                            content = job.get("content", "")
                            if not any(kw in content.lower() for kw in FRONTEND_KEYWORDS[:6]):
                                continue

                        # Get location
                        location_parts = []
                        for loc in job.get("location", {}).get("name", "").split(","):
                            location_parts.append(loc.strip())
                        location = ", ".join(location_parts) if location_parts else "Remote"

                        # Parse posted date
                        posted = None
                        if job.get("updated_at"):
                            try:
                                posted = datetime.fromisoformat(
                                    job["updated_at"].replace("Z", "+00:00")
                                )
                            except (ValueError, TypeError):
                                pass

                        url = job.get("absolute_url", "")
                        description = job.get("content", "")

                        jobs.append(
                            _normalize_job(
                                title=title,
                                company=company.replace("-", " ").title(),
                                url=url,
                                location=location,
                                salary=None,
                                source="greenhouse",
                                posted_at=posted,
                                extra_text=description,
                            )
                        )
                except Exception as e:
                    logger.warning(f"Greenhouse board {company} failed: {e}")
                    continue

        logger.info(f"Greenhouse Boards: scraped {len(jobs)} frontend jobs (auto-apply ready)")
    except Exception as e:
        logger.error(f"Greenhouse boards scraper failed: {e}")
    return jobs


# ──────────────────────────────────────────────
# Master scraper
# ──────────────────────────────────────────────

async def scrape_all_sources() -> list[dict]:
    """
    Run all scrapers concurrently and return deduplicated results.
    Failed scrapers are logged but don't block others.
    """
    import asyncio

    results = await asyncio.gather(
        scrape_remotive(),
        scrape_weworkremotely(),
        scrape_indeed_rss(),
        scrape_arbeitnow(),
        scrape_jobicy(),
        scrape_greenhouse_boards(),  # NEW: Direct ATS jobs
        return_exceptions=True,
    )

    all_jobs = []
    seen_hashes = set()

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Scraper {i} raised exception: {result}")
            continue
        for job in result:
            if job is None:
                continue
                
            # Filter out jobs older than 60 days
            if job.get("posted_at"):
                from datetime import datetime, timezone
                job_posted = job["posted_at"]
                if job_posted.tzinfo is None:
                    job_posted = job_posted.replace(tzinfo=timezone.utc)
                diff = datetime.now(timezone.utc) - job_posted
                if diff.days > 60:
                    continue

            h = job.get("url_hash") or hash_url(job["url"])
            if h not in seen_hashes:
                seen_hashes.add(h)
                all_jobs.append(job)

    logger.info(f"Total scraped: {len(all_jobs)} unique frontend jobs from {len(results)} sources")
    return all_jobs
