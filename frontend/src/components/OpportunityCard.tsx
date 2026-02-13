import { Link } from "react-router-dom";
import {
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Zap,
  Trophy,
  AlertTriangle,
} from "lucide-react";
import clsx from "clsx";
import type { Opportunity } from "../api/client";
import ScoreDisplay, { ScoreBar } from "./ScoreDisplay";

interface OpportunityCardProps {
  opportunity: Opportunity;
  className?: string;
}

// Payment tier badge colors and labels (dark theme)
const tierConfig: Record<number, { color: string; label: string }> = {
  1: {
    color: "bg-signal-success/20 text-signal-success border-signal-success/50",
    label: "T1: ACTIVE SPENDER",
  },
  2: {
    color: "bg-signal-info/20 text-signal-info border-signal-info/50",
    label: "T2: READY TO BUY",
  },
  3: {
    color: "bg-signal-warning/20 text-signal-warning border-signal-warning/50",
    label: "T3: CHURNING",
  },
  4: {
    color: "bg-medium text-text-secondary border-light",
    label: "T4: PRICE AWARE",
  },
};

// Journey stage badge colors (dark theme)
const journeyConfig: Record<string, { color: string; label: string }> = {
  churning: {
    color:
      "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
    label: "CHURNING",
  },
  ready: {
    color: "bg-signal-success/20 text-signal-success border-signal-success/50",
    label: "READY",
  },
  considering: {
    color: "bg-signal-warning/20 text-signal-warning border-signal-warning/50",
    label: "CONSIDERING",
  },
  aware: {
    color: "bg-signal-info/20 text-signal-info border-signal-info/50",
    label: "AWARE",
  },
  unaware: {
    color: "bg-medium text-text-tertiary border-light",
    label: "UNAWARE",
  },
};

// Risk level badge colors (dark theme)
const riskConfig: Record<string, { color: string; label: string }> = {
  low: {
    color: "bg-signal-success/20 text-signal-success border-signal-success/50",
    label: "LOW RISK",
  },
  medium: {
    color: "bg-signal-warning/20 text-signal-warning border-signal-warning/50",
    label: "MED RISK",
  },
  high: {
    color:
      "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
    label: "HIGH RISK",
  },
};

// Niche badge - all use violet for Mission Control theme
const nicheColor =
  "bg-signal-violet/20 text-signal-violet border-signal-violet/50";

/**
 * Mission Control Brutalism Opportunity Card
 *
 * Full-width card with 4px status border
 * Score bars instead of colored numbers
 * Square badges, monospace labels
 */
export default function OpportunityCard({
  opportunity,
  className,
}: OpportunityCardProps) {
  const statusBorderClasses: Record<string, string> = {
    new: "status-border-new",
    saved: "status-border-saved",
    rejected: "status-border-rejected",
    in_progress: "status-border-in_progress",
  };

  const tierInfo = opportunity.payment_signal_tier
    ? tierConfig[opportunity.payment_signal_tier]
    : null;
  const journeyInfo = opportunity.purchase_journey_stage
    ? journeyConfig[opportunity.purchase_journey_stage]
    : null;
  const riskInfo = opportunity.risk_level
    ? riskConfig[opportunity.risk_level]
    : null;

  // Niche info (Pivot 2)
  const primaryNiche = opportunity.primary_niche;
  const nicheScore = primaryNiche && opportunity.niche_scores?.[primaryNiche];

  return (
    <div
      className={clsx(
        "bg-dark border border-light p-5",
        statusBorderClasses[opportunity.status] || "border-l-4 border-l-light",
        "hover:bg-medium/50 transition-colors",
        "card-scan-in",
        className,
      )}
    >
      {/* Header Row: Status + Badges + Total Score */}
      <div className="flex items-start justify-between gap-4 mb-3">
        {/* Left: Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Badge */}
          <span className={clsx("badge", `badge-${opportunity.status}`)}>
            {opportunity.status.replace("_", " ").toUpperCase()}
          </span>

          {/* Niche Badge (Pivot 2) */}
          {primaryNiche && nicheScore && (
            <span
              className={clsx("badge border", nicheColor)}
              title={`Niche fit: ${nicheScore.fit_score.toFixed(1)}/10`}
            >
              {nicheScore.niche_name.toUpperCase()}
            </span>
          )}

          {/* Payment Intent Badge (Pivot 3) */}
          {tierInfo && (
            <span className={clsx("badge border", tierInfo.color)}>
              {tierInfo.label}
            </span>
          )}

          {/* Product Type */}
          {opportunity.product_type && (
            <span className="badge badge-sector">
              {opportunity.product_type.toUpperCase()}
            </span>
          )}
        </div>

        {/* Right: Total Score */}
        <div className="flex items-center gap-2">
          <ScoreDisplay
            score={opportunity.total_score}
            size="lg"
            showBar={false}
          />
          <span className="text-text-tertiary font-mono text-xs">/10</span>
        </div>
      </div>

      {/* Title */}
      <Link
        to={`/opportunities/${opportunity.id}`}
        className="block text-lg font-body font-semibold text-text-primary hover:text-radar-500 transition-colors mb-2"
      >
        {opportunity.title}
      </Link>

      {/* Summary */}
      {opportunity.summary && (
        <p className="text-sm text-text-secondary font-body line-clamp-2 mb-4">
          {opportunity.summary}
        </p>
      )}

      {/* Meta Row: Source + Time */}
      <div className="flex items-center gap-4 text-xs font-mono text-text-tertiary mb-4">
        {opportunity.source && <span>{opportunity.source.toUpperCase()}</span>}
        {opportunity.source_engagement !== undefined &&
          opportunity.source_engagement > 0 && (
            <span>{opportunity.source_engagement} engagement</span>
          )}
        {opportunity.source_url && (
          <a
            href={opportunity.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-radar-500 hover:text-radar-400"
          >
            SOURCE <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Score Bars Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-light/50">
        <ScoreBar score={opportunity.demand_score} label="DEMAND" />
        <ScoreBar score={opportunity.market_score} label="MARKET" />
        <ScoreBar score={opportunity.feasibility_score} label="FEASIBLE" />
        <ScoreBar score={opportunity.revenue_score} label="REVENUE" />
      </div>

      {/* Additional Signals Row (compact) */}
      {(tierInfo ||
        journeyInfo ||
        riskInfo ||
        opportunity.success_prediction ||
        opportunity.similar_successes?.length) && (
        <div className="flex items-center gap-2 flex-wrap mt-4 pt-4 border-t border-light/50">
          {/* Journey Stage Badge */}
          {journeyInfo && opportunity.purchase_journey_stage !== "unaware" && (
            <span className={clsx("badge border text-xs", journeyInfo.color)}>
              {journeyInfo.label}
            </span>
          )}

          {/* Revenue Potential */}
          {opportunity.revenue_potential_score &&
            opportunity.revenue_potential_score >= 5 && (
              <span className="badge border bg-signal-success/20 text-signal-success border-signal-success/50 text-xs">
                <TrendingUp className="w-3 h-3 mr-1" />
                REV: {opportunity.revenue_potential_score.toFixed(1)}
              </span>
            )}

          {/* Monthly Price Estimate */}
          {opportunity.monthly_price_estimate && (
            <span className="badge border bg-medium text-text-secondary border-light text-xs">
              ~${opportunity.monthly_price_estimate}/MO
            </span>
          )}

          {/* Churning From */}
          {opportunity.churning_from &&
            opportunity.churning_from.length > 0 && (
              <span className="badge border bg-signal-warning/20 text-signal-warning border-signal-warning/50 text-xs">
                <Zap className="w-3 h-3 mr-1" />
                LEAVING: {opportunity.churning_from.slice(0, 2).join(", ")}
              </span>
            )}

          {/* Success Prediction (Pivot 4) */}
          {opportunity.success_prediction &&
            opportunity.success_prediction >= 50 && (
              <span className="badge border bg-signal-violet/20 text-signal-violet border-signal-violet/50 text-xs">
                <Trophy className="w-3 h-3 mr-1" />
                {opportunity.success_prediction.toFixed(0)}% MATCH
              </span>
            )}

          {/* Similar Successes (Pivot 4) */}
          {opportunity.similar_successes &&
            opportunity.similar_successes.length > 0 && (
              <span
                className="badge border bg-signal-violet/20 text-signal-violet border-signal-violet/50 text-xs"
                title={`Similar to: ${opportunity.similar_successes.join(", ")}`}
              >
                LIKE {opportunity.similar_successes[0].toUpperCase()}
              </span>
            )}

          {/* Risk Level (Pivot 4) */}
          {riskInfo && opportunity.risk_level !== "medium" && (
            <span className={clsx("badge border text-xs", riskInfo.color)}>
              {opportunity.risk_level === "high" && (
                <AlertTriangle className="w-3 h-3 mr-1" />
              )}
              {riskInfo.label}
            </span>
          )}
        </div>
      )}

      {/* View Detail Link */}
      <div className="flex justify-end mt-4">
        <Link
          to={`/opportunities/${opportunity.id}`}
          className="flex items-center gap-1 text-xs font-mono text-text-tertiary hover:text-radar-500 transition-colors"
        >
          VIEW DETAIL
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
