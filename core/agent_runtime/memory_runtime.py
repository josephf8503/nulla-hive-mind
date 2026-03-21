from __future__ import annotations

from typing import Any


def maybe_handle_memory_fast_path(
    agent: Any,
    user_input: str,
    *,
    session_id: str,
    source_context: dict[str, object] | None,
    maybe_handle_memory_command_fn: Any,
) -> dict[str, Any] | None:
    handled, response = maybe_handle_memory_command_fn(user_input, session_id=session_id)
    if handled:
        return agent._fast_path_result(
            session_id=session_id,
            user_input=user_input,
            response=response,
            confidence=0.93,
            source_context=source_context,
            reason="memory_command",
        )
    return agent._maybe_handle_companion_memory_fast_path(
        user_input,
        session_id=session_id,
        source_context=source_context,
    )


def model_final_response_text(model_execution: Any) -> str:
    final_text = str(getattr(model_execution, "output_text", "") or "").strip()
    if final_text:
        return final_text
    structured = getattr(model_execution, "structured_output", None)
    if isinstance(structured, dict):
        return str(structured.get("summary") or structured.get("message") or "").strip()
    return ""


def chat_surface_cache_or_memory_source(model_execution: Any) -> bool:
    source = str(getattr(model_execution, "source", "") or "").strip().lower()
    return source in {"exact_cache_hit", "memory_hit"}


def chat_surface_model_final_text(model_execution: Any) -> str:
    if chat_surface_cache_or_memory_source(model_execution):
        return ""
    return model_final_response_text(model_execution)


def chat_surface_honest_degraded_response(
    agent: Any,
    model_execution: Any,
    *,
    user_input: str = "",
    interpretation: Any | None = None,
) -> str:
    source = str(getattr(model_execution, "source", "") or "").strip().lower()
    live_mode = agent._live_info_mode(user_input, interpretation=interpretation) if str(user_input or "").strip() else ""
    if source in {"exact_cache_hit", "memory_hit", "no_provider_available"} and live_mode == "fresh_lookup":
        query = agent._normalize_live_info_query(user_input, mode=live_mode)
        return agent._live_info_failure_text(query=query, mode=live_mode)
    if source == "exact_cache_hit":
        return (
            "I found a matching cached answer for this topic, but this chat path requires a live model response, "
            "so I'm not passing cached text off as a fresh answer."
        )
    if source == "memory_hit":
        return (
            "I found relevant local memory for this topic, but this chat path requires a live model response, "
            "so I'm not presenting remembered text as a fresh answer."
        )
    if source == "no_provider_available":
        return (
            "I couldn't get a live model response in this run, so I'm not going to recycle cached or remembered "
            "text as if it were fresh."
        )
    return (
        "I couldn't get a usable model response in this run, so I'm not going to recycle cached or remembered "
        "text as if it were fresh."
    )
