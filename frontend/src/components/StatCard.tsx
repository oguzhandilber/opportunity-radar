import { ReactNode, useEffect, useState } from "react";
import clsx from "clsx";

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
  animate?: boolean;
}

/**
 * Mission Control Brutalism Stat Card
 *
 * Terminal-style with massive centered numbers
 * Visible borders, trend indicators
 */
export default function StatCard({
  title,
  value,
  icon,
  trend,
  className,
  animate = true,
}: StatCardProps) {
  const [displayValue, setDisplayValue] = useState(animate ? 0 : value);
  const numericValue =
    typeof value === "number" ? value : parseInt(value.toString(), 10);
  const isNumeric = !isNaN(numericValue);

  // Count-up animation for numeric values
  useEffect(() => {
    if (!animate || !isNumeric) {
      setDisplayValue(value);
      return;
    }

    const duration = 800;
    const steps = 20;
    const stepDuration = duration / steps;
    const increment = numericValue / steps;
    let current = 0;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current = Math.min(Math.round(increment * step), numericValue);
      setDisplayValue(current);

      if (step >= steps) {
        clearInterval(timer);
        setDisplayValue(numericValue);
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [value, animate, isNumeric, numericValue]);

  return (
    <div
      className={clsx(
        "border border-light bg-dark p-6",
        "flex flex-col",
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="label-mono">{title}</span>
        {icon && <div className="text-text-tertiary">{icon}</div>}
      </div>

      {/* Massive Centered Number */}
      <div className="flex-1 flex items-center justify-center py-4">
        <span
          className={clsx(
            "font-display font-bold text-text-primary count-up",
            "text-5xl md:text-6xl tracking-tight",
          )}
        >
          {displayValue}
        </span>
      </div>

      {/* Trend Indicator */}
      {trend && (
        <div className="pt-4 border-t border-light/50">
          <div
            className={clsx(
              "flex items-center gap-2 font-mono text-sm",
              trend.value >= 0 ? "text-signal-success" : "text-signal-critical",
            )}
          >
            <span className="font-bold">{trend.value >= 0 ? "▲" : "▼"}</span>
            <span>
              {trend.value >= 0 ? "+" : ""}
              {trend.value}
            </span>
            <span className="text-text-tertiary">{trend.label}</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact stat for use in sidebars or smaller spaces
 */
export function StatCompact({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-light/30 last:border-0">
      <span className="label-mono">{label}</span>
      <span className="font-display font-bold text-text-primary">{value}</span>
    </div>
  );
}
