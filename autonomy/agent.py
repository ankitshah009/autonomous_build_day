from __future__ import annotations

import time
from statistics import mean
from typing import List, Optional

from autonomy.executor import StepExecutor
from autonomy.perception import PerceptionModule
from autonomy.planner import Planner
from autonomy.sim_robot import SimRobot
from autonomy.telemetry import metrics_dict, world_snapshot
from autonomy.types import EpisodeMetrics, EpisodeResult, Goal, TelemetryFrame, WorldState


class Track1Agent:
    def __init__(
        self,
        robot: SimRobot,
        planner: Planner,
        perception: PerceptionModule,
        executor: StepExecutor,
        sink,
        max_retries_per_step: int = 2,
        max_replans: int = 3,
    ) -> None:
        self.robot = robot
        self.planner = planner
        self.perception = perception
        self.executor = executor
        self.sink = sink
        self.max_retries_per_step = max_retries_per_step
        self.max_replans = max_replans
        self._recent_results: List[int] = []

    def run_episode(self, goal: Goal, max_ticks: int = 80) -> EpisodeResult:
        state = WorldState()
        metrics = EpisodeMetrics()
        timeline: List[TelemetryFrame] = []
        start = time.monotonic()

        self.perception.reset()
        state = self.perception.update(state, self.robot.observe())
        plan = self.planner.build_plan(goal, state)
        cursor = 0
        retries_on_step = 0
        replans = 0

        for tick in range(max_ticks):
            state.tick = tick

            if self.robot.verify_goal(goal):
                metrics.success = True
                state.phase = "GOAL_REACHED"
                self._emit(timeline, state, metrics, plan, "VERIFY_GOAL")
                break

            if cursor >= len(plan):
                plan = self.planner.build_plan(goal, state)
                cursor = 0
                replans += 1
                metrics.replans = replans
                state.phase = "REPLAN_EMPTY_PLAN"
                self._emit(timeline, state, metrics, plan, "REPLAN")
                if replans > self.max_replans:
                    metrics.fail_reason = "replan_budget_exceeded"
                    break
                continue

            step = plan[cursor]
            state.phase = f"EXECUTE_{step.action}"
            ok, err = self.executor.run_step(step, self.robot, goal, state)
            metrics.steps_executed += 1

            state = self.perception.update(state, self.robot.observe())
            state.held_object_id = self.robot.held_object_id

            self._update_robot_state(state, step)

            if ok:
                state.last_error = None
                retries_on_step = 0
                cursor += 1
            else:
                state.last_error = err
                retries_on_step += 1
                metrics.retries += 1

                if retries_on_step > self.max_retries_per_step:
                    replans += 1
                    metrics.replans = replans
                    retries_on_step = 0
                    cursor = 0
                    plan = self.planner.build_plan(goal, state)
                    state.phase = "REPLAN_AFTER_FAILURE"
                    if replans > self.max_replans:
                        metrics.fail_reason = err or "replan_budget_exceeded"
                        self._emit(timeline, state, metrics, plan, "REPLAN_FAIL")
                        break

            self._emit(timeline, state, metrics, plan, step.label())
        else:
            metrics.fail_reason = "max_ticks_exceeded"

        metrics.duration_s = time.monotonic() - start
        if not metrics.success and metrics.fail_reason is None:
            metrics.fail_reason = "goal_not_reached"

        self._recent_results.append(1 if metrics.success else 0)
        self._recent_results = self._recent_results[-10:]

        # Final frame for stable dashboards.
        state.phase = "DONE_SUCCESS" if metrics.success else "DONE_FAILURE"
        self._emit(timeline, state, metrics, plan, "DONE")

        return EpisodeResult(goal=goal, metrics=metrics, timeline=timeline)

    def _recent_success_rate(self) -> Optional[float]:
        if not self._recent_results:
            return None
        return mean(self._recent_results)

    def _update_robot_state(self, state: WorldState, step: PlanStep) -> None:
        """Update robot state based on the executed step."""
        action = step.action
        if action == "SEARCH":
            # Simulate scanning movement
            state.joint_positions = [self.robot._rng.uniform(-1.57, 1.57) for _ in range(6)]
            state.joint_velocities = [self.robot._rng.uniform(-0.5, 0.5) for _ in range(6)]
        elif action == "NAVIGATE":
            # Simulate navigation to target
            state.joint_positions = [self.robot._rng.uniform(-3.14, 3.14) for _ in range(6)]
            state.joint_velocities = [self.robot._rng.uniform(0.1, 1.0) for _ in range(6)]
        elif action == "GRASP":
            state.gripper_state = "closed"
            state.joint_positions[5] = 0.0  # Assume joint 6 is gripper
            state.joint_velocities[5] = 0.0
        elif action == "PLACE_IN_BIN":
            state.gripper_state = "open"
            state.joint_positions[5] = 1.57  # Open gripper
            state.joint_velocities[5] = 0.0
        # Simulate battery drain and temperature
        state.battery_level = max(0.0, state.battery_level - self.robot._rng.uniform(0.1, 1.0))
        state.temperature = state.temperature + self.robot._rng.uniform(-0.5, 0.5)
        state.temperature = max(20.0, min(50.0, state.temperature))

    def _emit(
        self,
        timeline: List[TelemetryFrame],
        state: WorldState,
        metrics: EpisodeMetrics,
        plan,
        current_action: str,
    ) -> None:
        frame = TelemetryFrame(
            ts_ms=int(time.time() * 1000),
            phase=state.phase,
            plan=self.planner.summarize(plan),
            current_action=current_action,
            retries=metrics.retries,
            replans=metrics.replans,
            last_error=state.last_error,
            world=world_snapshot(state),
            metrics=metrics_dict(metrics, self._recent_success_rate()),
        )
        timeline.append(frame)
        self.sink.emit(frame)
