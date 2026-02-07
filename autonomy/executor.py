from __future__ import annotations

from typing import Optional, Tuple

from autonomy.planner import Planner
from autonomy.sim_robot import SimRobot
from autonomy.types import Goal, ObjClass, PlanStep, WorldState


class StepExecutor:
    """Dispatch layer from symbolic step to robot actions."""

    def __init__(self, planner: Planner) -> None:
        self._planner = planner

    def run_step(self, step: PlanStep, robot: SimRobot, goal: Goal, state: WorldState) -> Tuple[bool, Optional[str]]:
        action = step.action
        if action == "SEARCH":
            target_cls = self._resolve_search_target(step, goal)
            ok = robot.search(target_cls)
            return ok, None if ok else f"search_failed:{target_cls.value}"

        if action == "NAVIGATE":
            if not step.target_id:
                return False, "navigate_missing_target"
            ok = robot.navigate(step.target_id)
            return ok, None if ok else f"navigate_failed:{step.target_id}"

        if action == "GRASP":
            if not step.target_id:
                return False, "grasp_missing_target"
            ok = robot.grasp(step.target_id)
            return ok, None if ok else f"grasp_failed:{step.target_id}"

        if action == "PLACE_IN_BIN":
            if not step.target_id:
                return False, "place_missing_target"
            bin_id = step.note or "bin_1"
            ok = robot.place_in_bin(step.target_id, bin_id)
            return ok, None if ok else f"place_failed:{step.target_id}"

        if action == "VERIFY":
            ok = robot.verify_goal(goal)
            return ok, None if ok else "verify_failed"

        return False, f"unknown_action:{action}"

    def _resolve_search_target(self, step: PlanStep, goal: Goal) -> ObjClass:
        if step.target_id and "_" in step.target_id:
            maybe = step.target_id.split("_", 1)[0]
            for cls in ObjClass:
                if cls.value == maybe:
                    return cls
        parsed = self._planner.parse_target_class(step.note)
        if parsed:
            return parsed
        return goal.target_obj_class
