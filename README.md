---
title: SRE Incident Response Environment
emoji: 🚨
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
tags:
  - openenv
  - reinforcement-learning
  - multi-agent
  - sre
  - incident-response
short_description: Multi-agent SRE Incident Response OpenEnv Environment
---

# SRE Incident Response Environment

> A multi-agent OpenEnv environment where three expert AI personalities collaboratively vote to resolve production incidents.

---

## What This Environment Simulates

Every tech company running live services employs Site Reliability Engineers (SREs) whose job is to diagnose and resolve production incidents under pressure. This environment simulates that exact scenario.

An AI agent is presented with a live production incident — complete with real metrics (error rates, latency, CPU, memory) and diagnostic signals. It must choose the correct sequence of actions (investigate, rollback, scale up, escalate, etc.) to resolve the incident before time runs out.

**The multi-agent innovation:** Instead of one model deciding alone, three expert agents (DevOps Engineer, Security Analyst, Database Admin) independently vote on what action to take at each step. Their weighted votes are aggregated into a recommendation shown to the main agent — mirroring how real incident war rooms work.

---

## Real-World Utility

This environment is directly useful for:

- **Training autonomous incident response agents** — companies like PagerDuty, Datadog, Grafana are actively building AI-powered incident response. This provides a training sandbox.
- **Benchmarking LLM reasoning under pressure** — tests multi-step diagnostic reasoning with misleading signals (DDoS task).
- **Junior SRE training simulation** — safe sandbox before touching production systems.

---

## Action Space

| Action | Description |
|---|---|
| `investigate` | Reveal deeper diagnostic information |
| `restart` | Restart the affected service |
| `rollback` | Revert to the last stable deployment |
| `scale_up` | Add more compute/memory resources |
| `escalate` | Bring in a specialist team |
| `resolve` | Declare the incident resolved (valid only when error_rate < 0.25) |

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `incident_type` | string | deployment_failure / db_overload / ddos_attack |
| `affected_service` | string | Which service is down |
| `severity` | string | low / medium / high / critical |
| `error_rate` | float [0,1] | Current error rate |
| `latency_ms` | float | Average latency in ms |
| `cpu_usage` | float [0,1] | CPU load |
| `memory_usage` | float [0,1] | Memory load |
| `users_impacted` | int | Estimated affected users |
| `time_elapsed` | int | Steps taken so far |
| `max_steps` | int | Episode step limit (10) |
| `recent_deployment` | bool | Was there a recent deployment? |
| `traffic_spike` | bool | Is there abnormal traffic? |
| `db_connection_errors` | bool | Are DB connections failing? |
| `expert_recommendation` | string | Aggregated panel vote (3 agents, anonymous) |
| `last_action` | string | Previous action taken |
| `last_action_result` | string | What happened as a result |
| `last_action_error` | string | Error if action was invalid |
| `resolved` | bool | Whether incident is resolved |

---

## Tasks

### 🟢 Task 1 — Deployment Failure (Easy)
A bad deployment 8 minutes ago caused payment-api to fail. Error rate at 85%. Signals clearly point to the deployment. Optimal path: `rollback` → `resolve`.

### 🟡 Task 2 — DB Overload (Medium)
A runaway batch job is saturating the database. Auth-service degraded. No recent deployment — agent must not get distracted by irrelevant actions. Optimal path: `investigate` → `scale_up` → `resolve`.

### 🔴 Task 3 — DDoS Attack (Hard)
API gateway overwhelmed by bot traffic. Deliberately includes a `recent_deployment=True` flag as a red herring. Agents that blindly rollback will worsen the situation. Correct path requires `investigate` first to reveal the attack, then `escalate`.

---

## Reward Function

Partial reward is given at every step (range: 0.0 – 1.0):

- **Progress reward:** `0.10 + (error_rate_improvement × 0.50)` per valid action
- **Resolution bonus:** `0.50 + (steps_remaining / max_steps × 0.50)` — faster = higher
- **Invalid action penalty:** `-0.05` (action treated as no-op)
- **Wrong action penalty:** small negative from metric worsening
- All values clamped to `[0.0, 1.0]`

---

## Grader Scores (0.0 – 1.0)

| Task | Resolved ≤3 steps | ≤5 steps | ≤8 steps | Any resolve | Not resolved |
|---|---|---|---|---|---|
| deployment_failure | 1.00 | 0.85 | 0.65 | 0.45 | 0.00–0.30 |
| db_overload | 1.00 | 0.80 | 0.60 | 0.40 | 0.00–0.25 |
| ddos_attack | 1.00 | 0.75 | 0.55 | 0.35 | 0.00–0.20 |

Partial credit for metric improvement even without resolution.

---

## Multi-Agent Voting System

Three expert agents vote internally at each step:

| Agent | Personality | Voting Weight |
|---|---|---|
| DevOps Engineer | Fast operator, loves quick fixes | 0.40 |
| Security Analyst | Cautious, suspects attacks | 0.30 |
| Database Admin | Data-layer focused | 0.30 |

Each agent votes `(action, confidence)`. Final recommendation = weighted sum. **Individual votes are hidden** — only the aggregated recommendation is shown.

---

## Setup & Usage

### Local (Direct)
```bash
pip install -r requirements.txt
python inference.py
```

### Docker
```bash
docker build -t sre-incident-env .
docker run -p 7860:7860 sre-incident-env
```

### Environment Variables
```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token-here"
```

### API Endpoints
```
POST /reset   {"task": "deployment_failure"}
POST /step    {"action": "rollback"}
GET  /state
GET  /health
```

---

## Baseline Scores

Baseline agent: `Qwen/Qwen2.5-72B-Instruct`

| Task | Score | Steps | Resolved |
|---|---|---|---|
| deployment_failure | ~0.85 | ~3 | ✅ |
| db_overload | ~0.65 | ~5 | ✅ |
| ddos_attack | ~0.45 | ~7 | ⚠️ |

---

## Project Structure

```
sre_incident_env/
├── inference.py        ← Baseline inference script (mandatory)
├── openenv.yaml        ← OpenEnv manifest
├── Dockerfile          ← Container definition
├── requirements.txt
├── pyproject.toml
├── README.md
├── models.py           ← Pydantic: Action, Observation, Reward
├── client.py           ← HTTP client
├── __init__.py
└── server/
    ├── app.py          ← FastAPI server
    ├── environment.py  ← Core episode logic
    ├── incidents.py    ← 3 incident definitions + graders
    └── agents.py       ← 3 voting personalities
```

---

## Copyright (C) 2026 Tharun Gopinath
- Project : SRE Incident Response Environment
- License : GNU Affero General Public License v3 (AGPL-3.0)
- Citation: Tharun Gopinath. "SRE Incident Response Environment." 2026.
           https://github.com/tg1106/SRE-Incident-Response-Simulator
- Any use of this code, in whole or in part, must retain this header.
