from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Protocol

from autonomy.types import EpisodeMetrics, TelemetryFrame, WorldState


class TelemetrySink(Protocol):
    def emit(self, frame: TelemetryFrame) -> None:
        ...


class InMemorySink:
    def __init__(self) -> None:
        self.frames: List[TelemetryFrame] = []

    def emit(self, frame: TelemetryFrame) -> None:
        self.frames.append(frame)


class JsonlSink:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8")

    def emit(self, frame: TelemetryFrame) -> None:
        self._fh.write(json.dumps(frame.to_dict(), separators=(",", ":")) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


class StdoutSink:
    def emit(self, frame: TelemetryFrame) -> None:
        msg = {
            "phase": frame.phase,
            "action": frame.current_action,
            "retries": frame.retries,
            "replans": frame.replans,
            "last_error": frame.last_error,
            "success_rate": frame.metrics.get("success_rate_last10"),
        }
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


class UdpSink:
    """Sends telemetry as JSON over UDP for lightweight bridge processes."""

    def __init__(self, host: str, port: int) -> None:
        self._addr = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, frame: TelemetryFrame) -> None:
        payload = json.dumps(frame.to_dict(), separators=(",", ":")).encode("utf-8")
        self._sock.sendto(payload, self._addr)

    def close(self) -> None:
        self._sock.close()


class MultiSink:
    def __init__(self, sinks: Iterable[TelemetrySink]) -> None:
        self._sinks = list(sinks)

    def emit(self, frame: TelemetryFrame) -> None:
        for sink in self._sinks:
            sink.emit(frame)

    def close(self) -> None:
        for sink in self._sinks:
            close = getattr(sink, "close", None)
            if callable(close):
                close()


def world_snapshot(state: WorldState) -> dict:
    return {
        "tick": state.tick,
        "held_object_id": state.held_object_id,
        "last_error": state.last_error,
        "objects": [
            {
                "id": obj.obj_id,
                "cls": obj.cls.value,
                "confidence": round(obj.confidence, 3),
                "visible": obj.visible,
                "in_bin": obj.in_bin,
                "position": [round(v, 3) for v in obj.position],
            }
            for obj in sorted(state.objects.values(), key=lambda o: o.obj_id)
        ],
        "robot_state": {
            "joint_positions": [round(p, 3) for p in state.joint_positions],
            "joint_velocities": [round(v, 3) for v in state.joint_velocities],
            "gripper_state": state.gripper_state,
            "battery_level": round(state.battery_level, 1),
            "temperature": round(state.temperature, 1),
        },
    }


def metrics_dict(metrics: EpisodeMetrics, recent_success_rate: Optional[float]) -> dict:
    return {
        "success": metrics.success,
        "retries": metrics.retries,
        "replans": metrics.replans,
        "steps_executed": metrics.steps_executed,
        "duration_s": round(metrics.duration_s, 3),
        "fail_reason": metrics.fail_reason,
        "success_rate_last10": None if recent_success_rate is None else round(recent_success_rate, 3),
    }
