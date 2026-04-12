"""
inference.py — DM Manager Baseline Agent (v5)
Strictly follows the official sample inference.py log format.

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

from __future__ import annotations
import json, os, sys, time, uuid, requests
from typing import Any, Dict, List, Optional
from openai import OpenAI

# ── Required env vars (per hackathon spec) ──────────────────────────────────
API_BASE_URL     = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME       = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

API_KEY          = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "")
ENV_BASE_URL     = os.getenv("ENV_BASE_URL", "http://localhost:7860")

BENCHMARK = "dm-manager"
TASKS     = ["task_easy", "task_medium", "task_hard"]
SUCCESS_SCORE_THRESHOLD = 0.5

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)

# ── Official log functions (exact format from sample) ───────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ── env helpers ─────────────────────────────────────────────────────────────

def env_reset(task_id: str, session_id: str) -> Dict:
    seed = abs(hash(session_id)) % 10_000
    r = requests.post(f"{ENV_BASE_URL}/reset",
        params={"task_id": task_id, "session_id": session_id, "seed": seed}, timeout=30)
    r.raise_for_status()
    return r.json()

def env_step(action: Dict, session_id: str) -> Dict:
    r = requests.post(f"{ENV_BASE_URL}/step", json=action,
        params={"session_id": session_id}, timeout=30)
    r.raise_for_status()
    return r.json()

def env_grade(session_id: str) -> Dict:
    r = requests.post(f"{ENV_BASE_URL}/grade",
        params={"session_id": session_id}, timeout=30)
    r.raise_for_status()
    return r.json()

# ── LLM core ────────────────────────────────────────────────────────────────

def llm(system: str, user: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
        max_tokens=800, temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return raw.strip()

# ── LLM system prompts ───────────────────────────────────────────────────────

CLASSIFY_SYSTEM = """Classify a message as exactly one of: formal, emotional, or normal.
formal: work, business, banking, HR, deadlines, invoices, contracts, admin.
emotional: personal relationships, family, friends, feelings, support, distress.
normal: casual, everyday, neutral messages that are neither formal nor emotional.
Respond ONLY with JSON:
{"action_type": "classify", "message_id": "m001", "classification": "formal"}"""

PRIORITY_SYSTEM = """Order messages from MOST to LEAST important.
HIGH: urgent work deadlines, emotional distress, family concern, client messages.
MEDIUM: casual plans, partner messages, colleague thanks.
LOW: newsletters, delivery notifications, bank statements.
Respond ONLY with JSON (include ALL message IDs):
{"action_type": "prioritize", "priority_order": ["m001", "m002"]}"""

DRAFT_SYSTEM = """Write replies that perfectly match message tone.
FORMAL: Start "Dear [Name]," use: please, kindly, regards, confirm. End "Kind regards,"
EMOTIONAL: Warm, empathetic — use: here for you, I care, understand, always here, thinking of you, take care.
NORMAL: Casual — use: hey, sure, sounds good, no worries, will do.
Respond ONLY with JSON:
{"action_type": "draft_reply", "message_id": "m001", "draft_text": "reply here"}
Minimum 20 words. Match tone perfectly."""

# ── LLM action functions (LLM only — no fallbacks) ──────────────────────────

def llm_classify(msg: Dict) -> Dict:
    user = (f"Classify this message:\n\n"
            f"From: {msg['sender']}\nMessage: {msg['content']}\n\n"
            f"Return JSON: {{\"action_type\":\"classify\","
            f"\"message_id\":\"{msg['id']}\",\"classification\":\"formal|emotional|normal\"}}")
    raw    = llm(CLASSIFY_SYSTEM, user)
    action = json.loads(raw)
    clf    = action.get("classification", "").lower()
    if clf not in ("formal", "emotional", "normal"):
        raise ValueError(f"llm_classify: unexpected value '{clf}' for {msg['id']}")
    return {"action_type":"classify","message_id":msg["id"],"classification":clf}

def prioritize_messages(messages: List[Dict]) -> Dict:
    all_ids  = [m["id"] for m in messages]
    msg_list = "\n".join([
        f"ID:{m['id']} From:{m['sender']} Type:{m.get('message_type','?')} | {m['content'][:100]}"
        for m in messages
    ])
    user   = f"Prioritise these {len(messages)} messages:\n\n{msg_list}\n\nReturn JSON with all {len(messages)} IDs."
    raw    = llm(PRIORITY_SYSTEM, user)
    action = json.loads(raw)
    order  = action.get("priority_order", [])
    for mid in all_ids:
        if mid not in order: order.append(mid)
    return {"action_type":"prioritize","priority_order":order}

def draft_reply(msg: Dict) -> Dict:
    msg_type = msg.get("message_type","normal")
    user = (f"Write a {msg_type.upper()} reply:\n\n"
            f"From: {msg['sender']}\nMessage: {msg['content']}\n\n"
            f"Return JSON: {{\"action_type\":\"draft_reply\","
            f"\"message_id\":\"{msg['id']}\",\"draft_text\":\"reply\"}}")
    raw    = llm(DRAFT_SYSTEM, user)
    action = json.loads(raw)
    action["message_id"]  = msg["id"]
    action["action_type"] = "draft_reply"
    if not action.get("draft_text") or len(action["draft_text"].split()) < 10:
        raise ValueError(f"draft_reply: insufficient draft text returned for {msg['id']}")
    return action

# ── clamp score ──────────────────────────────────────────────────────────────

def clamp_score(score: float) -> float:
    return min(max(score, 0.0), 1.0)

# ── run one task episode ─────────────────────────────────────────────────────

def run_task(task_id: str) -> Dict[str, Any]:
    session_id = f"{task_id}_{uuid.uuid4().hex}"
    rewards: List[float] = []
    step_num = 0

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    reset_data = env_reset(task_id, session_id)
    obs        = reset_data["observation"]
    messages   = obs["messages"]
    pending    = list(obs["pending_actions"])

    def do_step(action: Dict) -> Dict:
        nonlocal step_num, messages
        step_num += 1
        result   = env_step(action, session_id)
        rv       = result["reward"]["value"]
        done     = result["done"]
        messages = result["observation"]["messages"]
        err_msg  = result["reward"].get("reason") if rv < 0 else None
        rewards.append(rv)
        log_step(step=step_num, action=action.get("action_type","unknown"),
                 reward=rv, done=done, error=err_msg)
        time.sleep(0.4)
        return result

    # ── CLASSIFY ─────────────────────────────────────────────────────────────
    if "classify" in pending:
        for msg in list(messages):
            action = llm_classify(msg)
            result = do_step(action)
            if result["done"]: break

    # ── PRIORITIZE ───────────────────────────────────────────────────────────
    if "prioritize" in pending:
        action = prioritize_messages(messages)
        result = do_step(action)

    # ── DRAFT REPLY ──────────────────────────────────────────────────────────
    if "draft_reply" in pending:
        for msg in list(messages):
            action = draft_reply(msg)
            result = do_step(action)
            if result["done"]: break

    grade_result = env_grade(session_id)
    final_score  = grade_result["score"]
    success      = final_score >= SUCCESS_SCORE_THRESHOLD
    score        = clamp_score(final_score)

    log_end(success=success, steps=step_num, score=score, rewards=rewards)

    return {"task_id":task_id,"steps":step_num,"score":score,
            "final_score":score,"success":success,"rewards":rewards}

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("="*60, flush=True)
    print(f"DM Manager — OpenEnv Baseline Inference v5", flush=True)
    print(f"Model: {MODEL_NAME} | Env: {ENV_BASE_URL}", flush=True)
    print("="*60, flush=True)

    all_results = []
    for task_id in TASKS:
        print(f"\n{'─'*40}\nRunning: {task_id}\n{'─'*40}", flush=True)
        try:
            all_results.append(run_task(task_id))
        except Exception as e:
            print(f"ERROR task_id={task_id} error={e}", file=sys.stderr, flush=True)
            log_end(success=False, steps=0, score=0.0, rewards=[0.0])
            all_results.append({"task_id":task_id,"score":0.0,"success":False,"error":str(e)})
        time.sleep(1)

    print("\n"+"="*60, flush=True)
    print("SUMMARY", flush=True)
    print("="*60, flush=True)
    total = 0.0
    for r in all_results:
        score  = r.get("score", 0.0)
        total += score
        status = "PASS" if r.get("success") else "FAIL"
        print(f"  {r['task_id']:15s} score={score:.2f}  [{status}]", flush=True)
    avg = total / len(all_results)
    print(f"\n  Average score: {avg:.2f}", flush=True)
    print("="*60, flush=True)

    with open("baseline_results.json","w") as f:
        json.dump({"model":MODEL_NAME,"api_base":API_BASE_URL,
                   "tasks":all_results,"average_score":avg}, f, indent=2)
    print("Results saved to baseline_results.json", flush=True)

if __name__ == "__main__":
    main()
