from __future__ import annotations

from collections.abc import Callable
from typing import Any


def sync_public_presence(
    agent: Any,
    *,
    status: str,
    source_context: dict[str, object] | None = None,
    get_agent_display_name_fn: Callable[[], str],
    audit_log_fn: Callable[..., Any],
) -> None:
    effective_status = agent._normalize_public_presence_status(status)
    with agent._public_presence_lock:
        agent._public_presence_status = effective_status
        if source_context is not None:
            agent._public_presence_source_context = dict(source_context)
    try:
        if agent._public_presence_registered:
            result = agent.public_hive_bridge.heartbeat_presence(
                agent_name=get_agent_display_name_fn(),
                capabilities=agent._public_capabilities(),
                status=effective_status,
                transport_mode=agent._public_transport_mode(source_context),
            )
            if not result.get("ok"):
                result = agent.public_hive_bridge.sync_presence(
                    agent_name=get_agent_display_name_fn(),
                    capabilities=agent._public_capabilities(),
                    status=effective_status,
                    transport_mode=agent._public_transport_mode(source_context),
                )
        else:
            result = agent.public_hive_bridge.sync_presence(
                agent_name=get_agent_display_name_fn(),
                capabilities=agent._public_capabilities(),
                status=effective_status,
                transport_mode=agent._public_transport_mode(source_context),
            )
        if result.get("ok"):
            agent._public_presence_registered = True
    except Exception as exc:
        audit_log_fn(
            "public_hive_presence_sync_error",
            target_id=agent.persona_id,
            target_type="agent",
            details={"error": str(exc), "status": effective_status},
        )
        return
    if not result.get("ok"):
        audit_log_fn(
            "public_hive_presence_sync_failed",
            target_id=agent.persona_id,
            target_type="agent",
            details={"status": effective_status, **dict(result or {})},
        )


def start_public_presence_heartbeat(
    agent: Any,
    *,
    thread_factory: Callable[..., Any],
) -> None:
    if agent._public_presence_running:
        return
    agent._public_presence_running = True
    agent._public_presence_thread = thread_factory(
        target=agent._public_presence_heartbeat_loop,
        name="nulla-public-presence",
        daemon=True,
    )
    agent._public_presence_thread.start()


def start_idle_commons_loop(
    agent: Any,
    *,
    thread_factory: Callable[..., Any],
) -> None:
    if agent._idle_commons_running:
        return
    agent._idle_commons_running = True
    agent._idle_commons_thread = thread_factory(
        target=agent._idle_commons_loop,
        name="nulla-idle-commons",
        daemon=True,
    )
    agent._idle_commons_thread.start()


def public_presence_heartbeat_loop(
    agent: Any,
    *,
    sleep_fn: Callable[[float], Any],
) -> None:
    while agent._public_presence_running:
        sleep_fn(120.0)
        with agent._public_presence_lock:
            last_status = str(agent._public_presence_status or "idle")
            source_context = dict(agent._public_presence_source_context or {})
        agent._sync_public_presence(
            status=agent._normalize_public_presence_status(last_status),
            source_context=source_context,
        )


def idle_commons_loop(
    agent: Any,
    *,
    sleep_fn: Callable[[float], Any],
    audit_log_fn: Callable[..., Any],
) -> None:
    while agent._idle_commons_running:
        sleep_fn(90.0)
        try:
            agent._maybe_run_idle_commons_once()
            agent._maybe_run_autonomous_hive_research_once()
        except Exception as exc:
            audit_log_fn(
                "idle_commons_loop_error",
                target_id=agent.persona_id,
                target_type="agent",
                details={"error": str(exc)},
            )


def idle_commons_session_id(*, get_local_peer_id_fn: Callable[[], str]) -> str:
    return f"agent-commons:{get_local_peer_id_fn()}"


def normalize_public_presence_status(agent: Any, status: str) -> str:
    lowered = str(status or "idle").strip().lower()
    if lowered == "busy":
        return "busy"
    return agent._idle_public_presence_status()


def idle_public_presence_status(*, load_preferences_fn: Callable[[], Any]) -> str:
    prefs = load_preferences_fn()
    return "idle" if bool(getattr(prefs, "accept_hive_tasks", True)) else "limited"
