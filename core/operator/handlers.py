from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.reasoning_engine import Plan

from .models import OperatorActionIntent, OperatorActionResult


def handle_list_tools(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    operator_capability_ledger_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    del intent, session_id
    ledger = operator_capability_ledger_fn()
    available = [entry for entry in ledger if entry.get("supported")]
    partial = [entry for entry in available if str(entry.get("support_level") or "").strip().lower() == "partial"]
    full = [entry for entry in available if str(entry.get("support_level") or "").strip().lower() != "partial"]
    unavailable = [entry for entry in ledger if not entry.get("supported")]
    lines = ["Available tool inventory:"]
    for entry in full:
        flag = "approval required" if entry.get("requires_approval") else "read-only"
        capability_id = str(entry.get("capability_id") or "").strip()
        surface = str(entry.get("surface") or "local_operator").strip()
        lines.append(f"- {capability_id} ({surface}, {flag}): {str(entry.get('claim') or '').strip()}")
    if partial:
        lines.append("")
        lines.append("Partially supported:")
        for entry in partial:
            capability_id = str(entry.get("capability_id") or "").strip()
            note = str(entry.get("partial_reason") or "").strip()
            lines.append(f"- {capability_id}: {str(entry.get('claim') or '').strip()}" + (f" ({note})" if note else ""))
    if unavailable:
        lines.append("")
        lines.append("Configured but currently unavailable:")
        for entry in unavailable:
            capability_id = str(entry.get("capability_id") or "").strip()
            lines.append(f"- {capability_id}: {str(entry.get('unsupported_reason') or '').strip()}")
    audit_log_fn(
        "operator_action_list_tools",
        target_id=task_id,
        target_type="task",
        details={"available_tool_ids": [str(entry.get("capability_id") or "").strip() for entry in available]},
    )
    return OperatorActionResult(
        ok=True,
        status="reported",
        response_text="\n".join(lines),
        details={"available_tools": available, "unavailable_tools": unavailable},
    )


def handle_inspect_processes(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    evaluate_local_action_fn: Any,
    inspect_processes_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    del intent, session_id
    gate = evaluate_local_action_fn(
        "inspect_processes",
        destructive=False,
        user_approved=True,
    )
    if gate.mode not in {"execute", "sandbox"}:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=f"I can't inspect running processes right now: {gate.reason}",
            details={"gate_mode": gate.mode},
        )
    rows = inspect_processes_fn()
    if not rows:
        return OperatorActionResult(
            ok=False,
            status="unavailable",
            response_text="I couldn't inspect running processes on this host.",
            details={},
        )
    lines = ["Top running processes by combined CPU and memory pressure:"]
    for row in rows[:6]:
        lines.append(
            f"- PID {row['pid']} {row['name']}: CPU {row['cpu_percent']:.1f}% | MEM {row['mem_percent']:.1f}%"
        )
    audit_log_fn(
        "operator_action_inspect_processes",
        target_id=task_id,
        target_type="task",
        details={"top_processes": rows[:6]},
    )
    return OperatorActionResult(
        ok=True,
        status="reported",
        response_text="\n".join(lines),
        details={"top_processes": rows[:6]},
    )


def handle_inspect_services(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    evaluate_local_action_fn: Any,
    inspect_services_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    del intent, session_id
    gate = evaluate_local_action_fn(
        "inspect_services",
        destructive=False,
        user_approved=True,
    )
    if gate.mode not in {"execute", "sandbox"}:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=f"I can't inspect services right now: {gate.reason}",
            details={"gate_mode": gate.mode},
        )
    rows = inspect_services_fn()
    if not rows:
        return OperatorActionResult(
            ok=False,
            status="unavailable",
            response_text="I couldn't inspect services or startup agents on this host.",
            details={},
        )
    lines = ["Visible services or startup agents:"]
    for row in rows[:8]:
        state = str(row.get("state") or "unknown")
        label = str(row.get("name") or "unknown")
        detail = str(row.get("detail") or "").strip()
        if detail:
            lines.append(f"- {label}: {state} | {detail}")
        else:
            lines.append(f"- {label}: {state}")
    audit_log_fn(
        "operator_action_inspect_services",
        target_id=task_id,
        target_type="task",
        details={"services": rows[:8]},
    )
    return OperatorActionResult(
        ok=True,
        status="reported",
        response_text="\n".join(lines),
        details={"services": rows[:8]},
    )


def handle_inspect_disk_usage(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    evaluate_local_action_fn: Any,
    resolve_target_path_fn: Any,
    inspect_storage_fn: Any,
    candidate_cleanup_roots_fn: Any,
    path_size_fn: Any,
    create_pending_action_fn: Any,
    fmt_bytes_fn: Any,
    monotonic_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    gate = evaluate_local_action_fn(
        "inspect_disk_usage",
        destructive=False,
        user_approved=True,
        reads_workspace=True,
    )
    if gate.mode not in {"execute", "sandbox"}:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=f"I can't inspect storage right now: {gate.reason}",
            details={"gate_mode": gate.mode},
        )

    target = resolve_target_path_fn(intent.target_path)
    if not target.exists():
        return OperatorActionResult(
            ok=False,
            status="missing_path",
            response_text=f"I couldn't inspect storage because this path does not exist: {target}",
            details={"target_path": str(target)},
        )

    summary = inspect_storage_fn(target)
    cleanup_roots = candidate_cleanup_roots_fn(intent.target_path)
    preview_total = int(sum(path_size_fn(path, deadline=monotonic_fn() + 0.8)["bytes"] for path in cleanup_roots))
    pending_action_id = None
    if cleanup_roots:
        pending_action_id = create_pending_action_fn(
            session_id=session_id,
            task_id=task_id,
            action_kind="cleanup_temp_files",
            scope={
                "paths": [str(path) for path in cleanup_roots],
                "target_path": str(target),
                "bytes_preview": preview_total,
            },
        )

    lines = [
        f"Storage scan for {target}",
        f"Free space on volume: {fmt_bytes_fn(summary['disk_free_bytes'])} / {fmt_bytes_fn(summary['disk_total_bytes'])}",
    ]
    if summary["top_entries"]:
        lines.append("Largest entries:")
        for row in summary["top_entries"][:6]:
            marker = " (approx)" if row.get("approximate") else ""
            lines.append(f"- {row['name']}: {fmt_bytes_fn(int(row['bytes']))}{marker}")
    else:
        lines.append("No large entries were found in the requested scope.")

    if cleanup_roots:
        lines.append("")
        lines.append(f"Safe temp cleanup preview: {fmt_bytes_fn(preview_total)} across {len(cleanup_roots)} bounded temp root(s).")
        for path in cleanup_roots[:4]:
            lines.append(f"- {path}")
        lines.append("")
        lines.append(
            f"If you want me to execute it, reply with: clean all temp files. Pending action id: {pending_action_id}"
        )

    audit_log_fn(
        "operator_action_inspect_disk_usage",
        target_id=task_id,
        target_type="task",
        details={
            "target_path": str(target),
            "cleanup_roots": [str(path) for path in cleanup_roots],
            "pending_action_id": pending_action_id,
        },
    )

    return OperatorActionResult(
        ok=True,
        status="reported",
        response_text="\n".join(lines),
        details={
            "target_path": str(target),
            "pending_action_id": pending_action_id,
            "cleanup_roots": [str(path) for path in cleanup_roots],
            "top_entries": summary["top_entries"],
        },
    )


def handle_cleanup_temp_files(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    load_pending_action_fn: Any,
    inspect_disk_usage_handler: Any,
    operator_intent_cls: Any,
    evaluate_local_action_fn: Any,
    path_size_fn: Any,
    delete_children_fn: Any,
    mark_action_executed_fn: Any,
    fmt_bytes_fn: Any,
    monotonic_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    pending = load_pending_action_fn(session_id=session_id, action_kind="cleanup_temp_files", action_id=intent.action_id)
    if pending is None:
        preview = inspect_disk_usage_handler(
            operator_intent_cls(kind="inspect_disk_usage", target_path=intent.target_path),
            task_id=task_id,
            session_id=session_id,
        )
        preview.response_text += "\nCleanup was not executed because there was no approved pending cleanup plan yet."
        preview.details["requires_user_approval"] = True
        return preview

    gate = evaluate_local_action_fn(
        "cleanup_temp_files",
        destructive=True,
        user_approved=bool(intent.approval_requested),
        writes_workspace=True,
    )
    if gate.requires_user_approval and not intent.approval_requested:
        return OperatorActionResult(
            ok=False,
            status="approval_required",
            response_text=(
                "Temp cleanup is ready but still needs explicit approval. "
                f"Reply with: approve cleanup {pending['action_id']} or just say clean all temp files."
            ),
            details={"action_id": pending["action_id"]},
        )
    if gate.mode not in {"execute", "sandbox"}:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=f"I can't run temp cleanup right now: {gate.reason}",
            details={"gate_mode": gate.mode},
        )

    scope = json.loads(str(pending.get("scope_json") or "{}"))
    cleanup_paths = [Path(str(value)).expanduser() for value in scope.get("paths") or []]
    before_total = 0
    after_total = 0
    deleted_files = 0
    deleted_dirs = 0
    errors: list[str] = []
    for root in cleanup_paths:
        if not root.exists():
            continue
        before_info = path_size_fn(root, deadline=monotonic_fn() + 1.2)
        before_total += int(before_info["bytes"])
        counts = delete_children_fn(root)
        deleted_files += int(counts["deleted_files"])
        deleted_dirs += int(counts["deleted_dirs"])
        errors.extend([str(item) for item in counts["errors"]])
        after_info = path_size_fn(root, deadline=monotonic_fn() + 1.2)
        after_total += int(after_info["bytes"])

    reclaimed = max(0, before_total - after_total)
    mark_action_executed_fn(
        pending["action_id"],
        result={
            "before_bytes": before_total,
            "after_bytes": after_total,
            "reclaimed_bytes": reclaimed,
            "deleted_files": deleted_files,
            "deleted_dirs": deleted_dirs,
            "errors": errors,
        },
    )

    learned_plan = Plan(
        summary="Verified user-space temp cleanup workflow with approval and before/after verification.",
        abstract_steps=[
            "inspect bounded temp roots",
            "prepare cleanup preview",
            "require explicit user approval",
            "delete child entries inside temp roots",
            "verify reclaimed space after cleanup",
        ],
        confidence=0.93 if reclaimed > 0 and not errors else 0.82,
        risk_flags=[],
        simulation_steps=[],
        safe_actions=[{"action": "cleanup_temp_files", "paths": [str(path) for path in cleanup_paths]}],
        reads_workspace=True,
        writes_workspace=True,
        requests_network=False,
        requests_subprocess=False,
        evidence_sources=["local_operator:cleanup_temp_files"],
    )

    response = (
        f"Temp cleanup finished. Reclaimed {fmt_bytes_fn(reclaimed)} "
        f"by deleting {deleted_files} files and {deleted_dirs} directories."
    )
    if errors:
        response += f" Some entries could not be removed ({len(errors)} issue(s))."

    audit_log_fn(
        "operator_action_cleanup_temp_files",
        target_id=task_id,
        target_type="task",
        details={
            "action_id": pending["action_id"],
            "paths": [str(path) for path in cleanup_paths],
            "reclaimed_bytes": reclaimed,
            "deleted_files": deleted_files,
            "deleted_dirs": deleted_dirs,
            "error_count": len(errors),
        },
    )

    return OperatorActionResult(
        ok=True,
        status="executed",
        response_text=response,
        details={
            "action_id": pending["action_id"],
            "reclaimed_bytes": reclaimed,
            "deleted_files": deleted_files,
            "deleted_dirs": deleted_dirs,
            "error_count": len(errors),
        },
        learned_plan=learned_plan,
    )


def handle_move_path(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    load_pending_action_fn: Any,
    parse_move_request_fn: Any,
    validate_move_scope_fn: Any,
    resolved_move_target_fn: Any,
    create_pending_action_fn: Any,
    mark_action_executed_fn: Any,
    evaluate_local_action_fn: Any,
    move_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    pending = load_pending_action_fn(session_id=session_id, action_kind="move_path", action_id=intent.action_id)
    if pending is None:
        parsed = parse_move_request_fn(
            intent.raw_text,
            fallback_source=intent.target_path,
            fallback_destination=intent.destination_path,
        )
        if not parsed:
            return OperatorActionResult(
                ok=False,
                status="invalid_request",
                response_text=(
                    "I can move or archive a bounded local path, but I need a quoted source path. "
                    'Use a format like: move "/path/to/source" to "/path/to/archive" '
                    'or archive "/path/to/source"'
                ),
                details={},
            )
        source = Path(str(parsed["source_path"])).expanduser()
        destination_dir = Path(str(parsed["destination_dir"])).expanduser()
        validation_error = validate_move_scope_fn(source, destination_dir)
        if validation_error:
            return OperatorActionResult(
                ok=False,
                status="blocked",
                response_text=validation_error,
                details={
                    "source_path": str(source),
                    "destination_dir": str(destination_dir),
                },
            )
        final_path = resolved_move_target_fn(source, destination_dir)
        if final_path.exists():
            return OperatorActionResult(
                ok=False,
                status="conflict",
                response_text=f"I won't move {source} because the destination already exists: {final_path}",
                details={
                    "source_path": str(source),
                    "destination_path": str(final_path),
                },
            )
        action_id = create_pending_action_fn(
            session_id=session_id,
            task_id=task_id,
            action_kind="move_path",
            scope={
                "source_path": str(source),
                "destination_dir": str(destination_dir),
                "destination_path": str(final_path),
            },
        )
        return OperatorActionResult(
            ok=True,
            status="approval_required",
            response_text=(
                f"Move preview ready.\n"
                f"- Source: {source}\n"
                f"- Destination: {final_path}\n\n"
                f"Reply with: approve move {action_id}"
            ),
            details={
                "action_id": action_id,
                "source_path": str(source),
                "destination_dir": str(destination_dir),
                "destination_path": str(final_path),
            },
        )

    gate = evaluate_local_action_fn(
        "move_path",
        destructive=True,
        user_approved=bool(intent.approval_requested),
        writes_workspace=True,
    )
    if gate.requires_user_approval and not intent.approval_requested:
        return OperatorActionResult(
            ok=False,
            status="approval_required",
            response_text=(
                "The move/archive action is ready but still needs explicit approval. "
                f"Reply with: approve move {pending['action_id']}"
            ),
            details={"action_id": pending["action_id"]},
        )
    if gate.mode not in {"execute", "sandbox"}:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=f"I can't move that path right now: {gate.reason}",
            details={"gate_mode": gate.mode},
        )

    scope = json.loads(str(pending.get("scope_json") or "{}"))
    source = Path(str(scope.get("source_path") or "")).expanduser()
    destination_dir = Path(str(scope.get("destination_dir") or "")).expanduser()
    final_path = Path(str(scope.get("destination_path") or "")).expanduser()
    validation_error = validate_move_scope_fn(source, destination_dir)
    if validation_error:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=validation_error,
            details={
                "action_id": pending["action_id"],
                "source_path": str(source),
                "destination_dir": str(destination_dir),
            },
        )
    if not source.exists():
        return OperatorActionResult(
            ok=False,
            status="missing_path",
            response_text=f"I can't move this path because it no longer exists: {source}",
            details={"action_id": pending["action_id"], "source_path": str(source)},
        )
    destination_dir.mkdir(parents=True, exist_ok=True)
    if final_path.exists():
        return OperatorActionResult(
            ok=False,
            status="conflict",
            response_text=f"I won't overwrite an existing destination: {final_path}",
            details={"action_id": pending["action_id"], "destination_path": str(final_path)},
        )
    try:
        move_fn(str(source), str(final_path))
    except Exception as exc:
        return OperatorActionResult(
            ok=False,
            status="execution_failed",
            response_text=f"I couldn't move {source} to {final_path}: {exc}",
            details={
                "action_id": pending["action_id"],
                "source_path": str(source),
                "destination_path": str(final_path),
                "error": str(exc),
            },
        )
    verified = final_path.exists() and not source.exists()
    mark_action_executed_fn(
        pending["action_id"],
        result={
            "source_path": str(source),
            "destination_path": str(final_path),
            "verified": verified,
        },
    )
    learned_plan = Plan(
        summary="Verified bounded file move/archive workflow with preview, approval, relocation, and post-move verification.",
        abstract_steps=[
            "validate the requested source and destination paths",
            "prepare a move preview",
            "require explicit user approval",
            "move the source into the approved destination",
            "verify the new path exists and the original path is gone",
        ],
        confidence=0.9 if verified else 0.72,
        risk_flags=[],
        simulation_steps=[],
        safe_actions=[{"action": "move_path", "source_path": str(source), "destination_path": str(final_path)}],
        reads_workspace=True,
        writes_workspace=True,
        requests_network=False,
        requests_subprocess=False,
        evidence_sources=["local_operator:move_path"],
    )
    audit_log_fn(
        "operator_action_move_path",
        target_id=task_id,
        target_type="task",
        details={
            "action_id": pending["action_id"],
            "source_path": str(source),
            "destination_path": str(final_path),
            "verified": verified,
        },
    )
    return OperatorActionResult(
        ok=True,
        status="executed",
        response_text=f"Move finished. {source.name} is now at {final_path}",
        details={
            "action_id": pending["action_id"],
            "source_path": str(source),
            "destination_path": str(final_path),
            "verified": verified,
        },
        learned_plan=learned_plan,
    )


def handle_schedule_calendar_event(
    intent: OperatorActionIntent,
    *,
    task_id: str,
    session_id: str,
    load_pending_action_fn: Any,
    parse_calendar_request_fn: Any,
    create_pending_action_fn: Any,
    evaluate_local_action_fn: Any,
    operator_intent_cls: Any,
    render_ics_fn: Any,
    mark_action_executed_fn: Any,
    data_path_fn: Any,
    audit_log_fn: Any,
) -> OperatorActionResult:
    pending = load_pending_action_fn(
        session_id=session_id,
        action_kind="schedule_calendar_event",
        action_id=intent.action_id,
    )
    if pending is None:
        parsed = parse_calendar_request_fn(intent.raw_text)
        if not parsed:
            return OperatorActionResult(
                ok=False,
                status="invalid_request",
                response_text=(
                    "I can schedule a meeting, but I need a title and time. "
                    'Use a format like: schedule a meeting "Ops Sync" on 2026-03-08 15:30 for 45m'
                ),
                details={},
            )
        action_id = create_pending_action_fn(
            session_id=session_id,
            task_id=task_id,
            action_kind="schedule_calendar_event",
            scope=parsed,
        )
        gate = evaluate_local_action_fn(
            "schedule_calendar_event",
            destructive=True,
            user_approved=bool(intent.approval_requested),
            writes_workspace=True,
        )
        if gate.mode in {"execute", "sandbox"} and not gate.requires_user_approval:
            return handle_schedule_calendar_event(
                operator_intent_cls(
                    kind="schedule_calendar_event",
                    approval_requested=True,
                    action_id=action_id,
                    raw_text=intent.raw_text,
                ),
                task_id=task_id,
                session_id=session_id,
                load_pending_action_fn=load_pending_action_fn,
                parse_calendar_request_fn=parse_calendar_request_fn,
                create_pending_action_fn=create_pending_action_fn,
                evaluate_local_action_fn=evaluate_local_action_fn,
                operator_intent_cls=operator_intent_cls,
                render_ics_fn=render_ics_fn,
                mark_action_executed_fn=mark_action_executed_fn,
                data_path_fn=data_path_fn,
                audit_log_fn=audit_log_fn,
            )
        return OperatorActionResult(
            ok=True,
            status="approval_required",
            response_text=(
                f"Meeting preview ready.\n"
                f"- Title: {parsed['title']}\n"
                f"- Starts: {parsed['start_iso']}\n"
                f"- Ends: {parsed['end_iso']}\n"
                f"- Calendar outbox: {parsed['outbox_dir']}\n\n"
                f"Reply with: approve calendar {action_id}"
            ),
            details={"action_id": action_id, **parsed},
        )

    gate = evaluate_local_action_fn(
        "schedule_calendar_event",
        destructive=True,
        user_approved=bool(intent.approval_requested),
        writes_workspace=True,
    )
    if gate.requires_user_approval and not intent.approval_requested:
        return OperatorActionResult(
            ok=False,
            status="approval_required",
            response_text=(
                "Calendar event is ready but still needs explicit approval. "
                f"Reply with: approve calendar {pending['action_id']}"
            ),
            details={"action_id": pending["action_id"]},
        )
    if gate.mode not in {"execute", "sandbox"}:
        return OperatorActionResult(
            ok=False,
            status="blocked",
            response_text=f"I can't create that calendar event right now: {gate.reason}",
            details={"gate_mode": gate.mode},
        )

    scope = json.loads(str(pending.get("scope_json") or "{}"))
    title = str(scope.get("title") or "NULLA Meeting")
    start_iso = str(scope.get("start_iso") or "")
    end_iso = str(scope.get("end_iso") or "")
    outbox_dir = Path(str(scope.get("outbox_dir") or data_path_fn("calendar_outbox"))).expanduser()
    outbox_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", title).strip("-").lower() or "meeting"
    filename = f"{slug}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.ics"
    ics_path = outbox_dir / filename
    ics_path.write_text(render_ics_fn(title=title, start_iso=start_iso, end_iso=end_iso), encoding="utf-8")
    mark_action_executed_fn(
        pending["action_id"],
        result={
            "title": title,
            "start_iso": start_iso,
            "end_iso": end_iso,
            "ics_path": str(ics_path),
        },
    )
    learned_plan = Plan(
        summary="Verified calendar-event creation workflow with preview, policy-aware approval, .ics emission, and path verification.",
        abstract_steps=[
            "parse requested meeting title and time",
            "prepare calendar preview",
            "request approval only when the current autonomy mode requires it",
            "emit .ics file into calendar outbox",
            "verify event artifact path exists",
        ],
        confidence=0.91,
        risk_flags=[],
        simulation_steps=[],
        safe_actions=[{"action": "schedule_calendar_event", "title": title, "ics_path": str(ics_path)}],
        reads_workspace=False,
        writes_workspace=True,
        requests_network=False,
        requests_subprocess=False,
        evidence_sources=["local_operator:schedule_calendar_event"],
    )
    audit_log_fn(
        "operator_action_schedule_calendar_event",
        target_id=task_id,
        target_type="task",
        details={"action_id": pending["action_id"], "ics_path": str(ics_path), "title": title},
    )
    return OperatorActionResult(
        ok=True,
        status="executed",
        response_text=f"Calendar event created. ICS written to {ics_path}",
        details={"action_id": pending["action_id"], "ics_path": str(ics_path), "title": title},
        learned_plan=learned_plan,
    )
