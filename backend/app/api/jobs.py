from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.auth import get_current_user, get_optional_user
from app.core.supabase import get_supabase_admin
from app.schemas.jobs import JobListingResponse, JobListResponse, RemoteType, RoleType
from app.services.match import compute_match_score, get_match_breakdown

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    search: Optional[str] = Query(None),
    remote: Optional[RemoteType] = Query(None),
    role_type: Optional[RoleType] = Query(None),
    skills: Optional[str] = Query(None, description="Comma-separated skills"),
    location: Optional[str] = Query(None),
    visa_sponsorship: Optional[bool] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    sort_by: str = Query("recent", pattern="^(recent|salary_desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    thread_id: Optional[str] = Query(None),
):
    sb = get_supabase_admin()

    query = sb.table("job_listings").select("*, hn_threads(title, month)", count="exact")

    if thread_id:
        query = query.eq("thread_id", thread_id)

    if search:
        query = query.or_(
            f"company.ilike.%{search}%,role.ilike.%{search}%,description.ilike.%{search}%,skills.cs.{{{search}}}"
        )

    if remote:
        query = query.eq("remote", remote.value)

    if role_type:
        query = query.eq("role_type", role_type.value)

    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        query = query.overlaps("skills", skill_list)

    if location:
        query = query.contains("location", [location])

    if visa_sponsorship is not None:
        query = query.eq("visa_sponsorship", visa_sponsorship)

    if salary_min is not None:
        query = query.gte("salary_max", salary_min)

    if salary_max is not None:
        query = query.lte("salary_min", salary_max)

    if sort_by == "salary_desc":
        query = query.order("salary_max", desc=True, nullsfirst=False)
    else:
        query = query.order("parsed_at", desc=True, nullsfirst=False)

    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()

    jobs = [_map_job(j) for j in (result.data or [])]
    total = result.count or 0

    return JobListResponse(jobs=jobs, total=total, page=page, per_page=per_page)


@router.get("/for-you", response_model=JobListResponse)
async def for_you_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
):
    sb = get_supabase_admin()
    user_id = user.id

    prefs_result = sb.table("user_preferences").select("*").eq("user_id", user_id).maybe_single().execute()
    prefs = prefs_result.data

    if not prefs:
        latest_thread = sb.table("hn_threads").select("id").order("month", desc=True).limit(1).execute()
        thread_filter = latest_thread.data[0]["id"] if latest_thread.data else None
        query = sb.table("job_listings").select("*", count="exact")
        if thread_filter:
            query = query.eq("thread_id", thread_filter)
        query = query.order("parsed_at", desc=True).range(0, per_page - 1)
        result = query.execute()
        jobs = [_map_job(j) for j in (result.data or [])]
        return JobListResponse(jobs=jobs, total=result.count or 0, page=1, per_page=per_page)

    latest_thread = sb.table("hn_threads").select("id").order("month", desc=True).limit(1).execute()
    thread_id = latest_thread.data[0]["id"] if latest_thread.data else None

    query = sb.table("job_listings").select("*", count="exact")
    if thread_id:
        query = query.eq("thread_id", thread_id)
    query = query.not_.is_("company", "null")

    result = query.execute()
    all_jobs = result.data or []

    scored_jobs = []
    for j in all_jobs:
        score = compute_match_score(j, prefs)
        j["match_score"] = score
        scored_jobs.append(j)

    scored_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    offset = (page - 1) * per_page
    page_jobs = scored_jobs[offset : offset + per_page]

    jobs = [_map_job(j) for j in page_jobs]
    return JobListResponse(jobs=jobs, total=len(scored_jobs), page=page, per_page=per_page)


@router.get("/{job_id}", response_model=JobListingResponse)
async def get_job(job_id: str):
    sb = get_supabase_admin()
    result = sb.table("job_listings").select("*").eq("id", job_id).single().execute()
    return _map_job(result.data)


@router.get("/{job_id}/match")
async def get_job_match(job_id: str, user=Depends(get_current_user)):
    sb = get_supabase_admin()
    job_result = sb.table("job_listings").select("*").eq("id", job_id).single().execute()
    job = job_result.data

    prefs_result = (
        sb.table("user_preferences")
        .select("*")
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )
    prefs = prefs_result.data

    if not prefs:
        return {
            "total_score": 0,
            "matched_skills": [],
            "skill_score": 0,
            "role_match": False,
            "location_match": False,
            "remote_match": False,
            "salary_fit": False,
        }

    return get_match_breakdown(job, prefs)


def _map_job(data: dict) -> JobListingResponse:
    return JobListingResponse(
        id=data["id"],
        thread_id=data.get("thread_id", ""),
        hn_comment_id=data.get("hn_comment_id", ""),
        company=data.get("company"),
        role=data.get("role"),
        role_type=data.get("role_type"),
        location=data.get("location") or [],
        remote=data.get("remote"),
        visa_sponsorship=data.get("visa_sponsorship"),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        salary_currency=data.get("salary_currency"),
        skills=data.get("skills") or [],
        description=data.get("description"),
        apply_url=data.get("apply_url"),
        apply_email=data.get("apply_email"),
        equity=data.get("equity"),
        parsed_at=data.get("parsed_at"),
        parse_confidence=data.get("parse_confidence"),
        raw_text=data.get("raw_text"),
        match_score=data.get("match_score"),
    )
