import clsx from "clsx";
import { AlertTriangle, Zap, TrendingUp } from "lucide-react";

interface ViralAlertProps {
  viralScore: number;
  isEarlyViral: boolean;
  signals: string[];
  hoursToViral?: number;
}

function getViralColor(score: number): {
  bg: string;
  text: string;
  border: string;
} {
  if (score >= 8) {
    return {
      bg: "bg-signal-violet/20",
      text: "text-signal-violet",
      border: "border-signal-violet/50",
    };
  }
  if (score >= 5) {
    return {
      bg: "bg-signal-info/20",
      text: "text-signal-info",
      border: "border-signal-info/50",
    };
  }
  return {
    bg: "bg-medium",
    text: "text-text-secondary",
    border: "border-light/50",
  };
}

export default function ViralAlert({
  viralScore,
  isEarlyViral,
  signals,
  hoursToViral,
}: ViralAlertProps) {
  const colors = getViralColor(viralScore);

  return (
    <div
      className={clsx(
        "bg-dark border p-4 relative overflow-hidden",
        colors.border,
        isEarlyViral && "animate-radar-pulse",
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isEarlyViral ? (
            <Zap className={clsx("w-4 h-4", colors.text)} />
          ) : (
            <TrendingUp className={clsx("w-4 h-4", colors.text)} />
          )}
          <span className="label-mono">
            {isEarlyViral ? "EARLY VIRAL" : "VIRAL DETECTED"}
          </span>
        </div>
        <div
          className={clsx(
            "px-2 py-1 rounded border font-mono text-xs font-bold",
            colors.bg,
            colors.text,
            colors.border,
          )}
        >
          {viralScore.toFixed(1)}/10
        </div>
      </div>

      {hoursToViral && (
        <div className="mb-3">
          <div className="text-xs font-mono text-text-tertiary mb-1">
            ESTIMATED TIME TO VIRAL
          </div>
          <div className={clsx("text-lg font-display font-bold", colors.text)}>
            ~{hoursToViral}h
          </div>
        </div>
      )}

      <div>
        <div className="text-xs font-mono text-text-tertiary mb-2">
          DETECTED SIGNALS
        </div>
        <div className="space-y-1">
          {signals.slice(0, 3).map((signal, index) => (
            <div
              key={index}
              className={clsx(
                "flex items-center gap-2 p-2 rounded border",
                colors.bg,
                colors.border,
              )}
            >
              <AlertTriangle className="w-3 h-3 shrink-0" />
              <span className="text-xs font-mono">{signal}</span>
            </div>
          ))}
          {signals.length > 3 && (
            <div className="text-xs font-mono text-text-tertiary text-center">
              +{signals.length - 3} more signals
            </div>
          )}
        </div>
      </div>

      {isEarlyViral && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-radar-500/10 to-transparent animate-pulse" />
        </div>
      )}
    </div>
  );
}
