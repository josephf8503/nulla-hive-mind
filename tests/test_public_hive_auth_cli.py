from __future__ import annotations

import json

import ops.ensure_public_hive_auth as cli


def test_main_emits_json_and_returns_zero_when_bootstrap_is_ready(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "ensure_public_hive_auth",
        lambda **kwargs: {"ok": True, "status": "hydrated_from_bundle", "target_path": "/tmp/agent-bootstrap.json"},
    )

    exit_code = cli.main(["--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["status"] == "hydrated_from_bundle"


def test_main_returns_nonzero_for_incomplete_bootstrap(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "ensure_public_hive_auth",
        lambda **kwargs: {"ok": False, "status": "missing_ssh_key", "target_path": "/tmp/agent-bootstrap.json"},
    )

    exit_code = cli.main([])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "status=missing_ssh_key" in captured.out
