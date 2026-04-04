"""
# -----------------------------------------------------------------------
# Copyright (C) 2026 Tharun Gopinath
# Project : SRE Incident Response Environment
# License : GNU Affero General Public License v3 (AGPL-3.0)
# Citation: Tharun Gopinath. "SRE Incident Response Environment." 2026.
#            https://github.com/tg1106/SRE-Incident-Response-Simulator
# Any use of this code, in whole or in part, must retain this header.
# -----------------------------------------------------------------------
inference.py — SRE Incident Response Environment
Baseline inference script for OpenEnv hackathon submission.

Mandatory stdout format:
    [START] task=<task> env=<env> model=<model>
    [STEP]  step=<n> action=<action> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import os
import sys
from typing import List, Optional

from openai import OpenAI

# Direct import — environment runs in-process (no server needed for inference)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server.environment import SREEnvironment
from models import SREAction

# ── Mandatory environment variables ──────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")    # No default — must be set externally

# ── Constants ─────────────────────────────────────────────────────────────────
BENCHMARK         = "sre-incident-env"
MAX_STEPS         = 10
SUCCESS_THRESHOLD = 0.50
TASKS             = ["deployment_failure", "db_overload", "ddos_attack"]

VALID_ACTIONS = [
    "investigate", "restart", "rollback", "scale_up", "escalate", "resolve"
]

SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) responding to a live production incident.

At each step you receive the current incident state. Choose exactly ONE action from:
  investigate  — look deeper to identify root cause
  restart      — restart the affected service
  rollback     — revert to the last stable deployment
  scale_up     — add more compute/memory resources
  escalate     — bring in a specialist team
  resolve      — declare the incident resolved (ONLY when error_rate is very low)

Rules:
- Read ALL metrics and signals carefully before acting
- The expert_recommendation is your multi-agent panel hint — use it
- Only call 'resolve' when error_rate is clearly below 0.25
- Respond with ONLY the single action word. No explanation. No punctuation.

Example response: rollback"""


# ── Logging helpers (STRICT FORMAT — do not modify) ──────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(obs: dict) -> str:
    return (
        f"INCIDENT REPORT\n"
        f"===============\n"
        f"Type          : {obs['incident_type']}\n"
        f"Service       : {obs['affected_service']} ({obs['severity']} severity)\n"
        f"\n"
        f"LIVE METRICS\n"
        f"------------\n"
        f"Error Rate    : {obs['error_rate']:.0%}\n"
        f"Latency       : {obs['latency_ms']:.0f} ms\n"
        f"CPU Usage     : {obs['cpu_usage']:.0%}\n"
        f"Memory Usage  : {obs['memory_usage']:.0%}\n"
        f"Users Impacted: {obs['users_impacted']:,}\n"
        f"\n"
        f"SIGNALS\n"
        f"-------\n"
        f"Recent Deployment : {obs['recent_deployment']}\n"
        f"Traffic Spike     : {obs['traffic_spike']}\n"
        f"DB Conn Errors    : {obs['db_connection_errors']}\n"
        f"\n"
        f"EXPERT PANEL  : {obs['expert_recommendation']}\n"
        f"\n"
        f"Step {obs['time_elapsed']}/{obs['max_steps']}\n"
        f"Last Action   : {obs.get('last_action') or 'None'}\n"
        f"Last Result   : {obs.get('last_action_result') or 'None'}\n"
        f"\n"
        f"Choose your action:"
    )


# ── LLM call ──────────────────────────────────────────────────────────────────

def get_action(client: OpenAI, obs: dict) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_prompt(obs)},
            ],
            max_tokens=10,
            temperature=0.2,
        )
        raw    = (response.choices[0].message.content or "").strip().lower()
        action = raw.split()[0] if raw else "investigate"
        return action if action in VALID_ACTIONS else "investigate"
    except Exception as exc:
        print(f"[DEBUG] LLM error: {exc}", flush=True)
        return "investigate"


# ── Task runner ───────────────────────────────────────────────────────────────

def run_task(client: OpenAI, env: SREEnvironment, task: str) -> None:
    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    rewards:     List[float] = []
    steps_taken: int         = 0
    score:       float       = 0.0
    success:     bool        = False

    try:
        obs = env.reset(task=task).dict()

        for step in range(1, MAX_STEPS + 1):
            if obs.get("resolved", False):
                break

            action = get_action(client, obs)
            result = env.step(SREAction(action=action))

            reward = result["reward"]
            done   = result["done"]
            error  = result["observation"].get("last_action_error")
            obs    = result["observation"]
            info   = result.get("info", {})

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action, reward=reward, done=done, error=error)

            if done:
                # Use grader score if available
                if info.get("grade") is not None:
                    score = float(info["grade"])
                break

        # Fallback: compute score from final state
        if score == 0.0:
            from server.incidents import grade_episode
            score = grade_episode(
                task,
                obs.get("resolved", False),
                steps_taken,
                obs.get("error_rate", 1.0),
            )

        score   = round(min(max(float(score), 0.0), 1.0), 3)
        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task '{task}' error: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    env    = SREEnvironment()

    for task in TASKS:
        run_task(client, env, task)


if __name__ == "__main__":
    main()
