import asyncio
import json
from datetime import datetime, timezone
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.supabase import get_supabase_admin

PARSE_SYSTEM_PROMPT = """You are a job listing parser. Given a raw Hacker News comment from a "Who's Hiring" thread, extract structured data. Return ONLY valid JSON matching this schema:
{
  "company": "string or null",
  "role": "string or null",
  "role_type": "full-time | part-time | contract | internship | null",
  "location": ["array of location strings"],
  "remote": "yes | no | hybrid | null",
  "visa_sponsorship": "boolean or null",
  "salary_min": "integer or null",
  "salary_max": "integer or null",
  "salary_currency": "string (e.g. USD) or null",
  "skills": ["array of technology/skill strings"],
  "description": "string - cleaned summary of the job",
  "apply_url": "string or null",
  "apply_email": "string or null",
  "equity": "boolean or null",
  "parse_confidence": "float 0.0-1.0 based on how complete and clear the post was"
}

Rules:
- If a field cannot be determined, use null.
- For salary, extract numbers only (no currency symbols). Normalize to annual USD if possible.
- For skills, extract programming languages, frameworks, tools, and technologies.
- For location, include city and country/state if mentioned.
- parse_confidence is 0.0–1.0 based on how much information you could extract."""


async def parse_thread_jobs(thread_id: str):
    """Parse all unparsed job listings in a thread using GPT-4o-mini."""
    sb = get_supabase_admin()

    result = (
        sb.table("job_listings")
        .select("id, raw_text")
        .eq("thread_id", thread_id)
        .is_("parsed_at", "null")
        .execute()
    )

    jobs = result.data or []
    if not jobs:
        sb.table("hn_threads").update({"status": "done"}).eq("id", thread_id).execute()
        return

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    batch_size = 20
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i : i + batch_size]
        tasks = [_parse_single(client, job) for job in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for job, parse_result in zip(batch, results):
            if isinstance(parse_result, Exception):
                sb.table("job_listings").update(
                    {"is_flagged": True}
                ).eq("id", job["id"]).execute()
                continue

            now = datetime.now(timezone.utc).isoformat()
            update_data = {
                "company": parse_result.get("company"),
                "role": parse_result.get("role"),
                "role_type": parse_result.get("role_type"),
                "location": parse_result.get("location") or [],
                "remote": parse_result.get("remote"),
                "visa_sponsorship": parse_result.get("visa_sponsorship"),
                "salary_min": parse_result.get("salary_min"),
                "salary_max": parse_result.get("salary_max"),
                "salary_currency": parse_result.get("salary_currency"),
                "skills": parse_result.get("skills") or [],
                "description": parse_result.get("description"),
                "apply_url": parse_result.get("apply_url"),
                "apply_email": parse_result.get("apply_email"),
                "equity": parse_result.get("equity"),
                "parse_confidence": parse_result.get("parse_confidence"),
                "parsed_at": now,
                "is_flagged": False,
            }

            sb.table("job_listings").update(update_data).eq("id", job["id"]).execute()

    sb.table("hn_threads").update({"status": "done"}).eq("id", thread_id).execute()


async def _parse_single(client: AsyncOpenAI, job: dict) -> dict:
    """Parse a single job listing comment using GPT-4o-mini."""
    raw_text = job.get("raw_text", "")
    if not raw_text or len(raw_text.strip()) < 20:
        return {"parse_confidence": 0.0}

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": raw_text[:4000]},
        ],
        temperature=0.1,
        max_tokens=1000,
    )

    content = response.choices[0].message.content
    return json.loads(content)
