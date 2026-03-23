from __future__ import annotations

import contextlib
from typing import Any

from core.agent_runtime import hive_topic_drafting as agent_hive_topic_drafting
from core.agent_runtime import hive_topic_pending as agent_hive_topic_pending
from core.agent_runtime import hive_topic_public_copy as agent_hive_topic_public_copy
from core.autonomous_topic_research import research_topic_from_signal
from core.credit_ledger import (
    escrow_credits_for_task,
    estimate_hive_task_credit_cost,
    get_credit_balance,
)
from core.privacy_guard import text_privacy_risks
from network import signer as signer_mod


def maybe_handle_hive_topic_create_request(
    agent: Any,
    user_input: str,
    *,
    task: Any,
    session_id: str,
    source_context: dict[str, object] | None,
) -> dict[str, Any] | None:
    draft = agent._extract_hive_topic_create_draft(user_input)
    if draft is None:
        return None

    if not agent.public_hive_bridge.enabled():
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="Public Hive is not enabled on this runtime, so I can't create a live Hive task. Hive truth: future/unsupported.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_topic_create_disabled",
            success=False,
            details={"status": "disabled"},
            mode_override="tool_failed",
            task_outcome="failed",
            workflow_summary=agent._action_workflow_summary(
                operator_kind="hive.create_topic",
                dispatch_status="disabled",
                details={"action_id": ""},
            ),
        )
    if not agent.public_hive_bridge.write_enabled():
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="Hive task creation is disabled here because public Hive auth is not configured for writes. Hive truth: future/unsupported.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_topic_create_missing_auth",
            success=False,
            details={"status": "missing_auth"},
            mode_override="tool_failed",
            task_outcome="failed",
            workflow_summary=agent._action_workflow_summary(
                operator_kind="hive.create_topic",
                dispatch_status="missing_auth",
                details={"action_id": ""},
            ),
        )

    variant_result = agent._build_hive_create_pending_variants(
        raw_input=user_input,
        draft=draft,
        task_id=task.task_id,
    )
    if not bool(variant_result.get("ok")):
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response=str(variant_result.get("response") or "I won't create that Hive task."),
            confidence=0.9,
            source_context=source_context,
            reason=str(variant_result.get("reason") or "hive_topic_create_privacy_blocked"),
            success=False,
            details={
                "status": "privacy_blocked",
                "privacy_risks": list(variant_result.get("privacy_risks") or []),
            },
            mode_override="tool_failed",
            task_outcome="failed",
            workflow_summary=agent._action_workflow_summary(
                operator_kind="hive.create_topic",
                dispatch_status="privacy_blocked",
                details={"action_id": ""},
            ),
        )
    pending = dict(variant_result.get("pending") or {})
    improved_variant = dict((pending.get("variants") or {}).get("improved") or {})
    title = str(improved_variant.get("title") or "").strip()
    summary = str(improved_variant.get("summary") or "").strip() or title
    preview_note = str(improved_variant.get("preview_note") or "")
    topic_tags = [
        str(item).strip()
        for item in list(improved_variant.get("topic_tags") or [])
        if str(item).strip()
    ][:8]
    if len(title) < 4:
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response=(
                "I can create the Hive task, but I still need a concrete title. "
                'Use a format like: create new task in Hive: "better watcher task UX".'
            ),
            confidence=0.42,
            source_context=source_context,
            reason="hive_topic_create_missing_title",
            success=False,
            details={"status": "missing_title"},
            mode_override="tool_failed",
            task_outcome="failed",
            workflow_summary=agent._action_workflow_summary(
                operator_kind="hive.create_topic",
                dispatch_status="missing_title",
                details={"action_id": ""},
            ),
        )

    dup = agent._check_hive_duplicate(title, summary)
    agent._remember_hive_create_pending(session_id, pending)
    estimated_cost = estimate_hive_task_credit_cost(
        title,
        summary,
        topic_tags=topic_tags,
        auto_start_research=bool(improved_variant.get("auto_start_research")),
    )
    dup_warning = ""
    if dup:
        dup_title = dup.get("title", "")
        dup_id = str(dup.get("topic_id") or "")[:8]
        dup_warning = (
            f"\n\nHeads up -- a similar topic already exists: "
            f"**{dup_title}** (#{dup_id}). Still want to create a new one?"
        )
    preview = agent._format_hive_create_preview(
        pending=pending,
        estimated_cost=estimated_cost,
        dup_warning=dup_warning,
        preview_note=preview_note,
    )
    return agent._action_fast_path_result(
        task_id=task.task_id,
        session_id=session_id,
        user_input=user_input,
        response=preview,
        confidence=0.95,
        source_context=source_context,
        reason="hive_topic_create_awaiting_confirmation",
        success=True,
        details={
            "status": "awaiting_confirmation",
            "title": title,
            "topic_tags": topic_tags,
            "default_variant": str(pending.get("default_variant") or "improved"),
        },
        mode_override="tool_preview",
        task_outcome="pending_approval",
        workflow_summary=agent._action_workflow_summary(
            operator_kind="hive.create_topic",
            dispatch_status="awaiting_confirmation",
            details={"action_id": ""},
        ),
    )


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
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response="The original Hive draft still looks private, so I won't post it. Use `send improved` instead.",
            confidence=0.92,
            source_context=source_context,
            reason="hive_topic_create_original_privacy_blocked",
            success=False,
            details={"status": "original_blocked"},
            mode_override="tool_failed",
            task_outcome="failed",
            workflow_summary=agent._action_workflow_summary(
                operator_kind="hive.create_topic",
                dispatch_status="original_blocked",
                details={"action_id": ""},
            ),
        )
    estimated_cost = estimate_hive_task_credit_cost(
        title,
        summary,
        topic_tags=topic_tags,
        auto_start_research=auto_start_research,
    )

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
                    lowered_error = error_text.lower()
                else:
                    if result.get("ok") and str(result.get("topic_id") or "").strip():
                        title = retry_title
                        summary = retry_summary
                        error_text = ""
                    else:
                        status = str(result.get("status") or "admission_blocked").strip() or "admission_blocked"
                        return agent._action_fast_path_result(
                            task_id=task.task_id,
                            session_id=session_id,
                            user_input=user_input,
                            response=agent._hive_topic_create_failure_text(status),
                            confidence=0.46,
                            source_context=source_context,
                            reason=f"hive_topic_create_{status}",
                            success=False,
                            details={"status": status, **dict(result)},
                            mode_override="tool_failed",
                            task_outcome="failed",
                            workflow_summary=agent._action_workflow_summary(
                                operator_kind="hive.create_topic",
                                dispatch_status=status,
                                details={"action_id": ""},
                            ),
                        )
            else:
                lowered_error = error_text.lower()
        if not error_text:
            topic_id = str(result.get("topic_id") or "").strip()
            if not result.get("ok") or not topic_id:
                status = str(result.get("status") or "topic_failed").strip() or "topic_failed"
                return agent._action_fast_path_result(
                    task_id=task.task_id,
                    session_id=session_id,
                    user_input=user_input,
                    response=agent._hive_topic_create_failure_text(status),
                    confidence=0.46,
                    source_context=source_context,
                    reason=f"hive_topic_create_{status}",
                    success=False,
                    details={"status": status, **dict(result)},
                    mode_override="tool_failed",
                    task_outcome="failed",
                    workflow_summary=agent._action_workflow_summary(
                        operator_kind="hive.create_topic",
                        dispatch_status=status,
                        details={"action_id": ""},
                    ),
                )
        if error_text:
            lowered_error = error_text.lower()
            status = (
                "invalid_auth"
                if "unauthorized" in lowered_error
                else "admission_blocked"
                if "brain hive admission blocked" in lowered_error
                else "topic_failed"
            )
            return agent._action_fast_path_result(
                task_id=task.task_id,
                session_id=session_id,
                user_input=user_input,
                response=agent._hive_topic_create_failure_text(status),
                confidence=0.46,
                source_context=source_context,
                reason=f"hive_topic_create_{status}",
                success=False,
                details={"status": status, "error": error_text},
                mode_override="tool_failed",
                task_outcome="failed",
                workflow_summary=agent._action_workflow_summary(
                    operator_kind="hive.create_topic",
                    dispatch_status=status,
                    details={"action_id": ""},
                ),
            )
    topic_id = str(result.get("topic_id") or "").strip()
    if not result.get("ok") or not topic_id:
        status = str(result.get("status") or "topic_failed").strip() or "topic_failed"
        return agent._action_fast_path_result(
            task_id=task.task_id,
            session_id=session_id,
            user_input=user_input,
            response=agent._hive_topic_create_failure_text(status),
            confidence=0.46,
            source_context=source_context,
            reason=f"hive_topic_create_{status}",
            success=False,
            details={"status": status, **dict(result)},
            mode_override="tool_failed",
            task_outcome="failed",
            workflow_summary=agent._action_workflow_summary(
                operator_kind="hive.create_topic",
                dispatch_status=status,
                details={"action_id": ""},
            ),
        )

    with contextlib.suppress(Exception):
        agent.hive_activity_tracker.note_watched_topic(session_id=session_id, topic_id=topic_id)
    tag_suffix = f" Tags: {', '.join(topic_tags[:6])}." if topic_tags else ""
    variant_suffix = (
        f" Using {variant or 'improved'} draft."
        if dict(pending.get("variants") or {}).get("original")
        else ""
    )
    response = f"Created Hive task `{title}` (#{topic_id[:8]}).{tag_suffix}{variant_suffix}"
    if estimated_cost > 0:
        peer_id = signer_mod.get_local_peer_id()
        if escrow_credits_for_task(
            peer_id,
            topic_id,
            estimated_cost,
            receipt_id=f"hive_task_escrow:{topic_id}",
        ):
            response = (
                f"{response} Reserved {estimated_cost:.1f} credits for Hive payouts. "
                f"Remaining balance: {get_credit_balance(peer_id):.2f}."
            )
        else:
            response = (
                f"{response} No credits were reserved because your current balance is "
                f"{get_credit_balance(peer_id):.2f}."
            )
    if auto_start_research:
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
            agent_hive_topic_pending.set_hive_interaction_state(
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
        else:
            failure_text = str(research_result.response_text or "").strip()
            if failure_text:
                response = f"{response} The task is live, but starting research failed: {failure_text}"
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


prepare_public_hive_topic_copy = agent_hive_topic_public_copy.prepare_public_hive_topic_copy
sanitize_public_hive_text = agent_hive_topic_public_copy.sanitize_public_hive_text
shape_public_hive_admission_safe_copy = agent_hive_topic_public_copy.shape_public_hive_admission_safe_copy
has_structured_hive_public_brief = agent_hive_topic_public_copy.has_structured_hive_public_brief
looks_like_raw_chat_transcript = agent_hive_topic_public_copy.looks_like_raw_chat_transcript
maybe_handle_hive_create_confirmation = agent_hive_topic_pending.maybe_handle_hive_create_confirmation
has_pending_hive_create_confirmation = agent_hive_topic_pending.has_pending_hive_create_confirmation
is_pending_hive_create_confirmation_input = agent_hive_topic_pending.is_pending_hive_create_confirmation_input
format_hive_create_preview = agent_hive_topic_pending.format_hive_create_preview
preview_text_snippet = agent_hive_topic_pending.preview_text_snippet
parse_hive_create_variant_choice = agent_hive_topic_pending.parse_hive_create_variant_choice
remember_hive_create_pending = agent_hive_topic_pending.remember_hive_create_pending
clear_hive_create_pending = agent_hive_topic_pending.clear_hive_create_pending
load_pending_hive_create = agent_hive_topic_pending.load_pending_hive_create
recover_hive_create_pending_from_history = agent_hive_topic_pending.recover_hive_create_pending_from_history


infer_hive_topic_tags = agent_hive_topic_public_copy.infer_hive_topic_tags
normalize_hive_topic_tag = agent_hive_topic_public_copy.normalize_hive_topic_tag
strip_wrapping_quotes = agent_hive_topic_public_copy.strip_wrapping_quotes
check_hive_duplicate = agent_hive_topic_drafting.check_hive_duplicate
clean_hive_title = agent_hive_topic_drafting.clean_hive_title
extract_hive_topic_create_draft = agent_hive_topic_drafting.extract_hive_topic_create_draft
extract_original_hive_topic_create_draft = agent_hive_topic_drafting.extract_original_hive_topic_create_draft
build_hive_create_pending_variants = agent_hive_topic_drafting.build_hive_create_pending_variants
normalize_hive_create_variant = agent_hive_topic_drafting.normalize_hive_create_variant
wants_hive_create_auto_start = agent_hive_topic_drafting.wants_hive_create_auto_start
looks_like_hive_topic_create_request = agent_hive_topic_drafting.looks_like_hive_topic_create_request
looks_like_hive_topic_drafting_request = agent_hive_topic_drafting.looks_like_hive_topic_drafting_request


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
