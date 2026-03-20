from __future__ import annotations

from pathlib import Path

from core.runtime_capabilities import runtime_capability_snapshot, runtime_capability_statuses
from core.runtime_context import RuntimeContext, RuntimeFeatureFlags, RuntimePaths


def _context(**feature_overrides: bool) -> RuntimeContext:
    flags = RuntimeFeatureFlags(
        local_only_mode=feature_overrides.get("local_only_mode", False),
        public_hive_enabled=feature_overrides.get("public_hive_enabled", True),
        helper_mesh_enabled=feature_overrides.get("helper_mesh_enabled", True),
        allow_workspace_writes=feature_overrides.get("allow_workspace_writes", False),
        allow_sandbox_execution=feature_overrides.get("allow_sandbox_execution", False),
        allow_remote_only_without_backend=feature_overrides.get("allow_remote_only_without_backend", True),
    )
    paths = RuntimePaths(
        project_root=Path("/tmp/project"),
        runtime_home=Path("/tmp/runtime"),
        data_dir=Path("/tmp/runtime/data"),
        config_home_dir=Path("/tmp/runtime/config"),
        docs_dir=Path("/tmp/project/docs"),
        project_config_dir=Path("/tmp/project/config"),
        workspace_root=Path("/tmp/project/workspace"),
        db_path=Path("/tmp/runtime/data/nulla.db"),
    )
    return RuntimeContext(
        mode="test",
        paths=paths,
        log_level="INFO",
        json_logs=True,
        feature_flags=flags,
    )


def test_runtime_capability_statuses_reflect_policy_disabled_surfaces() -> None:
    statuses = {item.name: item for item in runtime_capability_statuses(_context(public_hive_enabled=False, helper_mesh_enabled=False))}

    assert statuses["public_hive_surface"].state == "disabled_by_policy"
    assert statuses["helper_mesh"].state == "disabled_by_policy"
    assert statuses["simulated_payments"].state == "simulated"


def test_runtime_capability_snapshot_exposes_feature_flags_and_capability_rows() -> None:
    snapshot = runtime_capability_snapshot(
        _context(allow_workspace_writes=True, allow_sandbox_execution=True, allow_remote_only_without_backend=False)
    )

    assert snapshot["mode"] == "test"
    assert snapshot["feature_flags"]["allow_workspace_writes"] is True
    assert snapshot["feature_flags"]["allow_sandbox_execution"] is True
    assert snapshot["feature_flags"]["allow_remote_only_without_backend"] is False
    capabilities = {item["name"]: item for item in snapshot["capabilities"]}
    assert capabilities["workspace_write_tools"]["state"] == "implemented"
    assert capabilities["sandbox_execution"]["state"] == "implemented"
    assert capabilities["remote_only_backend_fallback"]["state"] == "disabled_by_policy"
