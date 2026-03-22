from __future__ import annotations

from core.execution import capabilities as extracted_capabilities
from core.tool_intent_executor import (
    capability_entry_for_intent,
    capability_gap_for_intent,
    capability_truth_for_request,
    render_capability_truth_response,
    runtime_capability_ledger,
    runtime_tool_specs,
    supported_public_capability_tags,
)


def test_tool_intent_executor_capability_facade_matches_extracted_module() -> None:
    assert runtime_capability_ledger() == extracted_capabilities.runtime_capability_ledger()
    assert runtime_tool_specs() == extracted_capabilities.runtime_tool_specs()
    assert supported_public_capability_tags() == extracted_capabilities.supported_public_capability_tags()


def test_tool_intent_executor_capability_helpers_match_extracted_module() -> None:
    assert capability_entry_for_intent("hive.list_available") == extracted_capabilities.capability_entry_for_intent(
        "hive.list_available"
    )
    assert capability_gap_for_intent("email.send") == extracted_capabilities.capability_gap_for_intent("email.send")
    assert capability_truth_for_request("can you send an email?") == extracted_capabilities.capability_truth_for_request(
        "can you send an email?"
    )
    assert render_capability_truth_response({"support_level": "unsupported", "reason": "nope"}) == extracted_capabilities.render_capability_truth_response(
        {"support_level": "unsupported", "reason": "nope"}
    )
