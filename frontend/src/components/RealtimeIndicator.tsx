import { useState, useEffect } from "react";
import { Wifi, WifiOff, Activity, Clock } from "lucide-react";
import { useDashboardWebSocket } from "../hooks/useWebSocket";

interface RealtimeIndicatorProps {
  clientId: string;
}

export function RealtimeIndicator({ clientId }: RealtimeIndicatorProps) {
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  const { connectionState } = useDashboardWebSocket(clientId);

  useEffect(() => {
    setLastUpdateTime(new Date());
  }, [connectionState]);

  const getStatusIcon = () => {
    switch (connectionState) {
      case "connected":
        return <Activity className="h-4 w-4 text-green-500" />;
      case "connecting":
        return <Wifi className="h-4 w-4 text-yellow-500" />;
      case "disconnected":
        return <WifiOff className="h-4 w-4 text-red-500" />;
      default:
        return <WifiOff className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (connectionState) {
      case "connected":
        return "Live";
      case "connecting":
        return "Connecting";
      case "disconnected":
        return "Offline";
      default:
        return "Unknown";
    }
  };

  const getStatusColor = () => {
    switch (connectionState) {
      case "connected":
        return "text-green-600 bg-green-50 border-green-200";
      case "connecting":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "disconnected":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const formatLastUpdate = () => {
    if (!lastUpdateTime) return "Never";

    const now = new Date();
    const diff = now.getTime() - lastUpdateTime.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) {
      return "Just now";
    } else if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      return lastUpdateTime.toLocaleDateString();
    }
  };

  return (
    <div className="flex items-center gap-2">
      <div
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-full border
          text-xs font-medium
          ${getStatusColor()}
          ${connectionState === "connected" ? "animate-pulse" : ""}
        `}
      >
        {getStatusIcon()}
        <span>{getStatusText()}</span>
      </div>

      {lastUpdateTime && (
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="h-3 w-3" />
          <span>{formatLastUpdate()}</span>
        </div>
      )}

      {connectionState === "connected" && (
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse delay-75" />
          <div className="w-2 h-2 bg-green-300 rounded-full animate-pulse delay-150" />
        </div>
      )}
    </div>
  );
}
