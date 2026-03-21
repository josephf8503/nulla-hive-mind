from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolIntentExecution:
    handled: bool
    ok: bool
    status: str
    response_text: str = ""
    user_safe_response_text: str = ""
    mode: str = "tool_failed"
    tool_name: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    learned_plan: Any = None


@dataclass
class WorkflowPlannerDecision:
    handled: bool
    reason: str
    next_payload: dict[str, Any] | None = None
    stop_after: bool = False


def _tool_observation(
    *,
    intent: str,
    tool_surface: str,
    ok: bool,
    status: str,
    **payload: Any,
) -> dict[str, Any]:
    observation = {
        "schema": "tool_observation_v1",
        "intent": str(intent or "").strip(),
        "tool_surface": str(tool_surface or "").strip(),
        "ok": bool(ok),
        "status": str(status or "").strip(),
    }
    for key, value in payload.items():
        if value in (None, "", [], {}):
            continue
        observation[str(key)] = value
    return observation
