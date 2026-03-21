from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

from apps.nulla_agent import NullaAgent, maybe_handle_memory_command
from core.agent_runtime import memory_runtime


def _build_agent() -> NullaAgent:
    return NullaAgent(backend_name="test-backend", device="channel-test", persona_id="default")


def test_maybe_handle_memory_fast_path_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.memory_runtime.maybe_handle_memory_fast_path",
        return_value={"response": "memory reply"},
    ) as maybe_handle_memory_fast_path:
        result = agent._maybe_handle_memory_fast_path(
            "remember this",
            session_id="memory-session",
            source_context={"surface": "openclaw"},
        )

    assert result == {"response": "memory reply"}
    maybe_handle_memory_fast_path.assert_called_once_with(
        agent,
        "remember this",
        session_id="memory-session",
        source_context={"surface": "openclaw"},
        maybe_handle_memory_command_fn=maybe_handle_memory_command,
    )


def test_maybe_handle_memory_fast_path_uses_app_level_memory_command_override() -> None:
    agent = _build_agent()

    with mock.patch("apps.nulla_agent.maybe_handle_memory_command", return_value=(True, "remembered")) as memory_command_mock, mock.patch.object(
        agent,
        "_fast_path_result",
        return_value={"response": "remembered", "response_class": "utility_answer"},
    ) as fast_path_result:
        result = agent._maybe_handle_memory_fast_path(
            "remember this",
            session_id="memory-session",
            source_context={"surface": "openclaw"},
        )

    assert result == {"response": "remembered", "response_class": "utility_answer"}
    memory_command_mock.assert_called_once_with("remember this", session_id="memory-session")
    fast_path_result.assert_called_once_with(
        session_id="memory-session",
        user_input="remember this",
        response="remembered",
        confidence=0.93,
        source_context={"surface": "openclaw"},
        reason="memory_command",
    )


def test_maybe_handle_memory_fast_path_uses_app_level_companion_override() -> None:
    agent = _build_agent()

    with mock.patch("apps.nulla_agent.maybe_handle_memory_command", return_value=(False, "")), mock.patch.object(
        agent,
        "_maybe_handle_companion_memory_fast_path",
        return_value={"response": "companion reply"},
    ) as companion_memory_fast_path:
        result = agent._maybe_handle_memory_fast_path(
            "continue that project we talked about",
            session_id="memory-session",
            source_context={"surface": "openclaw"},
        )

    assert result == {"response": "companion reply"}
    companion_memory_fast_path.assert_called_once_with(
        "continue that project we talked about",
        session_id="memory-session",
        source_context={"surface": "openclaw"},
    )


def test_model_final_response_text_facade_matches_extracted_module() -> None:
    agent = _build_agent()
    model_execution = SimpleNamespace(output_text="", structured_output={"summary": "summary from structure"})

    assert agent._model_final_response_text(model_execution) == memory_runtime.model_final_response_text(model_execution)


def test_chat_surface_model_final_text_hides_cache_and_memory_hits() -> None:
    agent = _build_agent()

    assert agent._chat_surface_model_final_text(SimpleNamespace(source="exact_cache_hit", output_text="cached")) == ""
    assert agent._chat_surface_model_final_text(SimpleNamespace(source="memory_hit", output_text="remembered")) == ""


def test_chat_surface_honest_degraded_response_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.memory_runtime.chat_surface_honest_degraded_response",
        return_value="delegated degraded response",
    ) as chat_surface_honest_degraded_response:
        result = agent._chat_surface_honest_degraded_response(
            SimpleNamespace(source="memory_hit"),
            user_input="what do you remember about this",
        )

    assert result == "delegated degraded response"
    chat_surface_honest_degraded_response.assert_called_once_with(
        agent,
        mock.ANY,
        user_input="what do you remember about this",
        interpretation=None,
    )
