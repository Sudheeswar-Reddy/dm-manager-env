"""
Task Graders for DM Manager
============================
Each grader takes the final environment state and returns a score in (0.0, 1.0).
Scores are strictly exclusive of 0.0 and 1.0 per hackathon validator requirements.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple


def _strict(score: float) -> float:
    """Clamp score to strictly open interval (0.0, 1.0)."""
    return round(min(max(score, 0.001), 0.999), 4)


def grade_task_easy(state: Dict[str, Any]) -> Tuple[float, str]:
    """
    Task Easy: Message Classification
    Score = fraction of messages correctly classified.
    """
    messages = state.get("messages", {})
    if not messages:
        return 0.001, "No messages found in state."

    correct = 0
    total = 0
    details = []

    for mid, msg in messages.items():
        gt = msg.get("ground_truth_type")
        agent = msg.get("message_type")
        total += 1
        if agent is None:
            details.append(f"{mid}: not classified")
        elif agent == gt:
            correct += 1
            details.append(f"{mid}: ✓ ({gt})")
        else:
            details.append(f"{mid}: ✗ agent={agent}, gt={gt}")

    score = correct / total if total > 0 else 0.0

    # Bonus: task completed without exhausting steps
    max_steps = 6
    steps_used = state.get("step_count", max_steps)
    efficiency_bonus = max(0.0, 0.1 * (1 - steps_used / max_steps))
    score = min(1.0, score + efficiency_bonus)

    report = f"Classification score: {correct}/{total} correct. {'; '.join(details)}."
    return _strict(score), report


def grade_task_medium(state: Dict[str, Any]) -> Tuple[float, str]:
    """
    Task Medium: Classification + Prioritization
    50% weight on classification, 50% on priority ordering.
    """
    messages = state.get("messages", {})
    if not messages:
        return 0.001, "No messages found."

    # Part 1 — classification
    correct_clf = sum(
        1 for m in messages.values()
        if m.get("message_type") == m.get("ground_truth_type")
    )
    clf_score = correct_clf / len(messages)

    # Part 2 — priority (check if high-priority msgs are in the agent's top positions)
    priority_rank = {"high": 3, "medium": 2, "low": 1}
    gt_sorted = sorted(
        messages.items(),
        key=lambda x: priority_rank.get(x[1].get("ground_truth_priority", "low"), 1),
        reverse=True,
    )
    gt_order = [mid for mid, _ in gt_sorted]

    from environment import _rank_overlap_score

    # Derive agent's implied order from their assigned priorities
    agent_priority_order = sorted(
        messages.keys(),
        key=lambda mid: priority_rank.get(
            messages[mid].get("priority") or "low", 1
        ),
        reverse=True,
    )
    priority_score = _rank_overlap_score(agent_priority_order, gt_order)

    # Penalise incomplete actions
    any_unclassified = any(m.get("message_type") is None for m in messages.values())
    if any_unclassified:
        clf_score *= 0.5  # penalty for incomplete classification

    combined = 0.5 * clf_score + 0.5 * priority_score
    report = (
        f"Classification: {clf_score:.2f}, Priority ordering: {priority_score:.2f}, "
        f"Combined: {combined:.2f}. GT order: {gt_order}."
    )
    return _strict(combined), report


def grade_task_hard(state: Dict[str, Any]) -> Tuple[float, str]:
    """
    Task Hard: Classification + Priority + Draft Quality
    Weights: 30% clf, 30% priority, 40% drafts.
    """
    messages = state.get("messages", {})
    if not messages:
        return 0.001, "No messages found."

    from environment import _rank_overlap_score, _score_draft, Message, MessageType, Priority

    # Part 1 — classification
    correct_clf = sum(
        1 for m in messages.values()
        if m.get("message_type") == m.get("ground_truth_type")
    )
    clf_score = correct_clf / len(messages)

    # Part 2 — priority ordering
    priority_rank_map = {"high": 3, "medium": 2, "low": 1}
    gt_sorted = sorted(
        messages.keys(),
        key=lambda mid: priority_rank_map.get(
            messages[mid].get("ground_truth_priority", "low"), 1
        ),
        reverse=True,
    )
    agent_order = sorted(
        messages.keys(),
        key=lambda mid: priority_rank_map.get(
            messages[mid].get("priority") or "low", 1
        ),
        reverse=True,
    )
    priority_score = _rank_overlap_score(agent_order, gt_sorted)

    # Part 3 — draft quality
    draft_scores = []
    for mid, m_dict in messages.items():
        draft = m_dict.get("draft_reply")
        if draft is None:
            draft_scores.append(0.0)
            continue
        # Reconstruct Message object for scoring
        msg_obj = Message(
            id=mid,
            sender=m_dict.get("sender", ""),
            content=m_dict.get("content", ""),
            timestamp=m_dict.get("timestamp", ""),
            ground_truth_type=m_dict.get("ground_truth_type"),
            ground_truth_priority=m_dict.get("ground_truth_priority"),
        )
        draft_scores.append(_score_draft(draft, msg_obj))
    draft_score = sum(draft_scores) / len(draft_scores) if draft_scores else 0.0

    # Combine
    combined = 0.30 * clf_score + 0.30 * priority_score + 0.40 * draft_score

    # Bonus: all drafts submitted
    all_drafted = all(m.get("draft_reply") for m in messages.values())
    if all_drafted:
        combined = min(1.0, combined + 0.05)

    report = (
        f"Classification: {clf_score:.2f}, Priority: {priority_score:.2f}, "
        f"Draft quality: {draft_score:.2f} (individual: {[round(s,2) for s in draft_scores]}), "
        f"Final: {combined:.2f}."
    )
    return _strict(combined), report


# ──────────────────────────────────────────────
# Grader registry
# ──────────────────────────────────────────────

GRADERS = {
    "task_easy": grade_task_easy,
    "task_medium": grade_task_medium,
    "task_hard": grade_task_hard,
}


def run_grader(task_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the appropriate grader and return result dict."""
    if task_id not in GRADERS:
        raise ValueError(f"Unknown task_id: {task_id}")
    score, report = GRADERS[task_id](state)
    return {
        "task_id": task_id,
        "score": score,
        "report": report,
        "passed": score >= 0.5,
    }
