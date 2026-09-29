"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchForYouJobs, saveJob, fetchSavedJobs } from "@/lib/api";
import type { JobListing } from "@/types";
import { JobCard } from "@/components/JobCard";
import { JobDrawer } from "@/components/JobDrawer";
import { Loader2, Sparkles, Settings } from "lucide-react";
import Link from "next/link";

export default function ForYouPage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<JobListing | null>(null);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());

  const loadJobs = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const result = await fetchForYouJobs(p);
      setJobs(result.jobs);
      setTotal(result.total);
      setPage(p);
    } catch (err) {
      console.error("Failed to load matched jobs:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
    fetchSavedJobs()
      .then((saved) => {
        setSavedJobIds(new Set(saved.map((s) => s.job_id)));
      })
      .catch(() => {});
  }, [loadJobs]);

  const handleSave = async (job: JobListing) => {
    try {
      if (savedJobIds.has(job.id)) return;
      await saveJob(job.id);
      setSavedJobIds((prev) => new Set([...prev, job.id]));
    } catch (err) {
      console.error("Failed to save job:", err);
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles size={24} className="text-hn" />
            For You
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Jobs matched to your preferences, sorted by relevance
          </p>
        </div>
        <Link
          href="/profile"
          className="btn-secondary text-sm flex items-center gap-1.5"
        >
          <Settings size={14} />
          Edit Preferences
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-gray-400" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-20 card p-10">
          <Sparkles size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">No matched jobs yet</p>
          <p className="text-gray-400 text-sm mt-2">
            Set up your preferences to get personalized matches
          </p>
          <Link href="/profile" className="btn-primary mt-4 inline-block">
            Set Preferences
          </Link>
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

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => loadJobs(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600 px-4">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => loadJobs(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="btn-secondary text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}

      <JobDrawer
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
        onSave={handleSave}
        isSaved={selectedJob ? savedJobIds.has(selectedJob.id) : false}
      />
    </div>
  );
}
