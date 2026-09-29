from pydantic import BaseModel
from typing import Optional
from enum import Enum


class NotifyFrequency(str, Enum):
    instant = "instant"
    daily = "daily"
    weekly = "weekly"


class ProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    notify_enabled: bool = False
    notify_frequency: NotifyFrequency = NotifyFrequency.weekly


class PreferencesResponse(BaseModel):
    id: Optional[str] = None
    roles: list[str] = []
    locations: list[str] = []
    remote_only: bool = False
    visa_sponsorship: bool = False
    skills: list[str] = []
    salary_min: Optional[int] = None
    excluded_companies: list[str] = []


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    notify_enabled: Optional[bool] = None
    notify_frequency: Optional[NotifyFrequency] = None


class UpdatePreferencesRequest(BaseModel):
    roles: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    remote_only: Optional[bool] = None
    visa_sponsorship: Optional[bool] = None
    skills: Optional[list[str]] = None
    salary_min: Optional[int] = None
    excluded_companies: Optional[list[str]] = None
