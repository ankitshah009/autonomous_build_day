from __future__ import annotations

from typing import List, Optional

from autonomy.types import Goal, ObjClass, PlanStep, WorldState


class Planner:
    """Readable symbolic planner for a pick-and-place Track-1 task."""

    def build_plan(self, goal: Goal, state: WorldState) -> List[PlanStep]:
        target = self._best_target(goal.target_obj_class, state)
        bin_obj = self._best_target(goal.target_location_obj_class, state, include_in_bin=True)

        if target is None:
            return [PlanStep(action="SEARCH", note=f"find_{goal.target_obj_class.value}")]

        if bin_obj is None:
            return [
                PlanStep(action="SEARCH", note=f"find_{goal.target_location_obj_class.value}"),
                PlanStep(action="SEARCH", note=f"find_{goal.target_obj_class.value}"),
            ]

        steps: List[PlanStep] = []
        if target.confidence < 0.6 or not target.visible:
            steps.append(PlanStep(action="SEARCH", target_id=target.obj_id, note="low_confidence_target"))
        steps.extend(
            [
                PlanStep(action="NAVIGATE", target_id=target.obj_id),
                PlanStep(action="GRASP", target_id=target.obj_id),
                PlanStep(action="NAVIGATE", target_id=bin_obj.obj_id),
                PlanStep(action="PLACE_IN_BIN", target_id=target.obj_id, note=bin_obj.obj_id),
                PlanStep(action="VERIFY", note=goal.target_obj_class.value),
            ]
        )
        return steps

    def _best_target(self, cls: ObjClass, state: WorldState, include_in_bin: bool = False):
        candidates = [
            obj
            for obj in state.objects.values()
            if obj.cls == cls and (include_in_bin or not obj.in_bin)
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda x: (x.visible, x.confidence), reverse=True)[0]

    @staticmethod
    def summarize(plan: List[PlanStep]) -> List[str]:
        return [step.label() for step in plan]

    @staticmethod
    def parse_target_class(note: str) -> Optional[ObjClass]:
        for cls in ObjClass:
            if cls.value in note:
                return cls
        return None
