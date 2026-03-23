from __future__ import annotations

import json
import re
from typing import Any

from core.memory import entries as memory_entries
from core.memory import learning as memory_learning
from core.memory.files import (
    MAX_CONVERSATION_LOG_BYTES as _MAX_CONVERSATION_LOG_BYTES,
)
from core.memory.files import (
    conversation_log_path,
    memory_entries_path,
    memory_path,
    operator_dense_profile_path,
    session_summaries_path,
    user_heuristics_path,
)
from core.memory.files import (
    ensure_memory_files as _ensure_memory_files,
)
from core.memory.files import (
    trim_jsonl_file as _trim_jsonl_file,
)
from core.memory.files import (
    utcnow as _utcnow,
)
from core.memory.policies import (
    describe_session_memory_policy,
    session_memory_policy,
    set_session_memory_policy,
)
from core.memory.policies import (
    ensure_session_policy_table as _ensure_session_policy_table,
)
from core.memory.policies import (
    parse_session_scope_command as _parse_session_scope_command,
)
from core.privacy_guard import share_scope_label

add_memory_fact = memory_entries.add_memory_fact
forget_memory = memory_entries.forget_memory
load_memory_excerpt = memory_entries.load_memory_excerpt
recent_conversation_events = memory_entries.recent_conversation_events
search_relevant_memory = memory_entries.search_relevant_memory
search_session_summaries = memory_entries.search_session_summaries
search_user_heuristics = memory_entries.search_user_heuristics
summarize_memory = memory_entries.summarize_memory
load_operator_dense_profile = memory_learning.load_operator_dense_profile
refresh_operator_dense_profile = memory_learning.refresh_operator_dense_profile

_keyword_tokens = memory_entries.keyword_tokens_filtered
_sanitize_fact = memory_entries.sanitize_fact
_trim_text = memory_entries.trim_text
_normalized_history = memory_learning.normalized_history
_record_assistant_dialogue_turn = memory_learning.record_assistant_dialogue_turn
_auto_capture_memory = memory_learning.auto_capture_memory
_update_user_heuristics = memory_learning.update_user_heuristics
_detect_implicit_feedback = memory_learning.detect_implicit_feedback
_update_session_summary = memory_learning.update_session_summary

__all__ = [
    "add_memory_fact",
    "append_conversation_event",
    "conversation_log_path",
    "describe_session_memory_policy",
    "ensure_memory_files",
    "forget_memory",
    "load_memory_excerpt",
    "load_operator_dense_profile",
    "maybe_handle_memory_command",
    "memory_entries_path",
    "memory_path",
    "operator_dense_profile_path",
    "recent_conversation_events",
    "refresh_operator_dense_profile",
    "search_relevant_memory",
    "search_session_summaries",
    "search_user_heuristics",
    "session_memory_policy",
    "session_summaries_path",
    "set_session_memory_policy",
    "summarize_memory",
    "user_heuristics_path",
]

_REMEMBER_RE = re.compile(r"^(?:remember(?: that)?|note(?: that)?|store(?: this)?)\s+(.+)$", re.IGNORECASE)
_FORGET_RE = re.compile(r"^(?:forget|erase)\s+(.+)$", re.IGNORECASE)


def ensure_memory_files() -> None:
    _ensure_memory_files(ensure_policy_table=_ensure_session_policy_table)


def append_conversation_event(
    *,
    session_id: str,
    user_input: str,
    assistant_output: str,
    source_context: dict[str, Any] | None = None,
) -> None:
    ensure_memory_files()
    history = _normalized_history((source_context or {}).get("conversation_history"))
    policy = session_memory_policy(session_id)
    assistant_text = str(assistant_output or "").strip()
    payload = {
        "ts": _utcnow(),
        "session_id": session_id,
        "surface": str((source_context or {}).get("surface", "")),
        "platform": str((source_context or {}).get("platform", "")),
        "user": str(user_input or "")[:4000],
        "assistant": assistant_text[:8000],
        "history_message_count": len(history),
        "share_scope": policy["share_scope"],
        "realm_label": policy.get("realm_label") or share_scope_label(policy["share_scope"]),
        "restricted_terms": list(policy.get("restricted_terms") or []),
    }
    path = conversation_log_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    _trim_jsonl_file(path, max_bytes=_MAX_CONVERSATION_LOG_BYTES)
    _record_assistant_dialogue_turn(
        session_id=session_id,
        assistant_output=assistant_text,
    )
    _auto_capture_memory(session_id=session_id, user_input=user_input)
    _update_user_heuristics(session_id=session_id, user_input=user_input)
    _detect_implicit_feedback(
        session_id=session_id,
        user_input=user_input,
        assistant_output=assistant_output,
    )
    _update_session_summary(
        session_id=session_id,
        user_input=user_input,
        assistant_output=assistant_output,
    )
    refresh_operator_dense_profile(session_id=session_id)


def maybe_handle_memory_command(user_text: str, *, session_id: str | None = None) -> tuple[bool, str]:
    text = str(user_text or "").strip()
    if not text:
        return False, ""
    lowered = text.lower()
    scope_command = _parse_session_scope_command(text)
    if scope_command is not None:
        action = str(scope_command.get("action") or "")
        if action == "show":
            return True, describe_session_memory_policy(session_id)
        if not session_id:
            return True, "I need an active session before I can change the share scope."
        result = set_session_memory_policy(
            str(session_id),
            share_scope=str(scope_command.get("share_scope") or "local_only"),
            restricted_terms=list(scope_command.get("restricted_terms") or []),
        )
        scope = result["share_scope"]
        if scope == "hive_mind":
            label = "SHARED PACK"
            scope_note = "Generalized learnings from this session can sync to the mesh after secret screening. Raw chat remains in the PRIVATE VAULT."
        elif scope == "public_knowledge":
            label = "HIVE/PUBLIC COMMONS"
            scope_note = "Generalized learnings from this session can be published as public claims after secret screening. Raw chat remains in the PRIVATE VAULT."
        else:
            label = "PRIVATE VAULT"
            scope_note = "Everything from this session stays on this node unless you reclassify it."
        protected = ""
        if result.get("restricted_terms"):
            protected = " Protected exceptions: " + ", ".join(list(result["restricted_terms"])[:6]) + "."
        stats = (
            f" Existing session shards updated: {int(result.get('updated_shards') or 0)}"
            f", shared now: {int(result.get('registered_shards') or 0)}"
            f", forced local by privacy guard: {int(result.get('blocked_shards') or 0)}."
        )
        return True, f"Session scope set to {label}. {scope_note}{protected}{stats}"
    if lowered in {"/memory", "what do you remember", "show memory"}:
        summary = summarize_memory(limit=8)
        if not summary:
            return True, "Memory is currently empty. Tell me what to remember."
        return True, "What I remember:\n" + "\n".join(f"- {line}" for line in summary)

    remember = _REMEMBER_RE.match(text)
    if remember:
        fact = remember.group(1).strip()
        if len(fact) < 3:
            return True, "Memory update skipped: fact is too short."
        added = add_memory_fact(fact)
        if added:
            return True, "Locked in. I’ll remember that."
        return True, "I already had that in memory."

    forget = _FORGET_RE.match(text)
    if forget:
        token = forget.group(1).strip()
        if len(token) < 2:
            return True, "Forget command skipped: provide a clearer keyword."
        removed = forget_memory(token)
        return True, f"Forget applied. Removed {removed} memory entr{'y' if removed == 1 else 'ies'}."

    return False, ""
