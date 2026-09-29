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
            .select("id")
            .eq("hn_post_id", hn_post_id)
            .maybe_single()
            .execute()
        )
        if existing.data:
            return existing.data["id"]

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

        if comments:
            rows = [
                {
                    "thread_id": thread_id,
                    "hn_comment_id": c["objectID"],
                    "raw_text": c.get("comment_text", ""),
                }
                for c in comments
                if c.get("comment_text") and c.get("parent_id") == int(hn_post_id)
            ]

            batch_size = 500
            for i in range(0, len(rows), batch_size):
                sb.table("job_listings").insert(rows[i : i + batch_size]).execute()

        sb.table("hn_threads").update({"status": "parsing"}).eq("id", thread_id).execute()

        return thread_id


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
