from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class RemoteType(str, Enum):
    yes = "yes"
    no = "no"
    hybrid = "hybrid"


class RoleType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"


class JobListingResponse(BaseModel):
    id: str
    thread_id: str
    hn_comment_id: str
    company: Optional[str] = None
    role: Optional[str] = None
    role_type: Optional[RoleType] = None
    location: list[str] = []
    remote: Optional[RemoteType] = None
    visa_sponsorship: Optional[bool] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    skills: list[str] = []
    description: Optional[str] = None
    apply_url: Optional[str] = None
    apply_email: Optional[str] = None
    equity: Optional[bool] = None
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None
    raw_text: Optional[str] = None
    match_score: Optional[float] = None


class JobListResponse(BaseModel):
    jobs: list[JobListingResponse]
    total: int
    page: int
    per_page: int


class JobFilters(BaseModel):
    search: Optional[str] = None
    remote: Optional[RemoteType] = None
    role_type: Optional[RoleType] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    visa_sponsorship: Optional[bool] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    sort_by: Optional[str] = "recent"  # recent, salary_desc, match
    page: int = 1
    per_page: int = 20
    thread_id: Optional[str] = None
