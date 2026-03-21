from __future__ import annotations

import contextlib
import re
import uuid
from typing import Any

_HIVE_REVIEW_ACTION_RE = re.compile(
    r"\b(?P<decision>approve|approved|reject|rejected|needs?\s+more\s+evidence|needs?\s+improvement|send\s+back|quarantine|void)\b"
    r"(?:\s+(?:the\s+)?)?"
    r"(?:(?P<object_type>post|topic)\s+)?"
    r"(?:#)?(?P<object_id>[a-z0-9][a-z0-9-]{5,255})\b",
    re.IGNORECASE,
)
_HIVE_TOPIC_FULL_ID_RE = re.compile(r"\b([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\b", re.IGNORECASE)
_HIVE_TOPIC_SHORT_ID_RE = re.compile(r"#\s*([0-9a-f]{8,12})\b", re.IGNORECASE)


def maybe_handle_hive_frontdoor(
    agent: Any,
    *,
    raw_user_input: str,
    effective_input: str,
    session_id: str,
    source_context: dict[str, object] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    hive_review_result = agent._maybe_handle_hive_review_command(
        effective_input,
        session_id=session_id,
        source_context=source_context,
    )
    if hive_review_result is not None:
        return hive_review_result, None, False

    pending_hive_create_confirmation = agent._is_pending_hive_create_confirmation_input(
        effective_input,
        session_id=session_id,
        source_context=source_context,
    )
    if not pending_hive_create_confirmation:
        hive_followup = agent._maybe_handle_hive_research_followup(
            effective_input,
            session_id=session_id,
            source_context=source_context,
        )
        if hive_followup is not None:
            return hive_followup, None, False

    raw_hive_create_draft = agent._extract_hive_topic_create_draft(raw_user_input)
    effective_hive_create_draft = raw_hive_create_draft or agent._extract_hive_topic_create_draft(effective_input)
    if effective_hive_create_draft is None and not pending_hive_create_confirmation:
        handled, response, model_wording_candidate, hive_command_details = agent._maybe_handle_hive_runtime_command(
            effective_input,
            session_id=session_id,
        )
        if not handled:
            recovered_hive_input = agent._recover_hive_runtime_command_input(effective_input)
            if recovered_hive_input:
                handled, response, model_wording_candidate, hive_command_details = agent._maybe_handle_hive_runtime_command(
                    recovered_hive_input,
                    session_id=session_id,
                )
        if handled:
            topic_rows = [
                dict(item)
                for item in list((hive_command_details or {}).get("topics") or [])
                if isinstance(item, dict) and str(item.get("topic_id") or "").strip()
            ]
            if topic_rows:
                agent._store_hive_topic_selection_state(session_id, topic_rows)
            if model_wording_candidate and agent._is_chat_truth_surface(source_context):
                return (
                    agent._chat_surface_hive_wording_result(
                        session_id=session_id,
                        user_input=effective_input,
                        source_context=source_context,
                        response_class=agent._classify_hive_text_response(response),
                        reason="hive_activity_model_wording",
                        observations=agent._chat_surface_hive_command_observations(hive_command_details or {}),
                        fallback_response=agent._chat_surface_hive_degraded_response(hive_command_details or {}),
                    ),
                    effective_hive_create_draft,
                    pending_hive_create_confirmation,
                )
            return (
                agent._fast_path_result(
                    session_id=session_id,
                    user_input=effective_input,
                    response=response,
                    confidence=0.89,
                    source_context=source_context,
                    reason="hive_activity_command",
                ),
                effective_hive_create_draft,
                pending_hive_create_confirmation,
            )

    if not pending_hive_create_confirmation:
        hive_status = agent._maybe_handle_hive_status_followup(
            effective_input,
            session_id=session_id,
            source_context=source_context,
        )
        if hive_status is not None:
            return hive_status, effective_hive_create_draft, False

    return None, effective_hive_create_draft, pending_hive_create_confirmation


def maybe_handle_hive_review_command(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
) -> dict[str, Any] | None:
    clean = " ".join(str(user_input or "").split()).strip()
    lowered = clean.lower()
    if not clean:
        return None
    if agent._looks_like_hive_review_queue_command(lowered):
        return agent._handle_hive_review_queue_command(
            clean,
            session_id=session_id,
            source_context=source_context,
        )
    review_action = agent._parse_hive_review_action(clean)
    if review_action is not None:
        return agent._handle_hive_review_action(
            clean,
            session_id=session_id,
            source_context=source_context,
            review_action=review_action,
        )
    if agent._looks_like_hive_cleanup_command(lowered):
        return agent._handle_hive_cleanup_command(
            clean,
            session_id=session_id,
            source_context=source_context,
        )
    return None


def looks_like_hive_review_queue_command(lowered: str) -> bool:
    compact = " ".join(str(lowered or "").split()).strip().lower()
    if not compact:
        return False
    if "hive" not in compact and "review" not in compact:
        return False
    return any(
        marker in compact
        for marker in (
            "review queue",
            "what needs review",
            "what is in review",
            "show review queue",
            "check review queue",
            "moderation queue",
            "review items",
            "pending reviews",
        )
    )


def parse_hive_review_action(user_input: str) -> dict[str, str] | None:
    match = _HIVE_REVIEW_ACTION_RE.search(user_input)
    if match is None:
        return None
    decision_phrase = " ".join(str(match.group("decision") or "").split()).strip().lower()
    object_type = str(match.group("object_type") or "").strip().lower()
    object_id = str(match.group("object_id") or "").strip()
    if not object_id:
        return None
    decision = {
        "approve": "approve",
        "approved": "approve",
        "reject": "void",
        "rejected": "void",
        "needs more evidence": "review_required",
        "needs improvement": "review_required",
        "send back": "review_required",
        "quarantine": "quarantine",
        "void": "void",
    }.get(decision_phrase)
    if not decision:
        return None
    if object_type not in {"post", "topic"}:
        object_type = "post" if object_id.startswith("post-") else "topic" if object_id.startswith("topic-") else "post"
    return {
        "decision": decision,
        "decision_phrase": decision_phrase,
        "object_type": object_type,
        "object_id": object_id,
    }


def looks_like_hive_cleanup_command(lowered: str) -> bool:
    compact = " ".join(str(lowered or "").split()).strip().lower()
    if "hive" not in compact and "nulla_smoke" not in compact and "smoke topic" not in compact:
        return False
    if "cleanup" not in compact and "clean up" not in compact and "remove" not in compact and "close" not in compact:
        return False
    return any(marker in compact for marker in ("smoke", "junk", "test artifact", "test topic", "noise"))


def handle_hive_review_queue_command(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
) -> dict[str, Any]:
    if not agent.public_hive_bridge.enabled():
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response="Public Hive is not enabled on this runtime, so I can't inspect the live review queue.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_review_queue_disabled",
        )
    rows = agent.public_hive_bridge.list_public_review_queue(limit=8)
    if not rows:
        response = "Hive review queue is empty right now."
    else:
        lines = ["Hive review queue:"]
        for row in rows[:6]:
            object_type = str(row.get("object_type") or "object").strip()
            object_id = str(row.get("object_id") or "").strip()
            preview = " ".join(str(row.get("preview") or "").split()).strip()
            moderation_state = str(row.get("moderation_state") or "review_required").strip()
            summary = dict(row.get("review_summary") or {})
            total_reviews = int(summary.get("total_reviews") or 0)
            current_state = str(summary.get("current_state") or moderation_state).strip()
            applied_state = str(summary.get("applied_state") or "").strip()
            state_suffix = f" -> {applied_state}" if applied_state and applied_state != current_state else ""
            snippet = preview[:120] + ("..." if len(preview) > 120 else "")
            lines.append(
                f"- [{object_type}] {object_id}: {current_state}{state_suffix}; reviews={total_reviews}; {snippet or 'No preview'}"
            )
        response = "\n".join(lines)
    return agent._fast_path_result(
        session_id=session_id,
        user_input=user_input,
        response=response,
        confidence=0.93,
        source_context=source_context,
        reason="hive_review_queue",
    )


def handle_hive_review_action(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    review_action: dict[str, str],
) -> dict[str, Any]:
    if not agent.public_hive_bridge.enabled():
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response="Public Hive is not enabled on this runtime, so I can't submit a moderation review.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_review_action_disabled",
        )
    if not agent.public_hive_bridge.write_enabled():
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response="Public Hive moderation writes are disabled here because live write auth is not configured.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_review_action_write_disabled",
        )
    result = agent.public_hive_bridge.submit_public_moderation_review(
        object_type=review_action["object_type"],
        object_id=review_action["object_id"],
        decision=review_action["decision"],
        note=f"NULLA operator review via chat: {review_action['decision_phrase']}",
    )
    if not result.get("ok"):
        response = f"Failed to submit Hive moderation review for {review_action['object_type']} `{review_action['object_id']}`."
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response=response,
            confidence=0.82,
            source_context=source_context,
            reason="hive_review_action_failed",
        )
    current_state = str(result.get("current_state") or "").strip() or review_action["decision"]
    quorum_reached = bool(result.get("quorum_reached"))
    response = (
        f"Submitted Hive moderation review for {review_action['object_type']} `{review_action['object_id']}`: "
        f"{review_action['decision']}. Current state `{current_state}`."
    )
    if quorum_reached:
        response = f"{response} Review quorum is reached."
    return agent._fast_path_result(
        session_id=session_id,
        user_input=user_input,
        response=response,
        confidence=0.95,
        source_context=source_context,
        reason="hive_review_action",
    )


def handle_hive_cleanup_command(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
) -> dict[str, Any]:
    if not agent.public_hive_bridge.enabled():
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response="Public Hive is not enabled on this runtime, so I can't clean live smoke topics.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_cleanup_disabled",
        )
    if not agent.public_hive_bridge.write_enabled():
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response="Public Hive cleanup writes are disabled here because live write auth is not configured.",
            confidence=0.9,
            source_context=source_context,
            reason="hive_cleanup_write_disabled",
        )
    topics = agent.public_hive_bridge.list_public_topics(
        limit=64,
        statuses=("open", "researching", "disputed", "partial", "needs_improvement", "solved", "closed"),
    )
    candidates = [
        topic
        for topic in topics
        if agent._looks_like_disposable_hive_cleanup_topic(topic)
        and str(topic.get("status") or "").strip().lower() != "closed"
    ]
    if not candidates:
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response="I didn't find any live disposable smoke topics to close.",
            confidence=0.92,
            source_context=source_context,
            reason="hive_cleanup_noop",
        )
    closed_count = 0
    failed_ids: list[str] = []
    for topic in candidates[:16]:
        topic_id = str(topic.get("topic_id") or "").strip()
        if not topic_id:
            continue
        result = agent.public_hive_bridge.update_public_topic_status(
            topic_id=topic_id,
            status="closed",
            note="Disposable smoke cleanup from NULLA operator surface.",
            idempotency_key=f"{topic_id}:cleanup:{uuid.uuid4().hex[:8]}",
        )
        if result.get("ok"):
            closed_count += 1
        else:
            failed_ids.append(topic_id[:8])
    response = f"Closed {closed_count} disposable Hive smoke topic{'s' if closed_count != 1 else ''}."
    if failed_ids:
        response = f"{response} Failed: {', '.join(failed_ids[:6])}."
    return agent._fast_path_result(
        session_id=session_id,
        user_input=user_input,
        response=response,
        confidence=0.94,
        source_context=source_context,
        reason="hive_cleanup_smoke_topics",
    )


def looks_like_disposable_hive_cleanup_topic(topic: dict[str, Any]) -> bool:
    title = str(topic.get("title") or "").strip()
    summary = str(topic.get("summary") or "").strip()
    tags = {
        str(item or "").strip().lower()
        for item in list(topic.get("topic_tags") or [])
        if str(item or "").strip()
    }
    combined = f"{title} {summary}".lower()
    return (
        "[nulla_smoke:" in combined
        or title.startswith("[NULLA_SMOKE]")
        or "nulla_smoke" in combined
        or ("smoke" in tags and any(marker in combined for marker in ("cleanup", "smoke", "test artifact", "disposable")))
    )


def maybe_handle_hive_research_followup(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    session_hive_state_fn: Any,
    clear_hive_interaction_state_fn: Any,
    set_hive_interaction_state_fn: Any,
    research_topic_from_signal_fn: Any,
) -> dict[str, Any] | None:
    clean = " ".join(str(user_input or "").split()).strip()
    lowered = clean.lower()
    hive_state = session_hive_state_fn(session_id)
    if agent._is_pending_hive_create_confirmation_input(
        clean,
        session_id=session_id,
        source_context=source_context,
        hive_state=hive_state,
    ):
        return None

    active_resume = agent._maybe_resume_active_hive_task(
        lowered, session_id=session_id, source_context=source_context, hive_state=hive_state,
    )
    if active_resume is not None:
        return active_resume

    topic_hint = agent._extract_hive_topic_hint(clean)
    history = list((source_context or {}).get("conversation_history") or [])
    pending_topic_ids = [
        str(item).strip()
        for item in list(hive_state.get("pending_topic_ids") or [])
        if str(item).strip()
    ]
    shown_titles = agent._interaction_shown_titles(hive_state)
    if not agent._looks_like_hive_research_followup(
        lowered,
        topic_hint=topic_hint,
        has_pending_topics=bool(pending_topic_ids),
        shown_titles=shown_titles,
        history_has_task_list=agent._history_mentions_hive_task_list(history)
        or str(hive_state.get("interaction_mode") or "") == "hive_task_selection_pending",
    ):
        return None
    if not agent.public_hive_bridge.enabled():
        response = "Public Hive is not enabled on this runtime, so I can't claim a live Hive task."
        if agent._is_chat_truth_surface(source_context):
            return agent._chat_surface_hive_wording_result(
                session_id=session_id,
                user_input=clean,
                source_context=source_context,
                response_class=agent.ResponseClass.TASK_FAILED_USER_SAFE,
                reason="hive_research_followup_model_wording",
                observations={
                    "channel": "hive",
                    "kind": "unsupported",
                    "truth_source": "future_or_unsupported",
                    "truth_label": "future/unsupported",
                    "truth_status": "disabled",
                    "presence_claim_state": "unsupported",
                    "presence_truth_label": "future/unsupported",
                    "presence_note": "public Hive is not enabled on this runtime",
                },
                fallback_response=response,
            )
        return agent._fast_path_result(
            session_id=session_id,
            user_input=clean,
            response=response,
            confidence=0.9,
            source_context=source_context,
            reason="hive_research_followup",
        )
    if not agent.public_hive_bridge.write_enabled():
        response = "Hive task claiming is disabled here because public Hive auth is not configured for writes."
        if agent._is_chat_truth_surface(source_context):
            return agent._chat_surface_hive_wording_result(
                session_id=session_id,
                user_input=clean,
                source_context=source_context,
                response_class=agent.ResponseClass.TASK_FAILED_USER_SAFE,
                reason="hive_research_followup_model_wording",
                observations={
                    "channel": "hive",
                    "kind": "unsupported",
                    "truth_source": "future_or_unsupported",
                    "truth_label": "future/unsupported",
                    "truth_status": "write_disabled",
                    "presence_claim_state": "unsupported",
                    "presence_truth_label": "future/unsupported",
                    "presence_note": "public Hive writes are not configured on this runtime",
                },
                fallback_response=response,
            )
        return agent._fast_path_result(
            session_id=session_id,
            user_input=clean,
            response=response,
            confidence=0.9,
            source_context=source_context,
            reason="hive_research_followup",
        )

    queue_rows = agent.public_hive_bridge.list_public_research_queue(limit=12)
    ambiguous_selection = agent._looks_like_ambiguous_hive_selection_followup(
        lowered,
        has_pending_topics=bool(pending_topic_ids),
        history_has_task_list=agent._history_mentions_hive_task_list(history)
        or str(hive_state.get("interaction_mode") or "") == "hive_task_selection_pending",
    )
    selection_scope = agent._interaction_scoped_queue_rows(queue_rows, hive_state) or queue_rows
    allow_default_pick = not ambiguous_selection or len(selection_scope) <= 1
    signal = agent._select_hive_research_signal(
        queue_rows,
        lowered=lowered,
        topic_hint=topic_hint,
        pending_topic_ids=agent._interaction_pending_topic_ids(hive_state) or pending_topic_ids,
        allow_default_pick=allow_default_pick,
    )
    if signal is None:
        if queue_rows and ambiguous_selection:
            response = agent._render_hive_research_queue_choices(
                selection_scope,
                lead="I still have multiple real Hive tasks open. Pick one by name or short `#id` and I’ll start there.",
            )
            if agent._is_chat_truth_surface(source_context):
                return agent._chat_surface_hive_wording_result(
                    session_id=session_id,
                    user_input=clean,
                    source_context=source_context,
                    response_class=agent.ResponseClass.TASK_SELECTION_CLARIFICATION,
                    reason="hive_research_followup_model_wording",
                    observations=agent._chat_surface_hive_queue_observations(
                        selection_scope,
                        lead="Multiple matching open Hive tasks are still available.",
                        truth_payload=agent._bridge_hive_truth_from_rows(selection_scope),
                    ),
                    fallback_response=response,
                )
            return agent._fast_path_result(
                session_id=session_id,
                user_input=clean,
                response=response,
                confidence=0.9,
                source_context=source_context,
                reason="hive_research_followup",
            )
        if topic_hint:
            response = f"I couldn't find an open Hive task matching `#{topic_hint}`."
        else:
            response = "I couldn't map that follow-up to a concrete open Hive task."
        if agent._is_chat_truth_surface(source_context):
            return agent._chat_surface_hive_wording_result(
                session_id=session_id,
                user_input=clean,
                source_context=source_context,
                response_class=agent.ResponseClass.TASK_SELECTION_CLARIFICATION,
                reason="hive_research_followup_model_wording",
                observations={
                    "channel": "hive",
                    "kind": "selection_clarification",
                    **agent._hive_truth_observation_fields(agent._bridge_hive_truth_from_rows(queue_rows)),
                },
                fallback_response=response,
            )
        return agent._fast_path_result(
            session_id=session_id,
            user_input=clean,
            response=response,
            confidence=0.84,
            source_context=source_context,
            reason="hive_research_followup",
        )

    topic_id = str(signal.get("topic_id") or "").strip()
    title = str(signal.get("title") or topic_id or "Hive topic").strip()
    clear_hive_interaction_state_fn(session_id)

    wants_background = any(
        marker in lowered
        for marker in ("background", "in the background", "while we chat", "while i chat", "keep chatting")
    )
    if wants_background:
        import threading as _threading

        _signal = dict(signal)
        _bridge = agent.public_hive_bridge
        _curiosity = agent.curiosity
        _tracker = agent.hive_activity_tracker

        def _bg_research() -> None:
            with contextlib.suppress(Exception):
                research_topic_from_signal_fn(
                    _signal,
                    public_hive_bridge=_bridge,
                    curiosity=_curiosity,
                    hive_activity_tracker=_tracker,
                    session_id=session_id,
                    auto_claim=True,
                )

        _threading.Thread(target=_bg_research, name=f"bg-research-{topic_id[:12]}", daemon=True).start()
        response = f"Started Hive research on `{title}` in the background. We can keep chatting — I'll work on it."
        return agent._fast_path_result(
            session_id=session_id,
            user_input=clean,
            response=response,
            confidence=0.92,
            source_context=source_context,
            reason="hive_research_background",
        )

    agent._sync_public_presence(status="busy", source_context=source_context)
    result = research_topic_from_signal_fn(
        signal,
        public_hive_bridge=agent.public_hive_bridge,
        curiosity=agent.curiosity,
        hive_activity_tracker=agent.hive_activity_tracker,
        session_id=session_id,
        auto_claim=True,
    )
    if not result.ok:
        response = str(result.response_text or f"Failed to start Hive research for `{topic_id}`.").strip()
        if agent._is_chat_truth_surface(source_context):
            return agent._chat_surface_hive_wording_result(
                session_id=session_id,
                user_input=clean,
                source_context=source_context,
                response_class=agent.ResponseClass.TASK_FAILED_USER_SAFE,
                reason="hive_research_followup_model_wording",
                observations=agent._chat_surface_hive_research_result_observations(
                    topic_id=topic_id,
                    title=title,
                    result=result,
                ),
                fallback_response=response,
            )
        return agent._fast_path_result(
            session_id=session_id,
            user_input=clean,
            response=response,
            confidence=0.84,
            source_context=source_context,
            reason="hive_research_followup",
        )

    set_hive_interaction_state_fn(
        session_id,
        mode="hive_task_active",
        payload={
            "active_topic_id": topic_id,
            "active_title": title,
            "claim_id": str(result.claim_id or "").strip(),
        },
    )

    summary = [
        f"Started Hive research on `{title}` (#{topic_id[:8]}).",
    ]
    if result.claim_id:
        summary.append(f"Claim `{result.claim_id[:8]}` is active.")
    query_count = len(list((result.details or {}).get("query_results") or []))
    if result.status == "completed":
        summary.append("The first bounded research pass already ran and posted its result.")
    else:
        summary.append("The research lane is active.")
    if query_count:
        summary.append(f"Bounded queries run: {query_count}.")
    if result.artifact_ids:
        summary.append(f"Artifacts packed: {len(result.artifact_ids)}.")
    if result.candidate_ids:
        summary.append(f"Candidate notes: {len(result.candidate_ids)}.")
    if str(result.result_status or "").strip().lower() == "researching":
        summary.append(
            "This fast reply only means the first bounded research pass finished."
        )
        summary.append(
            "Topic stays `researching` because NULLA still needs more evidence before it can honestly mark the task solved."
        )
    response = " ".join(summary)
    return agent._fast_path_result(
        session_id=session_id,
        user_input=clean,
        response=response,
        confidence=0.9,
        source_context=source_context,
        reason="hive_research_followup",
    )


def maybe_resume_active_hive_task(
    agent: Any,
    lowered: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    hive_state: dict[str, Any],
    set_hive_interaction_state_fn: Any,
    research_topic_from_signal_fn: Any,
) -> dict[str, Any] | None:
    interaction_mode = str(hive_state.get("interaction_mode") or "").strip().lower()
    if interaction_mode != "hive_task_active":
        return None
    if not agent._is_proceed_message(lowered):
        return None
    payload = dict(hive_state.get("interaction_payload") or {})
    topic_id = str(payload.get("active_topic_id") or "").strip()
    title = str(payload.get("active_title") or topic_id or "Hive topic").strip()
    if not topic_id:
        return None
    if not agent.public_hive_bridge.enabled():
        return None

    agent._sync_public_presence(status="busy", source_context=source_context)
    result = research_topic_from_signal_fn(
        {"topic_id": topic_id},
        public_hive_bridge=agent.public_hive_bridge,
        curiosity=agent.curiosity,
        hive_activity_tracker=agent.hive_activity_tracker,
        session_id=session_id,
        auto_claim=True,
    )
    if not result.ok:
        response = str(result.response_text or f"Research on `{title}` didn't complete cleanly.").strip()
        return agent._fast_path_result(
            session_id=session_id,
            user_input=lowered,
            response=response,
            confidence=0.84,
            source_context=source_context,
            reason="hive_research_active_resume",
        )

    set_hive_interaction_state_fn(
        session_id,
        mode="hive_task_active",
        payload={
            "active_topic_id": topic_id,
            "active_title": title,
            "claim_id": str(result.claim_id or "").strip(),
        },
    )

    quality = dict((result.details or {}).get("quality_summary") or {})
    q_status = str(quality.get("research_quality_status") or result.result_status or "researching").strip()
    query_count = len(list((result.details or {}).get("query_results") or []))
    nonempty = int(quality.get("nonempty_query_count") or 0)
    promoted = int(quality.get("promoted_finding_count") or 0)
    domains = int(quality.get("source_domain_count") or 0)

    summary_parts = [f"Research on `{title}` (#{topic_id[:8]}) completed."]
    if result.claim_id:
        summary_parts.append(f"Claim `{result.claim_id[:8]}` is active.")
    summary_parts.append(f"Quality: {q_status}.")
    if query_count:
        summary_parts.append(f"Queries: {nonempty}/{query_count} returned evidence.")
    if domains:
        summary_parts.append(f"Source domains: {domains}.")
    if promoted:
        summary_parts.append(f"Promoted findings: {promoted}.")
    if result.artifact_ids:
        summary_parts.append(f"Artifacts: {len(result.artifact_ids)}.")
    if q_status not in ("grounded", "solved"):
        summary_parts.append("Topic stays open — more evidence needed for grounded status.")
    response = " ".join(summary_parts)
    return agent._fast_path_result(
        session_id=session_id,
        user_input=lowered,
        response=response,
        confidence=0.92,
        source_context=source_context,
        reason="hive_research_active_resume",
    )


def extract_hive_topic_hint(text: str) -> str:
    clean = str(text or "").strip()
    if not clean:
        return ""
    full_match = _HIVE_TOPIC_FULL_ID_RE.search(clean)
    if full_match:
        return str(full_match.group(1) or "").strip().lower()
    short_match = _HIVE_TOPIC_SHORT_ID_RE.search(clean)
    if short_match:
        return str(short_match.group(1) or "").strip().lower()
    bare_short_match = re.fullmatch(r"[#\s]*([0-9a-f]{8,12})[.!?]*", clean, re.IGNORECASE)
    if bare_short_match:
        return str(bare_short_match.group(1) or "").strip().lower()
    return ""


def maybe_handle_hive_status_followup(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    session_hive_state_fn: Any,
) -> dict[str, Any] | None:
    clean = " ".join(str(user_input or "").split()).strip()
    lowered = clean.lower()
    if not agent._looks_like_hive_status_followup(lowered):
        return None
    if not agent.public_hive_bridge.enabled():
        return None

    hive_state = session_hive_state_fn(session_id)
    history = list((source_context or {}).get("conversation_history") or [])
    topic_hint = agent._extract_hive_topic_hint(clean)
    watched_topic_ids = [
        str(item).strip()
        for item in list(hive_state.get("watched_topic_ids") or [])
        if str(item).strip()
    ]
    resolved_topic_id = agent._resolve_hive_status_topic_id(
        topic_hint=topic_hint,
        watched_topic_ids=watched_topic_ids,
        history=history,
        interaction_state=hive_state,
    )
    if not resolved_topic_id:
        return None

    packet = agent.public_hive_bridge.get_public_research_packet(resolved_topic_id)
    topic = dict(packet.get("topic") or {})
    state = dict(packet.get("execution_state") or {})
    counts = dict(packet.get("counts") or {})
    posts = [dict(item) for item in list(packet.get("posts") or [])]
    title = str(topic.get("title") or resolved_topic_id).strip()
    status = str(topic.get("status") or state.get("topic_status") or "").strip().lower()
    execution_state = str(state.get("execution_state") or "").strip().lower()
    active_claim_count = int(state.get("active_claim_count") or counts.get("active_claim_count") or 0)
    artifact_count = int(state.get("artifact_count") or 0)
    post_count = int(counts.get("post_count") or len(posts))

    if status in {"solved", "closed"}:
        lead = f"Yes. `{title}` (#{resolved_topic_id[:8]}) is `{status}`."
    elif status == "partial":
        lead = f"No. `{title}` (#{resolved_topic_id[:8]}) is `partial` and still needs follow-up work."
    elif status == "needs_improvement":
        lead = f"No. `{title}` (#{resolved_topic_id[:8]}) is `needs_improvement` and has been sent back for more work."
    elif status:
        lead = f"No. `{title}` (#{resolved_topic_id[:8]}) is still `{status}`."
    else:
        lead = f"`{title}` (#{resolved_topic_id[:8]}) is still in progress."

    summary: list[str] = [lead]
    if execution_state == "claimed" or active_claim_count > 0:
        summary.append(f"Active claims: {active_claim_count}.")
    if post_count:
        summary.append(f"Posts: {post_count}.")
    if artifact_count:
        summary.append(f"Artifacts: {artifact_count}.")
    if status == "researching" and artifact_count > 0:
        summary.append("The first bounded pass landed, but the topic did not clear the solve threshold yet.")
    latest_post = posts[0] if posts else {}
    latest_post_kind = str(latest_post.get("post_kind") or "").strip().lower()
    latest_post_body = " ".join(str(latest_post.get("body") or "").split()).strip()
    if latest_post_kind or latest_post_body:
        label = latest_post_kind or "post"
        if latest_post_body:
            summary.append(f"Latest {label}: {latest_post_body[:220]}.")
    response = " ".join(part for part in summary if part)
    deterministic_review_statuses = {"partial", "needs_improvement"}
    if agent._is_chat_truth_surface(source_context) and status not in deterministic_review_statuses:
        return agent._chat_surface_hive_wording_result(
            session_id=session_id,
            user_input=clean,
            source_context=source_context,
            response_class=agent.ResponseClass.TASK_STATUS,
            reason="hive_status_model_wording",
            observations=agent._chat_surface_hive_status_observations(
                topic_id=resolved_topic_id,
                title=title,
                status=status,
                execution_state=execution_state,
                active_claim_count=active_claim_count,
                artifact_count=artifact_count,
                post_count=post_count,
                latest_post_kind=latest_post_kind,
                latest_post_body=latest_post_body,
                truth_payload=packet,
            ),
            fallback_response=response,
        )
    return agent._fast_path_result(
        session_id=session_id,
        user_input=clean,
        response=response,
        confidence=0.92,
        source_context=source_context,
        reason="hive_status_followup",
    )


def resolve_hive_status_topic_id(
    agent: Any,
    *,
    topic_hint: str,
    watched_topic_ids: list[str],
    history: list[dict[str, Any]],
    interaction_state: dict[str, Any] | None = None,
) -> str:
    interaction_payload = dict((interaction_state or {}).get("interaction_payload") or {})
    active_topic = str(interaction_payload.get("active_topic_id") or "").strip().lower()
    if active_topic and (not topic_hint or active_topic == topic_hint or active_topic.startswith(topic_hint)):
        return active_topic
    watched = [str(item).strip().lower() for item in list(watched_topic_ids or []) if str(item).strip()]
    if topic_hint:
        for topic_id in reversed(watched):
            if topic_id == topic_hint or topic_id.startswith(topic_hint):
                return topic_id
    history_hints = agent._history_hive_topic_hints(history)
    for hint in [topic_hint, *history_hints]:
        clean_hint = str(hint or "").strip().lower()
        if not clean_hint:
            continue
        for topic_id in reversed(watched):
            if topic_id == clean_hint or topic_id.startswith(clean_hint):
                return topic_id
    if watched:
        return watched[-1]

    lookup_rows = agent.public_hive_bridge.list_public_topics(
        limit=32,
        statuses=("open", "researching", "disputed", "partial", "needs_improvement", "solved", "closed"),
    )
    for hint in [topic_hint, *history_hints]:
        clean_hint = str(hint or "").strip().lower()
        if not clean_hint:
            continue
        for row in lookup_rows:
            topic_id = str(row.get("topic_id") or "").strip().lower()
            if topic_id == clean_hint or topic_id.startswith(clean_hint):
                return topic_id
    return ""


def looks_like_hive_status_followup(lowered: str) -> bool:
    text = str(lowered or "").strip().lower()
    if not text:
        return False
    if not any(marker in text for marker in ("research", "hive", "topic", "task", "done", "complete", "status", "finish", "finished")):
        return False
    for phrase in (
        "is research complete",
        "is the research complete",
        "is it complete",
        "is it done",
        "is research done",
        "did it finish",
        "did research finish",
        "is the task complete",
        "what is the status",
        "status?",
        "what's the status",
        "is that solved",
        "is it solved",
    ):
        if phrase in text:
            return True
    return False


def history_hive_topic_hints(agent: Any, history: list[dict[str, Any]] | None) -> list[str]:
    hints: list[str] = []
    for message in reversed(list(history or [])[-8:]):
        content = str(message.get("content") or "").strip()
        hint = agent._extract_hive_topic_hint(content)
        if hint:
            hints.append(hint)
    return hints


def looks_like_hive_research_followup(
    agent: Any,
    lowered: str,
    *,
    topic_hint: str,
    has_pending_topics: bool,
    shown_titles: list[str],
    history_has_task_list: bool,
) -> bool:
    text = str(lowered or "").strip().lower()
    normalized_text = agent._normalize_hive_topic_text(text)
    if topic_hint:
        bare_hint = f"#{topic_hint}"
        compact_text = re.sub(r"\s+", "", text.rstrip(".!?"))
        if compact_text in {topic_hint, bare_hint}:
            return True
        if any(
            phrase in text
            for phrase in (
                "this one",
                "that one",
                "go with this one",
                "lets go with this one",
                "let's go with this one",
                "start this",
                "start that",
                "start #",
                "claim #",
                "take this",
                "take #",
                "claim this",
                "pick this",
                "pick #",
                "work on #",
                "research #",
                "do #",
            )
        ):
            return True
        return bool(
            bare_hint in compact_text
            and any(
                phrase in text
                for phrase in (
                    "full research",
                    "research on this",
                    "research this",
                    "do this in full",
                    "do all step by step",
                    "lets do this",
                    "let's do this",
                    "do this",
                    "start this",
                    "start that",
                    "work on this",
                    "work on that",
                    "deliver to hive",
                    "deliver it to hive",
                    "post it to hive",
                    "submit it to hive",
                    "pls",
                    "please",
                    "full",
                )
            )
        )
    if (has_pending_topics or history_has_task_list) and shown_titles:
        normalized_titles = [
            agent._normalize_hive_topic_text(str(title or ""))
            for title in list(shown_titles or [])
            if str(title or "").strip()
        ]
        if normalized_text and normalized_text in normalized_titles:
            return True
    if (has_pending_topics or history_has_task_list) and any(
        phrase in text
        for phrase in (
            "yes",
            "ok",
            "okay",
            "ok let's go",
            "ok lets go",
            "lets go",
            "let's go",
            "go ahead",
            "do it",
            "do one",
            "start it",
            "take it",
            "claim it",
            "work on it",
            "review it",
            "review this",
            "look into it",
            "research it",
            "pick one",
            "do all step by step",
            "deliver to hive",
            "deliver it to hive",
            "post it to hive",
            "submit it to hive",
            "proceed",
            "carry on",
            "continue",
            "do all",
            "start working",
            "all good",
            "proceed with next steps",
            "proceed with that",
            "just do it",
            "deliver it",
            "submit it",
        )
    ):
        return True
    if (has_pending_topics or history_has_task_list) and any(
        phrase in text
        for phrase in (
            "first one",
            "1st one",
            "second one",
            "2nd one",
            "third one",
            "3rd one",
            "take the first one",
            "take the second one",
            "review the first one",
            "review the second one",
            "review the problem",
            "check the problem",
            "help with this",
            "help with that",
            "do all step by step",
        )
    ):
        return True
    if any(
        phrase in text
        for phrase in (
            "go with this one",
            "lets go with this one",
            "let's go with this one",
            "start this one",
            "start that one",
            "take this one",
            "take that one",
            "claim this one",
            "claim that one",
        )
    ) and any(marker in text for marker in ("[researching", "[open", "[disputed", "topic", "task", "hive", "#")):
        return True
    if "hive" in text and any(phrase in text for phrase in ("pick one", "start the hive research", "start hive research", "pick a task", "choose one")):
        return True
    return bool("research" in text and "pick one" in text)
