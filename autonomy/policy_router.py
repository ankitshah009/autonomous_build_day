from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional

from autonomy.types import WorldState

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    SYMBOLIC = "symbolic"
    ACT = "act"
    GROOT = "groot"


class PolicyRouter:
    """Routes action generation to symbolic planner, ACT policy, or GR00T."""

    def __init__(
        self,
        policy_type: PolicyType = PolicyType.SYMBOLIC,
        checkpoint_path: Optional[str] = None,
        server_url: Optional[str] = None,
    ) -> None:
        self.policy_type = policy_type
        self.checkpoint_path = checkpoint_path
        self.server_url = server_url
        self._act_policy: Any = None
        self._groot_client: Any = None

    def get_action(
        self,
        state: WorldState,
        language_instruction: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Return raw action dict for neural policies (ACT/GR00T).

        Returns None for symbolic mode (uses existing planner via StepExecutor).
        """
        if self.policy_type == PolicyType.SYMBOLIC:
            return None  # Symbolic planner handles this via StepExecutor
        elif self.policy_type == PolicyType.ACT:
            return self._act_inference(state)
        elif self.policy_type == PolicyType.GROOT:
            return self._groot_inference(state, language_instruction)
        return None

    def _act_inference(self, state: WorldState) -> Dict[str, Any]:
        if self._act_policy is None:
            self._load_act_policy()
        observation = {"camera_frames": state.camera_frames}
        action = self._act_policy.select_action(observation)
        return {"joint_positions": action.tolist()}

    def _load_act_policy(self) -> None:
        if not self.checkpoint_path:
            raise ValueError("checkpoint_path required for ACT policy")
        try:
            from lerobot.common.policies.act.modeling_act import ACTPolicy
            self._act_policy = ACTPolicy.from_pretrained(self.checkpoint_path)
            # Set model to inference mode (no gradient computation)
            self._act_policy.train(False)
            logger.info(f"Loaded ACT policy from {self.checkpoint_path}")
        except ImportError:
            raise ImportError("lerobot is required for ACT policy: pip install lerobot")

    def _groot_inference(
        self,
        state: WorldState,
        language_instruction: str,
    ) -> Dict[str, Any]:
        if self._groot_client is None:
            from autonomy.groot_client import GR00TClient
            self._groot_client = GR00TClient(
                server_url=self.server_url or "localhost:5555",
            )
        observation = {
            "camera_frames": state.camera_frames,
            "language": language_instruction,
        }
        return self._groot_client.infer(observation)
