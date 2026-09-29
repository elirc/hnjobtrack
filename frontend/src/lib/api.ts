import { createClient } from "./supabase";
import type {
  JobListResponse,
  JobListing,
  JobFilters,
  MatchBreakdown,
  SavedJob,
  SavedStatus,
  Profile,
  Preferences,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (session?.access_token) {
    return { Authorization: `Bearer ${session.access_token}` };
  }
  return {};
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...headers,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

// Jobs
export async function fetchJobs(
  filters: JobFilters = {}
): Promise<JobListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  return apiFetch<JobListResponse>(`/jobs?${params.toString()}`);
}

export async function fetchJob(id: string): Promise<JobListing> {
  return apiFetch<JobListing>(`/jobs/${id}`);
}

export async function fetchMatchBreakdown(
  jobId: string
): Promise<MatchBreakdown> {
  return apiFetch<MatchBreakdown>(`/jobs/${jobId}/match`);
}

export async function fetchForYouJobs(
  page = 1,
  perPage = 20
): Promise<JobListResponse> {
  return apiFetch<JobListResponse>(
    `/jobs/for-you?page=${page}&per_page=${perPage}`
  );
}

// Saved jobs
export async function saveJob(
  jobId: string,
  notes?: string
): Promise<SavedJob> {
  return apiFetch<SavedJob>(`/jobs/${jobId}/save`, {
    method: "POST",
    body: JSON.stringify({ notes, status: "saved" }),
  });
}

export async function updateSavedJob(
  jobId: string,
  data: { status?: SavedStatus; notes?: string }
): Promise<SavedJob> {
  return apiFetch<SavedJob>(`/jobs/${jobId}/save`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function unsaveJob(jobId: string): Promise<void> {
  await apiFetch(`/jobs/${jobId}/save`, { method: "DELETE" });
}

export async function fetchSavedJobs(
  status?: SavedStatus
): Promise<SavedJob[]> {
  const params = status ? `?status=${status}` : "";
  return apiFetch<SavedJob[]>(`/jobs/saved/all${params}`);
}

// Profile
export async function fetchProfile(): Promise<Profile> {
  return apiFetch<Profile>("/profile");
}

export async function updateProfile(
  data: Partial<Profile>
): Promise<Profile> {
  return apiFetch<Profile>("/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function fetchPreferences(): Promise<Preferences> {
  return apiFetch<Preferences>("/profile/preferences");
}

export async function updatePreferences(
  data: Partial<Preferences>
): Promise<Preferences> {
  return apiFetch<Preferences>("/profile/preferences", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
