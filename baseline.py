"""
# -----------------------------------------------------------------------
# Copyright (C) 2026 Tharun Gopinath
# Project : SRE Incident Response Environment
# License : GNU Affero General Public License v3 (AGPL-3.0)
# Citation: Tharun Gopinath. "SRE Incident Response Environment." 2026.
#            https://github.com/tg1106/SRE-Incident-Response-Simulator
# Any use of this code, in whole or in part, must retain this header.
# -----------------------------------------------------------------------
baseline.py — Rule-Based Baseline for SRE Incident Response Environment

No LLM. Pure rule-based logic using signals from the observation.
Similar structure to the SupportEnv baseline pattern.

Run:
    python3 baseline.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.environment import SREEnvironment
from models import SREAction

TASKS = ["deployment_failure", "db_overload", "ddos_attack"]


def rule_based_agent(obs: dict, actions_taken: list) -> str:
    """
    Rule-based policy.
    Reads signals from observation and decides action deterministically.

    Rules (in priority order):
    1. If error_rate is low enough → resolve
    2. If recent_deployment and no rollback yet → rollback
    3. If traffic_spike and no investigation yet → investigate
    4. If db_connection_errors and no scale_up yet → scale_up
    5. If nothing investigated yet → investigate
    6. Fallback → escalate
    """

    error_rate         = obs["error_rate"]
    recent_deployment  = obs["recent_deployment"]
    traffic_spike      = obs["traffic_spike"]
    db_errors          = obs["db_connection_errors"]

    # Rule 1 — resolve if metrics are good enough
    if error_rate <= 0.25:
        return "resolve"

    # Rule 2 — rollback if recent deployment caused the issue
    if recent_deployment and "rollback" not in actions_taken and not traffic_spike:
        return "rollback"

    # Rule 3 — investigate traffic spike (could be DDoS)
    if traffic_spike and "investigate" not in actions_taken:
        return "investigate"

    # Rule 4 — scale up if DB errors present
    if db_errors and "scale_up" not in actions_taken:
        return "scale_up"

    # Rule 5 — investigate if haven't yet
    if "investigate" not in actions_taken:
        return "investigate"

    # Rule 6 — escalate if still not resolved after investigation
    if "escalate" not in actions_taken:
        return "escalate"

    # Rule 7 — restart as last resort
    if "restart" not in actions_taken:
        return "restart"

    # Fallback — force resolve
    return "resolve"


def run_task(env: SREEnvironment, task: str) -> None:
    print(f"\n{'='*50}")
    print(f"TASK: {task.upper()}")
    print(f"{'='*50}")

    obs         = env.reset(task=task).model_dump()
    done        = False
    total_score = 0.0
    step        = 0
    actions_taken = []

    print(f"Incident   : {obs['incident_type']}")
    print(f"Service    : {obs['affected_service']}")
    print(f"Severity   : {obs['severity']}")
    print(f"Error Rate : {obs['error_rate']:.0%}")
    print(f"Users Hit  : {obs['users_impacted']:,}")
    print(f"Expert Says: {obs['expert_recommendation']}")
    print(f"{'-'*50}")

    while not done:
        step += 1

        # Agent decides action
        action = rule_based_agent(obs, actions_taken)
        actions_taken.append(action)

        # Step the environment
        result  = env.step(SREAction(action=action))
        obs     = result["observation"]
        reward  = result["reward"]
        done    = result["done"]
        info    = result["info"]

        total_score += reward

        print(
            f"Step {step:2d} | Action: {action:<12} | "
            f"Reward: {reward:.2f} | "
            f"Error Rate: {obs['error_rate']:.0%} | "
            f"Done: {done}"
        )

        if obs.get("last_action_error"):
            print(f"         ⚠️  Error: {obs['last_action_error']}")

    # Final result
    grade = info.get("grade", 0.0) or 0.0
    print(f"{'-'*50}")
    print(f"Resolved   : {obs['resolved']}")
    print(f"Steps Taken: {step}")
    print(f"Total Score: {total_score:.2f}")
    print(f"Grade (0-1): {grade:.3f}")
    print(f"{'='*50}")


def main():
    env = SREEnvironment()

    print("\n🚨 SRE INCIDENT RESPONSE — RULE-BASED BASELINE")
    print("No LLM. Pure signal-based decision logic.\n")

    all_grades = []

    for task in TASKS:
        run_task(env, task)

    print("\n📊 SUMMARY")
    print(f"{'='*50}")
    print("Run complete. Check Grade (0-1) per task above.")
    print("A perfect agent scores 1.000 on all 3 tasks.")


if __name__ == "__main__":
    main()