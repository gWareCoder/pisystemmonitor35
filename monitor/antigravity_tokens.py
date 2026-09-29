"""Antigravity token usage and quota monitor."""
import os
import json
import time
import sqlite3
import base64
from typing import Dict, Any

ANTIGRAVITY_BRAIN = os.path.expanduser("~/.gemini/antigravity/brain")
VSCDB_PATH = os.path.expanduser("~/.config/Antigravity/User/globalStorage/state.vscdb")


def estimate_tokens_from_text(text: str) -> int:
    """Estimate token count for Gemini models (~3.8 characters per token)."""
    if not text:
        return 0
    return int(len(text) / 3.8)


def get_user_plan_tier() -> str:
    """Retrieve active plan tier from state.vscdb."""
    if not os.path.exists(VSCDB_PATH):
        return "Google AI Pro"

    try:
        conn = sqlite3.connect(VSCDB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.userStatus'")
        row = c.fetchone()
        conn.close()

        if row and row[0]:
            raw_bytes = base64.b64decode(row[0])
            if b"g1-ultra-tier" in raw_bytes or b"Google AI Ultra" in raw_bytes:
                return "Google AI Ultra"
            if b"g1-pro-tier" in raw_bytes or b"Google AI Pro" in raw_bytes:
                return "Google AI Pro"
    except Exception:
        pass

    return "Google AI Pro"


def get_token_metrics(plan_budget: int = 500000, rolling_window_hours: float = 5.0) -> Dict[str, Any]:
    """
    Calculate tokens used in active session, rolling window, total tokens,
    and remaining tokens for the current plan budget.
    """
    session_tokens = 0
    rolling_tokens = 0
    total_tokens = 0
    active_conv_id = None
    plan_tier = get_user_plan_tier()

    now = time.time()
    cutoff_time = now - (rolling_window_hours * 3600.0)

    if os.path.exists(ANTIGRAVITY_BRAIN):
        # Find latest modified conversation directory as the active session
        conv_dirs = []
        try:
            for item in os.listdir(ANTIGRAVITY_BRAIN):
                item_path = os.path.join(ANTIGRAVITY_BRAIN, item)
                if os.path.isdir(item_path):
                    conv_dirs.append((item_path, os.path.getmtime(item_path), item))
        except Exception:
            pass

        conv_dirs.sort(key=lambda x: x[1], reverse=True)
        if conv_dirs:
            active_conv_id = conv_dirs[0][2]

        # Scan transcripts
        for item_path, mtime, conv_id in conv_dirs:
            t_full = os.path.join(item_path, ".system_generated", "logs", "transcript_full.jsonl")
            t_compact = os.path.join(item_path, ".system_generated", "logs", "transcript.jsonl")
            target_log = t_full if os.path.exists(t_full) else t_compact

            if not os.path.exists(target_log):
                continue

            try:
                with open(target_log, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            step = json.loads(line)
                            step_tokens = 0
                            # Extract step creation timestamp if available
                            step_time = mtime
                            if "created_at" in step and step["created_at"]:
                                # ISO timestamp e.g. 2026-09-29T20:26:15Z
                                pass

                            if "content" in step and step["content"]:
                                step_tokens += estimate_tokens_from_text(step["content"])
                            if "thinking" in step and step["thinking"]:
                                step_tokens += estimate_tokens_from_text(step["thinking"])

                            total_tokens += step_tokens

                            if conv_id == active_conv_id:
                                session_tokens += step_tokens

                            # Check rolling window
                            if mtime >= cutoff_time:
                                rolling_tokens += step_tokens
                        except Exception:
                            continue
            except Exception:
                continue

    # Ensure rolling_tokens includes at least the session tokens
    rolling_tokens = max(rolling_tokens, session_tokens)

    # Compute remaining tokens against plan budget
    remaining_tokens = max(0, plan_budget - rolling_tokens)
    pct_remaining = round((remaining_tokens / plan_budget) * 100.0, 1) if plan_budget > 0 else 0.0

    return {
        "plan_tier": plan_tier,
        "plan_budget": plan_budget,
        "session_tokens": session_tokens,
        "rolling_tokens": rolling_tokens,
        "total_tokens": total_tokens,
        "remaining_tokens": remaining_tokens,
        "percent_remaining": pct_remaining,
        "active_conversation": active_conv_id,
        "rolling_hours": rolling_window_hours,
    }


if __name__ == "__main__":
    metrics = get_token_metrics()
    print("Token Metrics:")
    print(f"  Plan: {metrics['plan_tier']}")
    print(f"  Session Used: {metrics['session_tokens']:,}")
    print(f"  Rolling {metrics['rolling_hours']}h Used: {metrics['rolling_tokens']:,}")
    print(f"  Budget: {metrics['plan_budget']:,}")
    print(f"  Remaining: {metrics['remaining_tokens']:,} ({metrics['percent_remaining']}%)")
    print(f"  Total Historical: {metrics['total_tokens']:,}")
