from __future__ import annotations

import contextlib
import uuid
from typing import Any


def handle_hive_topic_update_request(
    agent: Any,
    user_input: str,
    *,
    task: Any,
    session_id: str,
    source_context: dict[str, object] | None,
) -> dict[str, Any]:
    if not agent.public_hive_bridge.enabled():
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="Public Hive is not enabled on this runtime, so I can't edit a live Hive task.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_topic_update_disabled",
            success=False,
            details={"status": "disabled"},
            mode_override="tool_failed",
            task_outcome="failed",
        )
    if not agent.public_hive_bridge.write_enabled():
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="Hive task edits are disabled here because public Hive auth is not configured for writes.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_topic_update_missing_auth",
            success=False,
            details={"status": "missing_auth"},
            mode_override="tool_failed",
            task_outcome="failed",
        )
    topic = agent._resolve_hive_topic_for_mutation(
        session_id=session_id,
        topic_hint=agent._extract_hive_topic_hint(user_input),
    )
    if topic is None:
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="I couldn't resolve which Hive task to edit. Give me the task id or ask right after creating/listing it.",
            confidence=0.82,
            source_context=source_context,
            reason="hive_topic_update_missing_target",
            success=False,
            details={"status": "missing_topic"},
            mode_override="tool_failed",
            task_outcome="failed",
        )
    update_draft = agent._extract_hive_topic_update_draft(user_input)
    if update_draft is None:
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response=f"What should I change on Hive task `{str(topic.get('title') or '').strip()}`?",
            confidence=0.84,
            source_context=source_context,
            reason="hive_topic_update_missing_copy",
            success=False,
            details={"status": "missing_copy", "topic_id": str(topic.get('topic_id') or '')},
            mode_override="tool_failed",
            task_outcome="failed",
        )
    next_title = str(update_draft.get("title") or "").strip() or str(topic.get("title") or "").strip()
    next_summary = str(update_draft.get("summary") or "").strip() or str(topic.get("summary") or "").strip()
    public_copy = agent._prepare_public_hive_topic_copy(
        raw_input=user_input,
        title=next_title,
        summary=next_summary,
        mode="improved",
    )
    if not bool(public_copy.get("ok")):
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response=str(public_copy.get("response") or "I won't update that Hive task."),
            confidence=0.88,
            source_context=source_context,
            reason=str(public_copy.get("reason") or "hive_topic_update_privacy_blocked"),
            success=False,
            details={"status": "privacy_blocked"},
            mode_override="tool_failed",
            task_outcome="failed",
        )
    result = agent.public_hive_bridge.update_public_topic(
        topic_id=str(topic.get("topic_id") or "").strip(),
        title=str(public_copy.get("title") or "").strip(),
        summary=str(public_copy.get("summary") or "").strip(),
        topic_tags=[
            str(item).strip()
            for item in list(update_draft.get("topic_tags") or topic.get("topic_tags") or [])
            if str(item).strip()
        ][:8],
        idempotency_key=f"{str(topic.get('topic_id') or '').strip()}:update:{uuid.uuid4().hex[:8]}",
    )
    if not result.get("ok"):
        status = str(result.get("status") or "failed")
        if status == "route_unavailable":
            return agent._action_fast_path_result(
                task_id=task.task_id,
                session_id=session_id,
                user_input=user_input,
                response="Live Hive task edits are not available on the current public deployment yet. The local code supports it, but the public Hive nodes need an update first.",
                confidence=0.9,
                source_context=source_context,
                reason="hive_topic_update_route_unavailable",
                success=False,
                details={"status": status},
                mode_override="tool_failed",
                task_outcome="failed",
            )
        if status == "not_owner":
            return agent._action_fast_path_result(
                task_id=task.task_id,
                session_id=session_id,
                user_input=user_input,
                response="I can't edit that Hive task because this agent didn't create it.",
                confidence=0.9,
                source_context=source_context,
                reason="hive_topic_update_not_owner",
                success=False,
                details={"status": status},
                mode_override="tool_failed",
                task_outcome="failed",
            )
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="I couldn't update that Hive task.",
            confidence=0.82,
            source_context=source_context,
            reason="hive_topic_update_failed",
            success=False,
            details={"status": status},
            mode_override="tool_failed",
            task_outcome="failed",
        )
    topic_id = str(result.get("topic_id") or topic.get("topic_id") or "").strip()
    with contextlib.suppress(Exception):
        agent.hive_activity_tracker.note_watched_topic(session_id=session_id, topic_id=topic_id)
    updated = dict(result.get("topic_result") or {})
    updated_title = str(updated.get("title") or next_title).strip()
    return agent._action_fast_path_result(
        task_id=task.task_id,
        session_id=session_id,
        user_input=user_input,
        response=f"Updated Hive task `{updated_title}` (#{topic_id[:8]}).",
        confidence=0.95,
        source_context=source_context,
        reason="hive_topic_updated",
        success=True,
        details={"status": "updated", "topic_id": topic_id},
        mode_override="tool_executed",
        task_outcome="success",
    )
