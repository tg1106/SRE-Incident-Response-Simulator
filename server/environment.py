"""
environment.py — Core SRE Incident Response Environment
Manages episode state, processes actions, computes rewards.
"""

import copy
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional, Any

from models import SREAction, SREObservation
from server.incidents import INCIDENTS, grade_episode
from server.agents import get_expert_recommendation

MAX_STEPS         = 10
RESOLVE_THRESHOLD = 0.25   # error_rate must be below this to successfully resolve


class SREEnvironment:

    def __init__(self):
        self.task: str              = "deployment_failure"
        self.incident: Dict         = {}
        self.metrics: Dict          = {}
        self.signals: Dict          = {}
        self.step_count: int        = 0
        self.resolved: bool         = False
        self.episode_id: int        = 0
        self.last_action: Optional[str]        = None
        self.last_action_result: Optional[str] = None
        self.last_action_error: Optional[str]  = None

    # -----------------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------------

    def reset(self, task: str = "deployment_failure") -> SREObservation:
        self.task             = task
        self.incident         = copy.deepcopy(INCIDENTS[task])
        self.metrics          = copy.deepcopy(self.incident["initial_metrics"])
        self.signals          = copy.deepcopy(self.incident["signals"])
        self.step_count       = 0
        self.resolved         = False
        self.episode_id      += 1
        self.last_action      = None
        self.last_action_result = None
        self.last_action_error  = None
        return self._build_observation()

    def step(self, action: SREAction) -> Dict[str, Any]:
        self.step_count += 1
        old_error_rate  = self.metrics["error_rate"]
        error_msg       = None
        reward_val      = 0.10   # base reward for taking any action

        # ── RESOLVE ────────────────────────────────────────────────────────
        if action.action == "resolve":
            if self.metrics["error_rate"] <= RESOLVE_THRESHOLD:
                self.resolved         = True
                self.last_action_result = self.incident["action_effects"]["resolve"]["result_success"]
                steps_remaining = MAX_STEPS - self.step_count
                speed_bonus     = (steps_remaining / MAX_STEPS) * 0.50
                reward_val      = round(min(1.0, 0.50 + speed_bonus), 2)
            else:
                self.last_action_result = self.incident["action_effects"]["resolve"]["result_fail"]
                error_msg  = "Cannot resolve yet — error rate still too high"
                reward_val = 0.05

        # ── UNKNOWN ACTION ──────────────────────────────────────────────────
        elif action.action not in self.incident["action_effects"]:
            error_msg       = f"Unknown action: {action.action}"
            reward_val      = 0.0
            self.last_action_result = "Invalid action. No effect on environment."

        # ── VALID ACTIONS ───────────────────────────────────────────────────
        else:
            effect = self.incident["action_effects"][action.action]

            if not effect.get("valid", True):
                # Contextually invalid (e.g. rollback with no deployment)
                error_msg = f"Action '{action.action}' is not applicable here."
                reward_val = max(0.0, reward_val - 0.05)   # small penalty, still a no-op on logic
                self.last_action_result = effect["result"]
                self._apply_metric_changes(effect)         # apply negative effects
            else:
                self._apply_metric_changes(effect)
                self.last_action_result = effect["result"]

                # Some actions auto-resolve
                if effect.get("resolves", False) and self.metrics["error_rate"] <= RESOLVE_THRESHOLD:
                    self.resolved = True

                improvement = old_error_rate - self.metrics["error_rate"]
                reward_val  = round(min(1.0, max(0.05, 0.10 + improvement * 0.50)), 2)

        self.last_action      = action.action
        self.last_action_error = error_msg

        done = self.resolved or (self.step_count >= MAX_STEPS)
        obs  = self._build_observation()

        return {
            "observation": obs.dict(),
            "reward": reward_val,
            "done":   done,
            "info": {
                "episode_id": self.episode_id,
                "step":       self.step_count,
                "resolved":   self.resolved,
                "grade": grade_episode(
                    self.task,
                    self.resolved,
                    self.step_count,
                    self.metrics["error_rate"],
                ) if done else None,
            },
        }

    def state(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "step_count": self.step_count,
            "task":       self.task,
            "resolved":   self.resolved,
            "metrics":    self.metrics,
        }

    # -----------------------------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------------------------

    def _apply_metric_changes(self, effect: Dict) -> None:
        m = self.metrics
        m["error_rate"] = round(
            max(0.0, min(1.0, m["error_rate"] + effect.get("error_rate", 0.0))), 2
        )
        m["latency_ms"] = round(
            max(0.0, m["latency_ms"] + effect.get("latency_ms", 0.0)), 1
        )
        m["cpu_usage"] = round(
            max(0.0, min(1.0, m["cpu_usage"] + effect.get("cpu_usage", 0.0))), 2
        )
        m["memory_usage"] = round(
            max(0.0, min(1.0, m["memory_usage"] + effect.get("memory_usage", 0.0))), 2
        )
        m["users_impacted"] = max(
            0, m["users_impacted"] + effect.get("users_impacted", 0)
        )

    def _build_observation(self) -> SREObservation:
        rec = get_expert_recommendation(self.metrics, self.signals)
        return SREObservation(
            incident_type      = self.task,
            affected_service   = self.incident["affected_service"],
            severity           = self.incident["severity"],
            error_rate         = self.metrics["error_rate"],
            latency_ms         = self.metrics["latency_ms"],
            cpu_usage          = self.metrics["cpu_usage"],
            memory_usage       = self.metrics["memory_usage"],
            users_impacted     = self.metrics["users_impacted"],
            time_elapsed       = self.step_count,
            max_steps          = MAX_STEPS,
            recent_deployment  = self.signals["recent_deployment"],
            traffic_spike      = self.signals["traffic_spike"],
            db_connection_errors = self.signals["db_connection_errors"],
            expert_recommendation = rec,
            last_action        = self.last_action,
            last_action_result = self.last_action_result,
            last_action_error  = self.last_action_error,
            resolved           = self.resolved,
        )
