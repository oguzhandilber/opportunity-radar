import { useState } from "react";
import { Loader2, Save } from "lucide-react";
import { useSettings, useUpdateSetting } from "../hooks/useApi";

/**
 * Mission Control Brutalism Settings
 *
 * Dark theme configuration panel
 * Terminal-style inputs
 */
export default function Settings() {
  const { data: settings, isLoading } = useSettings();
  const updateSetting = useUpdateSetting();
  const [localSettings, setLocalSettings] = useState<Record<string, string>>(
    {},
  );

  const handleSave = (key: string) => {
    const value = localSettings[key];
    if (value !== undefined) {
      try {
        updateSetting.mutate({ key, value: JSON.parse(value) });
      } catch {
        updateSetting.mutate({ key, value });
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-radar-500" />
          <span className="font-mono text-sm text-text-secondary">
            LOADING CONFIG...
          </span>
        </div>
      </div>
    );
  }

  const settingsConfig = [
    {
      key: "scrape_interval_hours",
      label: "SCRAPE INTERVAL (HOURS)",
      description: "How often to run the automated scraper",
      type: "number",
    },
    {
      key: "max_posts_per_source",
      label: "MAX POSTS PER SOURCE",
      description: "Maximum number of posts to scrape from each source",
      type: "number",
    },
    {
      key: "min_opportunity_score",
      label: "MIN OPPORTUNITY SCORE",
      description: "Minimum score threshold for opportunities to be saved",
      type: "number",
    },
    {
      key: "enabled_sources",
      label: "ENABLED SOURCES",
      description:
        "Comma-separated list of enabled scrapers (reddit, hackernews, google_trends, product_hunt)",
      type: "text",
    },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
          CONFIGURATION
        </h1>
        <p className="text-text-secondary font-mono text-sm">
          System Parameters
        </p>
      </div>

      {/* Settings Panel */}
      <div className="bg-dark border border-light p-6 max-w-2xl">
        <div className="space-y-6">
          {settingsConfig.map((config) => {
            const currentValue = settings?.[config.key];
            const localValue = localSettings[config.key];
            const displayValue =
              localValue ??
              (currentValue !== undefined ? JSON.stringify(currentValue) : "");

            return (
              <div key={config.key}>
                <label className="label-mono mb-1 block">{config.label}</label>
                <p className="font-mono text-xs text-text-tertiary mb-2">
                  {config.description}
                </p>
                <div className="flex gap-2">
                  <input
                    type={config.type}
                    value={displayValue}
                    onChange={(e) =>
                      setLocalSettings({
                        ...localSettings,
                        [config.key]: e.target.value,
                      })
                    }
                    className="flex-1 min-h-[44px]"
                  />
                  <button
                    onClick={() => handleSave(config.key)}
                    disabled={
                      localValue === undefined || updateSetting.isPending
                    }
                    className="btn btn-primary flex items-center gap-2 min-h-[44px] disabled:opacity-50"
                  >
                    {updateSetting.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    SAVE
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* API Keys Info */}
      <div className="bg-dark border border-light p-6 max-w-2xl mt-6">
        <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
          API KEYS
        </h2>
        <p className="font-mono text-sm text-text-secondary mb-4">
          API keys are configured via environment variables for security. Update
          your .env file to change these settings.
        </p>
        <div className="bg-darkest border border-light p-4 font-mono text-sm">
          <div className="text-text-tertiary"># .env file</div>
          <div className="text-radar-500">
            CLAUDE_API_KEY=
            <span className="text-text-secondary">your_claude_api_key</span>
          </div>
          <div className="text-radar-500">
            GEMINI_API_KEY=
            <span className="text-text-secondary">your_gemini_api_key</span>
          </div>
          <div className="text-radar-500">
            REDDIT_CLIENT_ID=
            <span className="text-text-secondary">your_reddit_client_id</span>
          </div>
          <div className="text-radar-500">
            REDDIT_CLIENT_SECRET=
            <span className="text-text-secondary">
              your_reddit_client_secret
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
