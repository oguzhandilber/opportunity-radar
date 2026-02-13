import { Link } from "react-router-dom";
import clsx from "clsx";
import { TrendingUp, TrendingDown, Star, Zap } from "lucide-react";

interface Score {
  build_ease_score: number;
  revenue_potential_score: number;
  market_opportunity_score: number;
  rising_score: number;
  total_opportunity_score: number;
  confidence_score?: number;
  opportunity_summary?: string;
}

interface AppCardProps {
  app: {
    id: number;
    name: string;
    developer: string;
    icon_url: string;
    price: number;
    rating: number;
    rating_count: number;
    category: string;
    is_rising: boolean;
    is_new_release: boolean;
    trend_direction?: string;
    app_store_url: string;
  };
  scores?: Score;
  compact?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "text-radar-500";
  if (score >= 60) return "text-signal-info";
  if (score >= 40) return "text-signal-warning";
  return "text-text-tertiary";
}

function getScoreBg(score: number): string {
  if (score >= 80) return "bg-radar-500/20 border-radar-500";
  if (score >= 60) return "bg-signal-info/20 border-signal-info";
  if (score >= 40) return "bg-signal-warning/20 border-signal-warning";
  return "bg-text-tertiary/20 border-text-tertiary";
}

function formatRatingCount(count: number): string {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return count.toString();
}

export function AppCard({ app, scores, compact = false }: AppCardProps) {
  if (compact) {
    return (
      <Link to={`/app-store/${app.id}`} className="block no-underline">
        <div className="flex items-center gap-4 p-4 bg-dark border border-light hover:border-radar-500 transition-colors">
          <img
            src={app.icon_url || "https://via.placeholder.com/48"}
            alt={app.name}
            className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
          />
          <div className="flex-1 min-w-0">
            <h3 className="font-mono font-bold text-text-primary text-sm truncate">
              {app.name}
            </h3>
            <p className="font-mono text-xs text-text-tertiary truncate">
              {app.developer}
            </p>
          </div>
          {app.is_rising && (
            <TrendingUp className="w-4 h-4 text-radar-500 flex-shrink-0" />
          )}
          {scores && scores.total_opportunity_score > 0 && (
            <span
              className={clsx(
                "font-mono font-bold text-sm px-2 py-1 rounded border",
                getScoreColor(scores.total_opportunity_score),
                getScoreBg(scores.total_opportunity_score),
              )}
            >
              {scores.total_opportunity_score.toFixed(0)}
            </span>
          )}
        </div>
      </Link>
    );
  }

  return (
    <Link to={`/app-store/${app.id}`} className="block no-underline">
      <div className="bg-dark border border-light p-5 hover:border-radar-500 transition-all group">
        <div className="flex gap-4">
          {/* Icon */}
          <img
            src={app.icon_url || "https://via.placeholder.com/60"}
            alt={app.name}
            className="w-16 h-16 rounded-lg object-cover flex-shrink-0 border border-light"
          />

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-mono font-bold text-text-primary text-lg group-hover:text-radar-500 transition-colors">
                  {app.name}
                </h3>
                <p className="font-mono text-xs text-text-tertiary">
                  {app.developer}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {app.is_rising && (
                  <span className="flex items-center gap-1 px-2 py-1 bg-radar-500/20 border border-radar-500 rounded">
                    <TrendingUp className="w-3 h-3 text-radar-500" />
                    <span className="font-mono text-xs font-bold text-radar-500">
                      RISING
                    </span>
                  </span>
                )}
                {app.is_new_release && (
                  <span className="flex items-center gap-1 px-2 py-1 bg-signal-info/20 border border-signal-info rounded">
                    <Zap className="w-3 h-3 text-signal-info" />
                    <span className="font-mono text-xs font-bold text-signal-info">
                      NEW
                    </span>
                  </span>
                )}
              </div>
            </div>

            {/* Meta Info */}
            <div className="flex items-center gap-4 mt-3 font-mono text-xs text-text-tertiary">
              <span className="flex items-center gap-1">
                <Star className="w-3 h-3" />
                {app.rating.toFixed(1)}
              </span>
              <span>{formatRatingCount(app.rating_count)} reviews</span>
              <span>•</span>
              <span className="text-text-secondary">{app.category}</span>
              <span>•</span>
              {app.price > 0 ? (
                <span className="text-text-primary">
                  ${app.price.toFixed(2)}
                </span>
              ) : (
                <span className="text-radar-500 font-bold">FREE</span>
              )}
              {app.trend_direction && app.trend_direction !== "stable" && (
                <>
                  <span>•</span>
                  {app.trend_direction === "up" ? (
                    <TrendingUp className="w-3 h-3 text-radar-500" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-signal-critical" />
                  )}
                </>
              )}
            </div>

            {/* Scores */}
            {scores && (
              <div className="flex flex-wrap gap-2 mt-4">
                {scores.total_opportunity_score > 0 && (
                  <div
                    className={clsx(
                      "px-3 py-1.5 rounded border font-mono text-sm font-bold",
                      getScoreColor(scores.total_opportunity_score),
                      getScoreBg(scores.total_opportunity_score),
                    )}
                  >
                    TOTAL: {scores.total_opportunity_score.toFixed(0)}
                  </div>
                )}
                {scores.revenue_potential_score > 0 && (
                  <div
                    className={clsx(
                      "px-3 py-1.5 rounded border font-mono text-sm",
                      getScoreColor(scores.revenue_potential_score),
                      getScoreBg(scores.revenue_potential_score),
                    )}
                  >
                    REV: {scores.revenue_potential_score.toFixed(0)}
                  </div>
                )}
                {scores.market_opportunity_score > 0 && (
                  <div
                    className={clsx(
                      "px-3 py-1.5 rounded border font-mono text-sm",
                      getScoreColor(scores.market_opportunity_score),
                      getScoreBg(scores.market_opportunity_score),
                    )}
                  >
                    MKT: {scores.market_opportunity_score.toFixed(0)}
                  </div>
                )}
                {scores.build_ease_score > 0 && (
                  <div
                    className={clsx(
                      "px-3 py-1.5 rounded border font-mono text-sm",
                      getScoreColor(scores.build_ease_score),
                      getScoreBg(scores.build_ease_score),
                    )}
                  >
                    BUILD: {scores.build_ease_score.toFixed(0)}
                  </div>
                )}
                {scores.rising_score > 0 &&
                  scores.rising_score !== scores.total_opportunity_score && (
                    <div
                      className={clsx(
                        "px-3 py-1.5 rounded border font-mono text-sm",
                        getScoreColor(scores.rising_score),
                        getScoreBg(scores.rising_score),
                      )}
                    >
                      RISE: {scores.rising_score.toFixed(0)}
                    </div>
                  )}
              </div>
            )}

            {/* Summary */}
            {scores?.opportunity_summary && (
              <p className="font-mono text-xs text-text-tertiary mt-3 line-clamp-2">
                {scores.opportunity_summary}
              </p>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

export default AppCard;
