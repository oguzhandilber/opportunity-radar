import { useState } from "react";
import clsx from "clsx";
import {
  Copy,
  Zap,
  Target,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";

export interface CloneRecommendation {
  type: "direct_clone" | "feature_clone" | "platform_clone" | "upgrade_clone";
  similarity: number;
  description: string;
  opportunityScore: number;
  improvements?: string[];
}

interface CloneRecommendationsProps {
  recommendations: CloneRecommendation[];
  loading?: boolean;
}

const typeConfig = {
  direct_clone: {
    icon: Copy,
    label: "DIRECT CLONE",
    color:
      "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
    description: "Nearly identical app concept",
  },
  feature_clone: {
    icon: Target,
    label: "FEATURE CLONE",
    color: "bg-signal-warning/20 text-signal-warning border-signal-warning/50",
    description: "Core feature replication",
  },
  platform_clone: {
    icon: Zap,
    label: "PLATFORM CLONE",
    color: "bg-signal-info/20 text-signal-info border-signal-info/50",
    description: "Multi-sided marketplace",
  },
  upgrade_clone: {
    icon: TrendingUp,
    label: "UPGRADE CLONE",
    color: "bg-signal-success/20 text-signal-success border-signal-success/50",
    description: "Improved version opportunity",
  },
};

function getScoreColor(score: number): string {
  if (score >= 80) return "text-radar-500";
  if (score >= 60) return "text-signal-info";
  if (score >= 40) return "text-signal-warning";
  return "text-signal-critical";
}

function getScoreBg(score: number): string {
  if (score >= 80) return "bg-radar-500/20 border-radar-500";
  if (score >= 60) return "bg-signal-info/20 border-signal-info";
  if (score >= 40) return "bg-signal-warning/20 border-signal-warning";
  return "bg-signal-critical/20 border-signal-critical";
}

export default function CloneRecommendations({
  recommendations,
  loading = false,
}: CloneRecommendationsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (loading) {
    return (
      <div className="bg-dark border border-light p-6">
        <h2 className="font-mono font-bold text-text-primary text-lg mb-4">
          CLONE OPPORTUNITIES
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-medium/20 border border-light p-4 animate-pulse"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-light rounded"></div>
                <div className="flex-1">
                  <div className="h-4 bg-light rounded w-24 mb-2"></div>
                  <div className="h-3 bg-light rounded w-32"></div>
                </div>
                <div className="h-6 bg-light rounded w-16"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-dark border border-light p-6">
        <h2 className="font-mono font-bold text-text-primary text-lg mb-4">
          CLONE OPPORTUNITIES
        </h2>
        <div className="text-center py-8">
          <Copy className="w-12 h-12 text-text-tertiary mx-auto mb-3" />
          <p className="font-mono text-text-tertiary text-sm">
            NO CLONE OPPORTUNITIES FOUND
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-dark border border-light p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono font-bold text-text-primary text-lg">
          CLONE OPPORTUNITIES
        </h2>
        <span className="font-mono text-xs text-text-tertiary">
          {recommendations.length} OPPORTUNITIES
        </span>
      </div>

      <div className="space-y-3">
        {recommendations.map((recommendation, index) => {
          const config = typeConfig[recommendation.type];
          const Icon = config.icon;
          const isExpanded = expandedIndex === index;

          return (
            <div
              key={index}
              className="bg-medium/20 border border-light hover:border-radar-500/50 transition-all"
            >
              <div className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex flex-col items-center gap-2">
                    <div className={clsx("p-2 rounded border", config.color)}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span
                      className={clsx(
                        "font-mono text-xs px-2 py-1 rounded border",
                        config.color,
                      )}
                    >
                      {config.label}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-text-tertiary">
                          SIMILARITY
                        </span>
                        <div className="flex items-center gap-1">
                          <div className="w-16 bg-light rounded-full h-2">
                            <div
                              className={clsx(
                                "h-2 rounded-full transition-all duration-300",
                                recommendation.similarity >= 80
                                  ? "bg-radar-500"
                                  : recommendation.similarity >= 60
                                    ? "bg-signal-info"
                                    : recommendation.similarity >= 40
                                      ? "bg-signal-warning"
                                      : "bg-signal-critical",
                              )}
                              style={{ width: `${recommendation.similarity}%` }}
                            />
                          </div>
                          <span
                            className={clsx(
                              "font-mono text-xs font-bold",
                              getScoreColor(recommendation.similarity),
                            )}
                          >
                            {recommendation.similarity.toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-text-tertiary">
                          OPPORTUNITY
                        </span>
                        <span
                          className={clsx(
                            "font-mono text-xs font-bold px-2 py-1 rounded border",
                            getScoreColor(recommendation.opportunityScore),
                            getScoreBg(recommendation.opportunityScore),
                          )}
                        >
                          {recommendation.opportunityScore.toFixed(0)}
                        </span>
                      </div>
                    </div>

                    <p className="font-mono text-sm text-text-secondary mb-2">
                      {recommendation.description}
                    </p>

                    <p className="font-mono text-xs text-text-tertiary mb-3">
                      {config.description}
                    </p>

                    {recommendation.improvements &&
                      recommendation.improvements.length > 0 && (
                        <button
                          onClick={() =>
                            setExpandedIndex(isExpanded ? null : index)
                          }
                          className="flex items-center gap-2 font-mono text-xs text-radar-500 hover:text-radar-400 transition-colors"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="w-3 h-3" />
                              HIDE IMPROVEMENTS
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-3 h-3" />
                              SHOW {recommendation.improvements.length}{" "}
                              IMPROVEMENTS
                            </>
                          )}
                        </button>
                      )}
                  </div>
                </div>

                {isExpanded && recommendation.improvements && (
                  <div className="mt-4 pt-4 border-t border-light/50">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-signal-success" />
                      <span className="font-mono text-xs font-bold text-signal-success">
                        WHY CLONE
                      </span>
                    </div>
                    <ul className="space-y-1">
                      {recommendation.improvements.map(
                        (improvement, improvementIndex) => (
                          <li
                            key={improvementIndex}
                            className="flex items-start gap-2"
                          >
                            <div className="w-1 h-1 bg-radar-500 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="font-mono text-xs text-text-secondary">
                              {improvement}
                            </span>
                          </li>
                        ),
                      )}
                    </ul>
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
            <span>
              AVG SIMILARITY:{" "}
              {(
                recommendations.reduce((sum, r) => sum + r.similarity, 0) /
                recommendations.length
              ).toFixed(0)}
              %
            </span>
            <span>
              AVG OPPORTUNITY:{" "}
              {(
                recommendations.reduce(
                  (sum, r) => sum + r.opportunityScore,
                  0,
                ) / recommendations.length
              ).toFixed(0)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-3 h-3 text-signal-warning" />
            <span>VALIDATED CLONE TARGETS</span>
          </div>
        </div>
      </div>
    </div>
  );
}
