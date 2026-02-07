"use client";

import type { TelemetryData } from "../types";

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent: string;
}) {
  return (
    <div className={`metric-card border-${accent}/20`}>
      <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
        {label}
      </div>
      <div className={`font-mono text-2xl text-${accent}`}>{value}</div>
    </div>
  );
}

export function Scoreboard({ telemetry }: { telemetry: TelemetryData | null }) {
  if (!telemetry?.metrics) {
    return (
      <div className="panel p-5">
        <div className="panel-header">Performance</div>
        <p className="text-text-muted text-sm">No metrics yet</p>
      </div>
    );
  }

  const { metrics } = telemetry;
  const rate = metrics.success_rate_last10;
  const rateDisplay = rate != null ? `${(rate * 100).toFixed(0)}%` : "--";
  const rateColor =
    rate == null
      ? "text-muted"
      : rate >= 0.8
        ? "success"
        : rate >= 0.5
          ? "warning"
          : "error";

  return (
    <div className="panel p-5">
      <div className="panel-header">Performance</div>

      {/* Large success rate */}
      <div className="text-center mb-5">
        <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
          Success Rate (Last 10)
        </div>
        <div className={`font-mono text-5xl font-bold text-${rateColor}`}>
          {rateDisplay}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Retries" value={metrics.retries} accent="accent" />
        <MetricCard label="Replans" value={metrics.replans} accent="warning" />
        <MetricCard label="Steps" value={metrics.steps_executed} accent="text-secondary" />
        <MetricCard
          label="Duration"
          value={`${metrics.duration_s.toFixed(1)}s`}
          accent="text-secondary"
        />
      </div>

      {metrics.fail_reason && (
        <div className="mt-3 rounded-lg bg-error/10 border border-error/20 px-3 py-2">
          <span className="text-xs text-error font-mono">{metrics.fail_reason}</span>
        </div>
      )}
    </div>
  );
}
