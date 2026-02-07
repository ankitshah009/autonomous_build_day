"use client";

import type { TelemetryData } from "../types";

function GaugeBar({
  label,
  value,
  max,
  color,
  suffix,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
  suffix?: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-[10px] uppercase tracking-wider text-text-muted">
          {label}
        </span>
        <span className="font-mono text-xs text-text-secondary">
          {value.toFixed(1)}
          {suffix}
        </span>
      </div>
      <div className="gauge-bar">
        <div
          className="gauge-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

export function RobotStateGauges({
  telemetry,
}: {
  telemetry: TelemetryData | null;
}) {
  const rs = telemetry?.world?.robot_state;
  if (!rs) {
    return (
      <div className="panel p-5">
        <div className="panel-header">Robot State</div>
        <p className="text-text-muted text-sm">No robot state</p>
      </div>
    );
  }

  const batteryColor =
    rs.battery_level > 50
      ? "var(--success)"
      : rs.battery_level > 20
        ? "var(--warning)"
        : "var(--error)";

  const tempColor =
    rs.temperature < 35
      ? "var(--success)"
      : rs.temperature < 45
        ? "var(--warning)"
        : "var(--error)";

  return (
    <div className="panel p-5">
      <div className="panel-header">Robot State</div>

      <div className="space-y-4">
        <GaugeBar
          label="Battery"
          value={rs.battery_level}
          max={100}
          color={batteryColor}
          suffix="%"
        />
        <GaugeBar
          label="Temperature"
          value={rs.temperature}
          max={60}
          color={tempColor}
          suffix="C"
        />

        {/* Gripper */}
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-wider text-text-muted">
            Gripper
          </span>
          <span
            className={`font-mono text-xs px-2 py-0.5 rounded ${
              rs.gripper_state === "closed"
                ? "bg-accent/20 text-accent"
                : "bg-white/5 text-text-muted"
            }`}
          >
            {rs.gripper_state.toUpperCase()}
          </span>
        </div>

        {/* Joint positions - compact bar chart */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-text-muted mb-2">
            Joints ({rs.joint_positions.length})
          </div>
          <div className="flex gap-1 items-end h-8">
            {rs.joint_positions.map((pos, i) => {
              const normalized =
                Math.min(1, Math.max(0, (pos + Math.PI) / (2 * Math.PI)));
              return (
                <div
                  key={i}
                  className="flex-1 rounded-sm bg-accent/40"
                  style={{ height: `${normalized * 100}%`, minHeight: "2px" }}
                  title={`J${i + 1}: ${pos.toFixed(2)} rad`}
                />
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
