import { useState, useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

export interface WebSocketMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export function useWebSocket(url: string) {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionState, setConnectionState] = useState<
    "connecting" | "connected" | "disconnected"
  >("disconnected");
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    setConnectionState("connecting");

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setConnectionState("connected");
        setReconnectAttempts(0);
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          if (message.type === "opportunity_update") {
            queryClient.invalidateQueries({ queryKey: ["opportunities"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard"] });
          } else if (message.type === "scrape_complete") {
            queryClient.invalidateQueries({ queryKey: ["opportunities"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
            queryClient.invalidateQueries({ queryKey: ["scrape", "status"] });
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.current.onclose = () => {
        setConnectionState("disconnected");

        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttempts);
          setReconnectAttempts((prev) => prev + 1);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionState("disconnected");
      };
    } catch (error) {
      console.error("Failed to create WebSocket connection:", error);
      setConnectionState("disconnected");
    }
  }, [url, reconnectAttempts, queryClient]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setConnectionState("disconnected");
    setReconnectAttempts(0);
  }, []);

  const sendMessage = useCallback(
    (message: Omit<WebSocketMessage, "timestamp">) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        const fullMessage: WebSocketMessage = {
          ...message,
          timestamp: new Date().toISOString(),
        };
        ws.current.send(JSON.stringify(fullMessage));
        return true;
      }
      return false;
    },
    [],
  );

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (
        document.visibilityState === "visible" &&
        connectionState === "disconnected"
      ) {
        connect();
      } else if (document.visibilityState === "hidden") {
        disconnect();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [connectionState, connect, disconnect]);

  return {
    lastMessage,
    connectionState,
    sendMessage,
    reconnectAttempts,
    connect,
    disconnect,
  };
}

export interface AppUpdate {
  id: number;
  title: string;
  score: number;
  previous_score: number;
  change_type: "new" | "score_change" | "status_change";
  timestamp: string;
}

export interface Alert {
  id: string;
  type: "viral" | "score_threshold" | "new_opportunity";
  title: string;
  message: string;
  opportunity_id?: number;
  severity: "low" | "medium" | "high";
  timestamp: string;
  read: boolean;
}

export interface Forecast {
  sector: string;
  trend: "rising" | "falling" | "stable";
  confidence: number;
  timeframe: string;
  opportunities_count: number;
}

export function useDashboardWebSocket(clientId: string) {
  const wsUrl = `${process.env.VITE_WS_URL || "ws://localhost:8000"}/ws/${clientId}`;
  const { lastMessage, connectionState, sendMessage } = useWebSocket(wsUrl);

  const [appUpdates, setAppUpdates] = useState<AppUpdate[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);

  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case "app_update":
          setAppUpdates((prev) => [
            {
              ...lastMessage.payload,
              id: String(Date.now()),
            } as unknown as AppUpdate,
            ...prev.slice(0, 49),
          ]);
          break;
        case "alert":
          setAlerts((prev) => [
            {
              ...lastMessage.payload,
              id: String(Date.now()),
            } as unknown as Alert,
            ...prev.slice(0, 99),
          ]);
          break;
        case "forecast_update":
          setForecasts((prev) => {
            const newForecast = {
              ...lastMessage.payload,
              id: String(Date.now()),
            } as unknown as Forecast;
            const filtered = prev.filter(
              (f) => f.sector !== newForecast.sector,
            );
            return [newForecast, ...filtered].slice(0, 20);
          });
          break;
      }
    }
  }, [lastMessage]);

  const markAlertAsRead = useCallback(
    (alertId: string) => {
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, read: true } : alert,
        ),
      );

      sendMessage({
        type: "mark_alert_read",
        payload: { alert_id: alertId },
      });
    },
    [sendMessage],
  );

  const subscribeToOpportunities = useCallback(() => {
    sendMessage({
      type: "subscribe",
      payload: { channel: "opportunities" },
    });
  }, [sendMessage]);

  const subscribeToAlerts = useCallback(() => {
    sendMessage({
      type: "subscribe",
      payload: { channel: "alerts" },
    });
  }, [sendMessage]);

  const subscribeToForecasts = useCallback(() => {
    sendMessage({
      type: "subscribe",
      payload: { channel: "forecasts" },
    });
  }, [sendMessage]);

  useEffect(() => {
    if (connectionState === "connected") {
      subscribeToOpportunities();
      subscribeToAlerts();
      subscribeToForecasts();
    }
  }, [
    connectionState,
    subscribeToOpportunities,
    subscribeToAlerts,
    subscribeToForecasts,
  ]);

  return {
    appUpdates,
    alerts,
    forecasts,
    connectionState,
    markAlertAsRead,
    unreadAlertsCount: alerts.filter((alert) => !alert.read).length,
  };
}
