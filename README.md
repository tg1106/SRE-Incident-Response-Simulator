---
title: SRE Incident Response Environment
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

# 🚨 SRE Incident Response Environment

> A multi-agent OpenEnv environment where three expert AI personalities collaboratively vote to resolve live production incidents.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-green)](https://github.com/meta-pytorch/OpenEnv)
[![HuggingFace](https://img.shields.io/badge/🤗%20HuggingFace-Space-yellow)](https://huggingface.co/spaces/tg1106/SRE-Multi_Agent_Incident_Reporter_Stimulator)

---

## 📌 Table of Contents

1. [What is this?](#what-is-this)
2. [Real-World Utility](#real-world-utility)
3. [How It Works](#how-it-works)
4. [Multi-Agent Voting System](#multi-agent-voting-system)
5. [Tasks](#tasks)
6. [Action Space](#action-space)
7. [Observation Space](#observation-space)
8. [Reward Function](#reward-function)
9. [Grader Scores](#grader-scores)
10. [Installation Guide](#installation-guide)
11. [Running the Environment](#running-the-environment)
12. [API Endpoints](#api-endpoints)
13. [Baseline Scores](#baseline-scores)
14. [Project Structure](#project-structure)
15. [License & Citation](#license--citation)

---

## What is this?

Every tech company running live services employs **Site Reliability Engineers (SREs)** — engineers whose job is to diagnose and resolve production incidents under extreme pressure. When something breaks at 2am, they wake up, stare at dashboards, read logs, and make a call: rollback? restart? escalate? Every wrong move costs time. Every minute of downtime costs money.

**This environment trains an AI agent to do exactly that.**

An AI agent is presented with a live production incident — complete with real metrics (error rates, latency, CPU, memory) and diagnostic signals. It must choose the correct sequence of actions to resolve the incident before time runs out.

**The multi-agent innovation:** Instead of one model deciding alone, three expert agents (DevOps Engineer, Security Analyst, Database Admin) independently vote on what action to take at each step. Their weighted votes are aggregated into a recommendation — mirroring exactly how real incident war rooms work with humans.

---

## Real-World Utility

This environment is directly useful for:

- **Training autonomous incident response agents** — companies like PagerDuty, Datadog, and Grafana are actively building AI-powered incident response. This provides a training sandbox.
- **Benchmarking LLM reasoning under pressure** — tests multi-step diagnostic reasoning with deliberately misleading signals (DDoS task).
- **Junior SRE onboarding simulation** — safe sandbox to train engineers before touching production systems.
- **AI research** — novel multi-agent voting architecture for collaborative decision making under time pressure.

---

## How It Works

```
Incident fires 🚨
      ↓
Agent receives observation (metrics + signals + expert recommendation)
      ↓
3 Expert Agents vote internally (hidden)
      ↓
Weighted vote → expert_recommendation shown to agent
      ↓
Agent picks action
      ↓
Environment updates metrics + gives partial reward
      ↓
Repeat until resolved or max steps reached
```

---

## Multi-Agent Voting System

Three expert agents vote internally at each step. **Individual votes are anonymous** — only the aggregated weighted recommendation is shown to the main agent.

| Agent | Personality | Strategy | Weight |
|---|---|---|---|
| 🔴 DevOps Engineer | Fast operator | Loves quick fixes — rollback, restart, scale | 0.40 |
| 🔵 Security Analyst | Cautious | Suspects attacks, prefers investigating first | 0.30 |
| 🟡 Database Admin | Data-layer focused | Suspects DB issues, recommends scale_up | 0.30 |

Each agent outputs `(action, confidence_score)`. Final recommendation = weighted sum of confidence scores across all votes.

---

## Tasks

### 🟢 Task 1 — Deployment Failure (Easy)
**Service:** payment-api
**Scenario:** A bad deployment 8 minutes ago caused a service failure. Error rate at 85%.
**Signals:** `recent_deployment=True`, no traffic spike, no DB errors.
**Optimal path:** `rollback` → `resolve`
**What makes it easy:** Signals clearly and directly point to the root cause.

---

### 🟡 Task 2 — DB Overload (Medium)
**Service:** auth-service
**Scenario:** A runaway batch job is saturating the database. CPU at 92%, memory at 95%.
**Signals:** `db_connection_errors=True`, no recent deployment, no traffic spike.
**Optimal path:** `investigate` → `scale_up` → `resolve`
**What makes it medium:** No single obvious fix — requires understanding before acting.

---

### 🔴 Task 3 — DDoS Attack (Hard)
**Service:** api-gateway
**Scenario:** Massive bot traffic is overwhelming the gateway. 15,000 users impacted.
**Signals:** `traffic_spike=True`, `recent_deployment=True` ← **deliberate red herring**
**Optimal path:** `investigate` → `escalate` → `resolve`
**What makes it hard:** The `recent_deployment=True` flag is a trap. Agents that blindly rollback will worsen the situation. Must investigate first to uncover the real cause.

---

## Action Space

| Action | Description | When to use |
|---|---|---|
| `investigate` | Reveal deeper diagnostic information | When root cause is unclear |
| `restart` | Restart the affected service | Quick fix for transient failures |
| `rollback` | Revert to last stable deployment | When recent deployment is the cause |
| `scale_up` | Add more compute/memory resources | When resource exhaustion is the cause |
| `escalate` | Bring in a specialist team | For complex attacks or unknown causes |
| `resolve` | Declare the incident resolved | ONLY when `error_rate < 0.25` |

---

## Observation Space

| Field | Type | Range | Description |
|---|---|---|---|
| `incident_type` | string | — | deployment_failure / db_overload / ddos_attack |
| `affected_service` | string | — | Which service is down |
| `severity` | string | — | low / medium / high / critical |
| `error_rate` | float | [0.0, 1.0] | Current error rate |
| `latency_ms` | float | ≥ 0 | Average response latency in ms |
| `cpu_usage` | float | [0.0, 1.0] | CPU load |
| `memory_usage` | float | [0.0, 1.0] | Memory load |
| `users_impacted` | int | ≥ 0 | Estimated affected users |
| `time_elapsed` | int | 0–10 | Steps taken so far |
| `max_steps` | int | 10 | Episode step limit |
| `recent_deployment` | bool | — | Was there a deployment in the last 30 min? |
| `traffic_spike` | bool | — | Is there abnormal inbound traffic? |
| `db_connection_errors` | bool | — | Are database connections failing? |
| `expert_recommendation` | string | — | Aggregated weighted vote from 3 anonymous agents |
| `last_action` | string / null | — | The last action taken |
| `last_action_result` | string / null | — | What happened as a result |
| `last_action_error` | string / null | — | Error message if action was invalid |
| `resolved` | bool | — | Whether the incident has been resolved |

---

## Reward Function

Partial reward is provided at **every step** (always clamped to `[0.0, 1.0]`):

| Signal | Formula |
|---|---|
| Progress reward | `0.10 + (error_rate_drop × 0.50)` per valid action |
| Resolution bonus | `0.50 + (steps_remaining / max_steps × 0.50)` |
| Invalid action penalty | `-0.05` (action treated as no-op) |
| Wrong action | Metric worsening → naturally lower reward |

**Example:** Resolve in 2 steps → reward ≈ `0.50 + (8/10 × 0.50)` = **0.90**

---

## Grader Scores

Final episode score (0.0 – 1.0) based on resolution speed:

| Task | ≤ 2 steps | ≤ 3 steps | ≤ 5 steps | ≤ 8 steps | Not resolved |
|---|---|---|---|---|---|
| deployment_failure | 1.00 | 1.00 | 0.85 | 0.65 | 0.00–0.30 |
| db_overload | 1.00 | 1.00 | 0.80 | 0.60 | 0.00–0.25 |
| ddos_attack | 1.00 | 1.00 | 0.75 | 0.55 | 0.00–0.20 |

Partial credit is awarded for metric improvement even without full resolution.

---

## Installation Guide

### Prerequisites

Before you begin, make sure you have the following installed on your system:

**1. Check Python version (must be 3.10 or higher):**
```bash
python3 --version
```

**2. Check Git is installed:**
```bash
git --version
```

**3. Install Docker Desktop:**
Download from https://docs.docker.com/get-docker/ and make sure it is open and running before using Docker commands.

**4. HuggingFace account:**
Sign up for free at https://huggingface.co if you don't have one.

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/tg1106/SRE-Incident-Response-Simulator.git
cd SRE-Incident-Response-Simulator
```

---

### Step 2 — Install Python dependencies

```bash
pip3 install -r requirements.txt
```

This installs everything needed: `fastapi`, `uvicorn`, `pydantic`, `openai`, `requests`, `openenv-core`.

---

### Step 3 — Install additional dev tools

```bash
pip3 install python-dotenv
```

---

### Step 4 — Set up your environment variables

Create a `.env` file in the root of your project:

```bash
touch .env
```

Open it in any text editor and add the following:

```
HF_TOKEN=hf_your_actual_token_here
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

**How to get your HuggingFace token:**
1. Go to https://huggingface.co/settings/tokens
2. Click **New token**
3. Give it a name (e.g. `sre-env`)
4. Set Role to **Write**
5. Click **Generate token**
6. Copy it and paste into your `.env` file

> ⚠️ **Security warning:** Never commit your `.env` file to GitHub. It is already blocked by `.gitignore` in this repo.

---

## Running the Environment

### Option A — Run inference locally (fastest way to test)

This runs the full environment and all 3 tasks in-process. No Docker needed.

```bash
python3 inference.py
```

Expected output:
```
[START] task=deployment_failure env=sre-incident-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=rollback reward=0.47 done=true error=null
[END] success=true steps=1 score=1.000 rewards=0.47

[START] task=db_overload env=sre-incident-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=scale_up reward=0.28 done=false error=null
[STEP] step=2 action=resolve reward=0.75 done=true error=null
[END] success=true steps=2 score=1.000 rewards=0.28,0.75

[START] task=ddos_attack env=sre-incident-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=investigate reward=0.12 done=false error=null
[STEP] step=2 action=escalate reward=0.40 done=true error=null
[END] success=true steps=2 score=1.000 rewards=0.12,0.40
```

---

### Option B — Run as a local Docker server

**Step 1 — Open Docker Desktop** and wait until it shows "Engine running".

**Step 2 — Build the Docker image:**
```bash
docker build -t sre-incident-env .
```

**Step 3 — Run the container:**
```bash
docker run -p 7860:7860 sre-incident-env
```

**Step 4 — Test it is running:**
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "deployment_failure"}'
```

You should get a full JSON observation back.

**Step 5 — Stop the container when done:**
```bash
docker ps                      # find the container ID
docker stop <container_id>
```

---

### Option C — Use the live HuggingFace Space

No installation needed. Call the hosted API directly:

```bash
curl -X POST https://tg1106-sre-multi-agent-incident-reporter-stimulator.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "deployment_failure"}'
```

---

### Testing all 3 tasks manually

```bash
# Task 1 — Deployment Failure (Easy)
curl -X POST https://tg1106-sre-multi-agent-incident-reporter-stimulator.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "deployment_failure"}'

# Task 2 — DB Overload (Medium)
curl -X POST https://tg1106-sre-multi-agent-incident-reporter-stimulator.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "db_overload"}'

# Task 3 — DDoS Attack (Hard)
curl -X POST https://tg1106-sre-multi-agent-incident-reporter-stimulator.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "ddos_attack"}'
```

---

### Running the pre-submission validator

```bash
chmod +x validate-submission.sh
./validate-submission.sh https://tg1106-sre-multi-agent-incident-reporter-stimulator.hf.space
```

Expected output:
```
✅ PASSED -- HF Space is live and responds to /reset
✅ PASSED -- Docker build succeeded
✅ PASSED -- openenv validate passed

All 3/3 checks passed! Your submission is ready to submit.
```

---

## API Endpoints

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/reset` | `{"task": "deployment_failure"}` | Start a new episode |
| POST | `/step` | `{"action": "rollback"}` | Take one action step |
| GET | `/state` | — | Get current episode metadata |
| GET | `/health` | — | Health check |

**Valid tasks:** `deployment_failure` · `db_overload` · `ddos_attack`

**Valid actions:** `investigate` · `restart` · `rollback` · `scale_up` · `escalate` · `resolve`

---

## Baseline Scores

Baseline agent: `Qwen/Qwen2.5-72B-Instruct`

| Task | Score | Steps | Resolved |
|---|---|---|---|
| deployment_failure | 1.000 | 1 | ✅ |
| db_overload | 1.000 | 2 | ✅ |
| ddos_attack | 1.000 | 2 | ✅ |

---

## Project Structure

```
SRE-Incident-Response-Simulator/
│
├── inference.py            ← Baseline inference script (mandatory for submission)
├── openenv.yaml            ← OpenEnv manifest
├── Dockerfile              ← Container definition (port 7860)
├── requirements.txt        ← Python dependencies
├── pyproject.toml          ← Package config + server entry point
├── uv.lock                 ← Locked dependencies
├── validate-submission.sh  ← Pre-submission validator
├── README.md               ← You are here
├── LICENSE                 ← AGPL-3.0
├── .gitignore              ← Protects .env and secrets
│
├── models.py               ← Pydantic models: Action, Observation, Reward
├── client.py               ← HTTP client wrapper
├── __init__.py             ← Package exports
│
└── server/
    ├── app.py              ← FastAPI server (/reset /step /state /health)
    ├── environment.py      ← Core episode logic + reward computation
    ├── incidents.py        ← 3 incident definitions + graders (0.0–1.0)
    ├── agents.py           ← 3 voting personalities + vote aggregator
    └── __init__.py
```

---

## License & Citation

Copyright (C) 2026 Tharun Gopinath

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

**If you use this work in any form — research, product, service, or project — you must cite it as:**

```
Tharun Gopinath. "SRE Incident Response Environment."
Multi-Agent OpenEnv Environment. 2026.
https://github.com/tg1106/SRE-Incident-Response-Simulator
Licensed under AGPL-3.0.
```

See the [LICENSE](./LICENSE) file for full terms.