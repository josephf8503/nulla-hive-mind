from __future__ import annotations

from pathlib import Path
from unittest import mock

from core.runtime_paths import PROJECT_ROOT, resolve_workspace_root


def test_resolve_workspace_root_prefers_explicit_path(tmp_path: Path) -> None:
    explicit = tmp_path / "workspace"

    resolved = resolve_workspace_root(explicit)

    assert resolved == explicit.resolve()


def test_resolve_workspace_root_honors_environment_overrides(tmp_path: Path) -> None:
    workspace = tmp_path / "env-workspace"
    workspace.mkdir()
    with mock.patch.dict("os.environ", {"NULLA_WORKSPACE_ROOT": str(workspace)}, clear=False):
        resolved = resolve_workspace_root()

    assert resolved == workspace.resolve()


def test_resolve_workspace_root_falls_back_to_project_env_when_workspace_env_missing(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root"
    project_root.mkdir()
    with mock.patch.dict(
        "os.environ",
        {"NULLA_WORKSPACE_ROOT": "", "NULLA_PROJECT_ROOT": str(project_root)},
        clear=False,
    ):
        resolved = resolve_workspace_root()

    assert resolved == project_root.resolve()


def test_resolve_workspace_root_falls_back_to_project_root_when_cwd_is_missing() -> None:
    with mock.patch.dict("os.environ", {"NULLA_WORKSPACE_ROOT": "", "NULLA_PROJECT_ROOT": ""}, clear=False), mock.patch(
        "core.runtime_paths.Path.cwd",
        side_effect=FileNotFoundError,
    ):
        resolved = resolve_workspace_root()

    assert resolved == PROJECT_ROOT.resolve()
