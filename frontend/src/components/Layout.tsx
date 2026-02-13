import { useState } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Crosshair,
  Settings,
  Menu,
  X,
  Trophy,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { path: "/", label: "DASHBOARD", icon: LayoutDashboard },
  { path: "/opportunities", label: "OPPORTUNITIES", icon: Crosshair },
  { path: "/app-store", label: "APP STORE", icon: Trophy },
  { path: "/settings", label: "SETTINGS", icon: Settings },
];

/**
 * Mission Control Brutalism Layout
 *
 * Dark sidebar with radar animation
 * System status section
 * Navigation with square indicators
 */
export default function Layout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-darkest">
      {/* Mobile header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-dark border-b border-light z-30 flex items-center px-4">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 -ml-2 hover:bg-light min-w-[44px] min-h-[44px] flex items-center justify-center text-text-primary"
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-3 ml-2">
          <RadarLogo size="sm" />
          <span className="font-mono font-bold text-text-primary tracking-wider">
            OPPORTUNITY RADAR
          </span>
        </div>
      </header>

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/70 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 w-64 bg-dark border-r border-light z-50 transition-transform duration-300",
          "lg:translate-x-0 flex flex-col",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Header with Radar Logo */}
        <div className="flex items-center justify-between h-20 px-4 border-b border-light">
          <div className="flex items-center gap-3">
            <RadarLogo size="md" />
            <div className="flex flex-col">
              <span className="font-mono font-bold text-text-primary text-sm tracking-wider">
                OPPORTUNITY
              </span>
              <span className="font-mono font-bold text-radar-500 text-sm tracking-wider">
                RADAR
              </span>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 hover:bg-light min-w-[44px] min-h-[44px] flex items-center justify-center text-text-secondary"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-4 py-3 transition-all min-h-[44px] font-mono text-sm tracking-wider",
                  isActive
                    ? "bg-medium text-radar-500 border-l-2 border-l-radar-500"
                    : "text-text-secondary hover:text-text-primary hover:bg-medium/50",
                )}
              >
                {/* Square indicator */}
                <span
                  className={clsx(
                    "w-2 h-2 transition-colors",
                    isActive ? "bg-radar-500" : "bg-light",
                  )}
                />
                <Icon className="w-4 h-4" />
                <span className="font-bold">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* System Status Section */}
        <div className="p-4 border-t border-light">
          <div className="text-xs font-mono uppercase tracking-wider text-text-tertiary mb-3">
            System Status
          </div>
          <div className="space-y-2 text-sm font-mono">
            <div className="flex items-center gap-2 text-text-secondary">
              <span className="w-1.5 h-1.5 bg-signal-success rounded-full animate-pulse" />
              <span>ONLINE</span>
            </div>
            <SystemStatusItem label="LAST SCAN" value="Ready" />
            <SystemStatusItem label="TRACKING" value="-- targets" />
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 min-h-screen pt-16 lg:pt-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

/**
 * Radar Logo with Pulse Animation
 */
function RadarLogo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-14 h-14",
  };

  const innerSizeClasses = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-7 h-7",
  };

  return (
    <div className={clsx("radar-container", sizeClasses[size])}>
      {/* Pulse rings */}
      <div className="radar-pulse-ring" />
      <div className="radar-pulse-ring" />
      <div className="radar-pulse-ring" />

      {/* Center icon */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className={clsx(
            "flex items-center justify-center rounded-full bg-radar-500/20 border border-radar-500",
            sizeClasses[size],
          )}
        >
          <Crosshair
            className={clsx("text-radar-500", innerSizeClasses[size])}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * System Status Item
 */
function SystemStatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-text-tertiary">▸ {label}:</span>
      <span className="text-text-secondary">{value}</span>
    </div>
  );
}
