"""
agents.py — 3 Expert Voting Agents
Each agent has a distinct personality and strategy.
Votes are internal — only the weighted recommendation is exposed to the agent.
"""

from typing import Dict, Tuple


class DevOpsAgent:
    """
    Fast operator. Biased toward quick operational fixes.
    Loves: rollback, restart, scale_up
    Voting weight: 0.40
    """
    name   = "DevOps Engineer"
    weight = 0.40

    def vote(self, metrics: Dict, signals: Dict) -> Tuple[str, float]:
        recent_deployment = signals.get("recent_deployment", False)
        traffic_spike     = signals.get("traffic_spike", False)
        error_rate        = metrics["error_rate"]
        cpu_usage         = metrics["cpu_usage"]

        if recent_deployment and error_rate > 0.60:
            return "rollback", 0.85
        if cpu_usage > 0.85:
            return "scale_up", 0.80
        if error_rate > 0.50:
            return "restart", 0.65
        return "investigate", 0.50


class SecurityAgent:
    """
    Cautious. Suspects attacks. Prefers to understand before acting.
    Loves: investigate, escalate
    Voting weight: 0.30
    """
    name   = "Security Analyst"
    weight = 0.30

    def vote(self, metrics: Dict, signals: Dict) -> Tuple[str, float]:
        traffic_spike = signals.get("traffic_spike", False)
        error_rate    = metrics["error_rate"]

        if traffic_spike:
            return "investigate", 0.90
        if error_rate > 0.70:
            return "escalate", 0.70
        return "investigate", 0.55


class DBAAgent:
    """
    Focused on the data layer. Suspects DB-level issues first.
    Loves: scale_up, investigate
    Voting weight: 0.30
    """
    name   = "Database Admin"
    weight = 0.30

    def vote(self, metrics: Dict, signals: Dict) -> Tuple[str, float]:
        db_errors    = signals.get("db_connection_errors", False)
        memory_usage = metrics["memory_usage"]
        latency_ms   = metrics["latency_ms"]

        if db_errors:
            return "scale_up", 0.85
        if memory_usage > 0.85 and latency_ms > 2000:
            return "scale_up", 0.70
        return "investigate", 0.55


# ---------------------------------------------------------------------------
# VOTING AGGREGATOR
# ---------------------------------------------------------------------------

AGENTS = [DevOpsAgent(), SecurityAgent(), DBAAgent()]


def get_expert_recommendation(metrics: Dict, signals: Dict) -> str:
    """
    Run all 3 agents, collect weighted votes, return aggregated recommendation.
    Individual votes are anonymous — only the final recommendation is exposed.
    """
    vote_scores: Dict[str, float] = {}

    for agent in AGENTS:
        action, confidence = agent.vote(metrics, signals)
        weighted = agent.weight * confidence
        vote_scores[action] = vote_scores.get(action, 0.0) + weighted

    best_action = max(vote_scores, key=vote_scores.get)
    best_score  = vote_scores[best_action]

    if best_score >= 0.60:
        label = "high confidence"
    elif best_score >= 0.35:
        label = "moderate confidence"
    else:
        label = "low confidence"

    return f"Expert panel recommends '{best_action}' ({label})"
