from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.core.supabase import get_supabase_admin
from app.schemas.profile import (
    ProfileResponse,
    PreferencesResponse,
    UpdateProfileRequest,
    UpdatePreferencesRequest,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(user=Depends(get_current_user)):
    sb = get_supabase_admin()
    result = (
        sb.table("profiles")
        .select("*")
        .eq("id", user.id)
        .maybe_single()
        .execute()
    )

    if not result.data:
        sb.table("profiles").insert(
            {"id": user.id, "email": user.email}
        ).execute()
        return ProfileResponse(id=user.id, email=user.email)

    data = result.data
    return ProfileResponse(
        id=data["id"],
        email=data["email"],
        display_name=data.get("display_name"),
        notify_enabled=data.get("notify_enabled", False),
        notify_frequency=data.get("notify_frequency", "weekly"),
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(body: UpdateProfileRequest, user=Depends(get_current_user)):
    sb = get_supabase_admin()

    updates = body.model_dump(exclude_none=True)
    if updates.get("notify_frequency"):
        updates["notify_frequency"] = updates["notify_frequency"].value

    result = (
        sb.table("profiles")
        .upsert({"id": user.id, "email": user.email, **updates})
        .execute()
    )

    data = result.data[0]
    return ProfileResponse(
        id=data["id"],
        email=data["email"],
        display_name=data.get("display_name"),
        notify_enabled=data.get("notify_enabled", False),
        notify_frequency=data.get("notify_frequency", "weekly"),
    )


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(user=Depends(get_current_user)):
    sb = get_supabase_admin()
    result = (
        sb.table("user_preferences")
        .select("*")
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )

    if not result.data:
        return PreferencesResponse()

    data = result.data
    return PreferencesResponse(
        id=data["id"],
        roles=data.get("roles") or [],
        locations=data.get("locations") or [],
        remote_only=data.get("remote_only", False),
        visa_sponsorship=data.get("visa_sponsorship", False),
        skills=data.get("skills") or [],
        salary_min=data.get("salary_min"),
        excluded_companies=data.get("excluded_companies") or [],
    )


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    body: UpdatePreferencesRequest, user=Depends(get_current_user)
):
    sb = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)

    existing = (
        sb.table("user_preferences")
        .select("id")
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )

    if existing.data:
        result = (
            sb.table("user_preferences")
            .update(updates)
            .eq("user_id", user.id)
            .execute()
        )
    else:
        result = (
            sb.table("user_preferences")
            .insert({"user_id": user.id, **updates})
            .execute()
        )

    data = result.data[0]
    return PreferencesResponse(
        id=data["id"],
        roles=data.get("roles") or [],
        locations=data.get("locations") or [],
        remote_only=data.get("remote_only", False),
        visa_sponsorship=data.get("visa_sponsorship", False),
        skills=data.get("skills") or [],
        salary_min=data.get("salary_min"),
        excluded_companies=data.get("excluded_companies") or [],
    )
