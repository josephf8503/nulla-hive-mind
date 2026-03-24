from __future__ import annotations

import contextlib
from typing import Any

from core.autonomous_topic_research import research_topic_from_signal
from core.credit_ledger import escrow_credits_for_task, estimate_hive_task_credit_cost, get_credit_balance
from core.hive_activity_tracker import set_hive_interaction_state
from core.privacy_guard import text_privacy_risks
from network import signer as signer_mod


def execute_confirmed_hive_create(
    agent: Any,
    pending: dict[str, Any],
    *,
    task: Any,
    session_id: str,
    source_context: dict[str, object] | None,
    user_input: str,
    variant: str,
    research_topic_from_signal_fn: Any = research_topic_from_signal,
) -> dict[str, Any]:
    variants = {
        key: dict(value)
        for key, value in dict(pending.get("variants") or {}).items()
        if isinstance(value, dict)
    }
    selected = dict(variants.get(variant or "") or variants.get("improved") or {})
    title = str(selected.get("title") or pending.get("title") or "").strip()
    summary = str(selected.get("summary") or pending.get("summary") or "").strip() or title
    topic_tags = [
        str(item).strip()
        for item in list(selected.get("topic_tags") or pending.get("topic_tags") or [])
        if str(item).strip()
    ][:8]
    linked_task_id = pending.get("task_id") or task.task_id
    auto_start_research = bool(selected.get("auto_start_research") or pending.get("auto_start_research")) or agent._wants_hive_create_auto_start(user_input)
    if variant == "original" and text_privacy_risks(f"{title}\n{summary}"):
        return _build_failure_result(
            agent,
            task=task,
            session_id=session_id,
            user_input=user_input,
            source_context=source_context,
            status="original_blocked",
            reason="hive_topic_create_original_privacy_blocked",
            details={"status": "original_blocked"},
            response="The original Hive draft still looks private, so I won't post it. Use `send improved` instead.",
            confidence=0.92,
        )

    estimated_cost = estimate_hive_task_credit_cost(
        title,
        summary,
        topic_tags=topic_tags,
        auto_start_research=auto_start_research,
    )

    publish_result = _publish_topic_with_admission_retry(
        agent,
        title=title,
        summary=summary,
        topic_tags=topic_tags,
        linked_task_id=str(linked_task_id),
    )
    if not publish_result.get("ok"):
        status = str(publish_result.get("status") or "topic_failed")
        details = dict(publish_result.get("details") or {})
        return _build_failure_result(
            agent,
            task=task,
            session_id=session_id,
            user_input=user_input,
            source_context=source_context,
            status=status,
            reason=f"hive_topic_create_{status}",
            details=details,
            error=str(publish_result.get("error") or ""),
        )

    topic_id = str(publish_result.get("topic_id") or "").strip()
    title = str(publish_result.get("title") or title).strip()
    response = _build_created_response(
        title=title,
        topic_id=topic_id,
        topic_tags=topic_tags,
        variant=variant,
        pending=pending,
        estimated_cost=estimated_cost,
    )
    response = _maybe_reserve_hive_credits(
        response=response,
        estimated_cost=estimated_cost,
        topic_id=topic_id,
    )
    response = _maybe_start_auto_research(
        agent,
        response=response,
        topic_id=topic_id,
        title=title,
        session_id=session_id,
        source_context=source_context,
        auto_start_research=auto_start_research,
        research_topic_from_signal_fn=research_topic_from_signal_fn,
    )

    return agent._action_fast_path_result(
        task_id=task.task_id,
        session_id=session_id,
        user_input=user_input,
        response=response,
        confidence=0.95,
        source_context=source_context,
        reason="hive_topic_create_created",
        success=True,
        details={"status": "created", "topic_id": topic_id, "topic_tags": topic_tags},
        mode_override="tool_executed",
        task_outcome="success",
        workflow_summary=agent._action_workflow_summary(
            operator_kind="hive.create_topic",
            dispatch_status="created",
            details={"action_id": topic_id},
        ),
    )


def hive_topic_create_failure_text(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == "privacy_blocked_topic":
        return "I won't create that Hive task because it looks like it contains private or secret material."
    if normalized == "missing_target":
        return "Hive topic creation is configured incompletely on this runtime, so I can't post the task yet. Hive truth: future/unsupported."
    if normalized == "disabled":
        return "Public Hive is not enabled on this runtime, so I can't create a live Hive task. Hive truth: future/unsupported."
    if normalized == "missing_auth":
        return "Hive task creation is disabled here because public Hive auth is not configured for writes. Hive truth: future/unsupported."
    if normalized == "invalid_auth":
        return "Hive task creation is configured, but the live Hive rejected this runtime's write auth. I need to refresh public Hive auth before posting."
    if normalized == "admission_blocked":
        return "The live Hive rejected that task draft as too command-like or low-substance. I need to frame it as agent analysis before posting."
    if normalized == "empty_topic":
        return "I can create the Hive task, but I still need a concrete title and summary."
    return "I couldn't create that Hive task."


def _build_failure_result(
    agent: Any,
    *,
    task: Any,
    session_id: str,
    user_input: str,
    source_context: dict[str, object] | None,
    status: str,
    reason: str,
    details: dict[str, Any],
    response: str | None = None,
    confidence: float = 0.46,
    error: str = "",
) -> dict[str, Any]:
    payload = dict(details)
    if error:
        payload["error"] = error
    return agent._action_fast_path_result(
        task_id=task.task_id,
        session_id=session_id,
        user_input=user_input,
        response=response or agent._hive_topic_create_failure_text(status),
        confidence=confidence,
        source_context=source_context,
        reason=reason,
        success=False,
        details=payload,
        mode_override="tool_failed",
        task_outcome="failed",
        workflow_summary=agent._action_workflow_summary(
            operator_kind="hive.create_topic",
            dispatch_status=status,
            details={"action_id": ""},
        ),
    )


def _publish_topic_with_admission_retry(
    agent: Any,
    *,
    title: str,
    summary: str,
    topic_tags: list[str],
    linked_task_id: str,
) -> dict[str, Any]:
    result: dict[str, Any] | None = None
    error_text = ""
    try:
        result = agent.public_hive_bridge.create_public_topic(
            title=title,
            summary=summary,
            topic_tags=topic_tags,
            linked_task_id=linked_task_id,
            idempotency_key=f"{linked_task_id}:hive_create",
        )
    except Exception as exc:
        error_text = str(exc or "").strip()
        lowered_error = error_text.lower()
        if "user command instead of agent analysis" in lowered_error:
            retry_title, retry_summary, _ = agent._shape_public_hive_admission_safe_copy(
                title=title,
                summary=summary,
                force=True,
            )
            if retry_title != title or retry_summary != summary:
                try:
                    result = agent.public_hive_bridge.create_public_topic(
                        title=retry_title,
                        summary=retry_summary,
                        topic_tags=topic_tags,
                        linked_task_id=linked_task_id,
                        idempotency_key=f"{linked_task_id}:hive_create",
                    )
                except Exception as retry_exc:
                    error_text = str(retry_exc or error_text).strip()
                else:
                    if result.get("ok") and str(result.get("topic_id") or "").strip():
                        title = retry_title
                        error_text = ""
                    else:
                        status = str(result.get("status") or "admission_blocked").strip() or "admission_blocked"
                        return {
                            "ok": False,
                            "status": status,
                            "details": {"status": status, **dict(result)},
                        }
    if error_text:
        lowered_error = error_text.lower()
        status = (
            "invalid_auth"
            if "unauthorized" in lowered_error
            else "admission_blocked"
            if "brain hive admission blocked" in lowered_error
            else "topic_failed"
        )
        return {"ok": False, "status": status, "details": {"status": status}, "error": error_text}
    result = dict(result or {})
    topic_id = str(result.get("topic_id") or "").strip()
    if not result.get("ok") or not topic_id:
        status = str(result.get("status") or "topic_failed").strip() or "topic_failed"
        return {"ok": False, "status": status, "details": {"status": status, **result}}
    return {"ok": True, "topic_id": topic_id, "title": title}


def _build_created_response(
    *,
    title: str,
    topic_id: str,
    topic_tags: list[str],
    variant: str,
    pending: dict[str, Any],
    estimated_cost: float,
) -> str:
    tag_suffix = f" Tags: {', '.join(topic_tags[:6])}." if topic_tags else ""
    variant_suffix = (
        f" Using {variant or 'improved'} draft."
        if dict(pending.get("variants") or {}).get("original")
        else ""
    )
    response = f"Created Hive task `{title}` (#{topic_id[:8]}).{tag_suffix}{variant_suffix}"
    if estimated_cost <= 0:
        return response
    return response


def _maybe_reserve_hive_credits(
    *,
    response: str,
    estimated_cost: float,
    topic_id: str,
) -> str:
    if estimated_cost <= 0:
        return response
    peer_id = signer_mod.get_local_peer_id()
    if escrow_credits_for_task(
        peer_id,
        topic_id,
        estimated_cost,
        receipt_id=f"hive_task_escrow:{topic_id}",
    ):
        return (
            f"{response} Reserved {estimated_cost:.1f} credits for Hive payouts. "
            f"Remaining balance: {get_credit_balance(peer_id):.2f}."
        )
    return (
        f"{response} No credits were reserved because your current balance is "
        f"{get_credit_balance(peer_id):.2f}."
    )


def _maybe_start_auto_research(
    agent: Any,
    *,
    response: str,
    topic_id: str,
    title: str,
    session_id: str,
    source_context: dict[str, object] | None,
    auto_start_research: bool,
    research_topic_from_signal_fn: Any,
) -> str:
    with contextlib.suppress(Exception):
        agent.hive_activity_tracker.note_watched_topic(session_id=session_id, topic_id=topic_id)
    if not auto_start_research:
        return response
    signal = {"topic_id": topic_id, "title": title}
    agent._sync_public_presence(status="busy", source_context=source_context)
    research_result = research_topic_from_signal_fn(
        signal,
        public_hive_bridge=agent.public_hive_bridge,
        curiosity=agent.curiosity,
        hive_activity_tracker=agent.hive_activity_tracker,
        session_id=session_id,
        auto_claim=True,
    )
    if research_result.ok:
        set_hive_interaction_state(
            session_id,
            mode="hive_task_active",
            payload={
                "active_topic_id": topic_id,
                "active_title": title,
                "claim_id": str(research_result.claim_id or "").strip(),
            },
        )
        response = f"{response} Started Hive research on `{title}`."
        if research_result.claim_id:
            response = f"{response} Claim `{str(research_result.claim_id)[:8]}` is active."
        return response
    failure_text = str(research_result.response_text or "").strip()
    if failure_text:
        return f"{response} The task is live, but starting research failed: {failure_text}"
    return response
