"use client";

import { useState } from "react";
import type { JobFilters, RemoteType, RoleType } from "@/types";
import { SlidersHorizontal, X, ChevronDown, ChevronUp } from "lucide-react";

interface FilterSidebarProps {
  filters: JobFilters;
  onChange: (filters: JobFilters) => void;
  onReset: () => void;
}

export function FilterSidebar({
  filters,
  onChange,
  onReset,
}: FilterSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    remote: true,
    role_type: true,
    skills: true,
    salary: false,
    other: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const hasActiveFilters =
    filters.remote ||
    filters.role_type ||
    filters.skills ||
    filters.location ||
    filters.visa_sponsorship ||
    filters.salary_min ||
    filters.salary_max;

  const FilterContent = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <SlidersHorizontal size={16} />
          Filters
        </h3>
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="text-xs text-hn hover:text-hn-dark font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Remote */}
      <FilterSection
        title="Work Type"
        expanded={expandedSections.remote}
        onToggle={() => toggleSection("remote")}
      >
        <div className="space-y-1.5">
          {(
            [
              ["yes", "Remote"],
              ["hybrid", "Hybrid"],
              ["no", "On-site"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-900"
            >
              <input
                type="radio"
                name="remote"
                checked={filters.remote === value}
                onChange={() =>
                  onChange({
                    ...filters,
                    remote:
                      filters.remote === value
                        ? undefined
                        : (value as RemoteType),
                    page: 1,
                  })
                }
                className="text-hn focus:ring-hn"
              />
              {label}
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Role Type */}
      <FilterSection
        title="Role Type"
        expanded={expandedSections.role_type}
        onToggle={() => toggleSection("role_type")}
      >
        <div className="space-y-1.5">
          {(
            [
              ["full-time", "Full-time"],
              ["part-time", "Part-time"],
              ["contract", "Contract"],
              ["internship", "Internship"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-900"
            >
              <input
                type="radio"
                name="role_type"
                checked={filters.role_type === value}
                onChange={() =>
                  onChange({
                    ...filters,
                    role_type:
                      filters.role_type === value
                        ? undefined
                        : (value as RoleType),
                    page: 1,
                  })
                }
                className="text-hn focus:ring-hn"
              />
              {label}
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Skills */}
      <FilterSection
        title="Skills"
        expanded={expandedSections.skills}
        onToggle={() => toggleSection("skills")}
      >
        <input
          type="text"
          placeholder="e.g. TypeScript, React, Go"
          value={filters.skills || ""}
          onChange={(e) =>
            onChange({ ...filters, skills: e.target.value || undefined, page: 1 })
          }
          className="input"
        />
      </FilterSection>

      {/* Location */}
      <FilterSection
        title="Location"
        expanded={expandedSections.other}
        onToggle={() => toggleSection("other")}
      >
        <input
          type="text"
          placeholder="e.g. New York, London"
          value={filters.location || ""}
          onChange={(e) =>
            onChange({
              ...filters,
              location: e.target.value || undefined,
              page: 1,
            })
          }
          className="input"
        />
      </FilterSection>

      {/* Salary */}
      <FilterSection
        title="Salary Range"
        expanded={expandedSections.salary}
        onToggle={() => toggleSection("salary")}
      >
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.salary_min || ""}
            onChange={(e) =>
              onChange({
                ...filters,
                salary_min: e.target.value
                  ? parseInt(e.target.value)
                  : undefined,
                page: 1,
              })
            }
            className="input"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.salary_max || ""}
            onChange={(e) =>
              onChange({
                ...filters,
                salary_max: e.target.value
                  ? parseInt(e.target.value)
                  : undefined,
                page: 1,
              })
            }
            className="input"
          />
        </div>
      </FilterSection>

      {/* Visa */}
      <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-900 px-1">
        <input
          type="checkbox"
          checked={filters.visa_sponsorship || false}
          onChange={(e) =>
            onChange({
              ...filters,
              visa_sponsorship: e.target.checked || undefined,
              page: 1,
            })
          }
          className="text-hn focus:ring-hn rounded"
        />
        Visa sponsorship only
      </label>
    </div>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden flex items-center gap-2 btn-secondary text-sm"
      >
        <SlidersHorizontal size={16} />
        Filters
        {hasActiveFilters && (
          <span className="w-2 h-2 rounded-full bg-hn" />
        )}
      </button>

      {/* Mobile overlay */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-30 lg:hidden"
            onClick={() => setIsOpen(false)}
          />
          <div className="fixed left-0 top-0 h-full w-80 bg-white z-40 p-6 overflow-y-auto lg:hidden shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold">Filters</h3>
              <button onClick={() => setIsOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <FilterContent />
          </div>
        </>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:block w-64 shrink-0">
        <div className="card p-5 sticky top-20">
          <FilterContent />
        </div>
      </div>
    </>
  );
}

function FilterSection({
  title,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="border-t border-gray-100 pt-3">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full text-sm font-medium text-gray-700 hover:text-gray-900"
      >
        {title}
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {expanded && <div className="mt-2">{children}</div>}
    </div>
  );
}
