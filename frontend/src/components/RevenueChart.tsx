import { useMemo } from "react";

interface RevenueChartProps {
  data: {
    date: string;
    estimate: number;
  }[];
  showConfidenceInterval?: boolean;
}

function formatRevenue(amount: number): string {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`;
  }
  return `$${amount.toFixed(0)}`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function RevenueChart({
  data,
  showConfidenceInterval = false,
}: RevenueChartProps) {
  const { maxValue, scaledData, pathData, fillPath } = useMemo(() => {
    if (data.length === 0) {
      return { maxValue: 0, scaledData: [], pathData: "", fillPath: "" };
    }

    const maxValue = Math.max(...data.map((d) => d.estimate));
    const padding = maxValue * 0.1;
    const adjustedMax = maxValue + padding;

    const scaledData = data.map((point, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - (point.estimate / adjustedMax) * 100;
      return { ...point, x, y };
    });

    const pathData = scaledData
      .map((point, i) => `${i === 0 ? "M" : "L"} ${point.x},${point.y}`)
      .join(" ");

    const fillPath = `${pathData} L ${scaledData[scaledData.length - 1].x},100 L 0,100 Z`;

    return { maxValue, scaledData, pathData, fillPath };
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="bg-dark border border-light p-6">
        <div className="flex items-center justify-center h-48 text-text-tertiary font-mono text-sm">
          NO DATA AVAILABLE
        </div>
      </div>
    );
  }

  return (
    <div className="bg-dark border border-light p-6">
      <div className="mb-4">
        <span className="label-mono">REVENUE TREND</span>
      </div>

      <div className="relative h-48 w-full">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <g className="opacity-20">
            {[0, 25, 50, 75, 100].map((y, i) => (
              <line
                key={`h-${i}`}
                x1="0"
                y1={y}
                x2="100"
                y2={y}
                className="stroke-light"
                strokeWidth="0.2"
              />
            ))}
            {[0, 25, 50, 75, 100].map((x, i) => (
              <line
                key={`v-${i}`}
                x1={x}
                y1="0"
                x2={x}
                y2="100"
                className="stroke-light"
                strokeWidth="0.2"
              />
            ))}
          </g>

          {showConfidenceInterval && (
            <g className="opacity-20">
              <path d={fillPath} className="fill-radar-500" />
            </g>
          )}

          <path
            d={pathData}
            fill="none"
            className="stroke-radar-500"
            strokeWidth="0.8"
          />

          {scaledData.map((point, i) => (
            <circle
              key={i}
              cx={point.x}
              cy={point.y}
              r="1"
              className="fill-radar-500"
            />
          ))}
        </svg>
      </div>

      <div className="flex justify-between mt-3 px-1">
        {scaledData.map((point, i) => (
          <span
            key={i}
            className="font-mono text-xs text-text-tertiary"
            style={{
              display: i % Math.ceil(data.length / 6) === 0 ? "block" : "none",
            }}
          >
            {formatDate(point.date)}
          </span>
        ))}
      </div>

      <div className="flex flex-col items-end gap-2 absolute right-2 top-20 bottom-8">
        {[0, 0.25, 0.5, 0.75, 1].map((fraction, i) => (
          <span key={i} className="font-mono text-xs text-text-tertiary">
            {formatRevenue(maxValue * fraction)}
          </span>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-light flex justify-between">
        <div className="text-center">
          <span className="block font-mono text-xs text-text-tertiary mb-1">
            PEAK
          </span>
          <span className="block font-display font-bold text-sm text-text-primary">
            {formatRevenue(maxValue)}
          </span>
        </div>
        <div className="text-center">
          <span className="block font-mono text-xs text-text-tertiary mb-1">
            AVERAGE
          </span>
          <span className="block font-display font-bold text-sm text-text-primary">
            {formatRevenue(
              data.reduce((sum, d) => sum + d.estimate, 0) / data.length,
            )}
          </span>
        </div>
        <div className="text-center">
          <span className="block font-mono text-xs text-text-tertiary mb-1">
            PERIOD
          </span>
          <span className="block font-display font-bold text-sm text-text-primary">
            {data.length} {data.length === 1 ? "DAY" : "DAYS"}
          </span>
        </div>
      </div>
    </div>
  );
}
