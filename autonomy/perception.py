from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable

from autonomy.types import DetectedObject, WorldState


class PerceptionModule:
    """Lightweight temporal smoothing to avoid flickery world state."""

    def __init__(self, confidence_decay: float = 0.94) -> None:
        self._tracks: Dict[str, DetectedObject] = {}
        self._confidence_decay = confidence_decay

    def reset(self) -> None:
        self._tracks.clear()

    def update(self, state: WorldState, detections: Iterable[DetectedObject]) -> WorldState:
        seen = set()
        for det in detections:
            seen.add(det.obj_id)
            prev = self._tracks.get(det.obj_id)
            if prev:
                blended_conf = max(0.05, min(1.0, 0.6 * prev.confidence + 0.4 * det.confidence))
                merged = replace(det, confidence=blended_conf)
                self._tracks[det.obj_id] = merged
            else:
                self._tracks[det.obj_id] = det

        # Decay confidence for not-seen tracks instead of dropping instantly.
        for obj_id, obj in list(self._tracks.items()):
            if obj_id in seen:
                continue
            decayed = replace(obj, confidence=max(0.0, obj.confidence * self._confidence_decay), visible=False)
            if decayed.confidence < 0.12 and decayed.in_bin:
                del self._tracks[obj_id]
                continue
            self._tracks[obj_id] = decayed

        state.objects = dict(self._tracks)
        return state
