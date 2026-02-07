from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from autonomy.types import DetectedObject, Goal, ObjClass

logger = logging.getLogger(__name__)


class LeRobotAdapter:
    """Hardware adapter for SO-ARM100 via HuggingFace LeRobot SDK."""

    def __init__(
        self,
        robot_type: str = "so100_follower",
        port: str = "/dev/ttyACM0",
        camera_config: Optional[Dict[str, int]] = None,
    ) -> None:
        self.robot_type = robot_type
        self.port = port
        self.camera_config = camera_config or {"wrist": 0, "front": 2}
        self.held_object_id: Optional[str] = None
        self._robot: Any = None  # Lazy-loaded LeRobot instance
        self._perception: Any = None

    def _ensure_robot(self) -> None:
        if self._robot is not None:
            return
        try:
            from lerobot.common.robot_devices.robots.factory import make_robot
            self._robot = make_robot(self.robot_type, robot_kwargs={"port": self.port})
            self._robot.connect()
            logger.info(f"Connected to {self.robot_type} on {self.port}")
        except ImportError:
            raise ImportError("lerobot is required: pip install lerobot")

    def reset(self, seed: Optional[int] = None) -> None:
        self._ensure_robot()
        self.held_object_id = None
        # Move to home position
        # self._robot.move_to_home()
        logger.info("Robot reset to home position")

    def observe(self) -> List[DetectedObject]:
        # Observation comes from perception provider, not from robot directly
        return []

    def search(self, target_class: ObjClass) -> bool:
        self._ensure_robot()
        logger.info(f"Executing search sweep for {target_class.value}")
        # Execute a scanning trajectory
        # TODO: Implement search trajectory via LeRobot motor commands
        return True

    def navigate(self, target_id: str) -> bool:
        self._ensure_robot()
        logger.info(f"Navigating to {target_id}")
        # Move arm to pre-grasp position
        # TODO: Implement via inverse kinematics or learned trajectory
        return True

    def grasp(self, target_id: str) -> bool:
        self._ensure_robot()
        logger.info(f"Grasping {target_id}")
        # Close gripper
        # TODO: Implement gripper close + verify via force/current sensing
        self.held_object_id = target_id
        return True

    def place_in_bin(self, target_id: str, bin_id: str) -> bool:
        self._ensure_robot()
        logger.info(f"Placing {target_id} in {bin_id}")
        # Open gripper at bin position
        # TODO: Navigate to bin, open gripper
        self.held_object_id = None
        return True

    def verify_goal(self, goal: Goal) -> bool:
        # Use perception to check if target is in bin
        logger.info(
            f"Verifying goal: {goal.target_obj_class.value} "
            f"in {goal.target_location_obj_class.value}"
        )
        # TODO: Use camera perception to verify
        return True

    def disconnect(self) -> None:
        if self._robot is not None:
            self._robot.disconnect()
            self._robot = None
