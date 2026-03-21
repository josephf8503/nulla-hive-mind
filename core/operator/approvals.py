from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any


def create_pending_action(
    *,
    session_id: str,
    task_id: str,
    action_kind: str,
    scope: dict[str, Any],
    now_fn: Callable[[], str],
    get_connection_fn: Callable[[], Any],
) -> str:
    now = now_fn()
    action_id = str(uuid.uuid4())
    conn = get_connection_fn()
    try:
        conn.execute(
            """
            UPDATE operator_action_requests
            SET status = 'superseded', updated_at = ?
            WHERE session_id = ? AND action_kind = ? AND status = 'pending_approval'
            """,
            (now, session_id, action_kind),
        )
        conn.execute(
            """
            INSERT INTO operator_action_requests (
                action_id, session_id, task_id, action_kind, scope_json,
                result_json, status, created_at, updated_at, executed_at
            ) VALUES (?, ?, ?, ?, ?, '{}', 'pending_approval', ?, ?, NULL)
            """,
            (action_id, session_id, task_id, action_kind, json.dumps(scope, sort_keys=True), now, now),
        )
        conn.commit()
        return action_id
    finally:
        conn.close()


def load_pending_action(
    *,
    session_id: str,
    action_kind: str,
    action_id: str | None = None,
    get_connection_fn: Callable[[], Any],
) -> dict[str, Any] | None:
    conn = get_connection_fn()
    try:
        if action_id:
            row = conn.execute(
                """
                SELECT *
                FROM operator_action_requests
                WHERE action_id = ? AND session_id = ? AND action_kind = ? AND status = 'pending_approval'
                LIMIT 1
                """,
                (action_id, session_id, action_kind),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT *
                FROM operator_action_requests
                WHERE session_id = ? AND action_kind = ? AND status = 'pending_approval'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (session_id, action_kind),
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def mark_action_executed(
    action_id: str,
    *,
    result: dict[str, Any],
    now_fn: Callable[[], str],
    get_connection_fn: Callable[[], Any],
) -> None:
    now = now_fn()
    conn = get_connection_fn()
    try:
        conn.execute(
            """
            UPDATE operator_action_requests
            SET status = 'executed',
                result_json = ?,
                updated_at = ?,
                executed_at = ?
            WHERE action_id = ?
            """,
            (json.dumps(result, sort_keys=True), now, now, action_id),
        )
        conn.commit()
    finally:
        conn.close()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
