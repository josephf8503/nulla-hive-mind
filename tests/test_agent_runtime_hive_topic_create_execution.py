from __future__ import annotations

from core.agent_runtime import hive_topic_create, hive_topic_publish_flow


def test_hive_topic_create_execution_exports_stay_available_from_create_facade() -> None:
    assert hive_topic_create.execute_confirmed_hive_create is hive_topic_publish_flow.execute_confirmed_hive_create
    assert hive_topic_create.hive_topic_create_failure_text is hive_topic_publish_flow.hive_topic_create_failure_text


def test_hive_topic_create_failure_text_keeps_invalid_auth_copy() -> None:
    assert "rejected this runtime's write auth" in hive_topic_publish_flow.hive_topic_create_failure_text("invalid_auth")
