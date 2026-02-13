import clsx from "clsx";

interface ScoreDisplayProps {
  score: number | null;
  label?: string;
  size?: "sm" | "md" | "lg";
  showBar?: boolean;
  inline?: boolean;
}

/**
 * Mission Control Brutalism Score Display
 *
 * Bar-based visualization with 10 segments
 * Color coding: red (0-4) → amber (4-7) → green (7+)
 */
export default function ScoreDisplay({
  score,
  label,
  size = "md",
  showBar = true,
  inline = false,
}: ScoreDisplayProps) {
  if (score === null || score === undefined) {
    return <span className="text-text-tertiary font-mono">--</span>;
  }

  const getScoreColor = (score: number): "high" | "medium" | "low" => {
    if (score >= 7) return "high";
    if (score >= 4) return "medium";
    return "low";
  };

  const scoreColor = getScoreColor(score);

  const colorClasses = {
    high: "text-signal-success",
    medium: "text-signal-warning",
    low: "text-signal-critical",
  };

  const barColorClasses = {
    high: "bg-signal-success",
    medium: "bg-signal-warning",
    low: "bg-signal-critical",
  };

  const sizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-2xl",
  };

  const barSizeClasses = {
    sm: "h-1 w-1.5 gap-0.5",
    md: "h-2 w-2 gap-0.5",
    lg: "h-3 w-3 gap-1",
  };

  // Calculate filled segments (out of 10)
  const filledSegments = Math.round(score);
  const segments = Array.from({ length: 10 }, (_, i) => i < filledSegments);

  // Inline mode for compact display (label + bar + number in a row)
  if (inline) {
    return (
      <div className="flex items-center gap-3">
        {label && <span className="label-mono w-16 shrink-0">{label}</span>}
        {showBar && (
          <div className={clsx("flex items-center", barSizeClasses[size])}>
            {segments.map((filled, i) => (
              <div
                key={i}
                className={clsx(
                  "transition-colors duration-150",
                  size === "sm"
                    ? "h-1 w-1.5"
                    : size === "md"
                      ? "h-2 w-2"
                      : "h-3 w-3",
                  filled ? barColorClasses[scoreColor] : "bg-light",
                )}
              />
            ))}
          </div>
        )}
        <span
          className={clsx(
            "font-display font-bold shrink-0",
            sizeClasses[size],
            colorClasses[scoreColor],
          )}
        >
          {score.toFixed(1)}
        </span>
      </div>
    );
  }

  // Stacked mode (default) - label on top, bar + number below
  return (
    <div className="flex flex-col gap-1">
      {label && <span className="label-mono">{label}</span>}
      <div className="flex items-center gap-2">
        {showBar && (
          <div className={clsx("flex items-center", barSizeClasses[size])}>
            {segments.map((filled, i) => (
              <div
                key={i}
                className={clsx(
                  "transition-colors duration-150",
                  size === "sm"
                    ? "h-1 w-1.5"
                    : size === "md"
                      ? "h-2 w-2"
                      : "h-3 w-3",
                  filled ? barColorClasses[scoreColor] : "bg-light",
                )}
              />
            ))}
          </div>
        )}
        <span
          className={clsx(
            "font-display font-bold",
            sizeClasses[size],
            colorClasses[scoreColor],
          )}
        >
          {score.toFixed(1)}
        </span>
      </div>
    </div>
  );
}

/**
 * Compact score bar for use in cards - just the bar and number
 */
export function ScoreBar({
  score,
  label,
}: {
  score: number | null;
  label: string;
}) {
  return <ScoreDisplay score={score} label={label} size="sm" inline />;
}
