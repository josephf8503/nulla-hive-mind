from __future__ import annotations

from unittest import mock

from apps.nulla_agent import NullaAgent


def _build_agent() -> NullaAgent:
    return NullaAgent(backend_name="test-backend", device="channel-test", persona_id="default")


def test_fast_command_surface_credit_command_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.fast_command_surface.maybe_handle_credit_command",
        return_value={"response": "delegated credit"},
    ) as maybe_handle_credit_command:
        result = agent._maybe_handle_credit_command(
            "send 5 credits to peer-1",
            session_id="session-123",
            source_context={"surface": "openclaw"},
        )

    assert result == {"response": "delegated credit"}
    maybe_handle_credit_command.assert_called_once_with(
        agent,
        "send 5 credits to peer-1",
        session_id="session-123",
        source_context={"surface": "openclaw"},
        signer_module=mock.ANY,
        transfer_credits_fn=mock.ANY,
        get_credit_balance_fn=mock.ANY,
        escrow_credits_for_task_fn=mock.ANY,
        session_hive_state_fn=mock.ANY,
        runtime_session_id_fn=mock.ANY,
    )


def test_fast_command_surface_fast_path_result_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.fast_command_surface.fast_path_result",
        return_value={"response": "delegated fast path"},
    ) as fast_path_result:
        result = agent._fast_path_result(
            session_id="session-123",
            user_input="what time is it?",
            response="Current time is 12:00.",
            confidence=0.97,
            source_context={"surface": "openclaw"},
            reason="date_time_fast_path",
        )

    assert result == {"response": "delegated fast path"}
    fast_path_result.assert_called_once_with(
        agent,
        session_id="session-123",
        user_input="what time is it?",
        response="Current time is 12:00.",
        confidence=0.97,
        source_context={"surface": "openclaw"},
        reason="date_time_fast_path",
        append_conversation_event_fn=mock.ANY,
        audit_logger_module=mock.ANY,
    )


def test_fast_command_surface_action_fast_path_result_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.fast_command_surface.action_fast_path_result",
        return_value={"response": "delegated action"},
    ) as action_fast_path_result:
        result = agent._action_fast_path_result(
            task_id="task-123",
            session_id="session-123",
            user_input="post this to telegram",
            response="Queued the post.",
            confidence=0.91,
            source_context={"surface": "openclaw", "platform": "openclaw"},
            reason="channel_post_action",
            success=True,
            workflow_summary="posted",
        )

    assert result == {"response": "delegated action"}
    action_fast_path_result.assert_called_once_with(
        agent,
        task_id="task-123",
        session_id="session-123",
        user_input="post this to telegram",
        response="Queued the post.",
        confidence=0.91,
        source_context={"surface": "openclaw", "platform": "openclaw"},
        reason="channel_post_action",
        success=True,
        details=None,
        mode_override=None,
        task_outcome=None,
        learned_plan=None,
        workflow_summary="posted",
        append_conversation_event_fn=mock.ANY,
        audit_logger_module=mock.ANY,
        explicit_planner_style_requested_fn=mock.ANY,
    )


def test_fast_command_surface_help_and_capability_truth_facades_delegate_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.fast_command_surface.help_capabilities_text",
        return_value="help text",
    ) as help_capabilities_text, mock.patch(
        "core.agent_runtime.fast_command_surface.maybe_handle_capability_truth_request",
        return_value={"response": "truth"},
    ) as maybe_handle_capability_truth_request:
        help_text = agent._help_capabilities_text()
        result = agent._maybe_handle_capability_truth_request(
            "can you send email?",
            session_id="session-123",
            source_context={"surface": "openclaw"},
        )

    assert help_text == "help text"
    assert result == {"response": "truth"}
    help_capabilities_text.assert_called_once_with(agent)
    maybe_handle_capability_truth_request.assert_called_once_with(
        agent,
        "can you send email?",
        session_id="session-123",
        source_context={"surface": "openclaw"},
        capability_truth_for_request_fn=mock.ANY,
        render_capability_truth_response_fn=mock.ANY,
    )
