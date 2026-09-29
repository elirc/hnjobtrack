const SKILL_COLORS: Record<string, string> = {
  react: "bg-cyan-50 text-cyan-700",
  typescript: "bg-blue-50 text-blue-700",
  javascript: "bg-yellow-50 text-yellow-700",
  python: "bg-green-50 text-green-700",
  go: "bg-sky-50 text-sky-700",
  rust: "bg-orange-50 text-orange-700",
  java: "bg-red-50 text-red-700",
  "c++": "bg-violet-50 text-violet-700",
  ruby: "bg-rose-50 text-rose-700",
  postgresql: "bg-indigo-50 text-indigo-700",
  postgres: "bg-indigo-50 text-indigo-700",
  kubernetes: "bg-blue-50 text-blue-700",
  docker: "bg-sky-50 text-sky-700",
  aws: "bg-amber-50 text-amber-700",
  node: "bg-green-50 text-green-700",
  "node.js": "bg-green-50 text-green-700",
  swift: "bg-orange-50 text-orange-700",
  kotlin: "bg-purple-50 text-purple-700",
};

interface SkillBadgeProps {
  skill: string;
  size?: "sm" | "md";
}

export function SkillBadge({ skill, size = "sm" }: SkillBadgeProps) {
  const colorClass =
    SKILL_COLORS[skill.toLowerCase()] || "bg-gray-100 text-gray-600";

  return (
    <span
      className={`badge ${colorClass} ${size === "md" ? "px-3 py-1 text-sm" : ""}`}
    >
      {skill}
    </span>
  );
}
