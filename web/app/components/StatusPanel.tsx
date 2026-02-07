"use client";

import type { TelemetryData } from "../types";

function phaseColor(phase: string): string {
  if (phase.startsWith("DONE_SUCCESS") || phase === "GOAL_REACHED")
    return "bg-success/20 text-success";
  if (phase.startsWith("DONE_FAILURE") || phase.includes("FAIL"))
    return "bg-error/20 text-error";
  if (phase.includes("REPLAN"))
    return "bg-warning/20 text-warning";
  return "bg-accent/20 text-accent";
}

export function StatusPanel({ telemetry }: { telemetry: TelemetryData | null }) {
  if (!telemetry) {
    return (
      <div className="panel p-5">
        <div className="panel-header">Current State</div>
        <p className="text-text-muted text-sm">Waiting for telemetry...</p>
      </div>
    );
  }

  const hasError = !!telemetry.last_error;

  return (
    <div className="panel p-5">
      <div className="panel-header">Current State</div>

      <div className="space-y-4">
        {/* Phase */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
            Phase
          </div>
          <span className={`phase-badge ${phaseColor(telemetry.phase)}`}>
            {telemetry.phase}
          </span>
        </div>

        {/* Action */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
            Action
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`status-dot ${hasError ? "status-dot-error" : "status-dot-ok"}`}
            />
            <span className="font-mono text-sm">{telemetry.current_action}</span>
          </div>
        </div>

        {/* Retries / Replans */}
        <div className="flex gap-6">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
              Retries
            </div>
            <span className="font-mono text-lg">{telemetry.retries}</span>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
              Replans
            </div>
            <span className="font-mono text-lg">{telemetry.replans}</span>
          </div>
        </div>

        {/* Error */}
        {hasError && (
          <div className="rounded-lg bg-error/10 border border-error/30 p-3">
            <div className="text-[10px] uppercase tracking-wider text-error mb-1">
              Error
            </div>
            <div className="font-mono text-xs text-error/80">
              {telemetry.last_error}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
