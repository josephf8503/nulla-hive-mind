from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.reasoning_engine import Plan


@dataclass(frozen=True)
class OperatorActionIntent:
    kind: str
    target_path: str | None = None
    destination_path: str | None = None
    approval_requested: bool = False
    action_id: str | None = None
    raw_text: str = ""


@dataclass
class OperatorActionResult:
    ok: bool
    status: str
    response_text: str
    details: dict[str, Any]
    learned_plan: Plan | None = None
