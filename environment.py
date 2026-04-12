"""
DM Manager OpenEnv Environment — 
=====================================
Real-world simulation of managing a messaging inbox.


"""

from __future__ import annotations

import random
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class MessageType(str, Enum):
    FORMAL    = "formal"
    EMOTIONAL = "emotional"
    NORMAL    = "normal"

class Priority(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

class ActionType(str, Enum):
    CLASSIFY    = "classify"
    PRIORITIZE  = "prioritize"
    DRAFT_REPLY = "draft_reply"
    MARK_READ   = "mark_read"
    ARCHIVE     = "archive"


# ──────────────────────────────────────────────
# Core Data Models
# ──────────────────────────────────────────────

class Message(BaseModel):
    id: str
    sender: str
    content: str
    timestamp: str
    message_type: Optional[MessageType] = None
    priority: Optional[Priority] = None
    is_read: bool = False
    draft_reply: Optional[str] = None
    ground_truth_type: Optional[MessageType] = None
    ground_truth_priority: Optional[Priority] = None
    is_archivable: bool = False   # True for newsletters/notifications


class Observation(BaseModel):
    task_id: str
    task_description: str
    messages: List[Dict[str, Any]]
    current_step: int
    max_steps: int
    inbox_size: int
    unread_count: int
    pending_actions: List[str]
    last_action_feedback: Optional[str] = None


class Action(BaseModel):
    action_type: ActionType
    message_id: Optional[str] = None
    classification: Optional[MessageType] = None
    priority: Optional[Priority] = None
    draft_text: Optional[str] = None
    priority_order: Optional[List[str]] = None


class Reward(BaseModel):
    value: float = Field(..., ge=-1.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    reason: str = ""


# ──────────────────────────────────────────────
# Expanded Message Corpus (36 messages)
# ──────────────────────────────────────────────

SAMPLE_MESSAGES = [

    # ── FORMAL HIGH (8) ──────────────────────────────────────────────────────
    {
        "id": "m001", "sender": "HR Department",
        "content": "Dear Employee, please review and sign the updated NDA by Friday. This is mandatory for all staff. Regards, HR.",
        "timestamp": "2024-04-06 09:00", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m002", "sender": "Client – Apex Corp",
        "content": "Further to our meeting, I am writing to confirm the revised project timeline. Kindly acknowledge receipt at your earliest convenience.",
        "timestamp": "2024-04-06 10:15", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m004", "sender": "Manager – Priya",
        "content": "Please submit the Q1 report to me before the board meeting on Thursday. It is critical that all figures are verified.",
        "timestamp": "2024-04-06 11:00", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m013", "sender": "Finance – Rajan",
        "content": "Your invoice INV-2024-089 is overdue by 14 days. Please arrange payment or contact us to discuss. Failure to respond may result in account suspension.",
        "timestamp": "2024-04-06 09:30", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m014", "sender": "Legal – Compliance Team",
        "content": "Action required: Please complete your annual compliance training by end of this month. Non-completion will be escalated to your department head.",
        "timestamp": "2024-04-06 10:00", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m015", "sender": "CEO – Vikram Nair",
        "content": "I need your strategic input for the all-hands presentation on Monday. Please send me three talking points by tomorrow morning.",
        "timestamp": "2024-04-06 08:45", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m016", "sender": "IT Security",
        "content": "Urgent: We have detected unusual login activity on your account. Please reset your password immediately and confirm via reply.",
        "timestamp": "2024-04-06 07:50", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m017", "sender": "Client – Meridian Ltd",
        "content": "We are reconsidering the contract renewal unless the SLA breach from last quarter is formally addressed. Please arrange a call this week.",
        "timestamp": "2024-04-06 11:30", "ground_truth_type": "formal", "ground_truth_priority": "high",
        "is_archivable": False,
    },

    # ── FORMAL LOW (4) ────────────────────────────────────────────────────────
    {
        "id": "m003", "sender": "Bank Alerts",
        "content": "Your account statement for March 2024 is ready. Log in to view your transactions and download your statement.",
        "timestamp": "2024-04-06 08:30", "ground_truth_type": "formal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m018", "sender": "LinkedIn",
        "content": "You have 14 new connection requests and 3 profile views this week. Log in to manage your network.",
        "timestamp": "2024-04-06 06:00", "ground_truth_type": "formal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m019", "sender": "HR – Payroll",
        "content": "Your payslip for March 2024 has been uploaded to the employee portal. Please log in to download your payslip.",
        "timestamp": "2024-04-06 07:00", "ground_truth_type": "formal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m020", "sender": "IT Helpdesk",
        "content": "Your support ticket #HD-4421 has been resolved and closed. Please rate our service by clicking the link below.",
        "timestamp": "2024-04-06 08:00", "ground_truth_type": "formal", "ground_truth_priority": "low",
        "is_archivable": True,
    },

    # ── EMOTIONAL HIGH (6) ────────────────────────────────────────────────────
    {
        "id": "m005", "sender": "Mom",
        "content": "I haven't heard from you in days. Are you okay? Please call me when you get a chance. I miss you so much and I am worried.",
        "timestamp": "2024-04-06 07:45", "ground_truth_type": "emotional", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m006", "sender": "Best Friend – Arjun",
        "content": "Dude, I'm really struggling right now. Can we talk tonight? Feeling really low and could use your support. Don't want to be alone.",
        "timestamp": "2024-04-06 13:00", "ground_truth_type": "emotional", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m021", "sender": "Sister – Kavya",
        "content": "I had a really rough day and I just need someone to talk to. I keep crying and I don't know why. Can you call me please?",
        "timestamp": "2024-04-06 18:00", "ground_truth_type": "emotional", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m022", "sender": "Dad",
        "content": "Your mother is not feeling well and she keeps asking about you. Please find some time to visit us this weekend. We miss you a lot.",
        "timestamp": "2024-04-06 09:00", "ground_truth_type": "emotional", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m023", "sender": "Partner",
        "content": "I feel like we haven't really talked in weeks. I'm starting to feel disconnected from you. Can we have a proper conversation tonight, just us?",
        "timestamp": "2024-04-06 20:00", "ground_truth_type": "emotional", "ground_truth_priority": "high",
        "is_archivable": False,
    },
    {
        "id": "m024", "sender": "Mentor – Dr. Suresh",
        "content": "I wanted to reach out because I noticed you seemed withdrawn during our last session. I hope you are okay. I am always available if you want to talk.",
        "timestamp": "2024-04-06 16:00", "ground_truth_type": "emotional", "ground_truth_priority": "high",
        "is_archivable": False,
    },

    # ── EMOTIONAL MEDIUM (4) ──────────────────────────────────────────────────
    {
        "id": "m007", "sender": "Colleague – Sneha",
        "content": "I just wanted to say thank you for covering for me last week. It meant so much. You are genuinely the best and I really appreciate you.",
        "timestamp": "2024-04-06 12:00", "ground_truth_type": "emotional", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m008", "sender": "Partner",
        "content": "I feel like we haven't really talked in a while. Can we plan a proper dinner this weekend? I miss spending quality time with you.",
        "timestamp": "2024-04-06 14:00", "ground_truth_type": "emotional", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m025", "sender": "Friend – Meera",
        "content": "Hey, just wanted to check in on you. I know things have been hectic lately. Hope you are taking care of yourself. Thinking of you!",
        "timestamp": "2024-04-06 11:00", "ground_truth_type": "emotional", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m026", "sender": "Cousin – Rahul",
        "content": "Bro, happy birthday! I cannot believe it has already been a year. Hope you have an amazing day. We should catch up soon, it has been too long.",
        "timestamp": "2024-04-06 08:00", "ground_truth_type": "emotional", "ground_truth_priority": "medium",
        "is_archivable": False,
    },

    # ── NORMAL MEDIUM (6) ─────────────────────────────────────────────────────
    {
        "id": "m010", "sender": "Friend – Ravi",
        "content": "Hey, are you free this Saturday for cricket? We need one more player. Game starts at 8 AM at the usual ground.",
        "timestamp": "2024-04-06 15:00", "ground_truth_type": "normal", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m011", "sender": "Flatmate – Deepa",
        "content": "Hey, can you pick up milk on your way home? Also we are out of coffee and bread. I will pay you back tonight.",
        "timestamp": "2024-04-06 16:00", "ground_truth_type": "normal", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m027", "sender": "Gym Buddy – Kiran",
        "content": "Are we still on for the 6 AM session tomorrow? Let me know so I can set my alarm. Also new trainer starts this week.",
        "timestamp": "2024-04-06 19:00", "ground_truth_type": "normal", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m028", "sender": "Study Group – Ananya",
        "content": "Hey, we are meeting at the library tomorrow at 3 PM to revise for the finals. Can you make it? Bring your notes on chapter 7.",
        "timestamp": "2024-04-06 14:30", "ground_truth_type": "normal", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m029", "sender": "Neighbour – Uncle Krishnan",
        "content": "Hello, the parking spot in front of my gate was blocked again this morning. Could you please make sure it is kept clear? Thank you.",
        "timestamp": "2024-04-06 10:00", "ground_truth_type": "normal", "ground_truth_priority": "medium",
        "is_archivable": False,
    },
    {
        "id": "m030", "sender": "Team – Hackathon Group",
        "content": "Guys, we need to finalise our project idea by tonight. Can everyone jump on a quick call at 9 PM? Should take 20 minutes max.",
        "timestamp": "2024-04-06 17:00", "ground_truth_type": "normal", "ground_truth_priority": "medium",
        "is_archivable": False,
    },

    # ── NORMAL LOW (6) ────────────────────────────────────────────────────────
    {
        "id": "m009", "sender": "Zomato",
        "content": "Your order #ZM4920 has been delivered. Hope you enjoy your meal! Rate your experience and earn 50 reward points.",
        "timestamp": "2024-04-06 13:30", "ground_truth_type": "normal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m012", "sender": "Newsletter – TechCrunch",
        "content": "This week in tech: Meta launches new AR glasses, OpenAI releases GPT-5, quantum computing breakthrough and more stories.",
        "timestamp": "2024-04-06 06:00", "ground_truth_type": "normal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m031", "sender": "Swiggy",
        "content": "Flash sale! Get 40% off on your next 3 orders. Use code SAVE40 at checkout. Valid until midnight tonight only.",
        "timestamp": "2024-04-06 12:00", "ground_truth_type": "normal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m032", "sender": "YouTube",
        "content": "3 new videos from channels you subscribed to are waiting. Watch them now while they are trending.",
        "timestamp": "2024-04-06 07:00", "ground_truth_type": "normal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m033", "sender": "Amazon",
        "content": "Your package #AMZ-7812 has been shipped and is expected to arrive by Friday. Track your order in the app.",
        "timestamp": "2024-04-06 09:00", "ground_truth_type": "normal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
    {
        "id": "m034", "sender": "Hotstar",
        "content": "New season of your favourite show is now streaming! Plus 200 new titles added this month. Start watching now.",
        "timestamp": "2024-04-06 08:30", "ground_truth_type": "normal", "ground_truth_priority": "low",
        "is_archivable": True,
    },
]


def _sanitise(msg: Message) -> Dict[str, Any]:
    d = msg.model_dump()
    d.pop("ground_truth_type", None)
    d.pop("ground_truth_priority", None)
    d.pop("is_archivable", None)
    return d


# ──────────────────────────────────────────────
# Task Definitions (5 tasks)
# ──────────────────────────────────────────────

TASK_CONFIGS = {
    "task_easy": {
        "id": "task_easy",
        "description": (
            "TASK (Easy) — Message Classification: "
            "You have 4 messages in your inbox. Classify each one as "
            "'formal', 'emotional', or 'normal'. Use the CLASSIFY action for each message."
        ),
        "type_counts": {"formal": 2, "emotional": 1, "normal": 1},
        "required_actions": ["classify"],
        "max_steps": 8,
    },
    "task_medium": {
        "id": "task_medium",
        "description": (
            "TASK (Medium) — Inbox Triage: "
            "You have 6 mixed messages. First classify each message type, then submit a "
            "priority order (most to least important). Use CLASSIFY for each, then PRIORITIZE."
        ),
        "type_counts": {"formal": 2, "emotional": 2, "normal": 2},
        "required_actions": ["classify", "prioritize"],
        "max_steps": 14,
    },
    "task_hard": {
        "id": "task_hard",
        "description": (
            "TASK (Hard) — Full DM Management: "
            "You have 8 messages of varying types. Classify each, prioritize them all, "
            "then draft a contextually appropriate reply for each message. "
            "Replies must match tone: professional for formal, empathetic for emotional, "
            "casual for normal. Use CLASSIFY, PRIORITIZE, then DRAFT_REPLY for each."
        ),
        "type_counts": {"formal": 3, "emotional": 3, "normal": 2},
        "required_actions": ["classify", "prioritize", "draft_reply"],
        "max_steps": 30,
    },
    "task_urgent_triage": {
        "id": "task_urgent_triage",
        "description": (
            "TASK (Urgent Triage) — Crisis Inbox: "
            "You have 6 messages but 3 of them require IMMEDIATE action (high priority). "
            "Classify each message, then prioritize with HIGH-priority messages strictly "
            "ranked first. Missing a high-priority item will be penalised. "
            "Use CLASSIFY then PRIORITIZE."
        ),
        "type_counts": {"formal": 2, "emotional": 2, "normal": 2},
        "required_actions": ["classify", "prioritize"],
        "max_steps": 14,
        "urgent_bias": True,   # forces more HIGH-priority messages
    },
    "task_selective_archive": {
        "id": "task_selective_archive",
        "description": (
            "TASK (Selective Archive) — Inbox Cleanup: "
            "You have 8 messages. Classify each one, then ARCHIVE messages that are "
            "low-priority notifications or newsletters. Do NOT archive important messages "
            "or you will lose points. Use CLASSIFY then ARCHIVE for appropriate messages."
        ),
        "type_counts": {"formal": 2, "emotional": 2, "normal": 4},
        "required_actions": ["classify", "archive"],
        "max_steps": 20,
    },
}


# ──────────────────────────────────────────────
# Expanded Keyword Banks
# ──────────────────────────────────────────────

FORMAL_KEYWORDS = [
    # Greetings / closings
    "dear", "kind regards", "sincerely", "yours faithfully", "best regards",
    "to whom it may concern", "respected",
    # Request language
    "please", "kindly", "please find attached", "as per", "pursuant to",
    "with reference to", "in reference to", "further to", "as discussed",
    "i am writing to", "i would like to", "i wish to", "please note",
    "please be advised", "please confirm", "please review", "please action",
    "please respond", "please ensure", "please arrange", "please let me know",
    # Action / urgency
    "urgent", "mandatory", "required", "deadline", "by friday", "by end of day",
    "at the earliest", "at your earliest convenience", "immediately", "as soon as possible",
    "critical", "action required", "time-sensitive", "overdue", "escalate",
    # Business vocabulary
    "invoice", "nda", "contract", "agreement", "proposal", "report", "statement",
    "quarterly", "q1", "q2", "q3", "q4", "board meeting", "all-hands", "compliance",
    "policy", "procedure", "protocol", "sla", "kpi", "roi", "timeline", "milestone",
    "deliverable", "stakeholder", "client", "vendor", "procurement", "budget",
    "payroll", "payslip", "account", "transaction", "payment", "subscription",
    # Formal structures
    "attached", "enclosed", "regarding", "subject:", "re:", "fyi",
    "acknowledge", "confirm receipt", "noted", "duly noted",
]

EMOTIONAL_KEYWORDS = [
    # Concern / worry
    "miss you", "i miss", "are you okay", "worried about", "haven't heard",
    "hoping you are well", "thinking of you", "checking in on you", "how are you holding up",
    "it has been a while", "haven't really talked", "feel disconnected",
    # Distress signals
    "struggling", "feeling low", "really low", "having a rough", "rough day",
    "rough week", "breaking down", "keep crying", "don't know why", "overwhelmed",
    "exhausted", "burned out", "can't cope", "need support", "could use your support",
    "don't want to be alone", "feeling lonely", "need someone to talk to",
    "really hard right now", "going through a lot",
    # Warmth / affection
    "love you", "miss you so much", "so proud of you", "you're the best",
    "you mean so much", "genuinely the best", "means a lot", "really appreciate",
    "appreciate everything", "thank you for being there", "always been there for me",
    "birthday", "happy birthday", "celebrate", "glad you're in my life",
    # Requests for connection
    "can we talk", "can you call me", "please call", "please visit",
    "let's catch up", "quality time", "plan a dinner", "spend time together",
    "just us", "proper conversation", "i need you",
    # Emotional support language
    "here for you", "i care", "always here", "thinking of you", "take care",
    "take care of yourself", "you're not alone", "got your back", "lean on me",
    "support you", "understand how you feel", "know how hard", "empathise",
]

NORMAL_KEYWORDS = [
    # Casual greetings
    "hey", "hi there", "yo", "sup", "what's up", "howdy",
    # Plans / coordination
    "are you free", "free this weekend", "free tomorrow", "free tonight",
    "are we still on", "still on for", "let me know", "let me know if",
    "confirm", "heads up", "fyi", "just a reminder", "don't forget",
    "can you", "could you", "would you mind", "do you want to",
    # Casual acknowledgement
    "sure", "sounds good", "sounds great", "no worries", "no problem",
    "will do", "got it", "noted", "ok cool", "yeah", "yep", "totally",
    "makes sense", "works for me", "absolutely", "definitely",
    # Shopping / delivery / services
    "order", "delivered", "shipped", "package", "track", "rate your experience",
    "reward points", "discount", "sale", "offer", "promo code", "deal",
    "flash sale", "limited time", "expires tonight",
    # Entertainment / social
    "cricket", "game", "match", "watch", "streaming", "show", "movie",
    "new season", "trending", "playlist", "gym", "workout", "session",
    "library", "study", "notes", "meeting", "quick call", "call tonight",
    # Everyday requests
    "pick up", "milk", "coffee", "groceries", "on your way", "pay you back",
    "parking", "blocked", "keep clear",
    # Newsletter / notification markers
    "newsletter", "this week in", "top stories", "read more", "click here",
    "log in", "view your", "manage your", "new titles", "new videos",
    "subscribed channels", "unsubscribe",
]

# Negation words that reduce confidence in keyword match
NEGATION_WORDS = ["not", "never", "don't", "doesn't", "didn't", "won't",
                  "no longer", "without", "lack", "absent", "except"]


def _sanitise(msg: Message) -> Dict[str, Any]:
    d = msg.model_dump()
    d.pop("ground_truth_type", None)
    d.pop("ground_truth_priority", None)
    d.pop("is_archivable", None)
    return d


# ──────────────────────────────────────────────
# The Environment
# ──────────────────────────────────────────────

class DMManagerEnv:
    """OpenEnv-compliant DM Manager environment v2."""

    metadata = {
        "name": "dm-manager",
        "version": "2.0.0",
        "description": "Real-world DM inbox management: classify, prioritise, draft replies, and archive.",
    }

    def __init__(self, task_id: str = "task_easy", seed: int = 42):
        self.task_id   = task_id
        self.seed      = seed
        self._rng      = random.Random(seed)
        self._messages: Dict[str, Message] = {}
        self._step_count       = 0
        self._done             = False
        self._episode_rewards: List[float] = []
        self._action_log: List[Dict]       = []
        self._task_cfg  = TASK_CONFIGS[task_id]
        self._pending   = list(self._task_cfg["required_actions"])
        self._last_feedback    = "Episode started."
        self._archived_ids: List[str] = []

    # ── OpenEnv interface ──────────────────────

    def reset(self) -> Observation:
        cfg      = self._task_cfg
        msg_pool = {m["id"]: m for m in SAMPLE_MESSAGES}

        # Build type pools
        by_type: Dict[str, List[Dict]] = {"formal": [], "emotional": [], "normal": []}
        for m in SAMPLE_MESSAGES:
            by_type[m["ground_truth_type"]].append(m)

        # FIX: shuffle each pool with the seed so every different seed
        # produces a genuinely different message set
        for pool in by_type.values():
            self._rng.shuffle(pool)

        # urgent_bias: prefer HIGH-priority messages for urgent triage task
        urgent_bias = cfg.get("urgent_bias", False)

        selected: List[Dict] = []
        for msg_type, count in cfg["type_counts"].items():
            pool = by_type[msg_type]
            if urgent_bias:
                # Sort pool so HIGH-priority messages come first
                pool = sorted(pool, key=lambda m: 0 if m["ground_truth_priority"] == "high" else 1)
            chosen = pool[:count]
            selected.extend(chosen)

        self._rng.shuffle(selected)

        self._messages = {}
        for raw in selected:
            self._messages[raw["id"]] = Message(
                id=raw["id"],
                sender=raw["sender"],
                content=raw["content"],
                timestamp=raw["timestamp"],
                ground_truth_type=MessageType(raw["ground_truth_type"]),
                ground_truth_priority=Priority(raw["ground_truth_priority"]),
                is_archivable=raw.get("is_archivable", False),
            )

        self._step_count      = 0
        self._done            = False
        self._episode_rewards = []
        self._action_log      = []
        self._pending         = list(cfg["required_actions"])
        self._archived_ids    = []
        self._last_feedback   = "Episode started. Read the task description carefully."
        return self._make_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        self._step_count += 1
        reward, feedback  = self._process_action(action)
        self._episode_rewards.append(reward.value)
        self._last_feedback = feedback
        self._action_log.append({
            "step":   self._step_count,
            "action": action.model_dump(),
            "reward": reward.value,
        })

        if self._step_count >= self._task_cfg["max_steps"]:
            self._done = True
            feedback  += " [MAX STEPS REACHED]"

        obs = self._make_observation()
        info = {
            "step":               self._step_count,
            "cumulative_reward":  sum(self._episode_rewards),
            "pending_actions":    self._pending,
            "action_log":         self._action_log,
        }
        return obs, reward, self._done, info

    def state(self) -> Dict[str, Any]:
        return {
            "task_id":           self.task_id,
            "step_count":        self._step_count,
            "done":              self._done,
            "messages":          {mid: m.model_dump() for mid, m in self._messages.items()},
            "pending_actions":   self._pending,
            "episode_rewards":   self._episode_rewards,
            "cumulative_reward": sum(self._episode_rewards),
        }

    # ── Internal helpers ───────────────────────

    def _make_observation(self) -> Observation:
        cfg = self._task_cfg
        return Observation(
            task_id=self.task_id,
            task_description=cfg["description"],
            messages=[_sanitise(m) for m in self._messages.values()
                      if m.id not in self._archived_ids],
            current_step=self._step_count,
            max_steps=cfg["max_steps"],
            inbox_size=len(self._messages),
            unread_count=sum(1 for m in self._messages.values() if not m.is_read),
            pending_actions=list(self._pending),
            last_action_feedback=self._last_feedback,
        )

    def _process_action(self, action: Action) -> Tuple[Reward, str]:
        atype = action.action_type

        # ── CLASSIFY ──────────────────────────────────────────────────────────
        if atype == ActionType.CLASSIFY:
            if action.message_id not in self._messages:
                return Reward(value=-0.1, reason="Unknown message ID"), "Unknown message ID."
            msg = self._messages[action.message_id]
            if action.classification is None:
                return Reward(value=-0.05, reason="No classification given"), "Provide a classification."

            correct = action.classification == msg.ground_truth_type
            msg.message_type = action.classification
            msg.is_read = True

            # Partial credit: penalise by distance between types
            if correct:
                score = 0.3
            else:
                # formal↔emotional is worse than normal↔either
                wrong_pair = {action.classification.value, msg.ground_truth_type.value}
                score = -0.15 if wrong_pair == {"formal", "emotional"} else -0.1

            bd = {"classification_correct": 0.3 if correct else 0.0,
                  "classification_penalty": score if not correct else 0.0}

            all_classified = all(m.message_type is not None for m in self._messages.values())
            if all_classified and "classify" in self._pending:
                self._pending.remove("classify")
                if not self._pending:
                    self._done = True

            fb = (f"{'✓ Correct' if correct else '✗ Wrong'} — "
                  f"{msg.sender!r} is '{msg.ground_truth_type.value}'.")
            return Reward(value=round(score, 3), breakdown=bd, reason=fb), fb

        # ── PRIORITIZE ────────────────────────────────────────────────────────
        if atype == ActionType.PRIORITIZE:
            if "classify" in self._pending:
                return Reward(value=-0.1, reason="Classify all messages first"), \
                       "Classify all messages before prioritising."
            if not action.priority_order:
                return Reward(value=-0.05, reason="No priority order"), "Provide a priority_order list."

            priority_rank = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
            gt_sorted = sorted(
                self._messages.values(),
                key=lambda m: priority_rank[m.ground_truth_priority],
                reverse=True,
            )
            gt_order    = [m.id for m in gt_sorted]
            agent_order = action.priority_order

            base_score  = _rank_overlap_score(agent_order, gt_order)

            # Bonus: top-3 overlap (agent got the most critical messages first)
            top3_bonus = 0.0
            n_top = min(3, len(gt_order))
            gt_top = set(gt_order[:n_top])
            ag_top = set(agent_order[:n_top])
            top3_overlap = len(gt_top & ag_top) / max(n_top, 1)
            if top3_overlap >= 1.0:
                top3_bonus = 0.15
            elif top3_overlap >= 0.66:
                top3_bonus = 0.08

            # urgent_bias task: extra penalty if HIGH messages not at front
            urgent_penalty = 0.0
            if self._task_cfg.get("urgent_bias"):
                high_ids = {m.id for m in self._messages.values()
                            if m.ground_truth_priority == Priority.HIGH}
                first_n  = set(agent_order[:len(high_ids)])
                if not high_ids.issubset(first_n):
                    urgent_penalty = -0.2

            total = round(max(-1.0, min(1.0, base_score * 0.4 + top3_bonus + urgent_penalty)), 3)

            if "prioritize" in self._pending:
                self._pending.remove("prioritize")
                if not self._pending:
                    self._done = True

            fb = f"Priority score: {base_score:.2f} (top-3 bonus: {top3_bonus:.2f}). Ideal: {gt_order}."
            return Reward(value=total, breakdown={"priority_overlap": base_score,
                          "top3_bonus": top3_bonus, "urgent_penalty": urgent_penalty},
                          reason=fb), fb

        # ── DRAFT_REPLY ────────────────────────────────────────────────────────
        if atype == ActionType.DRAFT_REPLY:
            if action.message_id not in self._messages:
                return Reward(value=-0.1, reason="Unknown message ID"), "Unknown message ID."
            if not action.draft_text or len(action.draft_text.strip()) < 10:
                return Reward(value=-0.05, reason="Draft too short"), "Draft reply is too short."

            msg   = self._messages[action.message_id]
            score = _score_draft(action.draft_text, msg)
            msg.draft_reply = action.draft_text

            all_drafted = all(m.draft_reply is not None for m in self._messages.values())
            if all_drafted and "draft_reply" in self._pending:
                self._pending.remove("draft_reply")
                if not self._pending:
                    self._done = True

            fb = f"Draft quality: {score:.2f} for message from {msg.sender}."
            return Reward(value=round(score * 0.3, 3),
                          breakdown={"draft_quality": score}, reason=fb), fb

        # ── MARK_READ ──────────────────────────────────────────────────────────
        if atype == ActionType.MARK_READ:
            if action.message_id and action.message_id in self._messages:
                self._messages[action.message_id].is_read = True
                return Reward(value=0.01, reason="Marked as read"), "Message marked as read."
            return Reward(value=0.0, reason="Nothing done"), "No effect."

        # ── ARCHIVE ────────────────────────────────────────────────────────────
        if atype == ActionType.ARCHIVE:
            msg = self._messages.get(action.message_id)
            if not msg:
                return Reward(value=-0.05, reason="Unknown ID"), "Unknown message."

            if msg.is_archivable and msg.ground_truth_priority == Priority.LOW:
                self._archived_ids.append(msg.id)
                # Check if archive task is complete
                all_archivable = {m.id for m in self._messages.values() if m.is_archivable}
                if all_archivable.issubset(set(self._archived_ids)):
                    if "archive" in self._pending:
                        self._pending.remove("archive")
                        if not self._pending:
                            self._done = True
                return Reward(value=0.10, reason="Correctly archived low-priority"), \
                       "Good — low-priority message archived."

            if msg.ground_truth_priority == Priority.HIGH:
                return Reward(value=-0.30, reason="Archived critical message!"), \
                       "Heavy penalty — you archived an important message!"

            if msg.ground_truth_priority == Priority.MEDIUM:
                return Reward(value=-0.15, reason="Archived medium-priority message"), \
                       "Penalty — medium-priority message should not be archived."

            # low priority but not is_archivable (e.g. personal low)
            return Reward(value=0.02, reason="Archived low-priority (minor benefit)"), \
                   "Archived a low-priority message."

        return Reward(value=0.0, reason="No-op"), "Action had no effect."


# ──────────────────────────────────────────────
# Scoring Helpers
# ──────────────────────────────────────────────

def _rank_overlap_score(agent: List[str], ideal: List[str]) -> float:
    """Simplified Spearman rank correlation mapped to [0, 1]."""
    if not agent or not ideal:
        return 0.0
    ideal_rank = {mid: i for i, mid in enumerate(ideal)}
    agent_rank = {mid: i for i, mid in enumerate(agent)}
    shared = [m for m in agent if m in ideal_rank]
    if not shared:
        return 0.0
    n    = len(shared)
    d_sq = sum((ideal_rank[m] - agent_rank[m]) ** 2 for m in shared)
    rho  = 1 - (6 * d_sq) / max(n * (n ** 2 - 1), 1)
    return max(0.0, min(1.0, (rho + 1) / 2))


def _score_draft(draft: str, msg: Message) -> float:
    """
    Improved heuristic draft quality scorer (0–1).
    Checks: length, tone keywords, personalisation, negation handling,
    urgency language for formal, and copy-paste penalty.
    """
    d   = draft.lower()
    wds = draft.split()
    score = 0.0

    # ── Length tiers (0–0.20) ──────────────────────────────────────────────
    wc = len(wds)
    if wc >= 20:
        score += 0.20
    elif wc >= 12:
        score += 0.12
    elif wc >= 6:
        score += 0.06

    # ── Tone match (0–0.50) ────────────────────────────────────────────────
    gt = msg.ground_truth_type

    if gt == MessageType.FORMAL:
        hits = sum(1 for kw in FORMAL_KEYWORDS if kw in d)
        score += min(0.50, hits * 0.10)
        # Penalise casual language in formal reply
        casual_hits = sum(1 for kw in ["hey", "bro", "dude", "lol", "haha", "yo"] if kw in d)
        score -= casual_hits * 0.10
        # Bonus: urgency acknowledgement for high-priority formal messages
        if msg.ground_truth_priority == Priority.HIGH:
            urgency_hits = sum(1 for kw in ["immediately", "promptly", "right away",
                                             "as a matter of urgency", "without delay",
                                             "at the earliest", "will action"] if kw in d)
            score += min(0.10, urgency_hits * 0.05)

    elif gt == MessageType.EMOTIONAL:
        hits = sum(1 for kw in EMOTIONAL_KEYWORDS if kw in d)
        score += min(0.50, hits * 0.10)
        # Penalise robotic formal tone in emotional reply
        robot_hits = sum(1 for kw in ["dear sir", "to whom it may concern",
                                       "i am writing", "pursuant to"] if kw in d)
        score -= robot_hits * 0.10

    elif gt == MessageType.NORMAL:
        hits = sum(1 for kw in NORMAL_KEYWORDS if kw in d)
        score += min(0.40, hits * 0.10)

    # ── Personalisation: sender first name present (0.10) ─────────────────
    sender_first = msg.sender.split("–")[-1].strip().split()[0].lower()
    if sender_first in d:
        score += 0.10

    # ── Negation check: catches "I don't care" style replies (−0.15) ──────
    neg_hits = sum(1 for neg in NEGATION_WORDS if neg in d)
    if neg_hits >= 2:
        score -= 0.15

    # ── Copy-paste penalty: too many words lifted from original (−0.20) ───
    overlap = len(set(d.split()) & set(msg.content.lower().split()))
    if overlap / max(wc, 1) > 0.55:
        score -= 0.20

    return round(max(0.0, min(1.0, score)), 4)
