import { useState } from "react";
import clsx from "clsx";
import { BarChart3 } from "lucide-react";

interface RevenueBreakdown {
  categoryBenchmark: number;
  ratingFactor: number;
  priceFactor: number;
  velocityFactor: number;
  ageFactor: number;
}

interface RevenueCardProps {
  monthlyEstimate: number;
  yearlyEstimate: number;
  confidence: number;
  breakdown: RevenueBreakdown;
}

function formatRevenue(amount: number): string {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`;
  }
  return `$${amount.toFixed(0)}`;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "text-signal-success border-signal-success";
  if (confidence >= 0.4) return "text-signal-warning border-signal-warning";
  return "text-signal-critical border-signal-critical";
}

function getConfidenceBg(confidence: number): string {
  if (confidence >= 0.7) return "bg-signal-success/20";
  if (confidence >= 0.4) return "bg-signal-warning/20";
  return "bg-signal-critical/20";
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.7) return "HIGH";
  if (confidence >= 0.4) return "MED";
  return "LOW";
}

export function RevenueCard({
  monthlyEstimate,
  yearlyEstimate,
  confidence,
  breakdown,
}: RevenueCardProps) {
  const [showYearly, setShowYearly] = useState(false);
  const currentEstimate = showYearly ? yearlyEstimate : monthlyEstimate;
  const period = showYearly ? "YEAR" : "MO";

  return (
    <div className="bg-dark border border-light p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-radar-500" />
          <span className="label-mono">REVENUE ESTIMATE</span>
        </div>

        <div
          className={clsx(
            "px-2 py-1 border rounded font-mono text-xs font-bold",
            getConfidenceBg(confidence),
            getConfidenceColor(confidence),
          )}
        >
          {getConfidenceLabel(confidence)}
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-baseline gap-3">
          <span className="font-display font-bold text-4xl text-text-primary">
            {formatRevenue(currentEstimate)}
          </span>
          <span className="font-mono text-sm text-text-tertiary">
            /{period}
          </span>
        </div>

        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setShowYearly(false)}
            className={clsx(
              "px-3 py-1 border font-mono text-xs transition-colors",
              !showYearly
                ? "bg-radar-500 text-darkest border-radar-500"
                : "border-light text-text-tertiary hover:border-text-tertiary",
            )}
          >
            MONTHLY
          </button>
          <button
            onClick={() => setShowYearly(true)}
            className={clsx(
              "px-3 py-1 border font-mono text-xs transition-colors",
              showYearly
                ? "bg-radar-500 text-darkest border-radar-500"
                : "border-light text-text-tertiary hover:border-text-tertiary",
            )}
          >
            YEARLY
          </button>
        </div>
      </div>

      <div className="border-t border-light pt-4">
        <span className="label-mono text-xs mb-3 block">BREAKDOWN FACTORS</span>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-text-tertiary">
              Category
            </span>
            <span className="font-mono text-xs text-text-secondary">
              {(breakdown.categoryBenchmark * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-text-tertiary">Rating</span>
            <span className="font-mono text-xs text-text-secondary">
              {(breakdown.ratingFactor * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-text-tertiary">Price</span>
            <span className="font-mono text-xs text-text-secondary">
              {(breakdown.priceFactor * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-text-tertiary">
              Velocity
            </span>
            <span className="font-mono text-xs text-text-secondary">
              {(breakdown.velocityFactor * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-text-tertiary">Age</span>
            <span className="font-mono text-xs text-text-secondary">
              {(breakdown.ageFactor * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-light">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs text-text-tertiary">
            Confidence
          </span>
          <div className="flex items-center gap-2">
            <div className="w-16 h-1 bg-light rounded-full overflow-hidden">
              <div
                className={clsx(
                  "h-full transition-all duration-300",
                  confidence >= 0.7
                    ? "bg-signal-success"
                    : confidence >= 0.4
                      ? "bg-signal-warning"
                      : "bg-signal-critical",
                )}
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs text-text-secondary">
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
