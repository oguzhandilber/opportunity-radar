import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Loader2,
  RefreshCw,
  Trophy,
  TrendingUp,
  Zap,
  Star,
  Filter,
} from "lucide-react";
import clsx from "clsx";
import AppCard from "../components/AppCard";

interface Category {
  id: number;
  name: string;
  app_count: number;
  revenue_benchmark: number;
}

interface App {
  id: number;
  apple_app_id: string;
  name: string;
  developer: string;
  description?: string;
  icon_url: string;
  price: number;
  rating: number;
  rating_count: number;
  category: string;
  is_rising: boolean;
  is_new_release: boolean;
  trend_direction?: string;
  app_store_url: string;
  scores?: {
    build_ease_score: number;
    revenue_potential_score: number;
    market_opportunity_score: number;
    rising_score: number;
    total_opportunity_score: number;
    confidence_score: number;
    opportunity_summary?: string;
  };
}

interface Stats {
  total_apps: number;
  scored_apps: number;
  rising_apps: number;
  new_releases: number;
  scoring_coverage: number;
  average_scores: {
    total_opportunity: number;
    revenue_potential: number;
    market_opportunity: number;
    rising: number;
    build_ease: number;
  };
  categories: { name: string; count: number }[];
}

const API_BASE = "http://localhost:8000/api/app-store";

export function AppStoreDashboard() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [apps, setApps] = useState<App[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    total_pages: 0,
    total: 0,
  });
  const [scraping, setScraping] = useState(false);

  const [filters, setFilters] = useState({
    category: searchParams.get("category") || "",
    is_rising: searchParams.get("is_rising") === "true",
    is_new: searchParams.get("is_new") === "true",
    min_score: searchParams.get("min_score") || "0",
    sort_by: searchParams.get("sort_by") || "total_score",
    sort_order: searchParams.get("sort_order") || "desc",
  });

  const page = parseInt(searchParams.get("page") || "1");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const statsRes = await fetch(`${API_BASE}/stats`);
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }

      const catsRes = await fetch(`${API_BASE}/categories`);
      if (catsRes.ok) {
        setCategories(await catsRes.json());
      }

      const params = new URLSearchParams();
      params.set("page", page.toString());
      params.set("page_size", "20");
      if (filters.category) params.set("category", filters.category);
      if (filters.is_rising) params.set("is_rising", "true");
      if (filters.is_new) params.set("is_new", "true");
      if (filters.min_score) params.set("min_score", filters.min_score);
      params.set("sort_by", filters.sort_by);
      params.set("sort_order", filters.sort_order);

      const appsRes = await fetch(`${API_BASE}/apps?${params.toString()}`);
      if (appsRes.ok) {
        const data = await appsRes.json();
        setApps(data.items);
        setPagination({
          page: data.page,
          total_pages: data.total_pages,
          total: data.total,
        });
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const updateFilter = (key: string, value: string | boolean) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);

    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, String(value));
    } else {
      newParams.delete(key);
    }
    newParams.set("page", "1");
    setSearchParams(newParams);
  };

  const goToPage = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", newPage.toString());
    setSearchParams(newParams);
  };

  const triggerScrape = async () => {
    setScraping(true);
    try {
      await fetch(`${API_BASE}/scrape`, { method: "POST" });
      alert("Scraping initiated. Refresh in a few minutes.");
      setTimeout(() => fetchData(), 5000);
    } catch (error) {
      console.error("Error triggering scrape:", error);
    } finally {
      setScraping(false);
    }
  };

  if (loading) {
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
          <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider flex items-center gap-3">
            <Trophy className="w-6 h-6 text-radar-500" />
            APP STORE WINNERS
          </h1>
          <p className="text-text-secondary font-mono text-sm mt-1">
            Proven opportunities from the App Store
          </p>
        </div>

        <button
          onClick={triggerScrape}
          disabled={scraping}
          className="btn btn-primary flex items-center gap-2 min-h-[44px]"
        >
          {scraping ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              SCRAPING...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              REFRESH DATA
            </>
          )}
        </button>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-dark border border-light p-4">
            <div className="flex items-center gap-2 text-text-tertiary mb-2">
              <Trophy className="w-4 h-4" />
              <span className="font-mono text-xs uppercase tracking-wider">
                Total Apps
              </span>
            </div>
            <p className="font-display font-bold text-2xl text-text-primary">
              {stats.total_apps.toLocaleString()}
            </p>
          </div>

          <div className="bg-dark border border-light p-4">
            <div className="flex items-center gap-2 text-text-tertiary mb-2">
              <TrendingUp className="w-4 h-4" />
              <span className="font-mono text-xs uppercase tracking-wider">
                Rising
              </span>
            </div>
            <p className="font-display font-bold text-2xl text-radar-500">
              {stats.rising_apps.toLocaleString()}
            </p>
          </div>

          <div className="bg-dark border border-light p-4">
            <div className="flex items-center gap-2 text-text-tertiary mb-2">
              <Zap className="w-4 h-4" />
              <span className="font-mono text-xs uppercase tracking-wider">
                New
              </span>
            </div>
            <p className="font-display font-bold text-2xl text-signal-info">
              {stats.new_releases.toLocaleString()}
            </p>
          </div>

          <div className="bg-dark border border-light p-4">
            <div className="flex items-center gap-2 text-text-tertiary mb-2">
              <Star className="w-4 h-4" />
              <span className="font-mono text-xs uppercase tracking-wider">
                Avg Score
              </span>
            </div>
            <p className="font-display font-bold text-2xl text-text-primary">
              {stats.average_scores?.total_opportunity?.toFixed(1) || "--"}
            </p>
          </div>

          <div className="bg-dark border border-light p-4">
            <div className="flex items-center gap-2 text-text-tertiary mb-2">
              <Filter className="w-4 h-4" />
              <span className="font-mono text-xs uppercase tracking-wider">
                Scored
              </span>
            </div>
            <p className="font-display font-bold text-2xl text-text-primary">
              {stats.scoring_coverage}%
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-dark border border-light p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          {/* Category Filter */}
          <select
            className="input w-auto min-w-[160px]"
            value={filters.category}
            onChange={(e) => updateFilter("category", e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.name}>
                {cat.name} ({cat.app_count})
              </option>
            ))}
          </select>

          {/* Rising Toggle */}
          <button
            onClick={() => updateFilter("is_rising", !filters.is_rising)}
            className={clsx(
              "btn min-h-[44px] px-4",
              filters.is_rising ? "btn-primary" : "btn-secondary",
            )}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            RISING ONLY
          </button>

          {/* New Toggle */}
          <button
            onClick={() => updateFilter("is_new", !filters.is_new)}
            className={clsx(
              "btn min-h-[44px] px-4",
              filters.is_new ? "btn-primary" : "btn-secondary",
            )}
          >
            <Zap className="w-4 h-4 mr-2" />
            NEW RELEASES
          </button>

          {/* Score Filter */}
          <select
            className="input w-auto min-w-[140px]"
            value={filters.min_score}
            onChange={(e) => updateFilter("min_score", e.target.value)}
          >
            <option value="0">Any Score</option>
            <option value="70">Score 70+</option>
            <option value="80">Score 80+</option>
            <option value="90">Score 90+</option>
          </select>

          {/* Sort */}
          <select
            className="input w-auto min-w-[180px] ml-auto"
            value={`${filters.sort_by}-${filters.sort_order}`}
            onChange={(e) => {
              const [sort_by, sort_order] = e.target.value.split("-");
              updateFilter("sort_by", sort_by);
              updateFilter("sort_order", sort_order);
            }}
          >
            <option value="total_score-desc">Highest Score</option>
            <option value="rising_score-desc">Most Rising</option>
            <option value="revenue_potential_score-desc">Best Revenue</option>
            <option value="rating-desc">Highest Rated</option>
            <option value="rating_count-desc">Most Reviews</option>
          </select>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="font-mono text-sm text-text-tertiary">
          {pagination.total.toLocaleString()} apps found
        </span>
      </div>

      {/* Apps Grid */}
      {apps.length === 0 ? (
        <div className="bg-dark border border-light p-12 text-center">
          <Trophy className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
          <p className="font-mono text-text-secondary mb-4">
            No apps found matching your criteria.
          </p>
          <button
            onClick={triggerScrape}
            className="btn btn-primary min-h-[44px]"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            SCRAPE APP STORE
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {apps.map((app) => (
              <AppCard key={app.id} app={app} scores={app.scores} />
            ))}
          </div>

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => goToPage(page - 1)}
                disabled={page === 1}
                className="btn btn-secondary min-h-[44px] px-4"
              >
                ← PREV
              </button>

              {Array.from(
                { length: Math.min(5, pagination.total_pages) },
                (_, i) => {
                  let pageNum: number;
                  if (pagination.total_pages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= pagination.total_pages - 2) {
                    pageNum = pagination.total_pages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }

                  return (
                    <button
                      key={pageNum}
                      onClick={() => goToPage(pageNum)}
                      className={clsx(
                        "btn min-w-[44px] min-h-[44px] px-3",
                        page === pageNum ? "btn-primary" : "btn-secondary",
                      )}
                    >
                      {pageNum}
                    </button>
                  );
                },
              )}

              <button
                onClick={() => goToPage(page + 1)}
                disabled={page === pagination.total_pages}
                className="btn btn-secondary min-h-[44px] px-4"
              >
                NEXT →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default AppStoreDashboard;
