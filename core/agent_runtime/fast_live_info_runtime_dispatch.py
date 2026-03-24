from __future__ import annotations

from typing import Any

from .fast_live_info_runtime_results import live_info_result
from .fast_live_info_runtime_truth import (
    chat_truth_live_info_result,
    should_use_chat_truth_wording,
)


def build_live_info_response_result(
    agent: Any,
    *,
    session_id: str,
    user_input: str,
    query: str,
    live_mode: str,
    notes: list[dict[str, Any]],
    source_context: dict[str, object] | None,
    interpretation: Any,
    response_class: Any,
) -> dict[str, Any] | None:
    unresolved_price = agent._unresolved_price_lookup_response(query=query, notes=notes, mode=live_mode)
    if unresolved_price:
        return live_info_result(
            agent,
            session_id=session_id,
            user_input=user_input,
            response=unresolved_price,
            source_context=source_context,
        )
    if not notes and live_mode == "fresh_lookup":
        return None

    response = (
        agent._render_live_info_response(query=query, notes=notes, mode=live_mode)
        if notes
        else agent._live_info_failure_text(query=query, mode=live_mode)
    )
    if should_use_chat_truth_wording(agent, source_context=source_context, live_mode=live_mode, notes=notes):
        return chat_truth_live_info_result(
            agent,
            session_id=session_id,
            user_input=user_input,
            query=query,
            live_mode=live_mode,
            notes=notes,
            source_context=source_context,
            interpretation=interpretation,
            response_class=response_class,
            response=response,
        )
    return agent._fast_path_result(
        session_id=session_id,
        user_input=user_input,
        response=response,
        confidence=0.86 if notes else 0.52,
        source_context=source_context,
        reason="live_info_fast_path",
    )
