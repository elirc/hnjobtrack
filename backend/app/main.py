from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.api import jobs, saved, profile, admin
from app.services.scraper import scrape_latest_thread
from app.services.parser import parse_thread_jobs
from app.services.notifications import send_digest_notifications

scheduler = AsyncIOScheduler()


async def monthly_scrape_job():
    """Run on the 1st of each month to scrape and parse new thread."""
    thread_id = await scrape_latest_thread()
    if thread_id:
        await parse_thread_jobs(thread_id)
        # Notify "instant" users right after new thread is parsed
        await send_digest_notifications(frequency="instant")


async def daily_digest_job():
    """Send daily digest emails."""
    await send_digest_notifications(frequency="daily")


async def weekly_digest_job():
    """Send weekly digest emails every Monday."""
    await send_digest_notifications(frequency="weekly")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Monthly scrape on the 1st at noon UTC
    scheduler.add_job(monthly_scrape_job, "cron", day=1, hour=12, minute=0)
    # Daily digest at 9am UTC
    scheduler.add_job(daily_digest_job, "cron", hour=9, minute=0)
    # Weekly digest every Monday at 9am UTC
    scheduler.add_job(weekly_digest_job, "cron", day_of_week="mon", hour=9, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="HN Jobs API",
    description="Hacker News Who's Hiring job browser and tracker",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(saved.router)
app.include_router(profile.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
