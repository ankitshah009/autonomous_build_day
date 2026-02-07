/** Matches Python TelemetryFrame.to_dict() output exactly. */
export interface TelemetryData {
  ts_ms: number;
  phase: string;
  plan: string[];
  current_action: string;
  retries: number;
  replans: number;
  last_error: string | null;
  world: WorldSnapshot;
  metrics: MetricsSnapshot;
}

export interface WorldSnapshot {
  tick: number;
  held_object_id: string | null;
  last_error: string | null;
  objects: DetectedObject[];
  robot_state: RobotState;
}

export interface DetectedObject {
  id: string;
  cls: string;
  confidence: number;
  visible: boolean;
  in_bin: boolean;
  position: [number, number, number];
}

export interface RobotState {
  joint_positions: number[];
  joint_velocities: number[];
  gripper_state: string;
  battery_level: number;
  temperature: number;
}

export interface MetricsSnapshot {
  success: boolean;
  retries: number;
  replans: number;
  steps_executed: number;
  duration_s: number;
  fail_reason: string | null;
  success_rate_last10: number | null;
}
