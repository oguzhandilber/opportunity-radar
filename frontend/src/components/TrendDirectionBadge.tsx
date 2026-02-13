import clsx from "clsx";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

interface TrendDirectionBadgeProps {
  trend: "rising" | "falling" | "stable";
  velocity: number;
}

function getTrendConfig(trend: "rising" | "falling" | "stable") {
  switch (trend) {
    case "rising":
      return {
        bg: "bg-signal-success/20",
        text: "text-signal-success",
        border: "border-signal-success/50",
        icon: ArrowUp,
      };
    case "falling":
      return {
        bg: "bg-signal-critical/20",
        text: "text-signal-critical",
        border: "border-signal-critical/50",
        icon: ArrowDown,
      };
    case "stable":
      return {
        bg: "bg-medium",
        text: "text-text-tertiary",
        border: "border-light/50",
        icon: Minus,
      };
  }
}

export default function TrendDirectionBadge({
  trend,
  velocity,
}: TrendDirectionBadgeProps) {
  const config = getTrendConfig(trend);
  const Icon = config.icon;

  return (
    <div
      className={clsx(
        "inline-flex items-center gap-1 px-2 py-1 rounded border font-mono text-xs font-bold transition-colors",
        config.bg,
        config.text,
        config.border,
      )}
    >
      <Icon className="w-3 h-3" />
      <span>{Math.abs(velocity).toFixed(1)}</span>
    </div>
  );
}
