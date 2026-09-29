from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from app.schemas.jobs import JobListingResponse


class SavedStatus(str, Enum):
    saved = "saved"
    applied = "applied"
    interviewing = "interviewing"
    rejected = "rejected"
    offer = "offer"


class SaveJobRequest(BaseModel):
    notes: Optional[str] = None
    status: SavedStatus = SavedStatus.saved


class UpdateSavedJobRequest(BaseModel):
    notes: Optional[str] = None
    status: Optional[SavedStatus] = None


class SavedJobResponse(BaseModel):
    id: str
    job_id: str
    saved_at: datetime
    notes: Optional[str] = None
    status: SavedStatus
    job: Optional[JobListingResponse] = None
