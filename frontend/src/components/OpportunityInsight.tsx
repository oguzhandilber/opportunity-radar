import { useState } from "react";
import clsx from "clsx";
import {
  TrendingUp,
  Calendar,
  Zap,
  Copy,
  ChevronRight,
  ExternalLink,
  AlertCircle,
  Lightbulb,
  Target,
} from "lucide-react";

interface OpportunityInsightProps {
  insights: {
    type: "seasonal" | "viral" | "forecast" | "clone";
    title: string;
    description: string;
    impact: "high" | "medium" | "low";
    actionable: boolean;
    actionUrl?: string;
    actionText?: string;
  }[];
  loading?: boolean;
}

const typeConfig = {
  seasonal: {
    icon: Calendar,
    label: "SEASONAL",
    color: "bg-signal-info/20 text-signal-info border-signal-info/50",
    bgGradient: "from-signal-info/5 to-signal-info/10",
  },
  viral: {
    icon: Zap,
    label: "VIRAL",
    color:
      "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
    bgGradient: "from-signal-critical/5 to-signal-critical/10",
  },
  forecast: {
    icon: TrendingUp,
    label: "FORECAST",
    color: "bg-signal-success/20 text-signal-success border-signal-success/50",
    bgGradient: "from-signal-success/5 to-signal-success/10",
  },
  clone: {
    icon: Copy,
    label: "CLONE",
    color: "bg-signal-violet/20 text-signal-violet border-signal-violet/50",
    bgGradient: "from-signal-violet/5 to-signal-violet/10",
  },
};

const impactConfig = {
  high: {
    label: "HIGH IMPACT",
    color:
      "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
    dotColor: "bg-signal-critical",
  },
  medium: {
    label: "MED IMPACT",
    color: "bg-signal-warning/20 text-signal-warning border-signal-warning/50",
    dotColor: "bg-signal-warning",
  },
  low: {
    label: "LOW IMPACT",
    color: "bg-medium text-text-secondary border-light",
    dotColor: "bg-text-tertiary",
  },
};

export default function OpportunityInsight({
  insights,
  loading = false,
}: OpportunityInsightProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (loading) {
    return (
      <div className="bg-dark border border-light p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-mono font-bold text-text-primary text-lg">
            AI INSIGHTS
          </h2>
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-radar-500" />
            <span className="font-mono text-xs text-text-tertiary">
              ANALYZING...
            </span>
          </div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-medium/20 border border-light p-4 animate-pulse"
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-light rounded"></div>
                <div className="flex-1">
                  <div className="h-4 bg-light rounded w-32 mb-2"></div>
                  <div className="h-3 bg-light rounded w-full mb-2"></div>
                  <div className="h-3 bg-light rounded w-3/4"></div>
                </div>
                <div className="h-6 bg-light rounded w-20"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!insights || insights.length === 0) {
    return (
      <div className="bg-dark border border-light p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-mono font-bold text-text-primary text-lg">
            AI INSIGHTS
          </h2>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-signal-warning" />
            <span className="font-mono text-xs text-text-tertiary">
              NO INSIGHTS
            </span>
          </div>
        </div>
        <div className="text-center py-8">
          <Lightbulb className="w-12 h-12 text-text-tertiary mx-auto mb-3" />
          <p className="font-mono text-text-tertiary text-sm">
            NO INSIGHTS AVAILABLE
          </p>
          <p className="font-mono text-xs text-text-tertiary mt-1">
            CHECK BACK LATER
          </p>
        </div>
      </div>
    );
  }

  const highImpactCount = insights.filter((i) => i.impact === "high").length;
  const actionableCount = insights.filter((i) => i.actionable).length;

  return (
    <div className="bg-dark border border-light p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Lightbulb className="w-5 h-5 text-radar-500" />
          <h2 className="font-mono font-bold text-text-primary text-lg">
            AI INSIGHTS
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {highImpactCount > 0 && (
            <span className="font-mono text-xs text-signal-critical">
              {highImpactCount} HIGH PRIORITY
            </span>
          )}
          {actionableCount > 0 && (
            <span className="font-mono text-xs text-radar-500">
              {actionableCount} ACTIONABLE
            </span>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {insights.map((insight, index) => {
          const typeInfo = typeConfig[insight.type];
          const impactInfo = impactConfig[insight.impact];
          const Icon = typeInfo.icon;
          const isExpanded = expandedIndex === index;

          return (
            <div
              key={index}
              className={clsx(
                "border hover:border-radar-500/50 transition-all overflow-hidden",
                "bg-gradient-to-br",
                typeInfo.bgGradient,
              )}
            >
              <div className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex flex-col items-center gap-2">
                    <div className={clsx("p-2 rounded border", typeInfo.color)}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div
                      className={clsx(
                        "w-2 h-2 rounded-full",
                        impactInfo.dotColor,
                      )}
                    ></div>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={clsx(
                              "font-mono text-xs px-2 py-1 rounded border",
                              typeInfo.color,
                            )}
                          >
                            {typeInfo.label}
                          </span>
                          <span
                            className={clsx(
                              "font-mono text-xs px-2 py-1 rounded border",
                              impactInfo.color,
                            )}
                          >
                            {impactInfo.label}
                          </span>
                          {insight.actionable && (
                            <span className="font-mono text-xs px-2 py-1 rounded border bg-radar-500/20 text-radar-500 border-radar-500/50">
                              ACTIONABLE
                            </span>
                          )}
                        </div>
                        <h3 className="font-mono font-bold text-text-primary text-sm mb-2">
                          {insight.title}
                        </h3>
                      </div>
                    </div>

                    <p className="font-mono text-xs text-text-secondary leading-relaxed mb-3">
                      {insight.description}
                    </p>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {insight.actionable && (
                          <button
                            onClick={() =>
                              setExpandedIndex(isExpanded ? null : index)
                            }
                            className="flex items-center gap-2 font-mono text-xs text-radar-500 hover:text-radar-400 transition-colors"
                          >
                            <Target className="w-3 h-3" />
                            {isExpanded ? "HIDE ACTIONS" : "SHOW ACTIONS"}
                          </button>
                        )}
                      </div>

                      {insight.actionable && insight.actionUrl && (
                        <a
                          href={insight.actionUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 font-mono text-xs text-radar-500 hover:text-radar-400 transition-colors"
                        >
                          {insight.actionText || "TAKE ACTION"}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {isExpanded && insight.actionable && (
                  <div className="mt-4 pt-4 border-t border-light/50">
                    <div className="bg-medium/20 border border-light p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-radar-500" />
                        <span className="font-mono text-xs font-bold text-radar-500">
                          RECOMMENDED ACTIONS
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-start gap-2">
                          <ChevronRight className="w-3 h-3 text-radar-500 mt-0.5 flex-shrink-0" />
                          <span className="font-mono text-xs text-text-secondary">
                            Analyze market fit for this opportunity
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <ChevronRight className="w-3 h-3 text-radar-500 mt-0.5 flex-shrink-0" />
                          <span className="font-mono text-xs text-text-secondary">
                            Review competitor landscape and pricing
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <ChevronRight className="w-3 h-3 text-radar-500 mt-0.5 flex-shrink-0" />
                          <span className="font-mono text-xs text-text-secondary">
                            Create MVP validation plan
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-light/50">
        <div className="flex items-center justify-between font-mono text-xs text-text-tertiary">
          <div className="flex items-center gap-4">
            <span>TOTAL INSIGHTS: {insights.length}</span>
            <span>HIGH PRIORITY: {highImpactCount}</span>
            <span>ACTIONABLE: {actionableCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <Lightbulb className="w-3 h-3 text-radar-500" />
            <span>AI-POWERED ANALYSIS</span>
          </div>
        </div>
      </div>
    </div>
  );
}
