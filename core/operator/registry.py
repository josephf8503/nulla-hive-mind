from __future__ import annotations

import os
import shutil
from typing import Any


def operator_capability_ledger(*, tools: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for tool in list(tools if tools is not None else list_operator_tools()):
        tool_id = str(tool.get("tool_id") or "").strip()
        if not tool_id:
            continue
        guardrails = _operator_action_guardrails(tool_id, destructive=bool(tool.get("destructive")))
        available = bool(tool.get("available"))
        entries.append(
            {
                "capability_id": f"operator.{tool_id}",
                "surface": str(tool.get("category") or "local_operator").strip() or "local_operator",
                "claim": _operator_capability_claim(tool_id, destructive=guardrails["destructive"]),
                "supported": available,
                "support_level": _operator_capability_support_level(tool_id, available=available),
                "partial_reason": _operator_partial_support_reason(tool_id, available=available),
                "unsupported_reason": _operator_capability_unavailable_reason(tool_id),
                "nearby_capability_ids": _operator_nearby_capability_ids(tool_id),
                "intents": [f"operator.{tool_id}"] if tool_id not in {"discord_post", "telegram_send"} else [],
                "public_tag": f"operator.{tool_id}",
                "requires_approval": bool(guardrails["requires_approval"]),
                "destructive": bool(guardrails["destructive"]),
                "outward_facing": bool(guardrails["outward_facing"]),
                "privacy_sensitive": bool(guardrails["privacy_sensitive"]),
            }
        )
    return entries


def list_operator_tools() -> list[dict[str, Any]]:
    return [
        {
            "tool_id": "inspect_disk_usage",
            "category": "local_operator",
            "destructive": False,
            **_operator_action_guardrails("inspect_disk_usage", destructive=False),
            "available": True,
            "description": "Inspect disk usage and identify large directories or temp bloat.",
        },
        {
            "tool_id": "cleanup_temp_files",
            "category": "local_operator",
            "destructive": True,
            **_operator_action_guardrails("cleanup_temp_files", destructive=True),
            "available": True,
            "description": "Delete contents of bounded temp roots after explicit approval.",
        },
        {
            "tool_id": "inspect_processes",
            "category": "local_operator",
            "destructive": False,
            **_operator_action_guardrails("inspect_processes", destructive=False),
            "available": _process_inspection_available(),
            "description": "Inspect the heaviest running processes by CPU and memory use.",
        },
        {
            "tool_id": "inspect_services",
            "category": "local_operator",
            "destructive": False,
            **_operator_action_guardrails("inspect_services", destructive=False),
            "available": _service_inspection_available(),
            "description": "Inspect running services or startup agents on the local machine.",
        },
        {
            "tool_id": "schedule_calendar_event",
            "category": "calendar",
            "destructive": True,
            **_operator_action_guardrails("schedule_calendar_event", destructive=True),
            "available": True,
            "description": "Create a .ics calendar event in the local calendar outbox; balanced/strict modes still require approval.",
        },
        {
            "tool_id": "move_path",
            "category": "local_operator",
            "destructive": True,
            **_operator_action_guardrails("move_path", destructive=True),
            "available": True,
            "description": "Move or archive a bounded local file/folder after explicit approval.",
        },
        {
            "tool_id": "discord_post",
            "category": "communication",
            "destructive": True,
            **_operator_action_guardrails("discord_post", destructive=True),
            "available": _discord_available(),
            "description": "Send a Discord message through the configured bridge credentials.",
        },
        {
            "tool_id": "telegram_send",
            "category": "communication",
            "destructive": True,
            **_operator_action_guardrails("telegram_send", destructive=True),
            "available": _telegram_available(),
            "description": "Send a Telegram message through the configured bridge credentials.",
        },
    ]


def _operator_action_guardrails(tool_id: str, *, destructive: bool) -> dict[str, bool]:
    normalized = str(tool_id or "").strip().lower()
    outward_facing = normalized in {"discord_post", "telegram_send"}
    privacy_sensitive = outward_facing
    return {
        "destructive": bool(destructive),
        "outward_facing": outward_facing,
        "privacy_sensitive": privacy_sensitive,
        "requires_approval": bool(destructive or outward_facing or privacy_sensitive),
    }


def _operator_capability_claim(tool_id: str, *, destructive: bool) -> str:
    claims = {
        "inspect_disk_usage": "inspect disk usage on the local machine",
        "cleanup_temp_files": "clean bounded temp roots on the local machine after explicit approval",
        "inspect_processes": "inspect running processes on the local machine",
        "inspect_services": "inspect running services or startup agents on the local machine",
        "schedule_calendar_event": "create local calendar events after approval when required",
        "move_path": "move or archive bounded local paths after explicit approval",
        "discord_post": "send Discord messages through the configured bridge",
        "telegram_send": "send Telegram messages through the configured bridge",
    }
    claim = claims.get(tool_id, f"use operator action `{tool_id}`")
    if destructive and "approval" not in claim:
        return f"{claim} after explicit approval"
    return claim


def _operator_capability_unavailable_reason(tool_id: str) -> str:
    reasons = {
        "discord_post": "Discord bridge sending is not configured on this runtime.",
        "telegram_send": "Telegram bridge sending is not configured on this runtime.",
        "inspect_processes": "Process inspection is not available on this host/runtime.",
        "inspect_services": "Service inspection is not available on this host/runtime.",
    }
    return reasons.get(tool_id, f"Operator capability `{tool_id}` is not available on this host/runtime.")


def _operator_capability_support_level(tool_id: str, *, available: bool) -> str:
    if not available:
        return "unsupported"
    if tool_id == "schedule_calendar_event":
        return "partial"
    return "full"


def _operator_partial_support_reason(tool_id: str, *, available: bool) -> str:
    if not available:
        return ""
    if tool_id == "schedule_calendar_event":
        return "This writes a local .ics event into the calendar outbox, not a universal live calendar-service integration."
    return ""


def _operator_nearby_capability_ids(tool_id: str) -> list[str]:
    mapping = {
        "discord_post": ["operator.telegram_send"],
        "telegram_send": ["operator.discord_post"],
    }
    return list(mapping.get(tool_id, []))


def _operator_nearby_alternatives(tool_id: str) -> list[str]:
    if tool_id in {"discord_post", "telegram_send"}:
        return ["I can draft the message text here before you send it yourself."]
    return []


def _process_inspection_available() -> bool:
    if os.name == "nt":
        return True
    return shutil.which("ps") is not None


def _service_inspection_available() -> bool:
    if os.name == "nt":
        return True
    return bool(shutil.which("systemctl") or shutil.which("launchctl"))


def _discord_available() -> bool:
    return bool(
        str(os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
        or str(os.environ.get("DISCORD_BOT_TOKEN") or "").strip()
    )


def _telegram_available() -> bool:
    return bool(
        str(os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
        and (
            str(os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
            or str(os.environ.get("TELEGRAM_CHAT_IDS_JSON") or "").strip()
        )
    )
