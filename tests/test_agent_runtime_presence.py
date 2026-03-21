from __future__ import annotations

from unittest import mock

from apps.nulla_agent import NullaAgent
from core.agent_runtime import presence


def _build_agent() -> NullaAgent:
    return NullaAgent(backend_name="test-backend", device="channel-test", persona_id="default")


def test_sync_public_presence_uses_app_level_name_provider() -> None:
    agent = _build_agent()

    with mock.patch("apps.nulla_agent.get_agent_display_name", return_value="Patched Agent"), mock.patch.object(
        agent.public_hive_bridge,
        "sync_presence",
        return_value={"ok": True, "status": "posted"},
    ) as sync_presence:
        agent._sync_public_presence(status="idle", source_context={"surface": "openclaw"})

    assert sync_presence.call_args.kwargs["agent_name"] == "Patched Agent"
    assert agent._public_presence_registered is True


def test_start_public_presence_heartbeat_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.presence.start_public_presence_heartbeat",
        return_value=None,
    ) as start_public_presence_heartbeat:
        agent._start_public_presence_heartbeat()

    start_public_presence_heartbeat.assert_called_once_with(
        agent,
        thread_factory=mock.ANY,
    )


def test_start_idle_commons_loop_facade_delegates_to_extracted_module() -> None:
    agent = _build_agent()

    with mock.patch(
        "core.agent_runtime.presence.start_idle_commons_loop",
        return_value=None,
    ) as start_idle_commons_loop:
        agent._start_idle_commons_loop()

    start_idle_commons_loop.assert_called_once_with(
        agent,
        thread_factory=mock.ANY,
    )


def test_normalize_public_presence_status_facade_matches_extracted_module() -> None:
    agent = _build_agent()

    assert agent._normalize_public_presence_status("busy") == presence.normalize_public_presence_status(agent, "busy")


def test_idle_public_presence_status_facade_matches_extracted_module() -> None:
    agent = _build_agent()

    assert agent._idle_public_presence_status() == presence.idle_public_presence_status(
        load_preferences_fn=mock.Mock(return_value=mock.Mock(accept_hive_tasks=True))
    )
