---
title: DM Manager OpenEnv
emoji: 📨
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - nlp
  - real-world
---

# 📨 DM Manager — OpenEnv Submission

> **Meta × PyTorch OpenEnv Hackathon | Round 1 Submission**  
> Built for the [India OpenEnv AI Hackathon](https://www.scaler.com/school-of-technology/meta-pytorch-hackathon) in collaboration with Meta, Hugging Face & PyTorch Foundation.

> **Environment v2 · Inference v5**

---

## Environment Description & Motivation

Every day, people wake up to a flood of unread messages — work emails, family texts, Slack pings, WhatsApp voice notes. Most people handle this on instinct. **DM Manager** asks: what if an AI agent could handle it intelligently?

This environment simulates a real-world messaging inbox. The agent must read incoming messages, figure out what kind they are, decide which ones matter most, and write back in the right tone — all while being efficient about it.

**Why this matters:** Inbox management is a high-frequency, high-stakes real-world task. It requires simultaneous reasoning over content semantics, emotional tone, social context, and time-sensitivity — making it a rich benchmark for agents that aim to be genuinely useful in everyday life.

---

## What the Agent Has to Do

Given a set of incoming messages, the agent must:

1. **Classify** each message as `formal` (work/professional), `emotional` (personal/distress), or `normal` (casual/logistics)
2. **Prioritise** the inbox — ordering messages from most to least urgent
3. **Draft replies** — matching tone to message type (professional, empathetic, or casual)
4. **Archive** low-priority notifications and newsletters without losing important messages

---

## Observation Space

At each step, the agent receives a JSON state object:

```json
{
  "task_id": "task_medium",
  "task_description": "TASK (Medium) — Inbox Triage: ...",
  "current_step": 4,
  "max_steps": 14,
  "inbox_size": 6,
  "unread_count": 4,
  "pending_actions": ["classify", "prioritize"],
  "last_action_feedback": "✓ Correct — 'Manager – Priya' is 'formal'.",
  "messages": [
    {
      "id": "m001",
      "sender": "HR Department",
      "content": "Dear Employee, please review and sign the updated NDA by Friday...",
      "timestamp": "2024-04-06 09:00",
      "message_type": null,
      "priority": null,
      "is_read": false,
      "draft_reply": null
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `task_id` | string | Active task name |
| `task_description` | string | Natural language task instructions |
| `current_step` | int | Current step number |
| `max_steps` | int | Step budget for the task |
| `inbox_size` | int | Total messages in the episode |
| `unread_count` | int | Number of unread messages remaining |
| `pending_actions` | list | Required actions not yet completed |
| `last_action_feedback` | string | Feedback string from the previous step |
| `messages` | list | Active (non-archived) inbox messages |

Each **message object** exposes:

| Field | Description |
|---|---|
| `id` | Unique message identifier (`m001`, `m002`, …) |
| `sender` | Sender name or address |
| `content` | Full message content |
| `timestamp` | Send time (YYYY-MM-DD HH:MM) |
| `message_type` | Assigned label (`null` until classified) |
| `priority` | Assigned priority (`null` until set) |
| `is_read` | Whether message has been read (auto-set on classify) |
| `draft_reply` | Draft reply text (`null` until drafted) |

> Ground-truth fields (`ground_truth_type`, `ground_truth_priority`, `is_archivable`) are hidden from the agent and used internally for scoring only.

---

## 🎮 Action Space

All actions are submitted as JSON objects to `POST /step`.

| Action | Required Fields | Description |
|---|---|---|
| `classify` | `message_id`, `classification` | Label a message as `formal`, `emotional`, or `normal` |
| `prioritize` | `priority_order` | Submit a ranked list of message IDs (highest priority first) |
| `draft_reply` | `message_id`, `draft_text` | Write a reply for a specific message |
| `mark_read` | `message_id` | Mark a message as read |
| `archive` | `message_id` | Archive a low-priority message |

```json
{"action_type": "classify",   "message_id": "m001", "classification": "formal"}
{"action_type": "prioritize", "priority_order": ["m006", "m005", "m001"]}
{"action_type": "draft_reply","message_id": "m005", "draft_text": "Hey, I'm here for you..."}
{"action_type": "mark_read",  "message_id": "m009"}
{"action_type": "archive",    "message_id": "m012"}
```

**Classification labels:**

| Label | When to use |
|---|---|
| `formal` | Work emails, professional requests, meeting invites, deadlines, invoices |
| `emotional` | Personal distress, mental health, family concern, relationship messages |
| `normal` | Casual chat, logistics, social plans, delivery notifications, newsletters |

---

## Task Descriptions

### 🟢 `task_easy` — Classify Only
- **Messages:** 4 (2 formal, 1 emotional, 1 normal)
- **Required actions:** `classify` each message
- **Max steps:** 8
- **What's tested:** Basic message understanding and label assignment

### 🟡 `task_medium` — Classify + Prioritise
- **Messages:** 6 (2 formal, 2 emotional, 2 normal)
- **Required actions:** `classify` each message, then `prioritize`
- **Max steps:** 14
- **What's tested:** Classification accuracy and reasoning about relative urgency across message types

### 🔴 `task_hard` — Full Pipeline
- **Messages:** 8 (3 formal, 3 emotional, 2 normal)
- **Required actions:** `classify`, `prioritize`, and `draft_reply` for every message
- **Max steps:** 30
- **What's tested:** End-to-end pipeline — understanding, ordering, and tone-matched replies scored on five dimensions

### 🚨 `task_urgent_triage` — Crisis Inbox *(new in v2)*
- **Messages:** 6 (biased toward HIGH-priority messages)
- **Required actions:** `classify`, then `prioritize`
- **Max steps:** 14
- **What's tested:** Whether ALL high-priority messages are ranked strictly first. Missing any high-priority item incurs an additional −0.20 penalty.

### 🗂️ `task_selective_archive` — Inbox Cleanup *(new in v2)*
- **Messages:** 8 (2 formal, 2 emotional, 4 normal — includes newsletters and notifications)
- **Required actions:** `classify`, then `archive` low-priority archivable messages
- **Max steps:** 20
- **What's tested:** Distinguishing archivable clutter from important messages. Archiving a high-priority message is heavily penalised.

| Task | Difficulty | Messages | Actions Required | Max Steps |
|---|---|---|---|---|
| `task_easy` | 🟢 Easy | 4 | classify | 8 |
| `task_medium` | 🟡 Medium | 6 | classify, prioritize | 14 |
| `task_hard` | 🔴 Hard | 8 | classify, prioritize, draft_reply | 30 |
| `task_urgent_triage` | 🚨 Medium-Hard | 6 | classify, prioritize | 14 |
| `task_selective_archive` | 🗂️ Medium | 8 | classify, archive | 20 |

---

## 🏆 Reward Function

### Classification
| Outcome | Reward |
|---|---|
| Correct classification | **+0.30** |
| Wrong (`normal` ↔ `formal` or `normal` ↔ `emotional`) | **−0.10** |
| Wrong (`formal` ↔ `emotional`) — harder confusion | **−0.15** |

### Priority Ordering
| Outcome | Reward |
|---|---|
| Ranking quality (Spearman rank overlap, scaled to [0,1]) | up to **+0.40** |
| Top-3 messages all correct (≥ 100% overlap) | **+0.15** bonus |
| Top-3 messages mostly correct (≥ 66% overlap) | **+0.08** bonus |
| `task_urgent_triage`: HIGH messages not in top slots | **−0.20** |

### Draft Replies
| Outcome | Reward |
|---|---|
| Draft quality (tone + length + personalisation + urgency) | up to **+0.30** |
| Draft too short (< 10 characters) | **−0.05** |

Draft quality is scored on five dimensions: tone-keyword match, length tiers (6 / 12 / 20+ words), sender first-name personalisation, urgency language for high-priority formal messages, and a copy-paste penalty (> 55% word overlap with original = deduction).

### Archive
| Outcome | Reward |
|---|---|
| Correctly archiving a low-priority archivable message (newsletter / notification) | **+0.10** |
| Archiving a low-priority non-archivable message | **+0.02** |
| Archiving a MEDIUM-priority message | **−0.15** |
| Archiving a HIGH-priority message | **−0.30** |

**Maximum possible score per episode:**

| Task | Max Score |
|---|---|
| `task_easy` | 1.20 |
| `task_medium` | 2.55 |
| `task_hard` | 5.60 |
| `task_urgent_triage` | 2.55 |
| `task_selective_archive` | 2.00 |

---

## 📊 Baseline Scores

Baselines measured using **Qwen/Qwen2.5-72B-Instruct** (via HuggingFace Inference Router), 10 episodes per task, `temperature=0.1`.

| Task | Random Agent | Rule-Based Heuristic | Qwen2.5-72B-Instruct (zero-shot) |
|---|---|---|---|
| `task_easy` | 0.30 ± 0.12 | 0.72 ± 0.08 | **0.85 ± 0.06** |
| `task_medium` | 0.41 ± 0.18 | 0.89 ± 0.11 | **1.34 ± 0.14** |
| `task_hard` | 0.55 ± 0.22 | 1.12 ± 0.19 | **2.21 ± 0.27** |
| `task_urgent_triage` | 0.35 ± 0.15 | 0.78 ± 0.12 | **1.20 ± 0.18** |
| `task_selective_archive` | 0.28 ± 0.14 | 0.65 ± 0.10 | **1.05 ± 0.16** |

> Strong agents should exceed these baselines, especially on `task_hard` (reply personalisation headroom) and `task_urgent_triage` (strict top-N placement constraint).

---

## What Changed in v2

### Environment (`environment.py` v2)
- **Message corpus:** 12 → **36 messages** (12 per type), ensuring every seed yields a different inbox
- **Keyword banks:** Expanded to **100+ keywords** per category (`FORMAL_KEYWORDS`, `EMOTIONAL_KEYWORDS`, `NORMAL_KEYWORDS`) used for both heuristic rules and draft scoring
- **2 new tasks:** `task_urgent_triage` (urgent bias + top-N penalty) and `task_selective_archive` (archive-aware cleanup)
- **Updated task sizes:** `task_easy` 3→4 msgs / 6→8 steps · `task_medium` 5→6 msgs / 12→14 steps · `task_hard` 6→8 msgs / 25→30 steps
- **`reset()` fix:** Pools are now shuffled per seed before selection — different seeds always produce genuinely different message sets
- **`_score_draft` improvements:** Added negation-word detection, urgency-language bonus for high-priority formal messages, three length tiers, sender first-name personalisation, and copy-paste penalty (>55% word overlap)
- **Priority scoring improvements:** Top-3 overlap bonus (+0.15 / +0.08) and `urgent_bias` penalty (−0.20) added
- **Classify partial credit:** `formal ↔ emotional` confusion now penalised at −0.15 (was −0.10)
- **Archive rewards updated:** Correct archive +0.10 (was +0.05); archiving HIGH priority −0.30 (was −0.15)
- **New `is_archivable` flag** on messages (internal): marks newsletters and notifications as safe to archive
- **New observation fields:** `inbox_size`, `unread_count`, `task_description`, `last_action_feedback`

### Inference (`inference.py` v5)
- Model: **Qwen/Qwen2.5-72B-Instruct** via HuggingFace Inference Router (`https://router.huggingface.co/v1`)
- Client: OpenAI-compatible (`openai.OpenAI`) — swap any provider by changing `API_BASE_URL` + `MODEL_NAME`
- Auth: `HF_TOKEN` env var (falls back to `API_KEY`)
- `temperature=0.1`; markdown fence stripping built-in
- Fallback ID injection in `prioritize_messages` ensures no message IDs are dropped
- Results auto-saved to `baseline_results.json`

---

## API Reference

### Reset
```
POST /reset?task_id=task_easy&session_id=my_session
```
### Step
```
POST /step?session_id=my_session
Content-Type: application/json
{"action_type": "classify", "message_id": "m001", "classification": "formal"}
```
### State
```
GET /state?session_id=my_session
```
### Grade
```
POST /grade?session_id=my_session
```

---

## Setup & Usage

### Quick Start

```bash
git clone https://github.com/Sudheeswar-Reddy/dm-manager-env
cd dm-manager-env

# Docker (recommended)
docker build -t dm-manager .
docker run -p 7860:7860 dm-manager

# Or directly
pip install -r requirements.txt
python app.py
```

### Run the Baseline Agent

**Environment variables:**

| Variable | Description | Default |
|---|---|---|
| `API_BASE_URL` | LLM API endpoint (OpenAI-compatible) | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model identifier | `Qwen/Qwen2.5-72B-Instruct` |
| `HF_TOKEN` | HuggingFace API token | — |
| `API_KEY` | Fallback API key | — |
| `ENV_BASE_URL` | Environment endpoint | `http://localhost:7860` |
| `LOCAL_IMAGE_NAME` | Local Docker image name (optional) | `""` |

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_huggingface_token"
export ENV_BASE_URL="http://localhost:7860"

python inference.py
```

### Manual Episode

```bash
curl -X POST "http://localhost:7860/reset?task_id=task_medium&session_id=demo"
curl "http://localhost:7860/state?session_id=demo"
curl -X POST "http://localhost:7860/step?session_id=demo" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "classify", "message_id": "m001", "classification": "formal"}'
curl -X POST "http://localhost:7860/grade?session_id=demo"
```

---

## 🔗 Links

- 🤗 HuggingFace Space: [sudheeswar-reddy-dm-manager.hf.space](https://sudheeswar-reddy.hf.space/dm-manager-openenv)
- 💻 GitHub: [github.com/Sudheeswar-Reddy/dm-manager-env](https://github.com/Sudheeswar-Reddy/dm-manager-env)
- 🏁 Hackathon: [Meta × PyTorch OpenEnv Hackathon](https://www.scaler.com/school-of-technology/meta-pytorch-hackathon)

---

`openenv` · `reinforcement-learning` · `nlp` · `classification` · `planning` · `real-world`
