"""
FastAPI application — DM Manager OpenEnv
==========================================
Exposes the OpenEnv interface as REST endpoints for Hugging Face Spaces.
"""

import os
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from environment import DMManagerEnv, Action, Observation, Reward, TASK_CONFIGS
from tasks import run_grader

app = FastAPI(
    title="DM Manager — OpenEnv",
    description="Real-world DM inbox management environment: classify, prioritise, and draft replies.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (supports multiple parallel sessions)
_sessions: Dict[str, DMManagerEnv] = {}


def _get_env(session_id: str) -> DMManagerEnv:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found. Call /reset first.")
    return _sessions[session_id]


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html><body style="font-family:sans-serif;padding:2rem;background:#0f172a;color:#e2e8f0">
    <h1>📨 DM Manager — OpenEnv</h1>
    <p>A real-world DM inbox management reinforcement learning environment.</p>
    <h3>Available Tasks</h3>
    <ul>
      <li><b>task_easy</b> — Classify 3 messages by type (formal/emotional/normal)</li>
      <li><b>task_medium</b> — Classify + prioritise 5 mixed messages</li>
      <li><b>task_hard</b> — Classify, prioritise, and draft replies for 6 messages</li>
    </ul>
    <h3>Endpoints</h3>
    <ul>
      <li>POST /reset?task_id=task_easy&session_id=s1</li>
      <li>POST /step?session_id=s1</li>
      <li>GET  /state?session_id=s1</li>
      <li>POST /grade?session_id=s1</li>
      <li>GET  /tasks — list all tasks</li>
      <li>GET  /health</li>
    </ul>
    <p><a href="/docs" style="color:#60a5fa">📖 Interactive API Docs (Swagger)</a></p>
    </body></html>
    """


@app.get("/health")
def health():
    return {"status": "ok", "environment": "dm-manager", "version": "1.0.0"}


# ──────────────────────────────────────────────
# OpenEnv interface
# ──────────────────────────────────────────────

@app.post("/reset")
def reset(task_id: str = "task_easy", session_id: str = "default", seed: int = 42):
    """Reset the environment for a given task. Returns initial observation."""
    if task_id not in TASK_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id. Choose from: {list(TASK_CONFIGS)}")
    env = DMManagerEnv(task_id=task_id, seed=seed)
    _sessions[session_id] = env
    obs = env.reset()
    return {"observation": obs.model_dump(), "session_id": session_id, "task_id": task_id}


@app.post("/step")
def step(action: Action, session_id: str = "default"):
    """Execute one action. Returns observation, reward, done, info."""
    env = _get_env(session_id)
    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state(session_id: str = "default"):
    """Return full internal environment state."""
    env = _get_env(session_id)
    return env.state()


@app.post("/grade")
def grade(session_id: str = "default"):
    """Run the task grader and return score [0.0–1.0]."""
    env = _get_env(session_id)
    s = env.state()
    result = run_grader(s["task_id"], s)
    return result


@app.get("/tasks")
def list_tasks():
    """List all available tasks."""
    return {
        tid: {
            "id": cfg["id"],
            "description": cfg["description"],
            "max_steps": cfg["max_steps"],
            "required_actions": cfg["required_actions"],
            "message_count": len(cfg["message_ids"]),
        }
        for tid, cfg in TASK_CONFIGS.items()
    }


@app.get("/action_space")
def action_space():
    return {
        "action_types": ["classify", "prioritize", "draft_reply", "mark_read", "archive"],
        "classify": {
            "description": "Classify a single message by type",
            "fields": {"action_type": "classify", "message_id": "str", "classification": "formal|emotional|normal"}
        },
        "prioritize": {
            "description": "Submit a ranked list of all message IDs from most to least important",
            "fields": {"action_type": "prioritize", "priority_order": "list[str]"}
        },
        "draft_reply": {
            "description": "Draft a contextually appropriate reply to a message",
            "fields": {"action_type": "draft_reply", "message_id": "str", "draft_text": "str"}
        },
        "mark_read": {
            "fields": {"action_type": "mark_read", "message_id": "str"}
        },
        "archive": {
            "fields": {"action_type": "archive", "message_id": "str"}
        },
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
