from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Tuple

from autonomy.types import DetectedObject, ObjClass, Vec3


class PerceptionProvider(Protocol):
    """Protocol for pluggable perception backends."""

    def capture(self) -> Tuple[List[DetectedObject], Dict[str, Any]]: ...
    def reset(self) -> None: ...


class SimPerceptionProvider:
    """Wraps SimRobot.observe() as a PerceptionProvider."""

    def __init__(self, robot) -> None:
        self._robot = robot

    def capture(self) -> Tuple[List[DetectedObject], Dict[str, Any]]:
        return self._robot.observe(), {}

    def reset(self) -> None:
        pass


class YOLOWorldDetector:
    """Open-vocabulary object detector using YOLO-World."""

    def __init__(
        self,
        classes: List[str],
        model_size: str = "s",
        confidence_threshold: float = 0.3,
    ) -> None:
        self._classes = classes
        self._model_size = model_size
        self._conf_threshold = confidence_threshold
        self._model = None  # Lazy-loaded

    def _load_model(self) -> None:
        try:
            from ultralytics import YOLO
            self._model = YOLO(f"yolov8{self._model_size}-worldv2")
            self._model.set_classes(self._classes)
        except ImportError:
            raise ImportError("ultralytics is required: pip install ultralytics>=8.1.0")

    def detect(self, frames: Dict[str, Any]) -> List[DetectedObject]:
        if self._model is None:
            self._load_model()
        # Detect objects in each frame, merge results
        detections: List[DetectedObject] = []
        obj_counter: Dict[str, int] = {}
        for cam_name, frame in frames.items():
            if frame is None:
                continue
            results = self._model.predict(frame, conf=self._conf_threshold, verbose=False)
            for r in results:
                for box in r.boxes:
                    cls_name = r.names[int(box.cls[0])]
                    obj_cls = self._map_class(cls_name)
                    count = obj_counter.get(cls_name, 0) + 1
                    obj_counter[cls_name] = count
                    # Derive rough position from bbox center (normalized)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx = (x1 + x2) / 2.0 / frame.shape[1]
                    cy = (y1 + y2) / 2.0 / frame.shape[0]
                    detections.append(DetectedObject(
                        obj_id=f"{cls_name}_{count}",
                        cls=obj_cls,
                        position=(cx, cy, 0.5),  # z=0.5 default without depth
                        confidence=float(box.conf[0]),
                        visible=True,
                    ))
        return detections

    def _map_class(self, name: str) -> ObjClass:
        name_lower = name.lower()
        for cls in ObjClass:
            if cls.value in name_lower:
                return cls
        return ObjClass.UNKNOWN


class CameraPerceptionProvider:
    """Captures from real USB cameras and runs object detection."""

    def __init__(
        self,
        camera_config: Dict[str, int],
        detector: Optional[YOLOWorldDetector] = None,
    ) -> None:
        self._camera_config = camera_config  # {"wrist": 0, "front": 2}
        self._detector = detector
        self._caps: Dict[str, Any] = {}

    def _ensure_cameras(self) -> None:
        if self._caps:
            return
        import cv2
        for name, idx in self._camera_config.items():
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self._caps[name] = cap

    def capture(self) -> Tuple[List[DetectedObject], Dict[str, Any]]:
        self._ensure_cameras()
        import cv2  # noqa: F811
        frames: Dict[str, Any] = {}
        for name, cap in self._caps.items():
            ret, frame = cap.read()
            if ret:
                frames[name] = frame

        detections: List[DetectedObject] = []
        if self._detector and frames:
            detections = self._detector.detect(frames)

        return detections, {"camera_frames": frames}

    def reset(self) -> None:
        pass

    def release(self) -> None:
        for cap in self._caps.values():
            cap.release()
        self._caps.clear()
