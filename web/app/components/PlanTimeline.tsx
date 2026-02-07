"use client";

import type { TelemetryData } from "../types";

export function PlanTimeline({ telemetry }: { telemetry: TelemetryData | null }) {
  if (!telemetry?.plan?.length) {
    return (
      <div className="panel p-5">
        <div className="panel-header">Execution Plan</div>
        <p className="text-text-muted text-sm">No active plan</p>
      </div>
    );
  }

  const currentIdx = telemetry.plan.indexOf(telemetry.current_action);

  return (
    <div className="panel p-5">
      <div className="panel-header">Execution Plan</div>

      <div className="space-y-1">
        {telemetry.plan.map((step, idx) => {
          const isCurrent = step === telemetry.current_action;
          const isDone = currentIdx >= 0 && idx < currentIdx;
          const isFuture = currentIdx >= 0 && idx > currentIdx;

          let stepClass = "plan-step";
          if (isCurrent) stepClass += " plan-step-active";
          else if (isDone) stepClass += " plan-step-done";

          let markerClass = "step-marker ";
          let markerContent: string | number = idx + 1;
          if (isDone) {
            markerClass += "bg-success/30 text-success";
            markerContent = "\u2713";
          } else if (isCurrent) {
            markerClass += "bg-accent text-white";
          } else {
            markerClass += "bg-white/5 text-text-muted";
          }

          return (
            <div key={idx} className={stepClass}>
              <div className={markerClass}>{markerContent}</div>
              <span
                className={`font-mono text-sm ${
                  isCurrent
                    ? "text-text-primary"
                    : isFuture
                      ? "text-text-muted"
                      : "text-text-secondary"
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
