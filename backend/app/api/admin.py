from fastapi import APIRouter, Depends, BackgroundTasks
from app.core.auth import require_admin
from app.core.supabase import get_supabase_admin
from app.services.scraper import scrape_latest_thread
from app.services.parser import parse_thread_jobs
from app.services.notifications import send_digest_notifications

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, _=Depends(require_admin)):
    background_tasks.add_task(_run_scrape_pipeline)
    return {"status": "scrape started", "message": "Scraping and parsing in background"}


async def _run_scrape_pipeline():
    thread_id = await scrape_latest_thread()
    if thread_id:
        await parse_thread_jobs(thread_id)
        await send_digest_notifications()


@router.get("/status")
async def get_pipeline_status(_=Depends(require_admin)):
    sb = get_supabase_admin()

    threads = (
        sb.table("hn_threads")
        .select("*")
        .order("month", desc=True)
        .limit(5)
        .execute()
    )

    stats = {}
    for thread in threads.data or []:
        tid = thread["id"]
        total = (
            sb.table("job_listings")
            .select("id", count="exact")
            .eq("thread_id", tid)
            .execute()
        )
        parsed = (
            sb.table("job_listings")
            .select("id", count="exact")
            .eq("thread_id", tid)
            .not_.is_("parsed_at", "null")
            .execute()
        )
        flagged = (
            sb.table("job_listings")
            .select("id", count="exact")
            .eq("thread_id", tid)
            .eq("is_flagged", True)
            .execute()
        )
        stats[thread["title"]] = {
            "status": thread["status"],
            "total_comments": total.count or 0,
            "parsed": parsed.count or 0,
            "flagged": flagged.count or 0,
            "scraped_at": thread["scraped_at"],
        }

    return {"threads": stats}


@router.post("/notify")
async def trigger_notifications(
    background_tasks: BackgroundTasks, _=Depends(require_admin)
):
    background_tasks.add_task(send_digest_notifications)
    return {"status": "notifications queued"}
