import asyncio
from services.ats_analyzer import analyze_resume_match
from loguru import logger

async def main():
    resume = """
    Software Engineer with 4 years experience.
    Skills: Next.js, React, Node.js, Python, PostgreSQL, MySQL.
    Experience building high-scale APIs and RESTful microservices.
    Familiar with Docker and AWS but primarily a frontend leaning full-stack dev.
    """
    
    jd = """
    Senior Full Stack Engineer
    At our company, we are seeking a leader to build scalable data pipelines.
    Required Tech: Python, Django, PostgreSQL, Kubernetes, AWS, Go.
    Nice to have: React, TypeScript, Kafka.
    """

    res = await analyze_resume_match(resume, jd)
    import pprint
    pprint.pprint(res)

if __name__ == "__main__":
    asyncio.run(main())
