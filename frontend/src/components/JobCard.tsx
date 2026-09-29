"use client";

import type { JobListing } from "@/types";
import { SkillBadge } from "./SkillBadge";
import { MatchScoreBar } from "./MatchScoreBar";
import {
  MapPin,
  Monitor,
  DollarSign,
  Bookmark,
  ExternalLink,
} from "lucide-react";

interface JobCardProps {
  job: JobListing;
  onSelect: (job: JobListing) => void;
  onSave?: (job: JobListing) => void;
  isSaved?: boolean;
}

export function JobCard({ job, onSelect, onSave, isSaved }: JobCardProps) {
  const salary = formatSalary(job);

  return (
    <div
      className="card p-5 hover:shadow-md transition-shadow cursor-pointer group"
      onClick={() => onSelect(job)}
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 truncate">
              {job.company || "Unknown Company"}
            </h3>
            {job.role_type && (
              <span className="badge bg-blue-50 text-blue-700">
                {job.role_type}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-3">
            {job.role || "Unknown Role"}
          </p>

          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-3">
            {job.location.length > 0 && (
              <span className="flex items-center gap-1">
                <MapPin size={12} />
                {job.location.slice(0, 2).join(", ")}
                {job.location.length > 2 && ` +${job.location.length - 2}`}
              </span>
            )}
            {job.remote && (
              <span className="flex items-center gap-1">
                <Monitor size={12} />
                <span
                  className={
                    job.remote === "yes"
                      ? "text-green-600 font-medium"
                      : job.remote === "hybrid"
                        ? "text-yellow-600 font-medium"
                        : ""
                  }
                >
                  {job.remote === "yes"
                    ? "Remote"
                    : job.remote === "hybrid"
                      ? "Hybrid"
                      : "On-site"}
                </span>
              </span>
            )}
            {salary && (
              <span className="flex items-center gap-1">
                <DollarSign size={12} />
                {salary}
              </span>
            )}
            {job.visa_sponsorship && (
              <span className="badge bg-purple-50 text-purple-700">Visa</span>
            )}
            {job.equity && (
              <span className="badge bg-emerald-50 text-emerald-700">
                Equity
              </span>
            )}
          </div>

          {job.skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {job.skills.slice(0, 6).map((skill) => (
                <SkillBadge key={skill} skill={skill} />
              ))}
              {job.skills.length > 6 && (
                <span className="text-xs text-gray-400">
                  +{job.skills.length - 6}
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          {job.match_score !== null && job.match_score !== undefined && (
            <MatchScoreBar score={job.match_score} />
          )}
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {onSave && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSave(job);
                }}
                className={`p-1.5 rounded-lg transition-colors ${
                  isSaved
                    ? "text-hn bg-orange-50"
                    : "text-gray-400 hover:text-hn hover:bg-orange-50"
                }`}
                title={isSaved ? "Saved" : "Save job"}
              >
                <Bookmark size={16} fill={isSaved ? "currentColor" : "none"} />
              </button>
            )}
            {job.hn_comment_id && (
              <a
                href={`https://news.ycombinator.com/item?id=${job.hn_comment_id}`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                title="View on HN"
              >
                <ExternalLink size={16} />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function formatSalary(job: JobListing): string | null {
  if (!job.salary_min && !job.salary_max) return null;
  const curr = job.salary_currency || "USD";
  const fmt = (n: number) => {
    if (n >= 1000) return `${Math.round(n / 1000)}k`;
    return String(n);
  };
  if (job.salary_min && job.salary_max) {
    return `$${fmt(job.salary_min)}-${fmt(job.salary_max)} ${curr}`;
  }
  if (job.salary_min) return `$${fmt(job.salary_min)}+ ${curr}`;
  if (job.salary_max) return `Up to $${fmt(job.salary_max)} ${curr}`;
  return null;
}
