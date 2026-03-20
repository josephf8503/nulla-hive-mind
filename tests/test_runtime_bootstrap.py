from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import pytest

from core.runtime_bootstrap import (
    RuntimeBackendSelection,
    bootstrap_runtime_environment,
    bootstrap_storage_environment,
    resolve_backend_selection,
)


def test_bootstrap_storage_environment_runs_storage_bootstrap_sequence() -> None:
    with mock.patch("core.runtime_bootstrap.ensure_runtime_dirs") as ensure_dirs, mock.patch(
        "core.runtime_bootstrap.run_migrations"
    ) as run_migrations, mock.patch(
        "core.runtime_bootstrap.healthcheck",
        return_value=True,
    ) as healthcheck:
        bootstrap_storage_environment()

    ensure_dirs.assert_called_once_with()
    run_migrations.assert_called_once_with(None)
    healthcheck.assert_called_once_with()


def test_bootstrap_storage_environment_checks_explicit_db_path_when_provided() -> None:
    with mock.patch("core.runtime_bootstrap.ensure_runtime_dirs"), mock.patch(
        "core.runtime_bootstrap.run_migrations"
    ) as run_migrations, mock.patch(
        "core.runtime_bootstrap.healthcheck",
        return_value=True,
    ) as healthcheck:
        bootstrap_storage_environment(db_path="/tmp/nulla-test.db")

    run_migrations.assert_called_once_with("/tmp/nulla-test.db")
    healthcheck.assert_called_once_with("/tmp/nulla-test.db")


def test_bootstrap_storage_environment_raises_when_database_healthcheck_fails() -> None:
    with mock.patch("core.runtime_bootstrap.ensure_runtime_dirs"), mock.patch(
        "core.runtime_bootstrap.run_migrations"
    ), mock.patch("core.runtime_bootstrap.healthcheck", return_value=False):
        with pytest.raises(RuntimeError, match=r"Database healthcheck failed\."):
            bootstrap_storage_environment()


def test_bootstrap_runtime_environment_runs_canonical_startup_sequence() -> None:
    with mock.patch("core.runtime_bootstrap.bootstrap_storage_environment") as bootstrap_storage, mock.patch(
        "core.runtime_bootstrap.policy_engine.load"
    ) as load_policy:
        bootstrap_runtime_environment(force_policy_reload=True)

    bootstrap_storage.assert_called_once_with()
    load_policy.assert_called_once_with(force_reload=True)


def test_bootstrap_runtime_environment_raises_when_database_healthcheck_fails() -> None:
    with mock.patch(
        "core.runtime_bootstrap.bootstrap_storage_environment",
        side_effect=RuntimeError("Database healthcheck failed."),
    ), mock.patch(
        "core.runtime_bootstrap.policy_engine.load"
    ) as load_policy:
        with pytest.raises(RuntimeError, match=r"Database healthcheck failed\."):
            bootstrap_runtime_environment()

    load_policy.assert_not_called()


def test_resolve_backend_selection_returns_real_backend_when_healthy() -> None:
    manager = mock.Mock()
    hardware = SimpleNamespace(accelerator="cuda")
    selection = SimpleNamespace(backend_name="torch", device="cuda", reason="gpu_detected")
    manager.detect_hardware.return_value = hardware
    manager.select_backend.return_value = selection
    manager.healthcheck.return_value = True

    resolved = resolve_backend_selection(manager=manager)

    assert resolved == RuntimeBackendSelection(
        backend_name="torch",
        device="cuda",
        reason="gpu_detected",
        hardware=hardware,
    )


def test_resolve_backend_selection_falls_back_to_remote_only_when_allowed() -> None:
    manager = mock.Mock()
    hardware = SimpleNamespace(accelerator="cpu")
    selection = SimpleNamespace(backend_name="onnxruntime", device="cpu", reason="backend_missing")
    manager.detect_hardware.return_value = hardware
    manager.select_backend.return_value = selection
    manager.healthcheck.return_value = False

    resolved = resolve_backend_selection(manager=manager, allow_remote_only=True)

    assert resolved == RuntimeBackendSelection(
        backend_name="remote_only",
        device="cpu",
        reason="backend_missing",
        hardware=hardware,
    )


def test_resolve_backend_selection_raises_when_remote_only_not_allowed() -> None:
    manager = mock.Mock()
    manager.detect_hardware.return_value = SimpleNamespace(accelerator="cpu")
    manager.select_backend.return_value = SimpleNamespace(
        backend_name="onnxruntime",
        device="cpu",
        reason="backend_missing",
    )
    manager.healthcheck.return_value = False

    with pytest.raises(RuntimeError, match=r"No supported backend found\."):
        resolve_backend_selection(manager=manager, allow_remote_only=False)
