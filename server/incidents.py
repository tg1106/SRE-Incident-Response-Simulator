"""
# -----------------------------------------------------------------------
# Copyright (C) 2026 Tharun Gopinath
# Project : SRE Incident Response Environment
# License : GNU Affero General Public License v3 (AGPL-3.0)
# Citation: Tharun Gopinath. "SRE Incident Response Environment." 2026.
#            https://github.com/tg1106/SRE-Incident-Response-Simulator
# Any use of this code, in whole or in part, must retain this header.
# -----------------------------------------------------------------------
incidents.py — 3 Incident Type Definitions
Each incident has: initial metrics, signals, action effects, grader.
"""

from typing import Dict, Any

INCIDENTS: Dict[str, Dict[str, Any]] = {

    # ------------------------------------------------------------------
    # TASK 1 — EASY
    # ------------------------------------------------------------------
    "deployment_failure": {
        "description": "A bad deployment 8 minutes ago caused a service failure.",
        "affected_service": "payment-api",
        "severity": "critical",
        "initial_metrics": {
            "error_rate": 0.85,
            "latency_ms": 1800.0,
            "cpu_usage": 0.65,
            "memory_usage": 0.70,
            "users_impacted": 8000,
        },
        "signals": {
            "recent_deployment": True,
            "traffic_spike": False,
            "db_connection_errors": False,
        },
        "action_effects": {
            "investigate": {
                "error_rate": -0.10,
                "latency_ms": -100.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "users_impacted": -500,
                "result": "Investigation reveals the new deployment introduced a null pointer exception in payment processing.",
                "valid": True,
            },
            "rollback": {
                "error_rate": -0.75,
                "latency_ms": -1400.0,
                "cpu_usage": -0.20,
                "memory_usage": -0.15,
                "users_impacted": -7500,
                "result": "Rollback successful. Service restored to previous stable version.",
                "valid": True,
                "resolves": True,
            },
            "restart": {
                "error_rate": -0.20,
                "latency_ms": -200.0,
                "cpu_usage": -0.05,
                "memory_usage": -0.05,
                "users_impacted": -500,
                "result": "Service restarted. Partial recovery — root cause (bad deployment) persists.",
                "valid": True,
            },
            "scale_up": {
                "error_rate": -0.05,
                "latency_ms": -100.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "users_impacted": -200,
                "result": "Scaled up compute. Minimal effect — this is a code-level issue, not resource-level.",
                "valid": True,
            },
            "escalate": {
                "error_rate": -0.50,
                "latency_ms": -800.0,
                "cpu_usage": -0.10,
                "memory_usage": -0.10,
                "users_impacted": -5000,
                "result": "Senior engineer identified the deployment issue and initiated rollback.",
                "valid": True,
            },
            "resolve": {
                "result_success": "Incident resolved. Payment service fully operational.",
                "result_fail": "Cannot close — error rate still too high. Incident remains open.",
                "valid": True,
            },
        },
    },

    # ------------------------------------------------------------------
    # TASK 2 — MEDIUM
    # ------------------------------------------------------------------
    "db_overload": {
        "description": "Database CPU and memory maxed out due to a runaway batch job.",
        "affected_service": "auth-service",
        "severity": "high",
        "initial_metrics": {
            "error_rate": 0.60,
            "latency_ms": 3200.0,
            "cpu_usage": 0.92,
            "memory_usage": 0.95,
            "users_impacted": 4500,
        },
        "signals": {
            "recent_deployment": False,
            "traffic_spike": False,
            "db_connection_errors": True,
        },
        "action_effects": {
            "investigate": {
                "error_rate": -0.08,
                "latency_ms": -200.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "users_impacted": -200,
                "result": "Investigation reveals a batch job running unoptimized queries — saturating the database.",
                "valid": True,
            },
            "scale_up": {
                "error_rate": -0.35,
                "latency_ms": -1500.0,
                "cpu_usage": -0.35,
                "memory_usage": -0.30,
                "users_impacted": -3000,
                "result": "Database scaled up. Resource pressure significantly relieved.",
                "valid": True,
            },
            "restart": {
                "error_rate": -0.20,
                "latency_ms": -800.0,
                "cpu_usage": -0.20,
                "memory_usage": -0.25,
                "users_impacted": -1500,
                "result": "Database restarted. Temporary relief — batch job will resume.",
                "valid": True,
            },
            "rollback": {
                "error_rate": 0.05,
                "latency_ms": 100.0,
                "cpu_usage": 0.02,
                "memory_usage": 0.02,
                "users_impacted": 200,
                "result": "No recent deployment found. Rollback failed. Situation worsened slightly.",
                "valid": False,
            },
            "escalate": {
                "error_rate": -0.45,
                "latency_ms": -2000.0,
                "cpu_usage": -0.40,
                "memory_usage": -0.45,
                "users_impacted": -4000,
                "result": "DBA team identified and killed the runaway batch job. Database recovering.",
                "valid": True,
            },
            "resolve": {
                "result_success": "Incident resolved. Auth service fully operational.",
                "result_fail": "Cannot resolve yet — database load still too high.",
                "valid": True,
            },
        },
    },

    # ------------------------------------------------------------------
    # TASK 3 — HARD
    # ------------------------------------------------------------------
    "ddos_attack": {
        "description": "DDoS attack overwhelming the API gateway. Recent deployment flag is a red herring.",
        "affected_service": "api-gateway",
        "severity": "critical",
        "initial_metrics": {
            "error_rate": 0.72,
            "latency_ms": 2400.0,
            "cpu_usage": 0.95,
            "memory_usage": 0.80,
            "users_impacted": 15000,
        },
        "signals": {
            "recent_deployment": True,   # RED HERRING
            "traffic_spike": True,
            "db_connection_errors": False,
        },
        "action_effects": {
            "investigate": {
                "error_rate": -0.05,
                "latency_ms": -100.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "users_impacted": -500,
                "result": "Investigation confirms massive bot traffic from external IPs. This is a DDoS attack — NOT a deployment issue.",
                "valid": True,
            },
            "rollback": {
                "error_rate": 0.10,
                "latency_ms": 200.0,
                "cpu_usage": 0.05,
                "memory_usage": 0.05,
                "users_impacted": 1000,
                "result": "Rollback had no effect. Attack traffic surges on. The deployment was NOT the cause.",
                "valid": False,
            },
            "restart": {
                "error_rate": -0.05,
                "latency_ms": -50.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "users_impacted": -200,
                "result": "Service restarted. Minimal effect. DDoS traffic resumes immediately.",
                "valid": True,
            },
            "scale_up": {
                "error_rate": -0.25,
                "latency_ms": -600.0,
                "cpu_usage": -0.20,
                "memory_usage": -0.15,
                "users_impacted": -5000,
                "result": "Scaled up infrastructure. Absorbing some DDoS load. Temporary relief.",
                "valid": True,
            },
            "escalate": {
                "error_rate": -0.60,
                "latency_ms": -1800.0,
                "cpu_usage": -0.55,
                "memory_usage": -0.50,
                "users_impacted": -14000,
                "result": "Security team activated DDoS mitigation rules. Attack traffic scrubbed. Service recovering.",
                "valid": True,
                "resolves": True,
            },
            "resolve": {
                "result_success": "Incident resolved. API gateway fully operational.",
                "result_fail": "Cannot resolve — attack traffic still active.",
                "valid": True,
            },
        },
    },
}


# ---------------------------------------------------------------------------
# GRADERS — Score 0.0 to 1.0
# Called at end of episode.
# ---------------------------------------------------------------------------

def grade_episode(
    task: str,
    resolved: bool,
    steps_taken: int,
    final_error_rate: float,
) -> float:
    """
    Compute a final score [0.0, 1.0] for a completed episode.
    Considers: resolution success + speed + metric improvement.
    """
    if task == "deployment_failure":
        if resolved:
            if steps_taken <= 2:   return 1.00
            if steps_taken <= 4:   return 0.85
            if steps_taken <= 7:   return 0.65
            return 0.45
        return round(max(0.0, (1.0 - final_error_rate) * 0.30), 2)

    if task == "db_overload":
        if resolved:
            if steps_taken <= 3:   return 1.00
            if steps_taken <= 5:   return 0.80
            if steps_taken <= 8:   return 0.60
            return 0.40
        return round(max(0.0, (1.0 - final_error_rate) * 0.25), 2)

    if task == "ddos_attack":
        if resolved:
            if steps_taken <= 3:   return 1.00
            if steps_taken <= 5:   return 0.75
            if steps_taken <= 8:   return 0.55
            return 0.35
        return round(max(0.0, (1.0 - final_error_rate) * 0.20), 2)

    return 0.0
