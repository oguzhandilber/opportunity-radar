import clsx from "clsx";

interface RevenueBadgeProps {
  monthlyRevenue: number;
  confidence: number;
}

function formatRevenue(amount: number): string {
  if (amount >= 1000000) {
    return `${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `${(amount / 1000).toFixed(0)}K`;
  }
  return amount.toFixed(0);
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "border-signal-success text-signal-success";
  if (confidence >= 0.4) return "border-signal-warning text-signal-warning";
  return "border-signal-critical text-signal-critical";
}

function getConfidenceBg(confidence: number): string {
  if (confidence >= 0.7) return "bg-signal-success/10";
  if (confidence >= 0.4) return "bg-signal-warning/10";
  return "bg-signal-critical/10";
}

export function RevenueBadge({
  monthlyRevenue,
  confidence,
}: RevenueBadgeProps) {
  return (
    <div
      className={clsx(
        "px-2 py-1 rounded border font-mono text-xs font-bold transition-colors",
        getConfidenceBg(confidence),
        getConfidenceColor(confidence),
      )}
    >
      ${formatRevenue(monthlyRevenue)}
      <span className="opacity-60 ml-1">/mo</span>
    </div>
  );
}
