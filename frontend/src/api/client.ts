import axios from "axios";

// API key can be configured via environment variable
const API_KEY = import.meta.env.VITE_API_KEY || "";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error(
        "Authentication required. Set VITE_API_KEY environment variable.",
      );
    }
    if (error.response?.status === 429) {
      console.error(
        "Rate limit exceeded. Please wait before making more requests.",
      );
    }
    return Promise.reject(error);
  },
);

// Types
export interface DashboardStats {
  total_opportunities: number;
  new_opportunities: number;
  saved_opportunities: number;
  total_posts_scraped: number;
  average_score: number;
  top_sectors: Array<{ sector: string; count: number }>;
  top_product_types: Array<{ type: string; count: number }>;
}

export interface Opportunity {
  id: number;
  title: string;
  summary: string | null;
  product_type: string | null;
  sector: string | null;
  business_model: string | null;
  demand_score: number | null;
  market_score: number | null;
  feasibility_score: number | null;
  revenue_score: number | null;
  total_score: number | null;
  confidence: number | null;
  competitors: Array<{
    name: string;
    url?: string;
    notes?: string;
    strengths?: string;
    weaknesses?: string;
  }> | null;
  suggested_features: Array<{
    feature: string;
    priority: string;
    description: string;
    effort?: string;
  }> | null;
  go_to_market: string | null;
  // Payment Intent fields (Pivot 3)
  payment_signal_tier: number | null; // 1-4, null if no signal
  payment_signal_strength: number | null; // 0.0-1.0
  mentioned_prices: Array<{
    amount: number;
    currency: string;
    period: string | null;
    type: string;
  }> | null;
  monthly_price_estimate: number | null;
  competitor_mentions: Array<{
    name: string;
    category: string;
    sentiment: string;
    churning: boolean;
  }> | null;
  churning_from: string[] | null;
  purchase_journey_stage:
    | "unaware"
    | "aware"
    | "considering"
    | "ready"
    | "churning"
    | null;
  journey_confidence: number | null;
  revenue_potential_score: number | null;
  // Historical Success Validation (Pivot 4)
  matched_patterns: Array<{
    name: string;
    category: string;
    score: number;
    outcome: string;
    matched_signals: string[];
  }> | null;
  pattern_match_score: number | null;
  success_prediction: number | null; // 0-100 percentage
  similar_successes: string[] | null;
  success_factors: Record<string, number> | null;
  prediction_confidence: number | null;
  risk_level: "low" | "medium" | "high" | null;
  // Niche Focus (Pivot 2)
  detected_niches: Array<{
    niche_id: string;
    niche_name: string;
    confidence: number;
    matched_keywords: string[];
  }> | null;
  primary_niche: string | null;
  niche_fit_score: number | null;
  niche_scores: Record<
    string,
    {
      niche_name: string;
      fit_score: number;
      opportunity_score: number;
      overall_score: number;
      market_attractiveness: number;
      competitive_landscape: "low" | "medium" | "high";
      recommendations: string[];
    }
  > | null;
  // Status and metadata
  status: "new" | "saved" | "rejected" | "in_progress";
  notes: string | null;
  created_at: string;
  updated_at: string;
  source: string | null;
  source_url: string | null;
  source_content?: string;
  source_author?: string;
  source_engagement?: number;
}

export interface ScrapeStatus {
  is_running: boolean;
  last_run: string | null;
  last_result: {
    posts_scraped?: number;
    opportunities_found?: number;
    errors?: Array<{ scraper?: string; error: string }>;
    error?: string;
  } | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// API functions
export const dashboardApi = {
  getStats: () =>
    api.get<DashboardStats>("/dashboard/stats").then((r) => r.data),
};

export const opportunitiesApi = {
  list: (params?: {
    status?: string;
    sector?: string;
    product_type?: string;
    niche?: string;
    min_score?: number;
    search?: string;
    source?: string;
    limit?: number;
    offset?: number;
  }) =>
    api
      .get<PaginatedResponse<Opportunity>>("/opportunities", { params })
      .then((r) => r.data),

  get: (id: number) =>
    api.get<Opportunity>(`/opportunities/${id}`).then((r) => r.data),

  update: (id: number, data: { status?: string; notes?: string }) =>
    api.patch(`/opportunities/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    api.delete(`/opportunities/${id}`).then((r) => r.data),

  analyze: (id: number) =>
    api.post(`/opportunities/${id}/analyze`).then((r) => r.data),
};

export const scrapeApi = {
  trigger: () => api.post("/scrape/trigger").then((r) => r.data),
  status: () => api.get<ScrapeStatus>("/scrape/status").then((r) => r.data),
};

export const settingsApi = {
  list: () => api.get<Record<string, unknown>>("/settings").then((r) => r.data),
  get: (key: string) => api.get(`/settings/${key}`).then((r) => r.data),
  set: (key: string, value: unknown) =>
    api.put(`/settings/${key}`, { value }).then((r) => r.data),
  delete: (key: string) => api.delete(`/settings/${key}`).then((r) => r.data),
};

export default api;
