"use client";

import { useEffect, useState } from "react";
import DOMPurify from "isomorphic-dompurify";
import type { JobListing, MatchBreakdown } from "@/types";
import { fetchMatchBreakdown } from "@/lib/api";
import { SkillBadge } from "./SkillBadge";
import {
  X,
  MapPin,
  Monitor,
  DollarSign,
  ExternalLink,
  Bookmark,
  Mail,
  Globe,
  Building,
  CheckCircle,
  Target,
} from "lucide-react";

interface JobDrawerProps {
  job: JobListing | null;
  onClose: () => void;
  onSave?: (job: JobListing) => void;
  isSaved?: boolean;
}

export function JobDrawer({ job, onClose, onSave, isSaved }: JobDrawerProps) {
  const [breakdown, setBreakdown] = useState<MatchBreakdown | null>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  useEffect(() => {
    if (job?.match_score && job.match_score > 0) {
      fetchMatchBreakdown(job.id)
        .then(setBreakdown)
        .catch(() => setBreakdown(null));
    } else {
      setBreakdown(null);
    }
  }, [job?.id, job?.match_score]);

  if (!job) return null;

  const salary = formatSalary(job);

  return (
    <>
      <div
        className="fixed inset-0 bg-black/30 z-40 transition-opacity"
        onClick={onClose}
      />
      <div className="fixed right-0 top-0 h-full w-full max-w-lg bg-white z-50 shadow-2xl overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h2 className="font-semibold text-lg text-gray-900 truncate">
            {job.company || "Job Details"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-6 py-6 space-y-6">
          {/* Header */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Building size={18} className="text-gray-400" />
              <h3 className="text-xl font-bold text-gray-900">
                {job.company || "Unknown Company"}
              </h3>
            </div>
            <p className="text-lg text-gray-600 ml-7">
              {job.role || "Unknown Role"}
            </p>
          </div>

          {/* Quick Info */}
          <div className="grid grid-cols-2 gap-3">
            {job.location.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin size={16} className="text-gray-400 shrink-0" />
                {job.location.join(", ")}
              </div>
            )}
            {job.remote && (
              <div className="flex items-center gap-2 text-sm">
                <Monitor size={16} className="text-gray-400 shrink-0" />
                <span
                  className={
                    job.remote === "yes"
                      ? "text-green-600 font-medium"
                      : job.remote === "hybrid"
                        ? "text-yellow-600 font-medium"
                        : "text-gray-600"
                  }
                >
                  {job.remote === "yes"
                    ? "Remote"
                    : job.remote === "hybrid"
                      ? "Hybrid"
                      : "On-site"}
                </span>
              </div>
            )}
            {salary && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <DollarSign size={16} className="text-gray-400 shrink-0" />
                {salary}
              </div>
            )}
            {job.role_type && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CheckCircle size={16} className="text-gray-400 shrink-0" />
                {job.role_type}
              </div>
            )}
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-2">
            {job.visa_sponsorship && (
              <span className="badge bg-purple-50 text-purple-700 px-3 py-1">
                Visa Sponsorship
              </span>
            )}
            {job.equity && (
              <span className="badge bg-emerald-50 text-emerald-700 px-3 py-1">
                Equity
              </span>
            )}
          </div>

          {/* Skills */}
          {job.skills.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                Skills & Technologies
              </h4>
              <div className="flex flex-wrap gap-2">
                {job.skills.map((skill) => (
                  <SkillBadge key={skill} skill={skill} size="md" />
                ))}
              </div>
            </div>
          )}

          {/* Match Breakdown */}
          {breakdown && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
                <Target size={16} className="text-hn" />
                Match Breakdown ({Math.round(breakdown.total_score)}%)
              </h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${breakdown.matched_skills.length > 0 ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-500"}`}>
                  <CheckCircle size={14} />
                  Skills ({breakdown.matched_skills.length})
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${breakdown.role_match ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-500"}`}>
                  <CheckCircle size={14} />
                  Role
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${breakdown.location_match ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-500"}`}>
                  <CheckCircle size={14} />
                  Location
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${breakdown.remote_match ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-500"}`}>
                  <CheckCircle size={14} />
                  Remote
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${breakdown.salary_fit ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-500"}`}>
                  <CheckCircle size={14} />
                  Salary
                </div>
              </div>
              {breakdown.matched_skills.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {breakdown.matched_skills.map((skill) => (
                    <SkillBadge key={skill} skill={skill} size="md" />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Description */}
          {job.description && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                Description
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                {job.description}
              </p>
            </div>
          )}

          {/* Raw text */}
          {job.raw_text && (
            <details className="group">
              <summary className="text-sm font-semibold text-gray-500 cursor-pointer hover:text-gray-700">
                Original HN Comment
              </summary>
              <div
                className="mt-2 text-sm text-gray-500 bg-gray-50 rounded-lg p-4 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(job.raw_text) }}
              />
            </details>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            {onSave && (
              <button
                onClick={() => onSave(job)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium transition-colors ${
                  isSaved
                    ? "bg-orange-50 text-hn border border-hn"
                    : "btn-primary"
                }`}
              >
                <Bookmark
                  size={16}
                  fill={isSaved ? "currentColor" : "none"}
                />
                {isSaved ? "Saved" : "Save Job"}
              </button>
            )}
            {job.apply_url && (
              <a
                href={job.apply_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-2 btn-primary"
              >
                <Globe size={16} />
                Apply
              </a>
            )}
            {job.apply_email && (
              <a
                href={`mailto:${job.apply_email}`}
                className="flex-1 flex items-center justify-center gap-2 btn-secondary"
              >
                <Mail size={16} />
                Email
              </a>
            )}
            <a
              href={`https://news.ycombinator.com/item?id=${job.hn_comment_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 btn-secondary px-3"
              title="View on Hacker News"
            >
              <ExternalLink size={16} />
            </a>
          </div>

          {/* Confidence */}
          {job.parse_confidence !== null && (
            <p className="text-xs text-gray-400 text-center">
              Parse confidence: {Math.round((job.parse_confidence || 0) * 100)}%
            </p>
          )}
        </div>
      </div>
    </>
  );
}

function formatSalary(job: JobListing): string | null {
  if (!job.salary_min && !job.salary_max) return null;
  const curr = job.salary_currency || "USD";
  const fmt = (n: number) => `$${n.toLocaleString()}`;
  if (job.salary_min && job.salary_max) {
    return `${fmt(job.salary_min)} - ${fmt(job.salary_max)} ${curr}`;
  }
  if (job.salary_min) return `${fmt(job.salary_min)}+ ${curr}`;
  if (job.salary_max) return `Up to ${fmt(job.salary_max)} ${curr}`;
  return null;
}
