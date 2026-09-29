interface MatchScoreBarProps {
  score: number;
  showLabel?: boolean;
}

export function MatchScoreBar({ score, showLabel = true }: MatchScoreBarProps) {
  const rounded = Math.round(score);
  const color =
    rounded >= 70
      ? "bg-green-500 text-green-700"
      : rounded >= 40
        ? "bg-yellow-500 text-yellow-700"
        : "bg-gray-400 text-gray-600";

  const bgColor =
    rounded >= 70
      ? "bg-green-50"
      : rounded >= 40
        ? "bg-yellow-50"
        : "bg-gray-50";

  return (
    <div className="flex items-center gap-2">
      {showLabel && (
        <span className={`text-xs font-semibold ${color.split(" ")[1]}`}>
          {rounded}%
        </span>
      )}
      <div className={`w-16 h-2 rounded-full ${bgColor}`}>
        <div
          className={`h-full rounded-full ${color.split(" ")[0]} transition-all`}
          style={{ width: `${Math.min(rounded, 100)}%` }}
        />
      </div>
    </div>
  );
}
