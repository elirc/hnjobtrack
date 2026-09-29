"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  fetchSavedJobs,
  updateSavedJob,
  unsaveJob,
} from "@/lib/api";
import { createClient } from "@/lib/supabase";
import type { SavedJob, SavedStatus } from "@/types";
import { JobDrawer } from "@/components/JobDrawer";
import { SkillBadge } from "@/components/SkillBadge";
import {
  Loader2,
  Bookmark,
  Trash2,
  MessageSquare,
  MapPin,
  Monitor,
  ChevronDown,
} from "lucide-react";

const STATUS_CONFIG: Record<
  SavedStatus,
  { label: string; color: string; bg: string }
> = {
  saved: { label: "Saved", color: "text-gray-600", bg: "bg-gray-100" },
  applied: { label: "Applied", color: "text-blue-700", bg: "bg-blue-50" },
  interviewing: {
    label: "Interviewing",
    color: "text-yellow-700",
    bg: "bg-yellow-50",
  },
  rejected: { label: "Rejected", color: "text-red-700", bg: "bg-red-50" },
  offer: { label: "Offer", color: "text-green-700", bg: "bg-green-50" },
};

export default function SavedJobsPage() {
  const router = useRouter();
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<SavedStatus | "all">("all");
  const [selectedJob, setSelectedJob] = useState<SavedJob | null>(null);
  const [editingNotes, setEditingNotes] = useState<string | null>(null);
  const [notesText, setNotesText] = useState("");

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) {
        router.push("/auth/login?redirect=/saved");
        return;
      }
      loadSaved();
    });
  }, []);

  const loadSaved = async (status?: SavedStatus) => {
    setLoading(true);
    try {
      const data = await fetchSavedJobs(status);
      setSavedJobs(data);
    } catch (err) {
      console.error("Failed to load saved jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (
    savedJob: SavedJob,
    newStatus: SavedStatus
  ) => {
    try {
      const updated = await updateSavedJob(savedJob.job_id, {
        status: newStatus,
      });
      setSavedJobs((prev) =>
        prev.map((s) => (s.id === savedJob.id ? { ...s, status: updated.status } : s))
      );
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleSaveNotes = async (savedJob: SavedJob) => {
    try {
      await updateSavedJob(savedJob.job_id, { notes: notesText });
      setSavedJobs((prev) =>
        prev.map((s) => (s.id === savedJob.id ? { ...s, notes: notesText } : s))
      );
      setEditingNotes(null);
    } catch (err) {
      console.error("Failed to update notes:", err);
    }
  };

  const handleUnsave = async (savedJob: SavedJob) => {
    try {
      await unsaveJob(savedJob.job_id);
      setSavedJobs((prev) => prev.filter((s) => s.id !== savedJob.id));
    } catch (err) {
      console.error("Failed to unsave:", err);
    }
  };

  const filtered =
    filterStatus === "all"
      ? savedJobs
      : savedJobs.filter((s) => s.status === filterStatus);

  const statusCounts = savedJobs.reduce(
    (acc, s) => {
      acc[s.status] = (acc[s.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bookmark size={24} className="text-hn" />
            Saved Jobs
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {savedJobs.length} total saved
          </p>
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          onClick={() => setFilterStatus("all")}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            filterStatus === "all"
              ? "bg-gray-900 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          All ({savedJobs.length})
        </button>
        {(
          Object.entries(STATUS_CONFIG) as [
            SavedStatus,
            (typeof STATUS_CONFIG)[SavedStatus],
          ][]
        ).map(([status, config]) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              filterStatus === status
                ? "bg-gray-900 text-white"
                : `${config.bg} ${config.color} hover:opacity-80`
            }`}
          >
            {config.label} ({statusCounts[status] || 0})
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-gray-400" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 card p-10">
          <Bookmark size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">No saved jobs</p>
          <p className="text-gray-400 text-sm mt-2">
            Browse jobs and save the ones you&apos;re interested in
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((saved) => (
            <div key={saved.id} className="card p-5">
              <div className="flex justify-between items-start gap-4">
                <div
                  className="flex-1 min-w-0 cursor-pointer"
                  onClick={() => setSelectedJob(saved)}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 truncate">
                      {saved.job?.company || "Unknown Company"}
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {saved.job?.role || "Unknown Role"}
                  </p>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-2">
                    {saved.job?.location && saved.job.location.length > 0 && (
                      <span className="flex items-center gap-1">
                        <MapPin size={12} />
                        {saved.job.location.slice(0, 2).join(", ")}
                      </span>
                    )}
                    {saved.job?.remote && (
                      <span className="flex items-center gap-1">
                        <Monitor size={12} />
                        {saved.job.remote === "yes" ? "Remote" : saved.job.remote === "hybrid" ? "Hybrid" : "On-site"}
                      </span>
                    )}
                  </div>
                  {saved.job?.skills && saved.job.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {saved.job.skills.slice(0, 4).map((skill) => (
                        <SkillBadge key={skill} skill={skill} />
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex flex-col items-end gap-2 shrink-0">
                  {/* Status dropdown */}
                  <div className="relative">
                    <select
                      value={saved.status}
                      onChange={(e) =>
                        handleStatusChange(
                          saved,
                          e.target.value as SavedStatus
                        )
                      }
                      className={`appearance-none pr-7 pl-3 py-1 rounded-full text-xs font-medium cursor-pointer ${STATUS_CONFIG[saved.status].bg} ${STATUS_CONFIG[saved.status].color} border-0 focus:ring-2 focus:ring-hn`}
                    >
                      {Object.entries(STATUS_CONFIG).map(([value, config]) => (
                        <option key={value} value={value}>
                          {config.label}
                        </option>
                      ))}
                    </select>
                    <ChevronDown
                      size={12}
                      className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                    />
                  </div>

                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        setEditingNotes(
                          editingNotes === saved.id ? null : saved.id
                        );
                        setNotesText(saved.notes || "");
                      }}
                      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Add notes"
                    >
                      <MessageSquare size={14} />
                    </button>
                    <button
                      onClick={() => handleUnsave(saved)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Remove"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Notes editor */}
              {editingNotes === saved.id && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <textarea
                    value={notesText}
                    onChange={(e) => setNotesText(e.target.value)}
                    placeholder="Add personal notes..."
                    rows={2}
                    className="input resize-none"
                  />
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => handleSaveNotes(saved)}
                      className="btn-primary text-xs px-3 py-1"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingNotes(null)}
                      className="btn-secondary text-xs px-3 py-1"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Existing notes display */}
              {saved.notes && editingNotes !== saved.id && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500 italic">{saved.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedJob?.job && (
        <JobDrawer
          job={selectedJob.job}
          onClose={() => setSelectedJob(null)}
          isSaved={true}
        />
      )}
    </div>
  );
}
