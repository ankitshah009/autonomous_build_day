from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class GR00TClient:
    """Client for GR00T N1.6 inference server (Isaac-GR00T PolicyClient wrapper)."""

    def __init__(self, server_url: str = "localhost:5555") -> None:
        self.server_url = server_url
        self._client: Any = None

    def _ensure_connection(self) -> None:
        if self._client is not None:
            return
        try:
            from gr00t.eval.service import PolicyClient
            host, port = self.server_url.rsplit(":", 1)
            self._client = PolicyClient(host=host, port=int(port))
            logger.info(f"Connected to GR00T server at {self.server_url}")
        except ImportError:
            logger.warning(
                "Isaac-GR00T SDK not installed. "
                "Install from https://github.com/NVIDIA/Isaac-GR00T"
            )
            raise

    def infer(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_connection()
        action = self._client.get_action(observation)
        return {
            "joint_positions": action.tolist() if hasattr(action, "tolist") else action,
        }

    def close(self) -> None:
        self._client = None
