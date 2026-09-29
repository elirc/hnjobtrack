export type RemoteType = "yes" | "no" | "hybrid";
export type RoleType = "full-time" | "part-time" | "contract" | "internship";
export type SavedStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "rejected"
  | "offer";
export type NotifyFrequency = "instant" | "daily" | "weekly";

export interface JobListing {
  id: string;
  thread_id: string;
  hn_comment_id: string;
  company: string | null;
  role: string | null;
  role_type: RoleType | null;
  location: string[];
  remote: RemoteType | null;
  visa_sponsorship: boolean | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  skills: string[];
  description: string | null;
  apply_url: string | null;
  apply_email: string | null;
  equity: boolean | null;
  parsed_at: string | null;
  parse_confidence: number | null;
  raw_text: string | null;
  match_score: number | null;
}

export interface JobListResponse {
  jobs: JobListing[];
  total: number;
  page: number;
  per_page: number;
}

export interface SavedJob {
  id: string;
  job_id: string;
  saved_at: string;
  notes: string | null;
  status: SavedStatus;
  job: JobListing | null;
}

export interface Profile {
  id: string;
  email: string;
  display_name: string | null;
  notify_enabled: boolean;
  notify_frequency: NotifyFrequency;
}

export interface Preferences {
  id: string | null;
  roles: string[];
  locations: string[];
  remote_only: boolean;
  visa_sponsorship: boolean;
  skills: string[];
  salary_min: number | null;
  excluded_companies: string[];
}

export interface MatchBreakdown {
  total_score: number;
  matched_skills: string[];
  skill_score: number;
  role_match: boolean;
  location_match: boolean;
  remote_match: boolean;
  salary_fit: boolean;
}

export interface JobFilters {
  search?: string;
  remote?: RemoteType;
  role_type?: RoleType;
  skills?: string;
  location?: string;
  visa_sponsorship?: boolean;
  salary_min?: number;
  salary_max?: number;
  sort_by?: "recent" | "salary_desc";
  page?: number;
  per_page?: number;
  thread_id?: string;
}
