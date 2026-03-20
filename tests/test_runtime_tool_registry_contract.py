from __future__ import annotations

from core.runtime_execution_tools import runtime_execution_capability_ledger, runtime_execution_tool_specs


def test_runtime_tool_specs_are_covered_by_capability_ledger() -> None:
    capability_intents = {
        str(intent).strip()
        for capability in runtime_execution_capability_ledger()
        for intent in list(capability.get("intents") or [])
        if str(intent).strip()
    }
    spec_intents = [str(spec.get("intent") or "").strip() for spec in runtime_execution_tool_specs()]

    assert spec_intents
    assert len(spec_intents) == len(set(spec_intents))
    assert set(spec_intents).issubset(capability_intents)
