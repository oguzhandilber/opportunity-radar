import { useState } from "react";
import {
  Loader2,
  Filter,
  X,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useOpportunities } from "../hooks/useApi";
import OpportunityCard from "../components/OpportunityCard";
import clsx from "clsx";

const statuses = ["all", "new", "saved", "in_progress", "rejected"];
const minScores = [0, 5, 6, 7, 8];
const sources = [
  "all",
  "hackernews",
  "twitter",
  "google_trends",
  "product_hunt",
  "reddit",
];
const niches = [
  "all",
  "fintech",
  "healthtech",
  "edtech",
  "devtools",
  "ecommerce",
  "saas",
  "ai_ml",
  "creator_economy",
  "hr_tech",
  "legal_tech",
  "proptech",
  "foodtech",
  "martech",
  "productivity",
  "security",
  "sales_tech",
];
const PAGE_SIZE = 20;

/**
 * Mission Control Brutalism Opportunity List
 *
 * Dark theme filter panel
 * Card scan-in animations
 * Terminal-style UI
 */
export default function OpportunityList() {
  const [filters, setFilters] = useState<{
    status?: string;
    min_score?: number;
    search?: string;
    source?: string;
    niche?: string;
  }>({});
  const [showFilters, setShowFilters] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(0);

  const { data, isLoading } = useOpportunities({
    ...(filters.status === "all" ? { ...filters, status: undefined } : filters),
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });

  const opportunities = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const clearFilters = () => {
    setFilters({});
    setPage(0);
  };

  const handleExport = (format: "csv" | "json") => {
    const params = new URLSearchParams();
    if (filters.status && filters.status !== "all")
      params.set("status", filters.status);
    if (filters.min_score)
      params.set("min_score", filters.min_score.toString());
    window.open(`/api/export/${format}?${params.toString()}`, "_blank");
  };

  const handleSearch = () => {
    setFilters({ ...filters, search: searchInput || undefined });
    setPage(0);
  };

  const hasFilters =
    filters.status ||
    filters.min_score ||
    filters.search ||
    filters.source ||
    filters.niche;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
            OPPORTUNITIES
          </h1>
          <p className="text-text-secondary font-mono text-sm">
            {total} targets found
          </p>
        </div>

        <div className="flex gap-2">
          {/* Export Dropdown */}
          <div className="relative group">
            <button className="btn btn-secondary flex items-center gap-2 min-h-[44px]">
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">EXPORT</span>
            </button>
            <div className="absolute right-0 mt-1 hidden group-hover:block group-focus-within:block bg-dark border border-light z-10 min-w-[140px]">
              <button
                onClick={() => handleExport("csv")}
                className="block w-full px-4 py-3 text-left font-mono text-sm text-text-secondary hover:bg-medium hover:text-text-primary min-h-[44px]"
              >
                EXPORT CSV
              </button>
              <button
                onClick={() => handleExport("json")}
                className="block w-full px-4 py-3 text-left font-mono text-sm text-text-secondary hover:bg-medium hover:text-text-primary min-h-[44px]"
              >
                EXPORT JSON
              </button>
            </div>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={clsx(
              "btn flex items-center gap-2 min-h-[44px]",
              showFilters || hasFilters ? "btn-primary" : "btn-secondary",
            )}
          >
            <Filter className="w-4 h-4" />
            <span className="hidden sm:inline">FILTERS</span>
            {hasFilters && (
              <span className="ml-1 w-5 h-5 bg-darkest text-radar-500 text-xs flex items-center justify-center font-bold">
                {Object.values(filters).filter(Boolean).length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-dark border border-light p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-mono font-bold text-text-primary tracking-wider">
              FILTERS
            </h3>
            {hasFilters && (
              <button
                onClick={clearFilters}
                className="text-sm font-mono text-signal-critical hover:text-red-400 flex items-center gap-1 min-h-[44px] px-2"
              >
                <X className="w-4 h-4" />
                CLEAR ALL
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div className="sm:col-span-2">
              <label className="label-mono mb-2 block">Search</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Search title or summary..."
                  className="flex-1"
                />
                <button
                  onClick={handleSearch}
                  className="btn btn-primary min-w-[44px] min-h-[44px]"
                >
                  <Search className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Status */}
            <div>
              <label className="label-mono mb-2 block">Status</label>
              <select
                value={filters.status || "all"}
                onChange={(e) => {
                  setFilters({
                    ...filters,
                    status:
                      e.target.value === "all" ? undefined : e.target.value,
                  });
                  setPage(0);
                }}
                className="w-full min-h-[44px]"
              >
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status.toUpperCase().replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            {/* Source */}
            <div>
              <label className="label-mono mb-2 block">Source</label>
              <select
                value={filters.source || "all"}
                onChange={(e) => {
                  setFilters({
                    ...filters,
                    source:
                      e.target.value === "all" ? undefined : e.target.value,
                  });
                  setPage(0);
                }}
                className="w-full min-h-[44px]"
              >
                {sources.map((src) => (
                  <option key={src} value={src}>
                    {src === "all"
                      ? "ALL SOURCES"
                      : src.toUpperCase().replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            {/* Min Score */}
            <div>
              <label className="label-mono mb-2 block">Min Score</label>
              <select
                value={filters.min_score || 0}
                onChange={(e) => {
                  setFilters({
                    ...filters,
                    min_score: Number(e.target.value) || undefined,
                  });
                  setPage(0);
                }}
                className="w-full min-h-[44px]"
              >
                {minScores.map((score) => (
                  <option key={score} value={score}>
                    {score === 0 ? "ANY" : `${score}+`}
                  </option>
                ))}
              </select>
            </div>

            {/* Niche */}
            <div>
              <label className="label-mono mb-2 block">Niche</label>
              <select
                value={filters.niche || "all"}
                onChange={(e) => {
                  setFilters({
                    ...filters,
                    niche:
                      e.target.value === "all" ? undefined : e.target.value,
                  });
                  setPage(0);
                }}
                className="w-full min-h-[44px]"
              >
                {niches.map((niche) => (
                  <option key={niche} value={niche}>
                    {niche === "all"
                      ? "ALL NICHES"
                      : niche.toUpperCase().replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Opportunity List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-radar-500" />
            <span className="font-mono text-sm text-text-secondary">
              SCANNING...
            </span>
          </div>
        </div>
      ) : opportunities && opportunities.length > 0 ? (
        <>
          <div className="space-y-4">
            {opportunities.map((opportunity) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-6 border-t border-light">
              <p className="font-mono text-sm text-text-secondary">
                SHOWING {page * PAGE_SIZE + 1}-
                {Math.min((page + 1) * PAGE_SIZE, total)} OF {total}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="btn btn-secondary min-h-[44px] min-w-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-mono text-sm text-text-secondary px-4">
                  PAGE {page + 1} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="btn btn-secondary min-h-[44px] min-w-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Next page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-dark border border-light p-12 text-center">
          <p className="font-mono text-text-secondary">NO TARGETS FOUND</p>
          <p className="font-mono text-sm text-text-tertiary mt-2">
            Adjust filters or run a new scan
          </p>
        </div>
      )}
    </div>
  );
}
