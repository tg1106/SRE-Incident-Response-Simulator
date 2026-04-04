"""
app.py — FastAPI Server for SRE Incident Response Environment
Endpoints: POST /reset  |  POST /step  |  GET /state  |  GET /health
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from models import SREAction
from server.environment import SREEnvironment

app = FastAPI(
    title="SRE Incident Response Environment",
    description="Multi-agent SRE Incident Response OpenEnv Environment",
    version="0.1.0",
)

VALID_TASKS = {"deployment_failure", "db_overload", "ddos_attack"}

# One global environment instance per container
_env = SREEnvironment()


class ResetRequest(BaseModel):
    task: Optional[str] = "deployment_failure"


@app.post("/reset")
def reset(request: ResetRequest = ResetRequest()):
    """Reset the environment and start a new episode."""
    task = request.task or "deployment_failure"
    if task not in VALID_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task '{task}'. Valid tasks: {sorted(VALID_TASKS)}"
        )
    obs = _env.reset(task=task)
    return JSONResponse(content=obs.dict(), status_code=200)


@app.post("/step")
def step(action: SREAction):
    """Take one step in the environment."""
    result = _env.step(action)
    return JSONResponse(content=result, status_code=200)


@app.get("/state")
def state():
    """Return current episode metadata."""
    return JSONResponse(content=_env.state(), status_code=200)


@app.get("/health")
def health():
    """Health check — used by HF Spaces."""
    return {"status": "ok", "env": "sre-incident-env", "version": "0.1.0"}
