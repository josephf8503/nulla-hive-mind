from __future__ import annotations

from typing import Any

from .fast_live_info_runtime_dispatch import build_live_info_response_result
from .fast_live_info_runtime_preflight import prepare_live_info_request
from .fast_live_info_runtime_results import disabled_live_info_result, live_info_result
from .fast_live_info_runtime_search import live_info_search_notes_with_fallback
from .fast_live_info_runtime_truth import (
    chat_truth_live_info_result,
    should_use_chat_truth_wording,
)

__all__ = [
    "build_live_info_response_result",
    "chat_truth_live_info_result",
    "disabled_live_info_result",
    "live_info_result",
    "live_info_search_notes_with_fallback",
    "maybe_handle_live_info_fast_path",
    "prepare_live_info_request",
    "should_use_chat_truth_wording",
]


def maybe_handle_live_info_fast_path(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    interpretation: Any,
    response_class: Any,
) -> dict[str, Any] | None:
    live_mode, query, preflight_result = prepare_live_info_request(
        agent,
        user_input,
        session_id=session_id,
        source_context=source_context,
        interpretation=interpretation,
    )
    if preflight_result is not None:
        return preflight_result
    if not live_mode:
        return None

    notes = live_info_search_notes_with_fallback(
        agent,
        session_id=session_id,
        user_input=user_input,
        query=query,
        live_mode=live_mode,
        interpretation=interpretation,
    )
    return build_live_info_response_result(
        agent,
        session_id=session_id,
        user_input=user_input,
        query=query,
        live_mode=live_mode,
        notes=notes,
        source_context=source_context,
        interpretation=interpretation,
        response_class=response_class,
    )
