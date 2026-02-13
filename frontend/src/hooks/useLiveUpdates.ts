import { useState, useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

export interface LiveUpdate {
  id: string;
  type:
    | "opportunity_created"
    | "opportunity_updated"
    | "score_changed"
    | "alert_triggered"
    | "scrape_completed";
  title: string;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
  read: boolean;
}

export function useLiveUpdates() {
  const [updates, setUpdates] = useState<LiveUpdate[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const queueRef = useRef<LiveUpdate[]>([]);
  const queryClient = useQueryClient();

  const addUpdate = useCallback(
    (update: Omit<LiveUpdate, "id" | "timestamp" | "read">) => {
      const newUpdate: LiveUpdate = {
        ...update,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        read: false,
      };

      setUpdates((prev) => [newUpdate, ...prev.slice(0, 999)]);
      queueRef.current.push(newUpdate);

      switch (update.type) {
        case "opportunity_created":
        case "opportunity_updated":
        case "score_changed":
          queryClient.invalidateQueries({ queryKey: ["opportunities"] });
          queryClient.invalidateQueries({ queryKey: ["dashboard"] });
          break;
        case "scrape_completed":
          queryClient.invalidateQueries({ queryKey: ["opportunities"] });
          queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
          queryClient.invalidateQueries({ queryKey: ["scrape", "status"] });
          break;
      }
    },
    [queryClient],
  );

  const markAsRead = useCallback((updateId?: string) => {
    if (updateId) {
      setUpdates((prev) =>
        prev.map((update) =>
          update.id === updateId ? { ...update, read: true } : update,
        ),
      );
    } else {
      setUpdates((prev) => prev.map((update) => ({ ...update, read: true })));
    }
  }, []);

  const markAsReadByType = useCallback((type: LiveUpdate["type"]) => {
    setUpdates((prev) =>
      prev.map((update) =>
        update.type === type ? { ...update, read: true } : update,
      ),
    );
  }, []);

  const clearRead = useCallback(() => {
    setUpdates((prev) => prev.filter((update) => !update.read));
  }, []);

  const clearAll = useCallback(() => {
    setUpdates([]);
    queueRef.current = [];
  }, []);

  const clearByType = useCallback((type: LiveUpdate["type"]) => {
    setUpdates((prev) => prev.filter((update) => update.type !== type));
    queueRef.current = queueRef.current.filter(
      (update) => update.type !== type,
    );
  }, []);

  const unreadCount = updates.filter((update) => !update.read).length;
  const unreadByType = useCallback(
    (type: LiveUpdate["type"]) => {
      return updates.filter((update) => update.type === type && !update.read)
        .length;
    },
    [updates],
  );

  const getLatestByType = useCallback(
    (type: LiveUpdate["type"]) => {
      return updates.find((update) => update.type === type);
    },
    [updates],
  );

  useEffect(() => {
    if (queueRef.current.length > 0 && document.visibilityState === "visible") {
      const batch = queueRef.current.splice(0, 10);
      batch.forEach(() => {});
    }
  }, [updates]);

  useEffect(() => {
    const interval = setInterval(() => {
      setUpdates((prev) => {
        if (prev.length > 1000) {
          return prev.slice(0, 1000);
        }
        return prev;
      });
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        setIsSubscribed(true);
      } else {
        setIsSubscribed(false);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, []);

  return {
    updates,
    unreadCount,
    addUpdate,
    markAsRead,
    markAsReadByType,
    clearRead,
    clearAll,
    clearByType,
    unreadByType,
    getLatestByType,
    isSubscribed,
  };
}
