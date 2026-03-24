from __future__ import annotations

import argparse
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core import audit_logger, feedback_engine, policy_engine
from core.agent_runtime import checkpoints as agent_checkpoint_runtime
from core.agent_runtime import fast_command_surface as agent_fast_command_surface
from core.agent_runtime import hive_followups as agent_hive_followups
from core.agent_runtime import hive_runtime as agent_hive_runtime
from core.agent_runtime import memory_runtime as agent_memory_runtime
from core.agent_runtime import nullabook as agent_nullabook_runtime
from core.agent_runtime import orchestrator as agent_orchestrator_runtime
from core.agent_runtime import presence as agent_presence_runtime
from core.agent_runtime import response as agent_response_runtime
from core.agent_runtime import response_policy as agent_response_policy
from core.agent_runtime import turn_dispatch as agent_turn_dispatch
from core.agent_runtime import turn_frontdoor as agent_turn_frontdoor
from core.agent_runtime import turn_reasoning as agent_turn_reasoning
from core.agent_runtime.builder_facade import BuilderFacadeMixin
from core.agent_runtime.chat_surface_facade import ChatSurfaceFacadeMixin
from core.agent_runtime.fast_path_facade import FastPathFacadeMixin
from core.agent_runtime.hive_topic_facade import HiveTopicFacadeMixin
from core.agent_runtime.public_hive_support import PublicHiveSupportMixin
from core.agent_runtime.research_tool_loop_facade import ResearchToolLoopFacadeMixin
from core.agent_runtime.task_persistence_support import TaskPersistenceSupportMixin
from core.autonomous_topic_research import pick_autonomous_research_signal, research_topic_from_signal
from core.channel_actions import dispatch_outbound_post_intent, parse_channel_post_intent
from core.credit_ledger import (
    escrow_credits_for_task,
    get_credit_balance,
    transfer_credits,
)
from core.curiosity_roamer import CuriosityRoamer
from core.hive_activity_tracker import (
    HiveActivityTracker,
    clear_hive_interaction_state,
    prune_stale_hive_interaction_state,
    session_hive_state,
    set_hive_interaction_state,
    update_session_hive_state,
)
from core.human_input_adapter import adapt_user_input, runtime_session_id
from core.identity_manager import load_active_persona
from core.knowledge_fetcher import request_relevant_holders
from core.local_operator_actions import dispatch_operator_action, parse_operator_action_intent
from core.logging_config import setup_logging
from core.media_analysis_pipeline import MediaAnalysisPipeline
from core.media_ingestion import build_media_context_snippets, ingest_media_evidence
from core.memory_first_router import MemoryFirstRouter
from core.onboarding import get_agent_display_name
from core.parent_orchestrator import orchestrate_parent_task
from core.persistent_memory import (
    append_conversation_event,
    ensure_memory_files,
    maybe_handle_memory_command,
    search_user_heuristics,
)
from core.public_hive_bridge import PublicHiveBridge
from core.reasoning_engine import (
    Plan,
    build_plan,
    explicit_planner_style_requested,
    inspect_user_response_shape,
    render_response,
    should_use_planner_renderer,
)
from core.runtime_continuity import (
    create_runtime_checkpoint,
    finalize_runtime_checkpoint,
    get_runtime_checkpoint,
    latest_resumable_checkpoint,
    mark_stale_runtime_checkpoints_interrupted,
    record_runtime_tool_progress,
    resume_runtime_checkpoint,
    update_runtime_checkpoint,
)
from core.runtime_execution_tools import execute_runtime_tool, looks_like_execution_request
from core.runtime_task_events import emit_runtime_event
from core.shard_synthesizer import build_generalized_query, from_task_result
from core.task_router import (
    chat_surface_execution_task_class,
    classify,
    create_task_record,
    load_task_record,
    looks_like_explicit_lookup_request,
    looks_like_public_entity_lookup_request,
    looks_like_semantic_hive_request,
    model_execution_profile,
)
from core.tiered_context_loader import TieredContextLoader
from core.tool_intent_executor import (
    _looks_like_workspace_bootstrap_request,
    execute_tool_intent,
    plan_tool_workflow,
    render_capability_truth_response,
    should_attempt_tool_intent,
)
from core.user_preferences import load_preferences, maybe_handle_preference_command
from network import signer as signer_mod
from retrieval.swarm_query import dispatch_query_shard
from retrieval.web_adapter import WebAdapter

_log = logging.getLogger(__name__)


_HIVE_TOPIC_FULL_ID_RE = re.compile(r"\b([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\b", re.IGNORECASE)
_HIVE_TOPIC_SHORT_ID_RE = re.compile(r"#\s*([0-9a-f]{8,12})\b", re.IGNORECASE)
_HIVE_CREATE_HARD_PRIVACY_RISKS = {
    "identity_marker",
    "name_disclosure",
    "location_disclosure",
    "phone_number",
    "postal_address",
}


@dataclass
class AgentRuntime:
    backend_name: str
    device: str
    persona_id: str
    swarm_enabled: bool


@dataclass
class GateDecision:
    mode: str
    reason: str
    requires_user_approval: bool
    allowed_actions: list[str]


class ResponseClass(str, Enum):
    SMALLTALK = "smalltalk"
    UTILITY_ANSWER = "utility_answer"
    TASK_LIST = "task_list"
    TASK_SELECTION_CLARIFICATION = "task_selection_clarification"
    TASK_STARTED = "task_started"
    TASK_STATUS = "task_status"
    TASK_FAILED_USER_SAFE = "task_failed_user_safe"
    RESEARCH_PROGRESS = "research_progress"
    APPROVAL_REQUIRED = "approval_required"
    SYSTEM_ERROR_USER_SAFE = "system_error_user_safe"
    GENERIC_CONVERSATION = "generic_conversation"


@dataclass
class ChatTurnResult:
    text: str
    response_class: ResponseClass
    workflow_summary: str = ""
    debug_origin: str | None = None
    allow_planner_style: bool = False


class NullaAgent(
    FastPathFacadeMixin,
    HiveTopicFacadeMixin,
    ChatSurfaceFacadeMixin,
    PublicHiveSupportMixin,
    TaskPersistenceSupportMixin,
    BuilderFacadeMixin,
    ResearchToolLoopFacadeMixin,
):
    ResponseClass = ResponseClass
    GateDecision = GateDecision
    ChatTurnResult = ChatTurnResult

    def __init__(self, backend_name: str, device: str, persona_id: str = "default"):
        self.backend_name = backend_name
        self.device = device
        self.persona_id = persona_id
        self.swarm_enabled = True
        self.context_loader = TieredContextLoader()
        self.memory_router = MemoryFirstRouter()
        self.curiosity = CuriosityRoamer()
        self.media_pipeline = MediaAnalysisPipeline()
        self.public_hive_bridge = PublicHiveBridge()
        self.hive_activity_tracker = HiveActivityTracker()
        self._public_presence_lock = threading.Lock()
        self._activity_lock = threading.Lock()
        self._public_presence_running = False
        self._public_presence_registered = False
        self._public_presence_status = "idle"
        self._public_presence_source_context: dict[str, object] | None = None
        self._public_presence_thread: threading.Thread | None = None
        self._idle_commons_running = False
        self._idle_commons_thread: threading.Thread | None = None
        self._last_user_activity_ts = time.time()
        self._last_idle_commons_ts = 0.0
        self._last_idle_hive_research_ts = 0.0
        self._idle_commons_seed_index = 0
        self._hive_create_pending: dict[str, dict[str, Any]] = {}
        self._nullabook_pending: dict[str, dict[str, str]] = {}

    def start(self) -> AgentRuntime:
        setup_logging(
            level=str(policy_engine.get("observability.log_level", "INFO")),
            json_output=bool(policy_engine.get("observability.json_logs", True)),
        )
        mark_stale_runtime_checkpoints_interrupted()
        ensure_memory_files()
        _ = load_active_persona(self.persona_id)
        self._sync_public_presence(status=self._idle_public_presence_status())
        if self._background_runtime_threads_enabled():
            self._start_public_presence_heartbeat()
            self._start_idle_commons_loop()

        return AgentRuntime(
            backend_name=self.backend_name,
            device=self.device,
            persona_id=self.persona_id,
            swarm_enabled=self.swarm_enabled,
        )

    def _background_runtime_threads_enabled(self) -> bool:
        if str(self.backend_name or "").strip().lower().startswith("test-"):
            return False
        if str(self.device or "").strip().lower().endswith("-test"):
            return False
        return not os.environ.get("PYTEST_CURRENT_TEST")

    def run_once(
        self,
        user_input: str,
        *,
        session_id_override: str | None = None,
        source_context: dict[str, object] | None = None,
    ) -> dict:
        persona = load_active_persona(self.persona_id)
        session_id = session_id_override or runtime_session_id(device=self.device, persona_id=self.persona_id)
        self._mark_user_activity()
        runtime_source_context = dict(source_context or {})
        interpreted = adapt_user_input(user_input, session_id=session_id)
        effective_input = interpreted.reconstructed_text or interpreted.normalized_text or user_input
        normalized_input = str(interpreted.normalized_text or "").strip()
        checkpoint_bundle = self._prepare_runtime_checkpoint(
            session_id=session_id,
            raw_user_input=user_input,
            effective_input=effective_input,
            source_context=runtime_source_context,
            allow_followup_resume=not self._blocks_runtime_followup_resume(
                session_id=session_id,
                source_context=runtime_source_context,
            ),
        )
        runtime_source_context = dict(checkpoint_bundle.get("source_context") or runtime_source_context)
        checkpoint_state = str(checkpoint_bundle.get("state") or "created")
        if checkpoint_state == "missing_resume":
            return self._fast_path_result(
                session_id=session_id,
                user_input=user_input,
                response=(
                    "No interrupted runtime task is available to resume in this session. "
                    "If you were retrying a Discord post: set DISCORD_WEBHOOK_URL or DISCORD_BOT_TOKEN+DISCORD_CHANNEL_ID. "
                    "For Telegram: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID. Then retry your original message."
                ),
                confidence=0.78,
                source_context=runtime_source_context,
                reason="runtime_resume_missing",
            )
        effective_input = str(checkpoint_bundle.get("effective_input") or effective_input)
        if checkpoint_state == "resumed":
            interpreted = adapt_user_input(effective_input, session_id=session_id)
            normalized_input = str(interpreted.normalized_text or "").strip()
        source_context = runtime_source_context
        source_surface = str((source_context or {}).get("surface", "cli")).lower()
        prune_stale_hive_interaction_state(session_id)
        self._emit_runtime_event(
            source_context,
            event_type="task_resumed" if checkpoint_state == "resumed" else "task_received",
            message=(
                f"Resuming interrupted task: {self._runtime_preview(effective_input)}"
                if checkpoint_state == "resumed"
                else f"Received request: {self._runtime_preview(effective_input)}"
            ),
            request_preview=self._runtime_preview(effective_input, limit=160),
            resume_available=checkpoint_state == "resumed",
        )

        frontdoor_bundle = self._handle_turn_frontdoor(
            raw_user_input=user_input,
            effective_input=effective_input,
            normalized_input=normalized_input,
            source_surface=source_surface,
            session_id=session_id,
            source_context=source_context,
            persona=persona,
            interpreted=interpreted,
        )
        frontdoor_result = frontdoor_bundle.get("result")
        if frontdoor_result is not None:
            return frontdoor_result

        self._sync_public_presence(status="busy", source_context=source_context)
        try:
            turn_bundle = self._prepare_turn_task_bundle(
                effective_input=effective_input,
                user_input=user_input,
                session_id=session_id,
                source_context=source_context,
                interpreted=interpreted,
            )
            frontdoor_result = turn_bundle.get("result")
            if frontdoor_result is not None:
                return frontdoor_result
            task = turn_bundle["task"]
            classification = dict(turn_bundle.get("classification") or {})

            return self._execute_grounded_turn(
                task=task,
                effective_input=effective_input,
                classification=classification,
                interpreted=interpreted,
                persona=persona,
                session_id=session_id,
                source_context=source_context,
            )
        except Exception as exc:
            self._finalize_runtime_checkpoint(
                source_context,
                status="interrupted",
                failure_text=str(exc),
            )
            self._emit_runtime_event(
                source_context,
                event_type="task_interrupted",
                message=f"Task failed: {self._runtime_preview(str(exc), limit=200)}",
            )
            raise
        finally:
            self._sync_public_presence(
                status=self._idle_public_presence_status(),
                source_context=source_context,
            )

    def _maybe_handle_memory_fast_path(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any] | None:
        return agent_memory_runtime.maybe_handle_memory_fast_path(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
            maybe_handle_memory_command_fn=maybe_handle_memory_command,
        )

    def _model_final_response_text(self, model_execution: Any) -> str:
        return agent_memory_runtime.model_final_response_text(model_execution)

    def _prepare_turn_task_bundle(
        self,
        *,
        effective_input: str,
        user_input: str,
        session_id: str,
        source_context: dict[str, object] | None,
        interpreted: Any,
    ) -> dict[str, Any]:
        return agent_turn_dispatch.prepare_turn_task_bundle(
            self,
            effective_input=effective_input,
            user_input=user_input,
            session_id=session_id,
            source_context=source_context,
            interpreted=interpreted,
            classify_fn=classify,
            parse_channel_post_intent_fn=parse_channel_post_intent,
            dispatch_outbound_post_intent_fn=dispatch_outbound_post_intent,
            parse_operator_action_intent_fn=parse_operator_action_intent,
            dispatch_operator_action_fn=dispatch_operator_action,
        )

    def _handle_turn_frontdoor(
        self,
        *,
        raw_user_input: str,
        effective_input: str,
        normalized_input: str,
        source_surface: str,
        session_id: str,
        source_context: dict[str, object] | None,
        persona: Any,
        interpreted: Any,
    ) -> dict[str, Any]:
        return agent_turn_frontdoor.handle_turn_frontdoor(
            self,
            raw_user_input=raw_user_input,
            effective_input=effective_input,
            normalized_input=normalized_input,
            source_surface=source_surface,
            session_id=session_id,
            source_context=source_context,
            persona=persona,
            interpreted=interpreted,
            maybe_handle_preference_command_fn=maybe_handle_preference_command,
            set_hive_interaction_state_fn=set_hive_interaction_state,
        )

    def _execute_grounded_turn(
        self,
        *,
        task: Any,
        effective_input: str,
        classification: dict[str, Any],
        interpreted: Any,
        persona: Any,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_turn_reasoning.execute_grounded_turn(
            self,
            task=task,
            effective_input=effective_input,
            classification=classification,
            interpreted=interpreted,
            persona=persona,
            session_id=session_id,
            source_context=source_context,
            adapt_user_input_fn=adapt_user_input,
            ingest_media_evidence_fn=ingest_media_evidence,
            build_media_context_snippets_fn=build_media_context_snippets,
            orchestrate_parent_task_fn=orchestrate_parent_task,
            build_plan_fn=build_plan,
            render_response_fn=render_response,
            explicit_planner_style_requested_fn=explicit_planner_style_requested,
            should_use_planner_renderer_fn=should_use_planner_renderer,
            request_relevant_holders_fn=request_relevant_holders,
            dispatch_query_shard_fn=dispatch_query_shard,
            build_generalized_query_fn=build_generalized_query,
            feedback_engine_module=feedback_engine,
            policy_engine_module=policy_engine,
            from_task_result_fn=from_task_result,
            append_conversation_event_fn=append_conversation_event,
            audit_logger_module=audit_logger,
        )

    def _chat_surface_cache_or_memory_source(self, model_execution: Any) -> bool:
        return agent_memory_runtime.chat_surface_cache_or_memory_source(model_execution)

    def _chat_surface_model_final_text(self, model_execution: Any) -> str:
        return agent_memory_runtime.chat_surface_model_final_text(model_execution)

    def _chat_surface_honest_degraded_response(
        self,
        model_execution: Any,
        *,
        user_input: str = "",
        interpretation: Any | None = None,
    ) -> str:
        return agent_memory_runtime.chat_surface_honest_degraded_response(
            self,
            model_execution,
            user_input=user_input,
            interpretation=interpretation,
        )

    def _maybe_handle_credit_command(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None = None,
    ) -> dict | None:
        return agent_fast_command_surface.maybe_handle_credit_command(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
            signer_module=signer_mod,
            transfer_credits_fn=transfer_credits,
            get_credit_balance_fn=get_credit_balance,
            escrow_credits_for_task_fn=escrow_credits_for_task,
            session_hive_state_fn=session_hive_state,
            runtime_session_id_fn=runtime_session_id,
        )

    def _fast_path_result(
        self,
        *,
        session_id: str,
        user_input: str,
        response: str,
        confidence: float,
        source_context: dict[str, object] | None,
        reason: str,
    ) -> dict:
        return agent_fast_command_surface.fast_path_result(
            self,
            session_id=session_id,
            user_input=user_input,
            response=response,
            confidence=confidence,
            source_context=source_context,
            reason=reason,
            append_conversation_event_fn=append_conversation_event,
            audit_logger_module=audit_logger,
        )

    def _action_fast_path_result(
        self,
        *,
        task_id: str,
        session_id: str,
        user_input: str,
        response: str,
        confidence: float,
        source_context: dict[str, object] | None,
        reason: str,
        success: bool,
        details: dict[str, object] | None = None,
        mode_override: str | None = None,
        task_outcome: str | None = None,
        learned_plan: Plan | None = None,
        workflow_summary: str = "",
    ) -> dict:
        return agent_fast_command_surface.action_fast_path_result(
            self,
            task_id=task_id,
            session_id=session_id,
            user_input=user_input,
            response=response,
            confidence=confidence,
            source_context=source_context,
            reason=reason,
            success=success,
            details=details,
            mode_override=mode_override,
            task_outcome=task_outcome,
            learned_plan=learned_plan,
            workflow_summary=workflow_summary,
            append_conversation_event_fn=append_conversation_event,
            audit_logger_module=audit_logger,
            explicit_planner_style_requested_fn=explicit_planner_style_requested,
        )

    def _is_chat_truth_surface(self, source_context: dict[str, object] | None) -> bool:
        surface = str((source_context or {}).get("surface", "") or "").strip().lower()
        return surface in {"channel", "openclaw", "api"}

    def _chat_truth_fast_path_backing_sources(self, reason: str) -> list[str]:
        mapping = {
            "live_info_fast_path": ["web_lookup"],
            "hive_activity_command": ["hive"],
            "hive_research_followup": ["hive"],
            "hive_status_followup": ["hive"],
        }
        return list(mapping.get(str(reason or "").strip(), []))

    def _chat_truth_action_backing_sources(
        self,
        *,
        reason: str,
        success: bool,
        task_outcome: str | None,
    ) -> list[str]:
        if not success and str(task_outcome or "").strip().lower() != "pending_approval":
            return []
        normalized = str(reason or "").strip().lower()
        sources: list[str] = []
        if normalized.startswith("hive_topic_create_"):
            sources.append("hive")
        if normalized.startswith("channel_post_"):
            sources.append("channel_action")
        if normalized.startswith("operator_action_"):
            sources.append("operator_action")
        if normalized.startswith("model_tool_intent_"):
            sources.append("tool_intent")
        return sources or (["tool_action"] if success else [])

    def _chat_truth_claim_metrics(
        self,
        response_text: str,
        *,
        tool_backing_sources: list[str],
    ) -> dict[str, object]:
        normalized = " ".join(str(response_text or "").split()).strip().lower()
        claim_patterns = (
            r"\b(i|we)\s+(checked|searched|looked up|looked|fetched|pulled|read|wrote|edited|updated|created|posted|sent|ran|executed|claimed)\b",
            r"^started hive research on\b",
            r"^created hive task\b",
            r"\blive weather results\b",
        )
        claim_present = any(re.search(pattern, normalized) for pattern in claim_patterns)
        claim_count = 1 if claim_present else 0
        backed_sources = [str(item).strip() for item in list(tool_backing_sources or []) if str(item).strip()]
        backed_claim_count = claim_count if backed_sources else 0
        return {
            "tool_claim_present": claim_present,
            "tool_claim_count": claim_count,
            "tool_backed_claim_present": bool(backed_claim_count),
            "tool_backed_claim_count": backed_claim_count,
            "tool_unbacked_claim_count": max(0, claim_count - backed_claim_count),
            "tool_backing_sources": backed_sources,
        }

    def _emit_chat_truth_metrics(
        self,
        *,
        task_id: str,
        reason: str,
        response_text: str,
        response_class: str,
        source_context: dict[str, object] | None,
        rendered_via: str,
        fast_path_hit: bool,
        model_inference_used: bool,
        model_final_answer_hit: bool,
        model_execution_source: str,
        tool_backing_sources: list[str] | None = None,
    ) -> None:
        if not self._is_chat_truth_surface(source_context):
            return
        surface = str((source_context or {}).get("surface", "") or "").strip().lower()
        render_metrics = inspect_user_response_shape(
            response_text,
            surface=surface,
            rendered_via=rendered_via,
        )
        claim_metrics = self._chat_truth_claim_metrics(
            response_text,
            tool_backing_sources=list(tool_backing_sources or []),
        )
        audit_logger.log(
            "agent_chat_truth_metrics",
            target_id=task_id,
            target_type="task",
            details={
                "version": "m1-r01",
                "reason": reason,
                "response_class": response_class,
                "source_surface": (source_context or {}).get("surface"),
                "source_platform": (source_context or {}).get("platform"),
                "rendered_via": rendered_via,
                "fast_path_hit": bool(fast_path_hit),
                "model_inference_used": bool(model_inference_used),
                "model_final_answer_hit": bool(model_final_answer_hit),
                "model_execution_source": model_execution_source,
                "planner_leakage": bool(render_metrics["planner_leakage"]),
                "template_renderer_hit": bool(render_metrics["template_renderer_hit"]),
                "template_fallback_hit": bool(render_metrics["template_fallback_hit"]),
                **claim_metrics,
            },
        )

    def _model_routing_profile(
        self,
        *,
        user_input: str,
        classification: dict[str, Any],
        interpretation: Any,
        source_context: dict[str, object] | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        routed = dict(classification or {})
        is_chat_surface = self._is_chat_truth_surface(source_context)
        planner_style_requested = bool(is_chat_surface and explicit_planner_style_requested(user_input))
        if is_chat_surface:
            routed["task_class"] = chat_surface_execution_task_class(
                str(classification.get("task_class") or "unknown"),
                user_input=user_input,
                context=getattr(interpretation, "as_context", lambda: {})(),
            )
            routed["routing_origin_task_class"] = str(classification.get("task_class") or "unknown")
            routed["planner_style_requested"] = planner_style_requested
        return routed, model_execution_profile(
            str(routed.get("task_class") or "unknown"),
            chat_surface=is_chat_surface,
            planner_style_requested=planner_style_requested,
        )

    def _explicit_runtime_workflow_request(
        self,
        *,
        user_input: str,
        task_class: str,
    ) -> bool:
        text = " ".join(str(user_input or "").split()).strip()
        if not text:
            return False
        lowered = f" {text.lower()} "
        if looks_like_execution_request(text, task_class="unknown"):
            return True
        if any(marker in lowered for marker in (" retry ", " rerun ", " rerun it ", " run tests ", " inspect logs ")):
            return True
        if any(marker in lowered for marker in (" find ", " inspect ", " trace ", " locate ", " search ", " read ", " open ")) and any(
            marker in lowered
            for marker in (
                " repo ",
                " repository ",
                " workspace ",
                " code ",
                " file ",
                " files ",
                " wiring ",
                " path ",
                " line ",
                " lines ",
                " function ",
                " symbol ",
                " import ",
            )
        ):
            return True
        if ("http://" in lowered or "https://" in lowered) and any(
            marker in lowered for marker in (" open ", " fetch ", " browse ", " render ")
        ):
            return True
        return bool(str(task_class or "").strip().lower() == "integration_orchestration" and any(marker in lowered for marker in (" write the files ", " edit the files ", " patch the files ", " create the files ", " generate the files ")))

    def _should_keep_ai_first_chat_lane(
        self,
        *,
        user_input: str,
        classification: dict[str, Any],
        interpretation: Any,
        source_context: dict[str, object] | None,
        checkpoint_state: dict[str, Any] | None,
    ) -> bool:
        if not self._is_chat_truth_surface(source_context):
            return False
        checkpoint_state = dict(checkpoint_state or {})
        if checkpoint_state.get("executed_steps") or checkpoint_state.get("pending_tool_payload") or checkpoint_state.get(
            "last_tool_payload"
        ):
            return False
        # Generic "do it/proceed" phrasing should only evict the chat lane when there is
        # actual resumable runtime state. Otherwise normal conversational requests like
        # "do all step by step" get misrouted into the tool planner and degrade to a
        # fake failure instead of using the provider/chat surface.
        if self._looks_like_explicit_resume_request(user_input):
            return False
        if self._live_info_mode(user_input, interpretation=interpretation):
            return True
        task_class = str(classification.get("task_class") or "unknown")
        routed_task_class = chat_surface_execution_task_class(
            task_class,
            user_input=user_input,
            context=getattr(interpretation, "as_context", lambda: {})(),
        )
        if self._explicit_runtime_workflow_request(
            user_input=user_input,
            task_class=task_class,
        ):
            return False
        lowered_input = " ".join(str(user_input or "").split()).strip().lower()
        if self._looks_like_hive_topic_drafting_request(lowered_input):
            return True
        if looks_like_public_entity_lookup_request(lowered_input) or looks_like_explicit_lookup_request(lowered_input):
            return False
        if any(marker in lowered_input for marker in ("create task", "create new task", "new task for", "add task", "add to hive", "add to the hive")):
            return False
        if "create" in lowered_input and "task" in lowered_input and ("hive" in lowered_input or "topic" in lowered_input):
            return False
        if self._looks_like_builder_request(user_input.lower()):
            return True
        return routed_task_class in {
            "chat_conversation",
            "chat_research",
            "general_advisory",
            "business_advisory",
            "food_nutrition",
            "relationship_advisory",
            "creative_ideation",
            "debugging",
            "dependency_resolution",
            "config",
            "system_design",
            "file_inspection",
            "shell_guidance",
            "integration_orchestration",
        }

    def _prepare_runtime_checkpoint(
        self,
        *,
        session_id: str,
        raw_user_input: str,
        effective_input: str,
        source_context: dict[str, object] | None,
        allow_followup_resume: bool = True,
    ) -> dict[str, Any]:
        return agent_checkpoint_runtime.prepare_runtime_checkpoint(
            self,
            session_id=session_id,
            raw_user_input=raw_user_input,
            effective_input=effective_input,
            source_context=source_context,
            allow_followup_resume=allow_followup_resume,
            latest_resumable_checkpoint_fn=latest_resumable_checkpoint,
            resume_runtime_checkpoint_fn=resume_runtime_checkpoint,
            create_runtime_checkpoint_fn=create_runtime_checkpoint,
        )

    def _blocks_runtime_followup_resume(
        self,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> bool:
        if self._nullabook_pending.get(session_id):
            return True
        hive_state = session_hive_state(session_id)
        if self._has_pending_hive_create_confirmation(
            session_id=session_id,
            hive_state=hive_state,
            source_context=source_context,
        ):
            return True
        interaction_mode = str(hive_state.get("interaction_mode") or "").strip().lower()
        return interaction_mode in {"hive_task_active", "hive_task_selection_pending"}

    def _resolve_runtime_task(
        self,
        *,
        effective_input: str,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> Any:
        return agent_checkpoint_runtime.resolve_runtime_task(
            self,
            effective_input=effective_input,
            session_id=session_id,
            source_context=source_context,
            get_runtime_checkpoint_fn=get_runtime_checkpoint,
            load_task_record_fn=load_task_record,
            create_task_record_fn=create_task_record,
        )

    def _update_runtime_checkpoint_context(
        self,
        source_context: dict[str, object] | None,
        *,
        task_id: str | None = None,
        task_class: str | None = None,
    ) -> None:
        agent_checkpoint_runtime.update_runtime_checkpoint_context(
            source_context,
            task_id=task_id,
            task_class=task_class,
            update_runtime_checkpoint_fn=update_runtime_checkpoint,
        )

    def _finalize_runtime_checkpoint(
        self,
        source_context: dict[str, object] | None,
        *,
        status: str,
        final_response: str = "",
        failure_text: str = "",
    ) -> None:
        agent_checkpoint_runtime.finalize_runtime_checkpoint(
            source_context,
            status=status,
            final_response=final_response,
            failure_text=failure_text,
            finalize_runtime_checkpoint_fn=finalize_runtime_checkpoint,
        )

    def _runtime_checkpoint_id(self, source_context: dict[str, object] | None) -> str:
        return agent_checkpoint_runtime.runtime_checkpoint_id(source_context)

    def _merge_runtime_source_contexts(
        self,
        primary: dict[str, Any] | None,
        secondary: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return agent_checkpoint_runtime.merge_runtime_source_contexts(self, primary, secondary)

    def _looks_like_explicit_resume_request(self, text: str) -> bool:
        normalized = self._resume_request_key(text)
        return normalized in {
            "continue",
            "resume",
            "retry",
            "try again",
            "continue please",
            "resume please",
            "keep going",
            "go on",
            "pick up where you left off",
        }

    def _looks_like_resume_request(self, text: str) -> bool:
        return self._looks_like_explicit_resume_request(text) or self._is_proceed_message(text)

    def _resume_request_key(self, text: str) -> str:
        return " ".join(str(text or "").strip().lower().split())

    def _session_hive_state(self, session_id: str) -> dict[str, Any]:
        return session_hive_state(session_id)

    def _set_hive_interaction_state(self, session_id: str, *, mode: str, payload: dict[str, Any]) -> None:
        set_hive_interaction_state(session_id, mode=mode, payload=payload)

    def _clear_hive_interaction_state(self, session_id: str) -> None:
        clear_hive_interaction_state(session_id)

    def _research_topic_from_signal(self, signal: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return research_topic_from_signal(signal, **kwargs)

    def _pick_autonomous_research_signal(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        return pick_autonomous_research_signal(rows)

    def _plan_tool_workflow(self, *args: Any, **kwargs: Any) -> Any:
        return plan_tool_workflow(*args, **kwargs)

    def _execute_tool_intent(self, *args: Any, **kwargs: Any) -> Any:
        return execute_tool_intent(*args, **kwargs)

    def _planned_search_query(self, *args: Any, **kwargs: Any) -> Any:
        return WebAdapter.planned_search_query(*args, **kwargs)

    def _search_query(self, *args: Any, **kwargs: Any) -> Any:
        return WebAdapter.search_query(*args, **kwargs)

    def _should_attempt_tool_intent(self, *args: Any, **kwargs: Any) -> Any:
        return should_attempt_tool_intent(*args, **kwargs)

    def _get_runtime_checkpoint(self, *args: Any, **kwargs: Any) -> Any:
        return get_runtime_checkpoint(*args, **kwargs)

    def _record_runtime_tool_progress(self, *args: Any, **kwargs: Any) -> Any:
        return record_runtime_tool_progress(*args, **kwargs)

    def _render_capability_truth_response(self, *args: Any, **kwargs: Any) -> Any:
        return render_capability_truth_response(*args, **kwargs)

    def _load_active_persona(self, *args: Any, **kwargs: Any) -> Any:
        return load_active_persona(*args, **kwargs)

    def _execute_runtime_tool(self, *args: Any, **kwargs: Any) -> Any:
        return execute_runtime_tool(*args, **kwargs)

    def _search_user_heuristics(self, query: str, **kwargs: Any) -> Any:
        return search_user_heuristics(query, **kwargs)

    def _looks_like_workspace_bootstrap_request(self, text: str) -> bool:
        return _looks_like_workspace_bootstrap_request(text)

    _nullabook_pending: dict[str, dict[str, str]]

    @staticmethod
    def _classify_nullabook_intent(lowered: str) -> str | None:
        return agent_nullabook_runtime.classify_nullabook_intent(lowered)

    def _maybe_handle_nullabook_fast_path(
        self,
        user_input: str,
        *,
        raw_user_input: str | None = None,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any] | None:
        return agent_nullabook_runtime.maybe_handle_nullabook_fast_path(
            self,
            user_input,
            raw_user_input=raw_user_input,
            session_id=session_id,
            source_context=source_context,
            signer_module=signer_mod,
        )

    def _try_compound_nullabook_message(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any] | None:
        return agent_nullabook_runtime.try_compound_nullabook_message(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
            signer_module=signer_mod,
        )

    def _handle_nullabook_pending_step(
        self,
        user_input: str,
        lowered: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
        pending: dict[str, str],
    ) -> dict[str, Any] | None:
        return agent_nullabook_runtime.handle_nullabook_pending_step(
            self,
            user_input,
            lowered,
            session_id=session_id,
            source_context=source_context,
            pending=pending,
            signer_module=signer_mod,
        )

    def _nullabook_step_handle(
        self, user_input: str, lowered: str, *, session_id: str, source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.nullabook_step_handle(
            self,
            user_input,
            lowered,
            session_id=session_id,
            source_context=source_context,
            signer_module=signer_mod,
        )

    def _nullabook_step_bio(
        self, user_input: str, *, session_id: str, source_context: dict[str, object] | None, pending: dict[str, str],
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.nullabook_step_bio(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
            pending=pending,
        )

    def _handle_nullabook_post(
        self, user_input: str, lowered: str, profile: Any, *, session_id: str, source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.handle_nullabook_post(
            self,
            user_input,
            lowered,
            profile,
            session_id=session_id,
            source_context=source_context,
        )

    def _execute_nullabook_post(
        self, content: str, profile: Any, *, session_id: str, source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.execute_nullabook_post(
            self,
            content,
            profile,
            session_id=session_id,
            source_context=source_context,
        )

    def _nullabook_result(
        self, session_id: str, user_input: str, source_context: dict[str, object] | None, response: str,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.nullabook_result(
            self,
            session_id,
            user_input,
            source_context,
            response,
        )

    def _sync_profile_to_hive(self, profile) -> None:
        agent_nullabook_runtime.sync_profile_to_hive(self, profile)

    @staticmethod
    def _is_nullabook_post_request(lowered: str) -> bool:
        return agent_nullabook_runtime.is_nullabook_post_request(lowered)

    @staticmethod
    def _is_nullabook_delete_request(lowered: str) -> bool:
        return agent_nullabook_runtime.is_nullabook_delete_request(lowered)

    @staticmethod
    def _is_nullabook_edit_request(lowered: str) -> bool:
        return agent_nullabook_runtime.is_nullabook_edit_request(lowered)

    def _handle_nullabook_delete(
        self, user_input: str, lowered: str, profile: Any,
        *, session_id: str, source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.handle_nullabook_delete(
            self,
            user_input,
            lowered,
            profile,
            session_id=session_id,
            source_context=source_context,
        )

    def _handle_nullabook_edit(
        self, user_input: str, lowered: str, profile: Any,
        *, session_id: str, source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.handle_nullabook_edit(
            self,
            user_input,
            lowered,
            profile,
            session_id=session_id,
            source_context=source_context,
        )

    @staticmethod
    def _extract_post_id(text: str) -> str:
        return agent_nullabook_runtime.extract_post_id(text)

    @staticmethod
    def _extract_edit_content(text: str) -> str:
        return agent_nullabook_runtime.extract_edit_content(text)

    @staticmethod
    def _is_nullabook_create_request(lowered: str) -> bool:
        return agent_nullabook_runtime.is_nullabook_create_request(lowered)

    @staticmethod
    def _extract_nullabook_bio_update(text: str) -> str:
        return agent_nullabook_runtime.extract_nullabook_bio_update(text)

    @staticmethod
    def _extract_twitter_handle(text: str) -> str:
        return agent_nullabook_runtime.extract_twitter_handle(text)

    @staticmethod
    def _extract_handle_from_text(text: str) -> str | None:
        return agent_nullabook_runtime.extract_handle_from_text(text)

    @staticmethod
    def _looks_like_nullabook_handle_rules_question(text: str, lowered: str) -> bool:
        return agent_nullabook_runtime.looks_like_nullabook_handle_rules_question(text, lowered)

    @staticmethod
    def _extract_post_content(text: str) -> str:
        return agent_nullabook_runtime.extract_post_content(text)

    @staticmethod
    def _is_substantive_post_content(text: str) -> bool:
        return agent_nullabook_runtime.is_substantive_post_content(text)

    @staticmethod
    def _looks_like_direct_social_post_request(lowered: str) -> bool:
        return agent_nullabook_runtime.looks_like_direct_social_post_request(lowered)

    @staticmethod
    def _strip_context_subject_suffix(text: str) -> str:
        return agent_nullabook_runtime.strip_context_subject_suffix(text)

    @staticmethod
    def _extract_display_name(text: str) -> str:
        return agent_nullabook_runtime.extract_display_name(text)

    def _handle_nullabook_rename(
        self, new_handle: str, profile: Any, *,
        session_id: str, user_input: str, source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_nullabook_runtime.handle_nullabook_rename(
            self,
            new_handle,
            profile,
            session_id=session_id,
            user_input=user_input,
            source_context=source_context,
        )

    def _render_credit_status(self, normalized_input: str) -> str:
        return agent_fast_command_surface.render_credit_status(normalized_input)

    def _maybe_attach_workflow(
        self,
        response: str,
        workflow_summary: str,
        *,
        source_context: dict[str, object] | None = None,
    ) -> str:
        return agent_response_policy.maybe_attach_workflow(
            self,
            response,
            workflow_summary,
            source_context=source_context,
        )

    def _turn_result(
        self,
        text: str,
        response_class: ResponseClass,
        *,
        workflow_summary: str = "",
        debug_origin: str | None = None,
        allow_planner_style: bool = False,
    ) -> ChatTurnResult:
        return agent_response_runtime.turn_result(
            ChatTurnResult,
            text,
            response_class,
            workflow_summary=workflow_summary,
            debug_origin=debug_origin,
            allow_planner_style=allow_planner_style,
        )

    def _decorate_chat_response(
        self,
        response: ChatTurnResult | str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
        workflow_summary: str = "",
        include_hive_footer: bool | None = None,
    ) -> str:
        return agent_response_runtime.decorate_chat_response(
            self,
            response,
            session_id=session_id,
            source_context=source_context,
            workflow_summary=workflow_summary,
            include_hive_footer=include_hive_footer,
        )

    def _shape_user_facing_text(self, result: ChatTurnResult) -> str:
        return agent_response_runtime.shape_user_facing_text(self, result)

    def _should_show_workflow_for_result(
        self,
        result: ChatTurnResult,
        *,
        source_context: dict[str, object] | None,
    ) -> bool:
        return agent_response_runtime.should_show_workflow_for_result(
            self,
            result,
            source_context=source_context,
        )

    def _sanitize_user_chat_text(
        self,
        text: str,
        *,
        response_class: ResponseClass,
        allow_planner_style: bool = False,
    ) -> str:
        return agent_response_runtime.sanitize_user_chat_text(
            self,
            text,
            response_class=response_class,
            allow_planner_style=allow_planner_style,
        )

    def _strip_runtime_preamble(self, text: str, *, allow_planner_style: bool = False) -> str:
        return agent_response_runtime.strip_runtime_preamble(text, allow_planner_style=allow_planner_style)

    def _strip_planner_leakage(self, text: str) -> str:
        return agent_response_runtime.strip_planner_leakage(self, text)

    def _contains_generic_planner_scaffold(self, text: str) -> bool:
        return agent_response_runtime.contains_generic_planner_scaffold(self, text)

    def _unwrap_summary_or_action_payload(self, text: str) -> str:
        return agent_response_runtime.unwrap_summary_or_action_payload(text)

    def _fast_path_response_class(self, *, reason: str, response: str) -> ResponseClass:
        return agent_response_policy.fast_path_response_class(self, reason=reason, response=response)

    def _classify_hive_text_response(self, response: str) -> ResponseClass:
        return agent_response_policy.classify_hive_text_response(self, response)

    def _action_response_class(
        self,
        *,
        reason: str,
        success: bool,
        task_outcome: str | None,
        response: str,
    ) -> ResponseClass:
        return agent_response_policy.action_response_class(
            self,
            reason=reason,
            success=success,
            task_outcome=task_outcome,
            response=response,
        )

    def _grounded_response_class(self, *, gate: GateDecision, classification: dict[str, Any]) -> ResponseClass:
        return agent_response_policy.grounded_response_class(self, gate=gate)

    def _apply_interaction_transition(self, session_id: str, result: ChatTurnResult) -> None:
        agent_orchestrator_runtime.apply_interaction_transition(
            self,
            session_id,
            result,
            session_hive_state_fn=session_hive_state,
            set_hive_interaction_state_fn=set_hive_interaction_state,
        )

    def _maybe_handle_hive_frontdoor(
        self,
        *,
        raw_user_input: str,
        effective_input: str,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
        return agent_hive_followups.maybe_handle_hive_frontdoor(
            self,
            raw_user_input=raw_user_input,
            effective_input=effective_input,
            session_id=session_id,
            source_context=source_context,
        )

    def _maybe_handle_hive_runtime_command(
        self,
        user_input: str,
        *,
        session_id: str,
    ) -> tuple[bool, str, bool, dict[str, Any] | None]:
        return agent_hive_runtime.maybe_handle_hive_runtime_command(
            self,
            user_input,
            session_id=session_id,
        )

    def _recover_hive_runtime_command_input(self, user_input: str) -> str:
        return agent_hive_runtime.recover_hive_runtime_command_input(
            self,
            user_input,
            looks_like_semantic_hive_request_fn=looks_like_semantic_hive_request,
        )

    def _hive_tracker_needs_bridge_fallback(self, response: str) -> bool:
        return agent_hive_runtime.hive_tracker_needs_bridge_fallback(response)

    def _looks_like_hive_prompt_control_command(self, user_input: str) -> bool:
        return agent_hive_runtime.looks_like_hive_prompt_control_command(user_input)

    def _maybe_handle_hive_bridge_fallback(
        self,
        user_input: str,
        *,
        session_id: str,
        tracker_response: str,
    ) -> dict[str, Any] | None:
        return agent_hive_runtime.maybe_handle_hive_bridge_fallback(
            self,
            user_input,
            session_id=session_id,
            tracker_response=tracker_response,
        )

    def _store_hive_topic_selection_state(
        self,
        session_id: str,
        topics: list[dict[str, Any]],
    ) -> None:
        agent_hive_runtime.store_hive_topic_selection_state(
            session_id,
            topics,
            session_hive_state_fn=session_hive_state,
            update_session_hive_state_fn=update_session_hive_state,
        )

    def _should_show_workflow_summary(
        self,
        *,
        response: str,
        workflow_summary: str,
        source_context: dict[str, object] | None,
    ) -> bool:
        return agent_response_policy.should_show_workflow_summary(
            response=response,
            workflow_summary=workflow_summary,
            source_context=source_context,
        )

    def _task_workflow_summary(
        self,
        *,
        classification: dict[str, Any],
        context_result: Any,
        model_execution: dict[str, Any],
        media_analysis: dict[str, Any],
        curiosity_result: dict[str, Any],
        gate_mode: str,
    ) -> str:
        return agent_orchestrator_runtime.task_workflow_summary(
            classification=classification,
            context_result=context_result,
            model_execution=model_execution,
            media_analysis=media_analysis,
            curiosity_result=curiosity_result,
            gate_mode=gate_mode,
        )

    def _action_workflow_summary(
        self,
        *,
        operator_kind: str,
        dispatch_status: str,
        details: dict[str, Any] | None,
    ) -> str:
        return agent_orchestrator_runtime.action_workflow_summary(
            operator_kind=operator_kind,
            dispatch_status=dispatch_status,
            details=details,
        )

    def _tool_intent_workflow_summary(
        self,
        *,
        tool_name: str,
        dispatch_status: str,
        provider_id: str | None,
        validation_state: str,
    ) -> str:
        lines = [
            f"- model selected tool intent `{tool_name or 'unknown'}`",
            f"- tool state: `{dispatch_status}`",
        ]
        provider = str(provider_id or "").strip()
        if provider:
            lines.append(f"- tool intent provider: `{provider}`")
        validation = str(validation_state or "").strip()
        if validation:
            lines.append(f"- tool intent validation: `{validation}`")
        return "\n".join(lines)

    def _tool_intent_direct_message(self, structured_output: Any) -> str | None:
        return agent_response_policy.tool_intent_direct_message(structured_output)

    def _append_tool_result_to_source_context(
        self,
        source_context: dict[str, Any] | None,
        *,
        execution: Any,
        tool_name: str,
    ) -> dict[str, Any]:
        return agent_response_policy.append_tool_result_to_source_context(
            self,
            source_context,
            execution=execution,
            tool_name=tool_name,
        )

    def _normalize_tool_history_message(self, item: dict[str, Any]) -> dict[str, str]:
        return agent_response_policy.normalize_tool_history_message(self, item)

    def _tool_surface_for_history(self, tool_name: str) -> str:
        return agent_response_policy.tool_surface_for_history(tool_name)

    def _tool_history_observation_payload(
        self,
        *,
        execution: Any,
        tool_name: str,
    ) -> dict[str, Any]:
        return agent_response_policy.tool_history_observation_payload(
            execution=execution,
            tool_name=tool_name,
        )

    def _tool_history_observation_prompt(self, observation: dict[str, Any]) -> str:
        return agent_orchestrator_runtime.tool_history_observation_prompt(observation)

    def _tool_history_observation_message(
        self,
        *,
        execution: Any,
        tool_name: str,
    ) -> dict[str, str]:
        return agent_response_policy.tool_history_observation_message(
            self,
            execution=execution,
            tool_name=tool_name,
        )

    def _tool_loop_final_message(self, synthesis: Any, executed_steps: list[dict[str, Any]]) -> str:
        return agent_orchestrator_runtime.tool_loop_final_message(synthesis, executed_steps)

    def _render_tool_loop_response(
        self,
        *,
        final_message: str,
        executed_steps: list[dict[str, Any]],
        include_step_summary: bool = True,
    ) -> str:
        return agent_orchestrator_runtime.render_tool_loop_response(
            final_message=final_message,
            executed_steps=executed_steps,
            include_step_summary=include_step_summary,
        )

    def _tool_intent_loop_workflow_summary(
        self,
        *,
        executed_steps: list[dict[str, Any]],
        provider_id: str | None,
        validation_state: str,
    ) -> str:
        return agent_orchestrator_runtime.tool_intent_loop_workflow_summary(
            executed_steps=executed_steps,
            provider_id=provider_id,
            validation_state=validation_state,
        )

    def _tool_step_summary(self, response_text: str, *, fallback: str) -> str:
        return agent_orchestrator_runtime.tool_step_summary(response_text, fallback=fallback)

    def _runtime_preview(self, text: str, *, limit: int = 220) -> str:
        return agent_orchestrator_runtime.runtime_preview(text, limit=limit)

    def _emit_runtime_event(
        self,
        source_context: dict[str, Any] | None,
        *,
        event_type: str,
        message: str,
        **details: Any,
    ) -> None:
        agent_orchestrator_runtime.emit_runtime_event(
            self,
            source_context,
            event_type=event_type,
            message=message,
            emit_runtime_event_fn=emit_runtime_event,
            **details,
        )

    def _live_runtime_stream_enabled(self, source_context: dict[str, Any] | None) -> bool:
        return agent_orchestrator_runtime.live_runtime_stream_enabled(source_context)

    def _sync_public_presence(
        self,
        *,
        status: str,
        source_context: dict[str, object] | None = None,
    ) -> None:
        agent_presence_runtime.sync_public_presence(
            self,
            status=status,
            source_context=source_context,
            get_agent_display_name_fn=get_agent_display_name,
            audit_log_fn=audit_logger.log,
        )

    def _start_public_presence_heartbeat(self) -> None:
        agent_presence_runtime.start_public_presence_heartbeat(
            self,
            thread_factory=threading.Thread,
        )

    def _start_idle_commons_loop(self) -> None:
        agent_presence_runtime.start_idle_commons_loop(
            self,
            thread_factory=threading.Thread,
        )

    def _public_presence_heartbeat_loop(self) -> None:
        agent_presence_runtime.public_presence_heartbeat_loop(
            self,
            sleep_fn=time.sleep,
        )

    def _idle_commons_loop(self) -> None:
        agent_presence_runtime.idle_commons_loop(
            self,
            sleep_fn=time.sleep,
            audit_log_fn=audit_logger.log,
        )

    def _maybe_run_idle_commons_once(self) -> None:
        agent_presence_runtime.maybe_run_idle_commons_once(
            self,
            load_preferences_fn=load_preferences,
            time_fn=time.time,
            audit_log_fn=audit_logger.log,
        )

    def _maybe_run_autonomous_hive_research_once(self) -> None:
        agent_presence_runtime.maybe_run_autonomous_hive_research_once(
            self,
            load_preferences_fn=load_preferences,
            time_fn=time.time,
            pick_signal_fn=pick_autonomous_research_signal,
            research_topic_fn=research_topic_from_signal,
            audit_log_fn=audit_logger.log,
        )

    def _mark_user_activity(self) -> None:
        with self._activity_lock:
            self._last_user_activity_ts = time.time()

    def _idle_commons_session_id(self) -> str:
        return agent_presence_runtime.idle_commons_session_id(
            get_local_peer_id_fn=signer_mod.get_local_peer_id,
        )

    def _normalize_public_presence_status(self, status: str) -> str:
        return agent_presence_runtime.normalize_public_presence_status(self, status)

    def _idle_public_presence_status(self) -> str:
        return agent_presence_runtime.idle_public_presence_status(
            load_preferences_fn=load_preferences,
        )

    _PROCEED_PATTERNS: frozenset[str] = frozenset({
        "proceed", "carry on", "continue", "do it", "do all", "go ahead",
        "start working", "yes", "yes proceed", "yes do it", "ok do it",
        "ok proceed", "ok go ahead", "deliver it", "submit it", "just do it",
        "yes pls", "yes please", "all good carry on", "proceed with next steps",
        "proceed with that", "all good", "no proceed",
    })
    _HIVE_REVIEW_ACTION_RE = re.compile(
        r"\b(?P<decision>approve|approved|reject|rejected|needs?\s+more\s+evidence|needs?\s+improvement|send\s+back|quarantine|void)\b"
        r"(?:\s+(?:the\s+)?)?"
        r"(?:(?P<object_type>post|topic)\s+)?"
        r"(?:#)?(?P<object_id>[a-z0-9][a-z0-9-]{5,255})\b",
        re.IGNORECASE,
    )

    def _is_proceed_message(self, text: str) -> bool:
        compact = " ".join(str(text or "").strip().lower().split()).strip(" \t\n\r?!.,")
        if compact in self._PROCEED_PATTERNS:
            return True
        padded = f" {compact} "
        if any(f" {p} " in padded for p in (
            "proceed", "carry on", "continue", "do it", "do all",
            "go ahead", "start working", "just do it",
        )):
            return True
        return bool(any(marker in compact for marker in ("do research", "start research", "run research", "deliver to hive", "deliver to the hive", "deliver it to hive", "deliver it to the hive", "submit to hive", "submit to the hive", "post to hive", "research and deliver", "research it", "do it properly")))

    def _maybe_handle_hive_review_command(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any] | None:
        return agent_hive_followups.maybe_handle_hive_review_command(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
        )

    def _looks_like_hive_review_queue_command(self, lowered: str) -> bool:
        return agent_hive_followups.looks_like_hive_review_queue_command(lowered)

    def _parse_hive_review_action(self, user_input: str) -> dict[str, str] | None:
        return agent_hive_followups.parse_hive_review_action(user_input)

    def _looks_like_hive_cleanup_command(self, lowered: str) -> bool:
        return agent_hive_followups.looks_like_hive_cleanup_command(lowered)

    def _handle_hive_review_queue_command(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_hive_followups.handle_hive_review_queue_command(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
        )

    def _handle_hive_review_action(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
        review_action: dict[str, str],
    ) -> dict[str, Any]:
        return agent_hive_followups.handle_hive_review_action(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
            review_action=review_action,
        )

    def _handle_hive_cleanup_command(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any]:
        return agent_hive_followups.handle_hive_cleanup_command(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
        )

    def _looks_like_disposable_hive_cleanup_topic(self, topic: dict[str, Any]) -> bool:
        return agent_hive_followups.looks_like_disposable_hive_cleanup_topic(topic)

    def _maybe_handle_hive_research_followup(
        self,
        user_input: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
    ) -> dict[str, Any] | None:
        return agent_hive_followups.maybe_handle_hive_research_followup(
            self,
            user_input,
            session_id=session_id,
            source_context=source_context,
            session_hive_state_fn=session_hive_state,
            clear_hive_interaction_state_fn=clear_hive_interaction_state,
            set_hive_interaction_state_fn=set_hive_interaction_state,
            research_topic_from_signal_fn=research_topic_from_signal,
        )

    def _maybe_resume_active_hive_task(
        self,
        lowered: str,
        *,
        session_id: str,
        source_context: dict[str, object] | None,
        hive_state: dict[str, Any],
    ) -> dict[str, Any] | None:
        return agent_hive_followups.maybe_resume_active_hive_task(
            self,
            lowered,
            session_id=session_id,
            source_context=source_context,
            hive_state=hive_state,
            set_hive_interaction_state_fn=set_hive_interaction_state,
            research_topic_from_signal_fn=research_topic_from_signal,
        )

    def _extract_hive_topic_hint(self, text: str) -> str:
        return agent_hive_followups.extract_hive_topic_hint(text)

    def _default_gate(self, plan: Plan, classification: dict) -> GateDecision:
        risk_flags = set(classification.get("risk_flags") or []) | set(plan.risk_flags or [])

        hard_block = {
            "destructive_command",
            "privileged_action",
            "persistence_attempt",
            "exfiltration_hint",
            "shell_injection_risk",
        }

        if any(flag in hard_block for flag in risk_flags):
            return GateDecision(
                mode="blocked",
                reason="Blocked by safety policy due to risk flags.",
                requires_user_approval=False,
                allowed_actions=[],
            )

        if classification.get("task_class") == "risky_system_action":
            return GateDecision(
                mode="advice_only",
                reason="System-sensitive task forced to advice-only.",
                requires_user_approval=True,
                allowed_actions=[],
            )

        return GateDecision(
            mode="advice_only",
            reason="v1 defaults to advice-only.",
            requires_user_approval=False,
            allowed_actions=[],
        )


def main() -> int:
    parser = argparse.ArgumentParser(prog="nulla-agent")
    parser.add_argument("--backend", default="auto")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--persona", default="default")
    parser.add_argument("--input", default="")
    parser.add_argument("--json", action="store_true", help="Print full response payload as JSON.")
    args = parser.parse_args()

    from core.runtime_bootstrap import bootstrap_runtime_mode

    backend_name = str(args.backend)
    device = str(args.device)
    boot = bootstrap_runtime_mode(
        mode="agent",
        force_policy_reload=True,
        resolve_backend=backend_name == "auto" or device == "auto",
    )

    if backend_name == "auto" or device == "auto":
        selection = boot.backend_selection
        if selection is None:
            raise RuntimeError("Runtime bootstrap did not resolve a backend selection.")
        backend_name = backend_name if backend_name != "auto" else selection.backend_name
        device = device if device != "auto" else selection.device

    agent = NullaAgent(
        backend_name=backend_name,
        device=device,
        persona_id=str(args.persona),
    )
    agent.start()
    if not str(args.input or "").strip():
        print("Nulla agent started. Provide --input for one-shot execution.")
        return 0

    result = agent.run_once(str(args.input))
    if bool(args.json):
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(str(result.get("response") or "").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
