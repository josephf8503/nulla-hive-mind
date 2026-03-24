from __future__ import annotations

from typing import Any

from core.hive_activity_tracker import clear_hive_interaction_state, session_hive_state, set_hive_interaction_state


def has_pending_hive_create_confirmation(
    agent: Any,
    *,
    session_id: str,
    hive_state: dict[str, Any],
    source_context: dict[str, object] | None,
) -> bool:
    pending = agent._hive_create_pending.get(session_id)
    if pending and str(pending.get("title") or "").strip():
        return True

    payload = dict(hive_state.get("interaction_payload") or {})
    stored = dict(payload.get("pending_hive_create") or {})
    if str(stored.get("title") or "").strip():
        return True

    recovered = agent._recover_hive_create_pending_from_history(
        history=list((source_context or {}).get("conversation_history") or []),
        fallback_task_id="",
    )
    return recovered is not None


def remember_hive_create_pending(
    agent: Any,
    session_id: str,
    pending: dict[str, Any],
    *,
    set_hive_interaction_state_fn: Any = set_hive_interaction_state,
) -> None:
    variants = {
        key: agent._normalize_hive_create_variant(
            title=str(dict(value).get("title") or ""),
            summary=str(dict(value).get("summary") or ""),
            topic_tags=[
                str(item).strip()
                for item in list(dict(value).get("topic_tags") or [])
                if str(item).strip()
            ][:8],
            auto_start_research=bool(dict(value).get("auto_start_research")),
            preview_note=str(dict(value).get("preview_note") or ""),
        )
        for key, value in dict(pending.get("variants") or {}).items()
        if isinstance(value, dict)
    }
    if not variants:
        variants["improved"] = agent._normalize_hive_create_variant(
            title=str(pending.get("title") or "").strip(),
            summary=str(pending.get("summary") or "").strip(),
            topic_tags=[
                str(item).strip()
                for item in list(pending.get("topic_tags") or [])
                if str(item).strip()
            ][:8],
            auto_start_research=bool(pending.get("auto_start_research")),
        )
    payload = {
        "title": str((variants.get("improved") or {}).get("title") or pending.get("title") or "").strip(),
        "summary": str((variants.get("improved") or {}).get("summary") or pending.get("summary") or "").strip(),
        "topic_tags": list((variants.get("improved") or {}).get("topic_tags") or [])[:8],
        "task_id": str(pending.get("task_id") or "").strip(),
        "auto_start_research": bool((variants.get("improved") or {}).get("auto_start_research") or pending.get("auto_start_research")),
        "default_variant": str(pending.get("default_variant") or "improved"),
        "variants": variants,
        "original_blocked_reason": str(pending.get("original_blocked_reason") or "").strip(),
    }
    agent._hive_create_pending[session_id] = dict(payload)
    set_hive_interaction_state_fn(
        session_id,
        mode="hive_topic_create_pending",
        payload={"pending_hive_create": payload},
    )


def clear_hive_create_pending(
    agent: Any,
    session_id: str,
    *,
    session_hive_state_fn: Any = session_hive_state,
    clear_hive_interaction_state_fn: Any = clear_hive_interaction_state,
) -> None:
    agent._hive_create_pending.pop(session_id, None)
    hive_state = session_hive_state_fn(session_id)
    if str(hive_state.get("interaction_mode") or "").strip().lower() == "hive_topic_create_pending":
        clear_hive_interaction_state_fn(session_id)


def load_pending_hive_create(
    agent: Any,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    fallback_task_id: str,
    allow_history_recovery: bool,
    session_hive_state_fn: Any = session_hive_state,
) -> dict[str, Any] | None:
    pending = agent._hive_create_pending.get(session_id)
    if pending:
        return dict(pending)

    hive_state = session_hive_state_fn(session_id)
    payload = dict(hive_state.get("interaction_payload") or {})
    stored = dict(payload.get("pending_hive_create") or {})
    if stored and (str(stored.get("title") or "").strip() or dict(stored.get("variants") or {})):
        variants = {
            key: agent._normalize_hive_create_variant(
                title=str(dict(value).get("title") or ""),
                summary=str(dict(value).get("summary") or ""),
                topic_tags=[
                    str(item).strip()
                    for item in list(dict(value).get("topic_tags") or [])
                    if str(item).strip()
                ][:8],
                auto_start_research=bool(dict(value).get("auto_start_research")),
                preview_note=str(dict(value).get("preview_note") or ""),
            )
            for key, value in dict(stored.get("variants") or {}).items()
            if isinstance(value, dict)
        }
        if not variants and str(stored.get("title") or "").strip():
            variants["improved"] = agent._normalize_hive_create_variant(
                title=str(stored.get("title") or "").strip(),
                summary=str(stored.get("summary") or "").strip()
                or str(stored.get("title") or "").strip(),
                topic_tags=[
                    str(item).strip()
                    for item in list(stored.get("topic_tags") or [])
                    if str(item).strip()
                ][:8],
                auto_start_research=bool(stored.get("auto_start_research")),
            )
        recovered = {
            "title": str((variants.get("improved") or {}).get("title") or stored.get("title") or "").strip(),
            "summary": str((variants.get("improved") or {}).get("summary") or stored.get("summary") or "").strip()
            or str(stored.get("title") or "").strip(),
            "topic_tags": list((variants.get("improved") or {}).get("topic_tags") or [])[:8],
            "task_id": str(stored.get("task_id") or "").strip() or fallback_task_id,
            "auto_start_research": bool((variants.get("improved") or {}).get("auto_start_research") or stored.get("auto_start_research")),
            "default_variant": str(stored.get("default_variant") or "improved"),
            "variants": variants,
            "original_blocked_reason": str(stored.get("original_blocked_reason") or "").strip(),
        }
        agent._hive_create_pending[session_id] = dict(recovered)
        return recovered

    if not allow_history_recovery:
        return None
    recovered = agent._recover_hive_create_pending_from_history(
        history=list((source_context or {}).get("conversation_history") or []),
        fallback_task_id=fallback_task_id,
    )
    if recovered is not None:
        agent._remember_hive_create_pending(session_id, recovered)
    return recovered


def recover_hive_create_pending_from_history(
    agent: Any,
    *,
    history: list[dict[str, Any]],
    fallback_task_id: str,
) -> dict[str, Any] | None:
    recent_messages = [dict(item) for item in list(history or [])[-8:] if isinstance(item, dict)]
    latest_user_text = ""
    latest_user_draft: dict[str, Any] | None = None
    for message in reversed(recent_messages):
        role = str(message.get("role") or "").strip().lower()
        content = str(message.get("content") or "")
        if not content:
            continue
        if latest_user_draft is None and role == "user":
            draft = agent._extract_hive_topic_create_draft(content)
            if draft is not None and str(draft.get("title") or "").strip():
                latest_user_text = content
                latest_user_draft = draft
                break

    if not latest_user_text or latest_user_draft is None:
        return None
    result = agent._build_hive_create_pending_variants(
        raw_input=latest_user_text,
        draft=latest_user_draft,
        task_id=fallback_task_id,
    )
    if not bool(result.get("ok")):
        return None
    return dict(result.get("pending") or {})
