from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

Vec3 = Tuple[float, float, float]


class ObjClass(str, Enum):
    CUP = "cup"
    BOTTLE = "bottle"
    TOOL = "tool"
    BIN = "bin"
    DRAWER = "drawer"
    UNKNOWN = "unknown"


@dataclass
class DetectedObject:
    obj_id: str
    cls: ObjClass
    position: Vec3
    confidence: float = 1.0
    visible: bool = True
    in_bin: bool = False
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorldState:
    tick: int = 0
    objects: Dict[str, DetectedObject] = field(default_factory=dict)
    held_object_id: Optional[str] = None
    drawer_open: bool = False
    last_error: Optional[str] = None
    phase: str = "IDLE"


@dataclass(frozen=True)
class Goal:
    goal_type: str
    target_obj_class: ObjClass
    target_location_obj_class: ObjClass = ObjClass.BIN


@dataclass(frozen=True)
class PlanStep:
    action: str
    target_id: Optional[str] = None
    note: str = ""

    def label(self) -> str:
        if self.target_id:
            return f"{self.action}({self.target_id})"
        return self.action


@dataclass
class EpisodeMetrics:
    success: bool = False
    retries: int = 0
    replans: int = 0
    steps_executed: int = 0
    fail_reason: Optional[str] = None
    duration_s: float = 0.0


@dataclass
class TelemetryFrame:
    ts_ms: int
    phase: str
    plan: List[str]
    current_action: str
    retries: int
    replans: int
    last_error: Optional[str]
    world: Dict[str, Any]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EpisodeResult:
    goal: Goal
    metrics: EpisodeMetrics
    timeline: List[TelemetryFrame]
