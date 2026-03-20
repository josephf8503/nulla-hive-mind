from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import mock

from core.bootstrap_adapters import FileTopicAdapter
from core.bootstrap_sync import publish_local_presence_snapshots, sync_from_bootstrap_topics
from core.runtime_paths import configure_runtime_home


def test_publish_local_presence_snapshots_uses_active_record_helper() -> None:
    adapter = mock.Mock()
    adapter.publish_snapshot.return_value = True

    with mock.patch("core.bootstrap_sync._get_active_peer_records", return_value=[]):
        written = publish_local_presence_snapshots(topic_names=["topic_a"], adapter=adapter)

    assert written == 1
    adapter.publish_snapshot.assert_called_once()


def test_sync_from_bootstrap_topics_returns_complete_result_fields() -> None:
    adapter = mock.Mock()
    adapter.fetch_snapshot.side_effect = [{"records": []}, None]

    with mock.patch("core.bootstrap_sync._merge_snapshot", return_value=2):
        result = sync_from_bootstrap_topics(topic_names=["topic_a", "topic_b"], adapter=adapter)

    assert result.topics_written == 0
    assert result.topics_read == 1
    assert result.records_merged == 2


def test_file_topic_adapter_defaults_to_runtime_bootstrap_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        configure_runtime_home(tmp)
        try:
            adapter = FileTopicAdapter()
            assert adapter.base_dir == (Path(tmp) / "data" / "bootstrap").resolve()
            assert adapter.base_dir != Path("bootstrap").resolve()
        finally:
            configure_runtime_home(None)


def test_publish_local_presence_snapshots_writes_to_active_runtime_home() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        configure_runtime_home(tmp)
        try:
            topic_name = "runtime_isolation_test"
            with mock.patch("core.bootstrap_sync._get_active_peer_records", return_value=[]), mock.patch(
                "core.bootstrap_sync.local_peer_id",
                return_value="peer-local",
            ), mock.patch(
                "core.bootstrap_sync.sign",
                return_value="signed",
            ), mock.patch("core.bootstrap_sync.audit_logger.log"):
                written = publish_local_presence_snapshots(topic_names=[topic_name])

            topic_path = Path(tmp) / "data" / "bootstrap" / f"{topic_name}.json"
            assert written == 1
            assert topic_path.exists()
            assert not (Path("bootstrap").resolve() / f"{topic_name}.json").exists()
            payload = json.loads(topic_path.read_text(encoding="utf-8"))
            assert payload["publisher_peer_id"] == "peer-local"
            assert payload["signature"] == "signed"
        finally:
            configure_runtime_home(None)
