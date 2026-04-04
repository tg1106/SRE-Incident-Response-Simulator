"""
# -----------------------------------------------------------------------
# Copyright (C) 2026 Tharun Gopinath
# Project : SRE Incident Response Environment
# License : GNU Affero General Public License v3 (AGPL-3.0)
# Citation: Tharun Gopinath. "SRE Incident Response Environment." 2026.
#            https://github.com/tg1106/SRE-Incident-Response-Simulator
# Any use of this code, in whole or in part, must retain this header.
# -----------------------------------------------------------------------
client.py — HTTP Client for SRE Incident Response Environment
Connects to the FastAPI server running in Docker / HF Space.
"""

import requests
from typing import Optional, Dict, Any

from models import SREAction, SREObservation

DEFAULT_BASE_URL = "http://localhost:7860"


class SREEnv:
    """
    Thin HTTP client that wraps the SRE environment server.
    Mirrors the same reset() / step() / state() interface as
    the in-process SREEnvironment class.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def reset(self, task: str = "deployment_failure") -> Dict[str, Any]:
        """Reset the environment. Returns raw observation dict."""
        resp = requests.post(
            f"{self.base_url}/reset",
            json={"task": task},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def step(self, action: str, reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Take one step. Returns {observation, reward, done, info}."""
        payload = {"action": action}
        if reasoning:
            payload["reasoning"] = reasoning
        resp = requests.post(
            f"{self.base_url}/step",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def state(self) -> Dict[str, Any]:
        """Return current episode metadata."""
        resp = requests.get(f"{self.base_url}/state", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        """No-op for HTTP client — connection is stateless."""
        pass
