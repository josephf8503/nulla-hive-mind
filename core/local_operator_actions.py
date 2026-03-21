from __future__ import annotations

import contextlib
import csv
import fnmatch
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core import audit_logger, policy_engine
from core.execution_gate import ExecutionGate
from core.operator import approvals as operator_approvals
from core.operator import calendar as operator_calendar
from core.operator import handlers as operator_handlers
from core.operator.models import OperatorActionIntent, OperatorActionResult
from core.operator import parser as operator_parser
from core.operator import registry as operator_registry
from core.operator import storage as operator_storage
from core.operator import system as operator_system
from core.operator.parser import _extract_quoted_values
from core.reasoning_engine import Plan
from core.runtime_paths import data_path
from storage.db import get_connection

_TIME_RE = re.compile(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.IGNORECASE)
_ISO_DATETIME_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})(?:[ T](\d{1,2}:\d{2}))?\b")
_DURATION_RE = re.compile(r"\bfor\s+(\d+)\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b", re.IGNORECASE)
_TEMPISH_NAMES = {"temp", "tmp", "cache", "caches"}


def operator_capability_ledger() -> list[dict[str, Any]]:
    return operator_registry.operator_capability_ledger(tools=list_operator_tools())


def parse_operator_action_intent(user_text: str) -> OperatorActionIntent | None:
    return operator_parser.parse_operator_action_intent(user_text)


def list_operator_tools() -> list[dict[str, Any]]:
    return operator_registry.list_operator_tools()


def dispatch_operator_action(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    if intent.kind == "list_tools":
        return _handle_list_tools(intent, task_id=task_id, session_id=session_id)
    if intent.kind == "inspect_processes":
        return _handle_inspect_processes(intent, task_id=task_id, session_id=session_id)
    if intent.kind == "inspect_services":
        return _handle_inspect_services(intent, task_id=task_id, session_id=session_id)
    if intent.kind == "inspect_disk_usage":
        return _handle_inspect_disk_usage(intent, task_id=task_id, session_id=session_id)
    if intent.kind == "cleanup_temp_files":
        return _handle_cleanup_temp_files(intent, task_id=task_id, session_id=session_id)
    if intent.kind == "move_path":
        return _handle_move_path(intent, task_id=task_id, session_id=session_id)
    if intent.kind == "schedule_calendar_event":
        return _handle_schedule_calendar_event(intent, task_id=task_id, session_id=session_id)
    return OperatorActionResult(
        ok=False,
        status="unsupported",
        response_text="I recognized an operator action request, but that action is not wired on this runtime yet.",
        details={
            "kind": intent.kind,
            "capability_gap": {
                "requested_capability": f"operator.{intent.kind}",
                "requested_label": intent.kind,
                "support_level": "unsupported",
                "gap_kind": "unwired",
                "reason": f"Operator action `{intent.kind}` is not wired on this runtime.",
                "nearby_alternatives": operator_registry._operator_nearby_alternatives(intent.kind),
            },
        },
    )


def _handle_list_tools(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_list_tools(
        intent,
        task_id=task_id,
        session_id=session_id,
        operator_capability_ledger_fn=operator_capability_ledger,
        audit_log_fn=audit_logger.log,
    )


def _handle_inspect_processes(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_inspect_processes(
        intent,
        task_id=task_id,
        session_id=session_id,
        evaluate_local_action_fn=ExecutionGate.evaluate_local_action,
        inspect_processes_fn=_inspect_processes,
        audit_log_fn=audit_logger.log,
    )


def _handle_inspect_services(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_inspect_services(
        intent,
        task_id=task_id,
        session_id=session_id,
        evaluate_local_action_fn=ExecutionGate.evaluate_local_action,
        inspect_services_fn=_inspect_services,
        audit_log_fn=audit_logger.log,
    )


def _handle_inspect_disk_usage(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_inspect_disk_usage(
        intent,
        task_id=task_id,
        session_id=session_id,
        evaluate_local_action_fn=ExecutionGate.evaluate_local_action,
        resolve_target_path_fn=_resolve_target_path,
        inspect_storage_fn=_inspect_storage,
        candidate_cleanup_roots_fn=_candidate_cleanup_roots,
        path_size_fn=_path_size,
        create_pending_action_fn=_create_pending_action,
        fmt_bytes_fn=_fmt_bytes,
        monotonic_fn=time.monotonic,
        audit_log_fn=audit_logger.log,
    )


def _handle_cleanup_temp_files(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_cleanup_temp_files(
        intent,
        task_id=task_id,
        session_id=session_id,
        load_pending_action_fn=_load_pending_action,
        inspect_disk_usage_handler=_handle_inspect_disk_usage,
        operator_intent_cls=OperatorActionIntent,
        evaluate_local_action_fn=ExecutionGate.evaluate_local_action,
        path_size_fn=_path_size,
        delete_children_fn=_delete_children,
        mark_action_executed_fn=_mark_action_executed,
        fmt_bytes_fn=_fmt_bytes,
        monotonic_fn=time.monotonic,
        audit_log_fn=audit_logger.log,
    )


def _handle_move_path(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_move_path(
        intent,
        task_id=task_id,
        session_id=session_id,
        load_pending_action_fn=_load_pending_action,
        parse_move_request_fn=_parse_move_request,
        validate_move_scope_fn=_validate_move_scope,
        resolved_move_target_fn=_resolved_move_target,
        create_pending_action_fn=_create_pending_action,
        mark_action_executed_fn=_mark_action_executed,
        evaluate_local_action_fn=ExecutionGate.evaluate_local_action,
        move_fn=shutil.move,
        audit_log_fn=audit_logger.log,
    )


def _handle_schedule_calendar_event(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
) -> OperatorActionResult:
    return operator_handlers.handle_schedule_calendar_event(
        intent,
        task_id=task_id,
        session_id=session_id,
        load_pending_action_fn=_load_pending_action,
        parse_calendar_request_fn=_parse_calendar_request,
        create_pending_action_fn=_create_pending_action,
        evaluate_local_action_fn=ExecutionGate.evaluate_local_action,
        operator_intent_cls=OperatorActionIntent,
        render_ics_fn=_render_ics,
        mark_action_executed_fn=_mark_action_executed,
        data_path_fn=data_path,
        audit_log_fn=audit_logger.log,
    )


def _resolve_target_path(raw_path: str | None) -> Path:
    return operator_storage.resolve_target_path(
        raw_path,
        os_name=os.name,
        env=os.environ,
        home_dir_fn=Path.home,
    )


def _inspect_storage(target: Path) -> dict[str, Any]:
    return operator_storage.inspect_storage(
        target,
        disk_usage_fn=shutil.disk_usage,
        path_size_fn=_path_size,
        monotonic_fn=time.monotonic,
    )


def _path_size(path: Path, *, deadline: float, max_entries: int = 6000) -> dict[str, Any]:
    return operator_storage.path_size(
        path,
        deadline=deadline,
        max_entries=max_entries,
        walk_fn=os.walk,
        monotonic_fn=time.monotonic,
    )


def _inspect_processes() -> list[dict[str, Any]]:
    return operator_system.inspect_processes(
        os_name=os.name,
        subprocess_run=subprocess.run,
        csv_module=csv,
    )


def _inspect_services() -> list[dict[str, Any]]:
    return operator_system.inspect_services(
        os_name=os.name,
        subprocess_run=subprocess.run,
        which_fn=shutil.which,
    )


def _parse_calendar_request(text: str) -> dict[str, Any] | None:
    return operator_calendar.parse_calendar_request(
        text,
        extract_quoted_values_fn=_extract_quoted_values,
        data_path_fn=data_path,
        now_fn=lambda: datetime.now().astimezone(),
    )


def _render_ics(*, title: str, start_iso: str, end_iso: str) -> str:
    return operator_calendar.render_ics(
        title=title,
        start_iso=start_iso,
        end_iso=end_iso,
        uuid_fn=uuid.uuid4,
        now_fn=lambda: datetime.now(timezone.utc),
    )


def _parse_move_request(
    text: str,
    *,
    fallback_source: str | None = None,
    fallback_destination: str | None = None,
) -> dict[str, str] | None:
    return operator_storage.parse_move_request(
        text,
        fallback_source=fallback_source,
        fallback_destination=fallback_destination,
        extract_quoted_values_fn=_extract_quoted_values,
        data_path_fn=data_path,
        expandvars_fn=os.path.expandvars,
    )


def _candidate_cleanup_roots(target_path: str | None) -> list[Path]:
    return operator_storage.candidate_cleanup_roots(
        target_path,
        env=os.environ,
        gettempdir_fn=tempfile.gettempdir,
        is_temp_cleanup_path_fn=_is_temp_cleanup_path,
        expandvars_fn=os.path.expandvars,
    )


def _is_temp_cleanup_path(path: Path) -> bool:
    return operator_storage.is_temp_cleanup_path(
        path,
        path_is_denied_fn=_path_is_denied,
        tempish_names=_TEMPISH_NAMES,
        gettempdir_fn=tempfile.gettempdir,
        home_dir_fn=Path.home,
        is_relative_to_fn=_is_relative_to,
    )


def _operator_safe_path(path: Path) -> bool:
    return operator_storage.operator_safe_path(
        path,
        path_is_denied_fn=_path_is_denied,
        gettempdir_fn=tempfile.gettempdir,
        data_path_fn=data_path,
        is_relative_to_fn=_is_relative_to,
        home_dir_fn=Path.home,
    )


def _validate_move_scope(source: Path, destination_dir: Path) -> str | None:
    return operator_storage.validate_move_scope(
        source,
        destination_dir,
        operator_safe_path_fn=_operator_safe_path,
        resolved_move_target_fn=_resolved_move_target,
        is_relative_to_fn=_is_relative_to,
    )


def _resolved_move_target(source: Path, destination_dir: Path) -> Path:
    return operator_storage.resolved_move_target(source, destination_dir)


def _path_is_denied(path: Path) -> bool:
    return operator_storage.path_is_denied(path, policy_get=policy_engine.get)


def _delete_children(root: Path) -> dict[str, Any]:
    return operator_storage.delete_children(root, rmtree_fn=shutil.rmtree)


def _create_pending_action(*, session_id: str, task_id: str, action_kind: str, scope: dict[str, Any]) -> str:
    return operator_approvals.create_pending_action(
        session_id=session_id,
        task_id=task_id,
        action_kind=action_kind,
        scope=scope,
        now_fn=_utcnow,
        get_connection_fn=get_connection,
    )


def _load_pending_action(*, session_id: str, action_kind: str, action_id: str | None = None) -> dict[str, Any] | None:
    return operator_approvals.load_pending_action(
        session_id=session_id,
        action_kind=action_kind,
        action_id=action_id,
        get_connection_fn=get_connection,
    )


def _mark_action_executed(action_id: str, *, result: dict[str, Any]) -> None:
    operator_approvals.mark_action_executed(
        action_id,
        result=result,
        now_fn=_utcnow,
        get_connection_fn=get_connection,
    )


def _fmt_bytes(value: int) -> str:
    return operator_storage.fmt_bytes(value)


def _is_relative_to(path: Path, base: Path) -> bool:
    return operator_storage.is_relative_to(path, base)


def _utcnow() -> str:
    return operator_approvals.utcnow()
