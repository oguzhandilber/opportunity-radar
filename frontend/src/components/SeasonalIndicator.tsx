import clsx from "clsx";
import { Calendar, TrendingUp } from "lucide-react";

interface SeasonalIndicatorProps {
  seasonalScore: number;
  peakMonths: number[];
  upcomingEvents: string[];
}

const monthNames = [
  "JAN",
  "FEB",
  "MAR",
  "APR",
  "MAY",
  "JUN",
  "JUL",
  "AUG",
  "SEP",
  "OCT",
  "NOV",
  "DEC",
];

function getSeasonalColor(score: number): {
  bg: string;
  text: string;
  border: string;
} {
  if (score >= 7) {
    return {
      bg: "bg-signal-success/20",
      text: "text-signal-success",
      border: "border-signal-success/50",
    };
  }
  if (score >= 4) {
    return {
      bg: "bg-signal-warning/20",
      text: "text-signal-warning",
      border: "border-signal-warning/50",
    };
  }
  return {
    bg: "bg-medium",
    text: "text-text-tertiary",
    border: "border-light/50",
  };
}

function formatScore(score: number): string {
  if (score >= 7) return "HIGH";
  if (score >= 4) return "MEDIUM";
  return "LOW";
}

export default function SeasonalIndicator({
  seasonalScore,
  peakMonths,
  upcomingEvents,
}: SeasonalIndicatorProps) {
  const colors = getSeasonalColor(seasonalScore);
  const nextEvent = upcomingEvents[0];

  return (
    <div className="bg-dark border border-light p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-radar-500" />
          <span className="label-mono">SEASONAL</span>
        </div>
        <div
          className={clsx(
            "px-2 py-1 rounded border font-mono text-xs font-bold",
            colors.bg,
            colors.text,
            colors.border,
          )}
        >
          {formatScore(seasonalScore)} ({seasonalScore.toFixed(1)})
        </div>
      </div>

      <div className="mb-3">
        <div className="text-xs font-mono text-text-tertiary mb-1">
          PEAK MONTHS
        </div>
        <div className="flex gap-1 flex-wrap">
          {monthNames.map((month, index) => (
            <div
              key={month}
              className={clsx(
                "w-6 h-6 flex items-center justify-center text-[10px] font-mono border transition-colors",
                peakMonths.includes(index + 1)
                  ? "bg-radar-500/20 text-radar-500 border-radar-500/50"
                  : "bg-medium text-text-tertiary border-light/50",
              )}
            >
              {month}
            </div>
          ))}
        </div>
      </div>

      {nextEvent && (
        <div
          className={clsx(
            "flex items-center gap-2 p-2 rounded border",
            colors.bg,
            colors.border,
          )}
        >
          <TrendingUp className="w-3 h-3" />
          <span className="text-xs font-mono">{nextEvent}</span>
        </div>
      )}
    </div>
  );
}
