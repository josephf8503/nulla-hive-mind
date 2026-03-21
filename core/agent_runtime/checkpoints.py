from __future__ import annotations

from collections.abc import Callable
from typing import Any


def prepare_runtime_checkpoint(
    agent: Any,
    *,
    session_id: str,
    raw_user_input: str,
    effective_input: str,
    source_context: dict[str, object] | None,
    allow_followup_resume: bool = True,
    latest_resumable_checkpoint_fn: Callable[[str], dict[str, Any] | None],
    resume_runtime_checkpoint_fn: Callable[..., dict[str, Any] | None],
    create_runtime_checkpoint_fn: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    base_source_context = dict(source_context or {})
    base_source_context.setdefault("runtime_session_id", session_id)
    base_source_context.setdefault("session_id", session_id)
    resumable = latest_resumable_checkpoint_fn(session_id)
    explicit_resume = agent._looks_like_explicit_resume_request(raw_user_input)
    wants_resume = explicit_resume or (allow_followup_resume and agent._is_proceed_message(raw_user_input))
    same_request_retry = bool(
        resumable
        and agent._resume_request_key(effective_input)
        == agent._resume_request_key(str(resumable.get("request_text") or ""))
    )
    if resumable and (wants_resume or same_request_retry):
        resumed = resume_runtime_checkpoint_fn(
            str(resumable.get("checkpoint_id") or ""),
            source_context=base_source_context,
        )
        if resumed is not None:
            merged_source_context = dict(resumed.get("source_context") or {})
            merged_source_context.update(base_source_context)
            merged_source_context["runtime_session_id"] = session_id
            merged_source_context["session_id"] = session_id
            merged_source_context["runtime_checkpoint_id"] = str(resumed.get("checkpoint_id") or "")
            return {
                "state": "resumed",
                "checkpoint": resumed,
                "effective_input": str(resumed.get("request_text") or effective_input),
                "source_context": merged_source_context,
            }
    if explicit_resume and not resumable:
        return {
            "state": "missing_resume",
            "checkpoint": None,
            "effective_input": effective_input,
            "source_context": base_source_context,
        }
    checkpoint = create_runtime_checkpoint_fn(
        session_id=session_id,
        request_text=effective_input,
        source_context=base_source_context,
    )
    base_source_context["runtime_session_id"] = session_id
    base_source_context["session_id"] = session_id
    base_source_context["runtime_checkpoint_id"] = str(checkpoint.get("checkpoint_id") or "")
    return {
        "state": "created",
        "checkpoint": checkpoint,
        "effective_input": effective_input,
        "source_context": base_source_context,
    }


def resolve_runtime_task(
    agent: Any,
    *,
    effective_input: str,
    session_id: str,
    source_context: dict[str, object] | None,
    get_runtime_checkpoint_fn: Callable[[str], dict[str, Any] | None],
    load_task_record_fn: Callable[[str], Any],
    create_task_record_fn: Callable[..., Any],
) -> Any:
    checkpoint_id = agent._runtime_checkpoint_id(source_context)
    if checkpoint_id:
        checkpoint = get_runtime_checkpoint_fn(checkpoint_id)
        if checkpoint:
            existing_task = load_task_record_fn(str(checkpoint.get("task_id") or ""))
            if existing_task is not None:
                return existing_task
    return create_task_record_fn(effective_input, session_id=session_id)


def update_runtime_checkpoint_context(
    source_context: dict[str, object] | None,
    *,
    task_id: str | None = None,
    task_class: str | None = None,
    update_runtime_checkpoint_fn: Callable[..., Any],
) -> None:
    checkpoint_id = runtime_checkpoint_id(source_context)
    if not checkpoint_id:
        return
    update_runtime_checkpoint_fn(
        checkpoint_id,
        task_id=task_id,
        task_class=task_class,
        source_context=dict(source_context or {}),
    )


def finalize_runtime_checkpoint(
    source_context: dict[str, object] | None,
    *,
    status: str,
    final_response: str = "",
    failure_text: str = "",
    finalize_runtime_checkpoint_fn: Callable[..., Any],
) -> None:
    checkpoint_id = runtime_checkpoint_id(source_context)
    if not checkpoint_id:
        return
    finalize_runtime_checkpoint_fn(
        checkpoint_id,
        status=status,
        final_response=final_response,
        failure_text=failure_text,
    )


def runtime_checkpoint_id(source_context: dict[str, object] | None) -> str:
    return str((source_context or {}).get("runtime_checkpoint_id") or "").strip()


def merge_runtime_source_contexts(
    agent: Any,
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(primary or {})
    secondary_dict = dict(secondary or {})
    primary_history = [item for item in list(merged.get("conversation_history") or []) if isinstance(item, dict)]
    secondary_history = [item for item in list(secondary_dict.get("conversation_history") or []) if isinstance(item, dict)]
    merged.update(secondary_dict)
    history: list[dict[str, Any]] = []
    for item in (primary_history + secondary_history)[-16:]:
        normalized = agent._normalize_tool_history_message(item)
        role = str(normalized.get("role") or "").strip().lower()
        content = str(normalized.get("content") or "").strip()
        if role not in {"system", "user", "assistant"} or not content:
            continue
        history.append({"role": role, "content": content[:4000]})
    merged["conversation_history"] = history[-12:]
    return merged
