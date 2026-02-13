import { Loader2, Play, Crosshair, Bookmark, TrendingUp } from "lucide-react";
import {
  useDashboardStats,
  useScrapeStatus,
  useTriggerScrape,
} from "../hooks/useApi";
import StatCard from "../components/StatCard";

/**
 * Mission Control Brutalism Dashboard
 *
 * 2x2 grid layout with massive centered numbers
 * Terminal-style with count-up animations
 */
export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: scrapeStatus } = useScrapeStatus();
  const triggerScrape = useTriggerScrape();

  const handleScrape = () => {
    triggerScrape.mutate();
  };

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-radar-500" />
          <span className="font-mono text-sm text-text-secondary">
            LOADING DASHBOARD...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
            MISSION CONTROL
          </h1>
          <p className="text-text-secondary font-mono text-sm">
            Opportunity Radar Status
          </p>
        </div>

        <button
          onClick={handleScrape}
          disabled={scrapeStatus?.is_running || triggerScrape.isPending}
          className="btn btn-primary flex items-center gap-2 min-h-[44px]"
        >
          {scrapeStatus?.is_running || triggerScrape.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              SCANNING...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              RUN SCAN
            </>
          )}
        </button>
      </div>

      {/* Stats Grid - 2x2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <StatCard
          title="TOTAL OPPORTUNITIES"
          value={stats?.total_opportunities ?? 0}
          icon={<Crosshair className="w-6 h-6" />}
          trend={
            stats?.new_opportunities
              ? { value: stats.new_opportunities, label: "new this week" }
              : undefined
          }
        />
        <StatCard
          title="NEW TARGETS"
          value={stats?.new_opportunities ?? 0}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <StatCard
          title="SAVED"
          value={stats?.saved_opportunities ?? 0}
          icon={<Bookmark className="w-6 h-6" />}
        />
        <StatCard
          title="AVG SCORE"
          value={stats?.average_score?.toFixed(1) ?? "--"}
          animate={false}
        />
      </div>

      {/* Scrape Status */}
      {scrapeStatus?.last_result && (
        <div className="bg-dark border border-light p-6 mb-8">
          <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
            LAST SCAN RESULT
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="border-l-2 border-l-radar-500 pl-4">
              <span className="label-mono">Posts Scraped</span>
              <p className="font-display font-bold text-2xl text-text-primary mt-1">
                {scrapeStatus.last_result.posts_scraped ?? 0}
              </p>
            </div>
            <div className="border-l-2 border-l-signal-success pl-4">
              <span className="label-mono">Opportunities Found</span>
              <p className="font-display font-bold text-2xl text-text-primary mt-1">
                {scrapeStatus.last_result.opportunities_found ?? 0}
              </p>
            </div>
            <div className="border-l-2 border-l-signal-info pl-4">
              <span className="label-mono">Last Run</span>
              <p className="font-mono text-sm text-text-secondary mt-2">
                {scrapeStatus.last_run
                  ? new Date(scrapeStatus.last_run).toLocaleString()
                  : "Never"}
              </p>
            </div>
          </div>
          {scrapeStatus.last_result.errors &&
            scrapeStatus.last_result.errors.length > 0 && (
              <div className="mt-4 p-4 bg-signal-critical/10 border border-signal-critical/50">
                <p className="font-mono text-sm font-bold text-signal-critical mb-2">
                  ERRORS:
                </p>
                <ul className="font-mono text-sm text-signal-critical space-y-1">
                  {scrapeStatus.last_result.errors.map((err, i) => (
                    <li key={i}>
                      {err.scraper && `[${err.scraper.toUpperCase()}] `}
                      {err.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      )}

      {/* Top Sectors & Product Types */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark border border-light p-6">
          <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
            TOP SECTORS
          </h2>
          {stats?.top_sectors && stats.top_sectors.length > 0 ? (
            <div className="space-y-3">
              {stats.top_sectors.map((sector, i) => (
                <div
                  key={sector.sector}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-text-tertiary w-4">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-body text-text-primary">
                      {sector.sector}
                    </span>
                  </div>
                  <span className="badge badge-sector">{sector.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-mono text-text-tertiary">NO DATA</p>
          )}
        </div>

        <div className="bg-dark border border-light p-6">
          <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
            TOP PRODUCT TYPES
          </h2>
          {stats?.top_product_types && stats.top_product_types.length > 0 ? (
            <div className="space-y-3">
              {stats.top_product_types.map((type, i) => (
                <div
                  key={type.type}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-text-tertiary w-4">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-body text-text-primary">
                      {type.type}
                    </span>
                  </div>
                  <span className="badge badge-niche">{type.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-mono text-text-tertiary">NO DATA</p>
          )}
        </div>
      </div>
    </div>
  );
}
