"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { fetchJobs, saveJob, fetchSavedJobs } from "@/lib/api";
import { createClient } from "@/lib/supabase";
import type { JobListing, JobFilters, SavedJob, RemoteType, RoleType } from "@/types";
import { JobCard } from "@/components/JobCard";
import { JobDrawer } from "@/components/JobDrawer";
import { FilterSidebar } from "@/components/FilterSidebar";
import { Search, Loader2 } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<JobListing | null>(null);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [user, setUser] = useState<{ id: string } | null>(null);

  const [filters, setFilters] = useState<JobFilters>(() => {
    const remote = searchParams.get("remote");
    const role_type = searchParams.get("role_type");
    const sort = searchParams.get("sort");
    return {
      search: searchParams.get("search") || undefined,
      remote: (remote === "yes" || remote === "no" || remote === "hybrid" ? remote : undefined) as RemoteType | undefined,
      role_type: (role_type === "full-time" || role_type === "part-time" || role_type === "contract" || role_type === "internship" ? role_type : undefined) as RoleType | undefined,
      skills: searchParams.get("skills") || undefined,
      location: searchParams.get("location") || undefined,
      visa_sponsorship: searchParams.get("visa") === "true" || undefined,
      salary_min: searchParams.get("salary_min")
        ? parseInt(searchParams.get("salary_min")!)
        : undefined,
      salary_max: searchParams.get("salary_max")
        ? parseInt(searchParams.get("salary_max")!)
        : undefined,
      sort_by: (sort === "salary_desc" ? "salary_desc" : "recent"),
      page: parseInt(searchParams.get("page") || "1"),
      per_page: 20,
    };
  });

  const [searchInput, setSearchInput] = useState(filters.search || "");

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      if (data.user) {
        fetchSavedJobs().then((saved) => {
          setSavedJobIds(new Set(saved.map((s) => s.job_id)));
        }).catch(() => {});
      }
    });
  }, []);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchJobs(filters);
      setJobs(result.jobs);
      setTotal(result.total);
    } catch (err) {
      console.error("Failed to load jobs:", err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters((f) => ({ ...f, search: searchInput || undefined, page: 1 }));
  };

  const handleSave = async (job: JobListing) => {
    if (!user) {
      router.push(`/auth/login?redirect=/dashboard&save=${job.id}`);
      return;
    }
    try {
      if (savedJobIds.has(job.id)) return;
      await saveJob(job.id);
      setSavedJobIds((prev) => new Set([...prev, job.id]));
    } catch (err) {
      console.error("Failed to save job:", err);
    }
  };

  const totalPages = Math.ceil(total / (filters.per_page || 20));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Search bar */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="relative">
          <Search
            size={20}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Search companies, roles, skills..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-base focus:outline-none focus:ring-2 focus:ring-hn focus:border-transparent shadow-sm"
          />
        </div>
      </form>

      <div className="flex gap-6">
        {/* Filters */}
        <FilterSidebar
          filters={filters}
          onChange={setFilters}
          onReset={() =>
            setFilters({ page: 1, per_page: 20, sort_by: "recent" })
          }
        />

        {/* Job list */}
        <div className="flex-1 min-w-0">
          {/* Sort & count */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              {total.toLocaleString()} jobs found
            </p>
            <select
              value={filters.sort_by || "recent"}
              onChange={(e) =>
                setFilters((f) => ({
                  ...f,
                  sort_by: e.target.value as "recent" | "salary_desc",
                  page: 1,
                }))
              }
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-hn"
            >
              <option value="recent">Most Recent</option>
              <option value="salary_desc">Highest Salary</option>
            </select>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={32} className="animate-spin text-gray-400" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-500 text-lg">No jobs found</p>
              <p className="text-gray-400 text-sm mt-1">
                Try adjusting your filters
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onSelect={setSelectedJob}
                  onSave={handleSave}
                  isSaved={savedJobIds.has(job.id)}
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() =>
                  setFilters((f) => ({
                    ...f,
                    page: Math.max(1, (f.page || 1) - 1),
                  }))
                }
                disabled={filters.page === 1}
                className="btn-secondary text-sm disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600 px-4">
                Page {filters.page} of {totalPages}
              </span>
              <button
                onClick={() =>
                  setFilters((f) => ({
                    ...f,
                    page: Math.min(totalPages, (f.page || 1) + 1),
                  }))
                }
                disabled={filters.page === totalPages}
                className="btn-secondary text-sm disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Job detail drawer */}
      <JobDrawer
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
        onSave={handleSave}
        isSaved={selectedJob ? savedJobIds.has(selectedJob.id) : false}
      />
    </div>
  );
}
