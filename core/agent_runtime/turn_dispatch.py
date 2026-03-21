from __future__ import annotations

from typing import Any


def prepare_turn_task_bundle(
    agent: Any,
    *,
    effective_input: str,
    user_input: str,
    session_id: str,
    source_context: dict[str, object] | None,
    interpreted: Any,
    classify_fn: Any,
    parse_channel_post_intent_fn: Any,
    dispatch_outbound_post_intent_fn: Any,
    parse_operator_action_intent_fn: Any,
    dispatch_operator_action_fn: Any,
) -> dict[str, Any]:
    task = agent._resolve_runtime_task(
        effective_input=effective_input,
        session_id=session_id,
        source_context=source_context,
    )
    agent._update_runtime_checkpoint_context(
        source_context,
        task_id=task.task_id,
    )
    classification_context = interpreted.as_context()
    if source_context:
        classification_context["source_context"] = dict(source_context)
        classification_context["source_surface"] = source_context.get("surface")
        classification_context["source_platform"] = source_context.get("platform")
    classification = classify_fn(effective_input, context=classification_context)
    agent._update_task_class(task.task_id, classification["task_class"])
    agent._update_runtime_checkpoint_context(
        source_context,
        task_id=task.task_id,
        task_class=str(classification.get("task_class") or "unknown"),
    )
    agent._emit_runtime_event(
        source_context,
        event_type="task_classified",
        message=f"Task classified as {classification.get('task_class') or 'unknown'!s}.",
        task_id=task.task_id,
        task_class=str(classification.get("task_class") or "unknown"),
    )

    post_intent, post_error = parse_channel_post_intent_fn(effective_input)
    if post_intent is not None:
        dispatch = dispatch_outbound_post_intent_fn(
            post_intent,
            task_id=task.task_id,
            session_id=session_id,
            source_context=source_context,
        )
        return {
            "result": agent._action_fast_path_result(
                task_id=task.task_id,
                session_id=session_id,
                user_input=effective_input,
                response=dispatch.response_text,
                confidence=0.95 if dispatch.ok else 0.42,
                source_context=source_context,
                reason=f"channel_post_{dispatch.status}",
                success=dispatch.ok,
                details={
                    "platform": dispatch.platform,
                    "target": dispatch.target,
                    "record_id": dispatch.record_id,
                    "error": dispatch.error,
                },
            )
        }
    if post_error:
        return {
            "result": agent._action_fast_path_result(
                task_id=task.task_id,
                session_id=session_id,
                user_input=effective_input,
                response=(
                    "I can do that, but I need the exact message text. "
                    "Use a format like: post to Discord: \"We are live tonight.\""
                ),
                confidence=0.40,
                source_context=source_context,
                reason="channel_post_missing_message",
                success=False,
                details={"error": post_error},
            )
        }

    operator_intent = parse_operator_action_intent_fn(user_input) or parse_operator_action_intent_fn(effective_input)
    if operator_intent is not None:
        dispatch = dispatch_operator_action_fn(
            operator_intent,
            task_id=task.task_id,
            session_id=session_id,
        )
        workflow_summary = agent._action_workflow_summary(
            operator_kind=operator_intent.kind,
            dispatch_status=dispatch.status,
            details=dispatch.details,
        )
        return {
            "result": agent._action_fast_path_result(
                task_id=task.task_id,
                session_id=session_id,
                user_input=effective_input,
                response=dispatch.response_text,
                confidence=dispatch.learned_plan.confidence if dispatch.learned_plan else (0.9 if dispatch.ok else 0.45),
                source_context=source_context,
                reason=f"operator_action_{dispatch.status}",
                success=dispatch.ok,
                details=dispatch.details,
                mode_override=(
                    "tool_executed"
                    if dispatch.status == "executed"
                    else "tool_preview"
                    if dispatch.status in {"reported", "approval_required"}
                    else "tool_failed"
                ),
                task_outcome=(
                    "success"
                    if dispatch.status == "executed"
                    else "pending_approval"
                    if dispatch.status in {"reported", "approval_required"}
                    else "failed"
                ),
                learned_plan=dispatch.learned_plan,
                workflow_summary=workflow_summary,
            )
        }

    hive_confirm = agent._maybe_handle_hive_create_confirmation(
        effective_input,
        task=task,
        session_id=session_id,
        source_context=source_context,
    )
    if hive_confirm is not None:
        return {"result": hive_confirm}

    raw_hive_create_draft = agent._extract_hive_topic_create_draft(user_input)
    hive_topic_mutation = agent._maybe_handle_hive_topic_mutation_request(
        user_input if raw_hive_create_draft is not None else effective_input,
        task=task,
        session_id=session_id,
        source_context=source_context,
    )
    if hive_topic_mutation is not None:
        return {"result": hive_topic_mutation}

    hive_topic_create = agent._maybe_handle_hive_topic_create_request(
        user_input if raw_hive_create_draft is not None else effective_input,
        task=task,
        session_id=session_id,
        source_context=source_context,
    )
    if hive_topic_create is not None:
        return {"result": hive_topic_create}

    builder_fast_path = agent._maybe_run_builder_controller(
        task=task,
        effective_input=effective_input,
        classification=classification,
        interpretation=interpreted,
        web_notes=[],
        session_id=session_id,
        source_context=source_context,
    )
    if builder_fast_path is not None:
        return {"result": builder_fast_path}

    return {
        "task": task,
        "classification": classification,
    }
