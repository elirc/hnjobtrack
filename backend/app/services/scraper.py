import httpx
from datetime import datetime, timezone
from app.core.supabase import get_supabase_admin

HN_ALGOLIA_BASE = "https://hn.algolia.com/api/v1"


async def scrape_latest_thread() -> str | None:
    """Find the latest 'Who's Hiring' thread and scrape all comments."""
    async with httpx.AsyncClient(timeout=30) as client:
        search_resp = await client.get(
            f"{HN_ALGOLIA_BASE}/search",
            params={
                "query": "Ask HN: Who is hiring?",
                "tags": "story,author_whoishiring",
                "hitsPerPage": 1,
            },
        )
        search_resp.raise_for_status()
        data = search_resp.json()

        if not data.get("hits"):
            return None

        thread = data["hits"][0]
        hn_post_id = thread["objectID"]
        title = thread["title"]

        sb = get_supabase_admin()

        existing = (
            sb.table("hn_threads")
            .select("id,status")
            .eq("hn_post_id", hn_post_id)
            .maybe_single()
            .execute()
        )
        if existing.data:
            # A prior run may have created the thread before its HTTP request
            # completed.  Re-fetch and upsert comments so retries are
            # resumable and idempotent instead of silently skipping the import.
            thread_id = existing.data["id"]
            if existing.data.get("status") == "done":
                return thread_id
            comments = await _fetch_all_comments(client, hn_post_id)
            await _import_comments(sb, thread_id, hn_post_id, comments)
            sb.table("hn_threads").update({"status": "parsing"}).eq("id", thread_id).execute()
            return thread_id

        now = datetime.now(timezone.utc).isoformat()
        month_str = _extract_month(title)

        thread_result = (
            sb.table("hn_threads")
            .insert(
                {
                    "hn_post_id": hn_post_id,
                    "title": title,
                    "month": month_str,
                    "scraped_at": now,
                    "status": "pending",
                }
            )
            .execute()
        )
        thread_id = thread_result.data[0]["id"]

        comments = await _fetch_all_comments(client, hn_post_id)
        await _import_comments(sb, thread_id, hn_post_id, comments)

        sb.table("hn_threads").update({"status": "parsing"}).eq("id", thread_id).execute()

        return thread_id


async def _import_comments(sb, thread_id: str, hn_post_id: str, comments: list[dict]) -> int:
    """Insert missing top-level comments, preserving existing raw and parsed data.

    The unique key in the schema makes retries safe even when a worker is
    interrupted between batches.  Returning the count gives callers/tests a
    attempted eligible-row count, not the number of newly inserted rows.
    """
    rows = [
        {
            "thread_id": thread_id,
            "hn_comment_id": c["objectID"],
            "raw_text": c.get("comment_text", ""),
        }
        for c in comments
        if c.get("comment_text") and c.get("parent_id") == int(hn_post_id)
    ]
    for i in range(0, len(rows), 500):
        sb.table("job_listings").upsert(
            rows[i : i + 500], on_conflict="thread_id,hn_comment_id", ignore_duplicates=True,
            default_to_null=False,
        ).execute()
    return len(rows)


async def _fetch_all_comments(
    client: httpx.AsyncClient, story_id: str
) -> list[dict]:
    """Fetch all top-level comments from a HN story using Algolia API."""
    all_comments = []
    page = 0

    while True:
        resp = await client.get(
            f"{HN_ALGOLIA_BASE}/search",
            params={
                "tags": f"comment,story_{story_id}",
                "hitsPerPage": 100,
                "page": page,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            break
        all_comments.extend(hits)
        if page >= data.get("nbPages", 0) - 1:
            break
        page += 1

    return all_comments


def _extract_month(title: str) -> str:
    """Extract month from thread title like 'Ask HN: Who is hiring? (January 2025)'."""
    import re

    match = re.search(r"\((\w+ \d{4})\)", title)
    if match:
        try:
            dt = datetime.strptime(match.group(1), "%B %Y")
            return dt.strftime("%Y-%m-01")
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-01")
