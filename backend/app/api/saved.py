from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.core.auth import get_current_user
from app.core.supabase import get_supabase_admin
from app.schemas.saved import (
    SaveJobRequest,
    UpdateSavedJobRequest,
    SavedJobResponse,
    SavedStatus,
)
from app.api.jobs import _map_job

router = APIRouter(prefix="/jobs", tags=["saved"])


@router.post("/{job_id}/save", response_model=SavedJobResponse)
async def save_job(job_id: str, body: SaveJobRequest, user=Depends(get_current_user)):
    sb = get_supabase_admin()
    user_id = user.id

    existing = (
        sb.table("saved_jobs")
        .select("*")
        .eq("user_id", user_id)
        .eq("job_id", job_id)
        .maybe_single()
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Job already saved")

    result = (
        sb.table("saved_jobs")
        .insert(
            {
                "user_id": user_id,
                "job_id": job_id,
                "notes": body.notes,
                "status": body.status.value,
            }
        )
        .execute()
    )
    saved = result.data[0]
    return _map_saved(saved)


@router.put("/{job_id}/save", response_model=SavedJobResponse)
async def update_saved_job(
    job_id: str, body: UpdateSavedJobRequest, user=Depends(get_current_user)
):
    sb = get_supabase_admin()
    user_id = user.id

    existing = (
        sb.table("saved_jobs")
        .select("*")
        .eq("user_id", user_id)
        .eq("job_id", job_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Saved job not found")

    updates = {}
    if body.status is not None:
        updates["status"] = body.status.value
    if body.notes is not None:
        updates["notes"] = body.notes

    if not updates:
        return _map_saved(existing.data)

    result = (
        sb.table("saved_jobs")
        .update(updates)
        .eq("user_id", user_id)
        .eq("job_id", job_id)
        .execute()
    )
    return _map_saved(result.data[0])


@router.delete("/{job_id}/save")
async def unsave_job(job_id: str, user=Depends(get_current_user)):
    sb = get_supabase_admin()
    sb.table("saved_jobs").delete().eq("user_id", user.id).eq("job_id", job_id).execute()
    return {"ok": True}


@router.get("/saved/all", response_model=list[SavedJobResponse])
async def list_saved_jobs(
    status: Optional[SavedStatus] = Query(None),
    user=Depends(get_current_user),
):
    sb = get_supabase_admin()
    query = (
        sb.table("saved_jobs")
        .select("*, job_listings(*)")
        .eq("user_id", user.id)
        .order("saved_at", desc=True)
    )
    if status:
        query = query.eq("status", status.value)

    result = query.execute()
    return [_map_saved(s) for s in (result.data or [])]


def _map_saved(data: dict) -> SavedJobResponse:
    job_data = data.get("job_listings")
    return SavedJobResponse(
        id=data["id"],
        job_id=data["job_id"],
        saved_at=data["saved_at"],
        notes=data.get("notes"),
        status=data["status"],
        job=_map_job(job_data) if job_data else None,
    )
