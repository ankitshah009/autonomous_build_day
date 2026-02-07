from __future__ import annotations

import random
from dataclasses import replace
from typing import Dict, List, Optional

from autonomy.types import DetectedObject, Goal, ObjClass


class SimRobot:
    """Simple stochastic world for Track-1 style autonomy testing."""

    def __init__(self, seed: int = 7) -> None:
        self._base_seed = seed
        self._rng = random.Random(seed)
        self._episode = 0
        self.held_object_id: Optional[str] = None
        self.objects: Dict[str, DetectedObject] = {}
        self.reset(seed)

    def reset(self, seed: Optional[int] = None) -> None:
        if seed is None:
            seed = self._base_seed + self._episode
        self._episode += 1
        self._rng = random.Random(seed)
        self.held_object_id = None

        cup_visible = self._rng.random() > 0.25
        cup = DetectedObject(
            obj_id="cup_1",
            cls=ObjClass.CUP,
            position=(self._rng.uniform(0.2, 0.9), self._rng.uniform(-0.4, 0.4), 0.75),
            confidence=0.75 if cup_visible else 0.2,
            visible=cup_visible,
            in_bin=False,
            properties={"graspable": "true"},
        )
        bottle = DetectedObject(
            obj_id="bottle_1",
            cls=ObjClass.BOTTLE,
            position=(self._rng.uniform(0.2, 0.9), self._rng.uniform(-0.4, 0.4), 0.75),
            confidence=0.7,
            visible=True,
            in_bin=False,
            properties={"graspable": "true"},
        )
        target_bin = DetectedObject(
            obj_id="bin_1",
            cls=ObjClass.BIN,
            position=(1.4, 0.0, 0.0),
            confidence=0.98,
            visible=True,
            in_bin=False,
            properties={"container": "true"},
        )

        self.objects = {
            cup.obj_id: cup,
            bottle.obj_id: bottle,
            target_bin.obj_id: target_bin,
        }

    def observe(self) -> List[DetectedObject]:
        """Return noisy detections. Some objects may be missed."""
        detections: List[DetectedObject] = []
        for obj in self.objects.values():
            if obj.cls == ObjClass.BIN:
                detections.append(replace(obj, confidence=0.97))
                continue

            # Simulate perception miss / confidence fluctuation.
            if not obj.visible and self._rng.random() < 0.75:
                continue
            if obj.in_bin and self._rng.random() < 0.85:
                continue

            conf_noise = self._rng.uniform(-0.12, 0.1)
            detections.append(
                replace(
                    obj,
                    confidence=max(0.05, min(1.0, obj.confidence + conf_noise)),
                )
            )
        return detections

    def target_in_bin(self, goal: Goal) -> bool:
        for obj in self.objects.values():
            if obj.cls == goal.target_obj_class and obj.in_bin:
                return True
        return False

    def _find_any(self, cls: ObjClass) -> Optional[DetectedObject]:
        candidates = [o for o in self.objects.values() if o.cls == cls and not o.in_bin]
        if not candidates:
            return None
        return sorted(candidates, key=lambda o: o.confidence, reverse=True)[0]

    def search(self, target_class: ObjClass) -> bool:
        target = self._find_any(target_class)
        if not target:
            return False
        if target.visible:
            return True
        # Search can reveal occluded target.
        discovered = self._rng.random() > 0.2
        if discovered:
            target.visible = True
            target.confidence = max(target.confidence, 0.65)
            return True
        return False

    def navigate(self, target_id: str) -> bool:
        if target_id not in self.objects:
            return False
        # Disturbance: object can drift when scene is dynamic.
        if self._rng.random() < 0.15:
            obj = self.objects[target_id]
            obj.position = (
                obj.position[0] + self._rng.uniform(-0.03, 0.03),
                obj.position[1] + self._rng.uniform(-0.03, 0.03),
                obj.position[2],
            )
        return self._rng.random() > 0.06

    def grasp(self, target_id: str) -> bool:
        if self.held_object_id is not None:
            return False
        target = self.objects.get(target_id)
        if not target or target.in_bin or not target.visible:
            return False
        # Grasp reliability decreases slightly when confidence is low.
        base = 0.88 if target.confidence >= 0.55 else 0.7
        success = self._rng.random() < base
        if success:
            self.held_object_id = target_id
        return success

    def place_in_bin(self, target_id: str, bin_id: str) -> bool:
        if bin_id not in self.objects:
            return False
        target = self.objects.get(target_id)
        if not target or self.held_object_id != target_id:
            return False
        success = self._rng.random() > 0.04
        if success:
            target.in_bin = True
            target.visible = False
            self.held_object_id = None
        return success

    def verify_goal(self, goal: Goal) -> bool:
        return self.target_in_bin(goal)
