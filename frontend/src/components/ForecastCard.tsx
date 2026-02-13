import React, { useState } from "react";
import clsx from "clsx";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
  Target,
} from "lucide-react";

interface ForecastCardProps {
  appId: number;
  currentScore: number;
  predictedScore: number;
  trend: "rising" | "falling" | "stable";
  confidence: number;
  reasoning: string[];
  loading?: boolean;
}

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

function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return "bg-signal-success";
  if (confidence >= 60) return "bg-signal-warning";
  return "bg-signal-critical";
}

export default function ForecastCard({
  appId,
  currentScore,
  predictedScore,
  trend,
  confidence,
  reasoning,
  loading = false,
}: ForecastCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (loading) {
    return (
      <div className="bg-dark border border-light p-5 animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-5 bg-light rounded w-32"></div>
          <div className="h-4 bg-light rounded w-16"></div>
        </div>
        <div className="flex items-center gap-4 mb-4">
          <div className="h-8 bg-light rounded w-16"></div>
          <div className="h-8 bg-light rounded w-16"></div>
          <div className="h-8 bg-light rounded w-20"></div>
        </div>
        <div className="h-4 bg-light rounded w-full mb-2"></div>
        <div className="h-4 bg-light rounded w-3/4"></div>
      </div>
    );
  }

  const scoreChange = predictedScore - currentScore;
  const trendColor =
    trend === "rising"
      ? "text-signal-success"
      : trend === "falling"
        ? "text-signal-critical"
        : "text-text-tertiary";

  return (
    <div className="bg-dark border border-light p-5 hover:border-radar-500/50 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-radar-500" />
          <h3 className="font-mono font-bold text-text-primary text-lg">
            APP #{appId} FORECAST
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-text-tertiary">
            CONFIDENCE
          </span>
          <div className="flex items-center gap-1">
            <div className="w-12 bg-light rounded-full h-2">
              <div
                className={clsx(
                  "h-2 rounded-full transition-all duration-300",
                  getConfidenceColor(confidence),
                )}
                style={{ width: `${confidence}%` }}
              />
            </div>
            <span
              className={clsx(
                "font-mono text-xs font-bold",
                getScoreColor(confidence),
              )}
            >
              {confidence.toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <div className="flex flex-col items-center">
          <span className="font-mono text-xs text-text-tertiary mb-1">
            CURRENT
          </span>
          <div
            className={clsx(
              "font-mono font-bold text-2xl px-3 py-1 rounded border",
              getScoreColor(currentScore),
              getScoreBg(currentScore),
            )}
          >
            {currentScore.toFixed(0)}
          </div>
        </div>

        <div className="flex flex-col items-center justify-center">
          {React.createElement(
            trend === "rising"
              ? TrendingUp
              : trend === "falling"
                ? TrendingDown
                : Minus,
            { className: clsx("w-5 h-5 mb-1 animate-pulse", trendColor) },
          )}
          <span className={clsx("font-mono text-xs font-bold", trendColor)}>
            {scoreChange >= 0 ? "+" : ""}
            {scoreChange.toFixed(0)}
          </span>
        </div>

        <div className="flex flex-col items-center">
          <span className="font-mono text-xs text-text-tertiary mb-1">
            PREDICTED
          </span>
          <div
            className={clsx(
              "font-mono font-bold text-2xl px-3 py-1 rounded border",
              getScoreColor(predictedScore),
              getScoreBg(predictedScore),
            )}
          >
            {predictedScore.toFixed(0)}
          </div>
        </div>

        <div className="flex-1"></div>

        <div className="flex flex-col items-center">
          <span className="font-mono text-xs text-text-tertiary mb-1">
            TREND
          </span>
          <span
            className={clsx(
              "font-mono text-sm font-bold px-3 py-1 rounded border",
              trendColor === "text-signal-success"
                ? "bg-signal-success/20 border-signal-success text-signal-success"
                : trendColor === "text-signal-critical"
                  ? "bg-signal-critical/20 border-signal-critical text-signal-critical"
                  : "bg-medium border-light text-text-tertiary",
            )}
          >
            {trend.toUpperCase()}
          </span>
        </div>
      </div>

      {reasoning && reasoning.length > 0 && (
        <div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 font-mono text-xs text-radar-500 hover:text-radar-400 transition-colors mb-3"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-3 h-3" />
                HIDE FORECAST REASONING
              </>
            ) : (
              <>
                <ChevronDown className="w-3 h-3" />
                SHOW {reasoning.length} REASONING POINTS
              </>
            )}
          </button>

          {isExpanded && (
            <div className="border-t border-light/50 pt-4">
              <div className="space-y-2">
                {reasoning.map((point, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <div
                      className={clsx(
                        "w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0",
                        trend === "rising"
                          ? "bg-signal-success"
                          : trend === "falling"
                            ? "bg-signal-critical"
                            : "bg-text-tertiary",
                      )}
                    ></div>
                    <span className="font-mono text-xs text-text-secondary leading-relaxed">
                      {point}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-light/50 flex items-center justify-between">
        <div className="flex items-center gap-4 font-mono text-xs text-text-tertiary">
          <span>
            CHANGE: {scoreChange >= 0 ? "+" : ""}
            {scoreChange.toFixed(1)}%
          </span>
          <span>PERIOD: 30 DAYS</span>
        </div>
        <div
          className={clsx(
            "font-mono text-xs px-2 py-1 rounded border",
            trend === "rising"
              ? "bg-signal-success/20 border-signal-success text-signal-success"
              : trend === "falling"
                ? "bg-signal-critical/20 border-signal-critical text-signal-critical"
                : "bg-medium border-light text-text-tertiary",
          )}
        >
          {trend === "rising"
            ? "BULLISH"
            : trend === "falling"
              ? "BEARISH"
              : "NEUTRAL"}
        </div>
      </div>
    </div>
  );
}
