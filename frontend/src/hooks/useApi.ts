import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  dashboardApi,
  opportunitiesApi,
  scrapeApi,
  settingsApi,
} from "../api/client";

// Dashboard hooks
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: dashboardApi.getStats,
  });
}

// Opportunity hooks
export function useOpportunities(params?: {
  status?: string;
  sector?: string;
  product_type?: string;
  min_score?: number;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["opportunities", params],
    queryFn: () => opportunitiesApi.list(params),
  });
}

export function useOpportunity(id: number) {
  return useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => opportunitiesApi.get(id),
    enabled: !!id,
  });
}

export function useUpdateOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: { status?: string; notes?: string };
    }) => opportunitiesApi.update(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({
        queryKey: ["opportunity", variables.id],
      });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Opportunity updated");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update opportunity");
    },
  });
}

export function useAnalyzeOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => opportunitiesApi.analyze(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["opportunity", id] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      toast.success("Analysis completed");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Analysis failed");
    },
  });
}

export function useDeleteOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: opportunitiesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Opportunity deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to delete opportunity");
    },
  });
}

// Scrape hooks
export function useScrapeStatus() {
  return useQuery({
    queryKey: ["scrape", "status"],
    queryFn: scrapeApi.status,
    refetchInterval: (query) => {
      // Poll every 5 seconds if scraping is in progress
      return query.state.data?.is_running ? 5000 : false;
    },
  });
}

export function useTriggerScrape() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: scrapeApi.trigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scrape", "status"] });
      toast.success("Scrape job started");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to start scrape");
    },
  });
}

// Settings hooks
export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: settingsApi.list,
  });
}

export function useUpdateSetting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) =>
      settingsApi.set(key, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Setting saved");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to save setting");
    },
  });
}
