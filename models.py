"""
# -----------------------------------------------------------------------
# Copyright (C) 2026 Tharun Gopinath
# Project : SRE Incident Response Environment
# License : GNU Affero General Public License v3 (AGPL-3.0)
# Citation: Tharun Gopinath. "SRE Incident Response Environment." 2026.
#            https://github.com/tg1106/SRE-Incident-Response-Simulator
# Any use of this code, in whole or in part, must retain this header.
# -----------------------------------------------------------------------
models.py — SRE Incident Response Environment
Defines all Pydantic models: Action, Observation, State
These are the typed contracts between agent and environment.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# ACTION
# What the agent can do at each step.
# ---------------------------------------------------------------------------

VALID_ACTIONS = [
    "investigate",   # Look deeper — reveals more signal about the incident
    "restart",       # Restart the affected service
    "rollback",      # Revert to last stable deployment
    "scale_up",      # Add more compute resources
    "escalate",      # Call a human expert (costs time, always works eventually)
    "resolve",       # Declare the incident resolved (ends episode)
]

class SREAction(BaseModel):
    """
    Action taken by the agent at each step.
    Must be one of the VALID_ACTIONS above.
    """
    action: str = Field(
        ...,
        description=f"One of: {VALID_ACTIONS}"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Optional: why the agent chose this action (for logging)"
    )


# ---------------------------------------------------------------------------
# OBSERVATION
# What the agent sees at each step.
# Voting is internal — agent only sees the final weighted decision hint.
# ---------------------------------------------------------------------------

class SREObservation(BaseModel):
    """
    Observation returned to the agent after each step.
    """

    # Incident context
    incident_type: str = Field(
        description="Type of incident: deployment_failure | ddos_attack | db_overload"
    )
    affected_service: str = Field(
        description="Which service is affected e.g. payment-api, auth-service"
    )
    severity: str = Field(
        description="Severity level: low | medium | high | critical"
    )

    # Live metrics (normalized 0.0 to 1.0)
    error_rate: float = Field(
        description="Current error rate (0.0 = no errors, 1.0 = total failure)"
    )
    latency_ms: float = Field(
        description="Current average latency in milliseconds"
    )
    cpu_usage: float = Field(
        description="CPU usage (0.0 to 1.0)"
    )
    memory_usage: float = Field(
        description="Memory usage (0.0 to 1.0)"
    )
    users_impacted: int = Field(
        description="Estimated number of users currently impacted"
    )

    # Episode progress
    time_elapsed: int = Field(
        description="Steps elapsed since incident started"
    )
    max_steps: int = Field(
        description="Maximum steps allowed in this episode"
    )

    # Signals / clues visible to agent
    recent_deployment: bool = Field(
        description="Was there a deployment in the last 30 minutes?"
    )
    traffic_spike: bool = Field(
        description="Is there an unusual traffic spike?"
    )
    db_connection_errors: bool = Field(
        description="Are there database connection errors?"
    )

    # Expert panel hint (internal votes are hidden, only aggregated hint shown)
    expert_recommendation: str = Field(
        description="Aggregated expert panel recommendation (weighted vote result)"
    )

    # Last action feedback
    last_action: Optional[str] = Field(
        default=None,
        description="The last action taken by the agent"
    )
    last_action_result: Optional[str] = Field(
        default=None,
        description="What happened as a result of the last action"
    )
    last_action_error: Optional[str] = Field(
        default=None,
        description="Error message if last action was invalid, else null"
    )

    # Is the incident resolved?
    resolved: bool = Field(
        default=False,
        description="Whether the incident has been resolved"
    )


# ---------------------------------------------------------------------------
# REWARD
# Partial reward at every step.
# ---------------------------------------------------------------------------

class SREReward(BaseModel):
    """
    Reward breakdown for transparency.
    Final reward is always clamped to [0.0, 1.0].
    """
    resolution_bonus: float = Field(
        default=0.0,
        description="Bonus for resolving the incident"
    )
    speed_bonus: float = Field(
        default=0.0,
        description="Bonus for resolving quickly (fewer steps = higher bonus)"
    )
    progress_reward: float = Field(
        default=0.0,
        description="Partial reward for improving system metrics each step"
    )
    invalid_action_penalty: float = Field(
        default=0.0,
        description="Penalty for taking an invalid/impossible action"
    )
    wrong_action_penalty: float = Field(
        default=0.0,
        description="Penalty for taking an action that worsens the situation"
    )
    total: float = Field(
        description="Final reward value, clamped to [0.0, 1.0]"
    )
