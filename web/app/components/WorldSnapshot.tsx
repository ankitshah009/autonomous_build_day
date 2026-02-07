"use client";

import type { TelemetryData, DetectedObject } from "../types";

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70
      ? "bg-success"
      : pct >= 40
        ? "bg-warning"
        : "bg-error";

  return (
    <div className="flex items-center gap-2">
      <div className="gauge-bar w-16">
        <div className={`gauge-fill ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-[10px] text-text-muted w-8">{pct}%</span>
    </div>
  );
}

function ObjectRow({
  obj,
  isHeld,
}: {
  obj: DetectedObject;
  isHeld: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between py-2 px-3 rounded-lg ${
        isHeld
          ? "bg-accent/10 border border-accent/30"
          : "hover:bg-white/[0.02]"
      } ${!obj.visible ? "opacity-40" : ""}`}
    >
      <div className="flex items-center gap-3">
        <span
          className={`status-dot ${
            obj.in_bin
              ? "status-dot-ok"
              : obj.visible
                ? "status-dot-warn"
                : "status-dot-error"
          }`}
        />
        <div>
          <div className="font-mono text-sm">{obj.id}</div>
          <div className="text-[10px] text-text-muted">
            {obj.cls}
            {isHeld ? " \u00b7 HELD" : ""}
            {obj.in_bin ? " \u00b7 IN BIN" : ""}
          </div>
        </div>
      </div>
      <ConfidenceBar value={obj.confidence} />
    </div>
  );
}

export function WorldSnapshot({
  telemetry,
}: {
  telemetry: TelemetryData | null;
}) {
  const world = telemetry?.world;
  if (!world?.objects?.length) {
    return (
      <div className="panel p-5">
        <div className="panel-header">World Snapshot</div>
        <p className="text-text-muted text-sm">No objects detected</p>
      </div>
    );
  }

  return (
    <div className="panel p-5">
      <div className="panel-header">
        World Snapshot
        <span className="ml-2 text-text-muted font-normal normal-case">
          tick {world.tick}
        </span>
      </div>

      <div className="space-y-1 max-h-52 overflow-y-auto">
        {world.objects.map((obj) => (
          <ObjectRow
            key={obj.id}
            obj={obj}
            isHeld={obj.id === world.held_object_id}
          />
        ))}
      </div>
    </div>
  );
}
