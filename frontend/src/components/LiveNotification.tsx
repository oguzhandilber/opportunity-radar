import { useState, useEffect, useRef } from "react";
import { X, TrendingUp, Target, BarChart3 } from "lucide-react";

interface LiveNotificationProps {
  notification: {
    type: "viral" | "score_change" | "match" | "forecast";
    title: string;
    message: string;
    timestamp: string;
  };
  onDismiss: () => void;
}

const icons = {
  viral: TrendingUp,
  score_change: Target,
  match: Target,
  forecast: BarChart3,
};

const colors = {
  viral: "text-green-600 bg-green-50 border-green-200",
  score_change: "text-blue-600 bg-blue-50 border-blue-200",
  match: "text-purple-600 bg-purple-50 border-purple-200",
  forecast: "text-orange-600 bg-orange-50 border-orange-200",
};

export function LiveNotification({
  notification,
  onDismiss,
}: LiveNotificationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartX, setDragStartX] = useState(0);
  const [currentX, setCurrentX] = useState(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const autoDismissDelay = 5000;

  useEffect(() => {
    setIsVisible(true);
    timeoutRef.current = setTimeout(() => {
      handleDismiss();
    }, autoDismissDelay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => {
      onDismiss();
    }, 300);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStartX(e.clientX - currentX);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const newX = e.clientX - dragStartX;
    setCurrentX(newX);

    if (Math.abs(newX) > 100) {
      handleDismiss();
    }
  };

  const handleMouseUp = () => {
    if (!isDragging) return;
    setIsDragging(false);
    setCurrentX(0);
  };

  const handleMouseLeave = () => {
    if (isDragging) {
      setIsDragging(false);
      setCurrentX(0);
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    setDragStartX(e.touches[0].clientX - currentX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;
    const newX = e.touches[0].clientX - dragStartX;
    setCurrentX(newX);

    if (Math.abs(newX) > 100) {
      handleDismiss();
    }
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
    setCurrentX(0);
  };

  const Icon = icons[notification.type];
  const colorClass = colors[notification.type];

  return (
    <div
      className={`
        relative pointer-events-auto
        transition-all duration-300 ease-out
        transform ${isVisible ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"}
        ${isDragging ? "transition-none" : ""}
      `}
      style={{
        transform: `translateX(${currentX}px)`,
        opacity: isVisible ? Math.max(0, 1 - Math.abs(currentX) / 200) : 0,
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div
        className={`
          max-w-sm w-full rounded-lg border shadow-lg p-4
          ${colorClass}
          cursor-pointer select-none
        `}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <Icon className="h-5 w-5" />
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">
              {notification.title}
            </p>
            <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
            <p className="text-xs text-gray-500 mt-2">
              {new Date(notification.timestamp).toLocaleTimeString()}
            </p>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDismiss();
            }}
            className="flex-shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </div>

        {isDragging && (
          <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-black/10 to-transparent pointer-events-none" />
        )}
      </div>
    </div>
  );
}
