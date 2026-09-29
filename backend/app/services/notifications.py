import resend
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.supabase import get_supabase_admin
from app.services.match import compute_match_score

resend.api_key = settings.resend_api_key

TOP_N_JOBS = 10


async def send_digest_notifications(frequency: str = "instant"):
    """Send job match digest emails to users with the specified notification frequency.

    Args:
        frequency: One of "instant", "daily", or "weekly". Only users whose
                   notify_frequency matches this value will receive emails.
    """
    sb = get_supabase_admin()

    profiles = (
        sb.table("profiles")
        .select("id, email, display_name, notify_frequency")
        .eq("notify_enabled", True)
        .eq("notify_frequency", frequency)
        .execute()
    )

    if not profiles.data:
        return

    latest_thread = (
        sb.table("hn_threads")
        .select("id, title")
        .order("month", desc=True)
        .limit(1)
        .execute()
    )
    if not latest_thread.data:
        return

    thread = latest_thread.data[0]
    thread_id = thread["id"]

    all_jobs_result = (
        sb.table("job_listings")
        .select("*")
        .eq("thread_id", thread_id)
        .not_.is_("company", "null")
        .execute()
    )
    all_jobs = all_jobs_result.data or []

    # For daily/weekly digests, only include jobs parsed since last digest window
    if frequency == "daily":
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        all_jobs = [j for j in all_jobs if j.get("parsed_at") and j["parsed_at"] >= cutoff.isoformat()]
    elif frequency == "weekly":
        cutoff = datetime.now(timezone.utc) - timedelta(weeks=1)
        all_jobs = [j for j in all_jobs if j.get("parsed_at") and j["parsed_at"] >= cutoff.isoformat()]

    if not all_jobs:
        return

    for profile in profiles.data:
        user_id = profile["id"]
        email = profile["email"]

        prefs_result = (
            sb.table("user_preferences")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        prefs = prefs_result.data
        if not prefs:
            continue

        scored = []
        for job in all_jobs:
            s = compute_match_score(job, prefs)
            if s > 20:
                scored.append({**job, "match_score": s})

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        top_jobs = scored[:TOP_N_JOBS]

        if not top_jobs:
            continue

        html = _build_email_html(profile, top_jobs, thread["title"])

        try:
            resend.Emails.send(
                {
                    "from": settings.from_email,
                    "to": [email],
                    "subject": f"Your Top Job Matches - {thread['title']}",
                    "html": html,
                }
            )

            sb.table("notifications_log").insert(
                {
                    "user_id": user_id,
                    "job_ids": [j["id"] for j in top_jobs],
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "email": email,
                }
            ).execute()
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")


def _build_email_html(profile: dict, jobs: list[dict], thread_title: str) -> str:
    name = profile.get("display_name") or profile["email"].split("@")[0]
    frontend = settings.frontend_url

    job_rows = ""
    for job in jobs:
        company = job.get("company") or "Unknown"
        role = job.get("role") or "Unknown Role"
        location = ", ".join(job.get("location") or ["Not specified"])
        remote = job.get("remote") or ""
        salary = ""
        if job.get("salary_min") and job.get("salary_max"):
            salary = f"${job['salary_min']:,} - ${job['salary_max']:,}"
        elif job.get("salary_min"):
            salary = f"${job['salary_min']:,}+"
        score = int(job.get("match_score", 0))
        skills = ", ".join((job.get("skills") or [])[:5])

        job_rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
          <td style="padding: 16px;">
            <div style="font-weight: 600; font-size: 16px; color: #111827;">{company}</div>
            <div style="color: #4b5563; margin-top: 4px;">{role}</div>
            <div style="color: #6b7280; font-size: 13px; margin-top: 4px;">
              {location} {f'| {remote}' if remote else ''} {f'| {salary}' if salary else ''}
            </div>
            <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">{skills}</div>
          </td>
          <td style="padding: 16px; text-align: center;">
            <span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 14px;">
              {score}%
            </span>
          </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f9fafb; padding: 40px 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="background: #ff6600; padding: 24px; text-align: center;">
          <h1 style="color: white; margin: 0; font-size: 24px;">HN Jobs</h1>
          <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">Your Top Job Matches</p>
        </div>
        <div style="padding: 24px;">
          <p style="color: #374151;">Hi {name},</p>
          <p style="color: #374151;">Here are your top job matches from <strong>{thread_title}</strong>:</p>
          <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
            {job_rows}
          </table>
          <div style="text-align: center; margin-top: 24px;">
            <a href="{frontend}/dashboard/for-you" style="background: #ff6600; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">
              View All Matches
            </a>
          </div>
        </div>
        <div style="background: #f9fafb; padding: 16px 24px; text-align: center; font-size: 12px; color: #9ca3af;">
          <a href="{frontend}/profile" style="color: #6b7280;">Manage preferences</a> |
          <a href="{frontend}/profile?unsubscribe=true" style="color: #6b7280;">Unsubscribe</a>
        </div>
      </div>
    </body>
    </html>
    """
