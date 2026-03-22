from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from core.execution.constants import _HIVE_TOOL_INTENTS, _MUTATING_OPERATOR_INTENTS
from core.execution.models import ToolIntentExecution


def normalize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        result = dict(payload)
    elif is_dataclass(payload):
        result = asdict(payload)
    elif isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except Exception:
            return {}
        result = dict(parsed) if isinstance(parsed, dict) else {}
    else:
        return {}
    arguments = result.get("arguments")
    if not isinstance(arguments, dict):
        result["arguments"] = {}
    return result


def inject_idempotency_key(intent: str, arguments: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
    if not idempotency_key:
        return dict(arguments)
    updated = dict(arguments)
    if intent in _HIVE_TOOL_INTENTS:
        updated["idempotency_key"] = idempotency_key
    if intent in _MUTATING_OPERATOR_INTENTS:
        updated.setdefault("action_id", idempotency_key)
    return updated


def execution_to_receipt(execution: ToolIntentExecution) -> dict[str, Any]:
    return {
        "handled": bool(execution.handled),
        "ok": bool(execution.ok),
        "status": str(execution.status or ""),
        "response_text": str(execution.response_text or ""),
        "user_safe_response_text": str(execution.user_safe_response_text or ""),
        "mode": str(execution.mode or ""),
        "tool_name": str(execution.tool_name or ""),
        "details": dict(execution.details or {}),
        "learned_plan": None,
    }


def execution_from_receipt(receipt: dict[str, Any]) -> ToolIntentExecution | None:
    payload = dict(receipt.get("execution") or {})
    if not payload:
        return None
    details = dict(payload.get("details") or {})
    details["from_receipt"] = True
    if receipt.get("idempotency_key"):
        details["idempotency_key"] = str(receipt.get("idempotency_key"))
    return ToolIntentExecution(
        handled=bool(payload.get("handled")),
        ok=bool(payload.get("ok")),
        status=str(payload.get("status") or ""),
        response_text=str(payload.get("response_text") or ""),
        user_safe_response_text=str(payload.get("user_safe_response_text") or ""),
        mode=str(payload.get("mode") or "tool_executed"),
        tool_name=str(payload.get("tool_name") or ""),
        details=details,
        learned_plan=None,
    )
