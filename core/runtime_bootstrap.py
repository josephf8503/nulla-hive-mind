from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core import policy_engine
from core.backend_manager import BackendManager
from core.runtime_paths import ensure_runtime_dirs
from storage.db import healthcheck
from storage.migrations import run_migrations


@dataclass(frozen=True)
class RuntimeBackendSelection:
    backend_name: str
    device: str
    reason: str
    hardware: Any


def bootstrap_storage_environment(*, db_path: str | Path | None = None) -> None:
    ensure_runtime_dirs()
    run_migrations(db_path)
    if not healthcheck(db_path):
        raise RuntimeError("Database healthcheck failed.")


def bootstrap_runtime_environment(*, force_policy_reload: bool = False) -> None:
    bootstrap_storage_environment()
    policy_engine.load(force_reload=force_policy_reload)


def resolve_backend_selection(
    *,
    manager: BackendManager | None = None,
    allow_remote_only: bool | None = None,
) -> RuntimeBackendSelection:
    backend_manager = manager or BackendManager()
    hardware = backend_manager.detect_hardware()
    selection = backend_manager.select_backend(hardware)
    if backend_manager.healthcheck(selection):
        return RuntimeBackendSelection(
            backend_name=str(selection.backend_name),
            device=str(selection.device),
            reason=str(getattr(selection, "reason", "") or ""),
            hardware=hardware,
        )

    remote_allowed = (
        policy_engine.allow_remote_only_without_backend()
        if allow_remote_only is None
        else bool(allow_remote_only)
    )
    if not remote_allowed:
        raise RuntimeError("No supported backend found.")

    return RuntimeBackendSelection(
        backend_name="remote_only",
        device="cpu",
        reason=str(getattr(selection, "reason", "") or "no_supported_backend"),
        hardware=hardware,
    )
