"use client";

import { VideoFeed } from "./components/VideoFeed";
import { StatusPanel } from "./components/StatusPanel";
import { PlanTimeline } from "./components/PlanTimeline";
import { Scoreboard } from "./components/Scoreboard";
import { RobotStateGauges } from "./components/RobotStateGauges";
import { WorldSnapshot } from "./components/WorldSnapshot";
import { useTelemetry } from "./hooks/useTelemetry";

/**
 * Inner dashboard content rendered inside <LiveKitRoom>.
 * Separated so useTelemetry() and useTracks() have room context.
 */
export function DashboardContent() {
  const telemetry = useTelemetry();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      {/* Left column — 2/3 width */}
      <div className="lg:col-span-2 space-y-5">
        <VideoFeed />
        <PlanTimeline telemetry={telemetry} />
      </div>

      {/* Right column — 1/3 width */}
      <div className="space-y-5">
        <StatusPanel telemetry={telemetry} />
        <Scoreboard telemetry={telemetry} />
        <RobotStateGauges telemetry={telemetry} />
        <WorldSnapshot telemetry={telemetry} />
      </div>
    </div>
  );
}
