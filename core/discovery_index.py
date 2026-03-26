from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from network.assist_models import CapabilityAd
from storage.db import get_connection

_VERIFIED_ENDPOINT_SOURCES = {"self", "api", "observed", "bootstrap"}
_ENDPOINT_SOURCE_PRIORITIES = {
    "self": 500,
    "api": 450,
    "observed": 400,
    "bootstrap": 300,
    "advertised": 200,
    "dht": 100,
    "block_found": 90,
}


@dataclass
class HelperCandidate:
    peer_id: str
    status: str
    trust_score: float
    capacity: int
    capability_match_score: float
    freshness_score: float
    total_score: float
    host_group_hint_hash: str | None = None


@dataclass(frozen=True)
class PeerEndpointCandidate:
    peer_id: str
    host: str
    port: int
    source: str
    last_seen_at: str
    last_probe_attempt_at: str = ""
    last_probe_delivery_ok: bool = False
    consecutive_probe_failures: int = 0


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _endpoint_source_priority(value: str) -> int:
    normalized = str(value or "").strip().lower()
    return _ENDPOINT_SOURCE_PRIORITIES.get(normalized, 0)


def _is_verified_endpoint_source(value: str) -> bool:
    return str(value or "").strip().lower() in _VERIFIED_ENDPOINT_SOURCES


def upsert_peer_minimal(peer_id: str) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM peers WHERE peer_id = ? LIMIT 1",
            (peer_id,),
        ).fetchone()

        if not row:
            now = _utcnow()
            conn.execute(
                """
                INSERT INTO peers (
                    peer_id, display_alias, trust_score, successful_shards, failed_shards,
                    strike_count, status, last_seen_at, created_at, updated_at
                ) VALUES (?, ?, 0.5, 0, 0, 0, 'active', ?, ?, ?)
                """,
                (peer_id, None, now, now, now),
            )
        else:
            conn.execute(
                "UPDATE peers SET last_seen_at = ?, updated_at = ? WHERE peer_id = ?",
                (_utcnow(), _utcnow(), peer_id),
            )

        conn.commit()
    finally:
        conn.close()


def register_capability_ad(ad: CapabilityAd) -> None:
    upsert_peer_minimal(ad.agent_id)

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_capabilities (
                peer_id, status, capabilities_json, compute_class, supported_models_json, capacity, trust_score,
                assist_filters_json, host_group_hint_hash,
                last_seen_at, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE((SELECT created_at FROM agent_capabilities WHERE peer_id = ?), ?),
                ?
            )
            """,
            (
                ad.agent_id,
                ad.status,
                json.dumps(ad.capabilities, sort_keys=True),
                ad.compute_class,
                json.dumps(ad.supported_models, sort_keys=True),
                ad.capacity,
                ad.trust_score,
                json.dumps(ad.assist_filters.model_dump(), sort_keys=True),
                ad.assist_filters.host_group_hint_hash,
                ad.timestamp.isoformat(),
                ad.agent_id,
                _utcnow(),
                _utcnow(),
            ),
        )

        conn.execute(
            """
            UPDATE peers
            SET trust_score = ?,
                last_seen_at = ?,
                updated_at = ?
            WHERE peer_id = ?
            """,
            (ad.trust_score, ad.timestamp.isoformat(), _utcnow(), ad.agent_id),
        )

        conn.commit()
    finally:
        conn.close()


def record_bootstrap_presence(
    *,
    peer_id: str,
    status: str,
    capabilities: list[str],
    capacity: int,
    trust_score: float,
    host_group_hint_hash: str | None = None,
) -> None:
    upsert_peer_minimal(peer_id)

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_capabilities (
                peer_id, status, capabilities_json, compute_class, supported_models_json, capacity, trust_score,
                assist_filters_json, host_group_hint_hash,
                last_seen_at, created_at, updated_at
            ) VALUES (
                ?, ?, ?, 'cpu_basic', '[]', ?, ?, '{}', ?, ?,
                COALESCE((SELECT created_at FROM agent_capabilities WHERE peer_id = ?), ?),
                ?
            )
            """,
            (
                peer_id,
                status,
                json.dumps(capabilities, sort_keys=True),
                capacity,
                trust_score,
                host_group_hint_hash,
                _utcnow(),
                peer_id,
                _utcnow(),
                _utcnow(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def peer_trust(peer_id: str) -> float:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT trust_score FROM peers WHERE peer_id = ? LIMIT 1",
            (peer_id,),
        ).fetchone()
        return float(row["trust_score"]) if row else 0.50
    finally:
        conn.close()


def host_group_hint_for_peer(peer_id: str) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT host_group_hint_hash FROM agent_capabilities WHERE peer_id = ? LIMIT 1",
            (peer_id,),
        ).fetchone()
        if not row or not row["host_group_hint_hash"]:
            return None
        return str(row["host_group_hint_hash"])
    finally:
        conn.close()


def same_host_group_suspect(local_host_group_hint_hash: str | None, remote_peer_id: str) -> bool:
    if not local_host_group_hint_hash:
        return False
    remote = host_group_hint_for_peer(remote_peer_id)
    return bool(remote and remote == local_host_group_hint_hash)


def _freshness_score(last_seen_at: str | None) -> float:
    dt = _parse_dt(last_seen_at)
    if not dt:
        return 0.2

    age = datetime.now(timezone.utc) - dt
    if age <= timedelta(minutes=5):
        return 1.0
    if age <= timedelta(minutes=30):
        return 0.8
    if age <= timedelta(hours=2):
        return 0.6
    if age <= timedelta(hours=12):
        return 0.4
    return 0.2


def _capability_match(required_capabilities: list[str], peer_capabilities: list[str]) -> float:
    if not required_capabilities:
        return 1.0
    req = set(required_capabilities)
    got = set(peer_capabilities)
    overlap = len(req & got)
    return overlap / max(1, len(req))


def _status_weight(status: str) -> float:
    return {
        "idle": 1.0,
        "limited": 0.6,
        "busy": 0.3,
        "offline": 0.0,
    }.get(status, 0.0)


def get_best_helpers(
    *,
    required_capabilities: list[str],
    exclude_peer_id: str | None = None,
    min_trust: float = 0.30,
    limit: int = 10,
    trusted_only: bool = False,
    exclude_host_group_hint_hash: str | None = None,
) -> list[HelperCandidate]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT a.peer_id, a.status, a.capabilities_json, a.capacity, a.trust_score,
                   a.host_group_hint_hash, a.last_seen_at
            FROM agent_capabilities a
            WHERE a.capacity > 0
            ORDER BY a.last_seen_at DESC
            LIMIT 500
            """
        ).fetchall()
    finally:
        conn.close()

    out: list[HelperCandidate] = []

    for row in rows:
        peer_id = row["peer_id"]
        if exclude_peer_id and peer_id == exclude_peer_id:
            continue

        trust = float(row["trust_score"])
        if trust < min_trust:
            continue
        if trusted_only and trust < 0.65:
            continue

        if exclude_host_group_hint_hash and row["host_group_hint_hash"] and row["host_group_hint_hash"] == exclude_host_group_hint_hash:
            continue

        status = str(row["status"])
        status_w = _status_weight(status)
        if status_w <= 0.0:
            continue

        try:
            caps = json.loads(row["capabilities_json"] or "[]")
        except Exception:
            caps = []

        cap_match = _capability_match(required_capabilities, caps)
        if cap_match <= 0.0:
            continue

        freshness = _freshness_score(row["last_seen_at"])
        capacity_score = min(1.0, float(row["capacity"]) / 4.0)

        total = (
            (0.35 * cap_match)
            + (0.25 * trust)
            + (0.20 * freshness)
            + (0.10 * status_w)
            + (0.10 * capacity_score)
        )

        out.append(
            HelperCandidate(
                peer_id=peer_id,
                status=status,
                trust_score=trust,
                capacity=int(row["capacity"]),
                capability_match_score=cap_match,
                freshness_score=freshness,
                total_score=max(0.0, min(1.0, total)),
                host_group_hint_hash=row["host_group_hint_hash"],
            )
        )

    out.sort(key=lambda x: x.total_score, reverse=True)
    return out[:limit]


def best_helpers_for_task_offer(offer: dict[str, Any], exclude_host_group_hint_hash: str | None = None) -> list[HelperCandidate]:
    try:
        required = json.loads(offer.get("required_capabilities_json", "[]"))
    except Exception:
        required = []

    return get_best_helpers(
        required_capabilities=required,
        exclude_peer_id=offer.get("parent_peer_id"),
        limit=min(int(offer.get("max_helpers", 1)) * 3, 12),
        exclude_host_group_hint_hash=exclude_host_group_hint_hash,
    )


def prune_stale_capabilities(max_age_hours: int = 24) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            DELETE FROM agent_capabilities
            WHERE last_seen_at < ?
            """,
            (cutoff,),
        )
        conn.commit()
        return int(cur.rowcount or 0)
    finally:
        conn.close()


def register_peer_endpoint(peer_id: str, host: str, port: int, source: str = "observed") -> None:
    if not host or port <= 0:
        return
    incoming_source = str(source or "observed")
    if not _is_verified_endpoint_source(incoming_source):
        register_peer_endpoint_candidate(peer_id, host, port, source=incoming_source)
        return

    conn = get_connection()
    try:
        existing = conn.execute(
            """
            SELECT host, port, source
            FROM peer_endpoints
            WHERE peer_id = ?
            LIMIT 1
            """,
            (peer_id,),
        ).fetchone()

        incoming_host = str(host)
        incoming_port = int(port)
        if existing:
            current_host = str(existing["host"])
            current_port = int(existing["port"])
            current_source = str(existing["source"] or "observed")
            same_endpoint = current_host == incoming_host and current_port == incoming_port
            if not same_endpoint and _endpoint_source_priority(incoming_source) < _endpoint_source_priority(current_source):
                return
            if same_endpoint and _endpoint_source_priority(incoming_source) < _endpoint_source_priority(current_source):
                incoming_source = current_source

        conn.execute(
            """
            INSERT OR REPLACE INTO peer_endpoints (
                peer_id, host, port, source, last_seen_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                peer_id,
                incoming_host,
                incoming_port,
                incoming_source,
                _utcnow(),
                _utcnow(),
            ),
        )
        conn.execute(
            """
            DELETE FROM peer_endpoint_candidates
            WHERE peer_id = ? AND host = ? AND port = ?
            """,
            (peer_id, incoming_host, incoming_port),
        )
        conn.commit()
    finally:
        conn.close()


def register_peer_endpoint_candidate(peer_id: str, host: str, port: int, source: str = "dht") -> None:
    if not host or port <= 0:
        return
    normalized_source = str(source or "dht").strip().lower() or "dht"
    if _is_verified_endpoint_source(normalized_source):
        register_peer_endpoint(peer_id, host, port, source=normalized_source)
        return

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO peer_endpoint_candidates (
                peer_id, host, port, source, first_seen_at, last_seen_at,
                last_probe_attempt_at, last_probe_delivery_ok, consecutive_probe_failures, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, '', 0, 0, ?)
            ON CONFLICT(peer_id, host, port, source) DO UPDATE SET
                last_seen_at = excluded.last_seen_at,
                updated_at = excluded.updated_at
            """,
            (
                peer_id,
                str(host),
                int(port),
                normalized_source,
                _utcnow(),
                _utcnow(),
                _utcnow(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def endpoint_for_peer(peer_id: str) -> tuple[str, int] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT host, port FROM peer_endpoints WHERE peer_id = ? LIMIT 1",
            (peer_id,),
        ).fetchone()
        if not row:
            return None
        return str(row["host"]), int(row["port"])
    finally:
        conn.close()


def candidate_endpoints_for_peer(peer_id: str, *, limit: int = 8) -> list[PeerEndpointCandidate]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT peer_id, host, port, source, last_seen_at,
                   last_probe_attempt_at, last_probe_delivery_ok, consecutive_probe_failures
            FROM peer_endpoint_candidates
            WHERE peer_id = ?
            ORDER BY consecutive_probe_failures ASC, updated_at DESC
            LIMIT ?
            """,
            (peer_id, max(1, int(limit))),
        ).fetchall()
    finally:
        conn.close()

    return [
        PeerEndpointCandidate(
            peer_id=str(row["peer_id"]),
            host=str(row["host"]),
            port=int(row["port"]),
            source=str(row["source"]),
            last_seen_at=str(row["last_seen_at"]),
            last_probe_attempt_at=str(row["last_probe_attempt_at"] or ""),
            last_probe_delivery_ok=bool(row["last_probe_delivery_ok"]),
            consecutive_probe_failures=int(row["consecutive_probe_failures"] or 0),
        )
        for row in rows
    ]


def recent_peer_endpoint_candidates(
    *,
    exclude_peer_id: str | None = None,
    limit: int = 32,
    cooldown_seconds: int = 0,
    max_consecutive_failures: int | None = None,
) -> list[PeerEndpointCandidate]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT peer_id, host, port, source, last_seen_at,
                   last_probe_attempt_at, last_probe_delivery_ok, consecutive_probe_failures
            FROM peer_endpoint_candidates
            ORDER BY consecutive_probe_failures ASC, updated_at DESC
            LIMIT ?
            """,
            (max(1, int(limit)) * 4,),
        ).fetchall()
    finally:
        conn.close()

    out: list[PeerEndpointCandidate] = []
    now = datetime.now(timezone.utc)
    for row in rows:
        peer_id = str(row["peer_id"])
        if exclude_peer_id and peer_id == exclude_peer_id:
            continue
        failures = int(row["consecutive_probe_failures"] or 0)
        if max_consecutive_failures is not None and failures >= max(0, int(max_consecutive_failures)):
            continue
        last_probe_attempt_at = str(row["last_probe_attempt_at"] or "")
        if cooldown_seconds > 0 and last_probe_attempt_at:
            probe_dt = _parse_dt(last_probe_attempt_at)
            if probe_dt is not None and (now - probe_dt).total_seconds() < max(0, int(cooldown_seconds)):
                continue
        out.append(
            PeerEndpointCandidate(
                peer_id=peer_id,
                host=str(row["host"]),
                port=int(row["port"]),
                source=str(row["source"]),
                last_seen_at=str(row["last_seen_at"]),
                last_probe_attempt_at=last_probe_attempt_at,
                last_probe_delivery_ok=bool(row["last_probe_delivery_ok"]),
                consecutive_probe_failures=failures,
            )
        )
        if len(out) >= max(1, int(limit)):
            break
    return out


def note_peer_endpoint_candidate_probe_result(
    peer_id: str,
    host: str,
    port: int,
    *,
    source: str,
    delivered: bool,
) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT consecutive_probe_failures
            FROM peer_endpoint_candidates
            WHERE peer_id = ? AND host = ? AND port = ? AND source = ?
            LIMIT 1
            """,
            (peer_id, str(host), int(port), str(source)),
        ).fetchone()
        if not row:
            return
        failures = 0 if delivered else (int(row["consecutive_probe_failures"] or 0) + 1)
        conn.execute(
            """
            UPDATE peer_endpoint_candidates
            SET last_probe_attempt_at = ?,
                last_probe_delivery_ok = ?,
                consecutive_probe_failures = ?,
                updated_at = ?
            WHERE peer_id = ? AND host = ? AND port = ? AND source = ?
            """,
            (
                _utcnow(),
                1 if delivered else 0,
                failures,
                _utcnow(),
                peer_id,
                str(host),
                int(port),
                str(source),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def recent_peer_endpoints(*, exclude_peer_id: str | None = None, limit: int = 32) -> list[tuple[str, str, int]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT peer_id, host, port
            FROM peer_endpoints
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    out: list[tuple[str, str, int]] = []
    for row in rows:
        if exclude_peer_id and row["peer_id"] == exclude_peer_id:
            continue
        out.append((str(row["peer_id"]), str(row["host"]), int(row["port"])))
    return out

# Phase 28: Progressive Trust Spot-Check Probability
def get_spot_check_probability(peer_id: str) -> float:
    """
    Brand new nodes: 100% spot check
    Trusted (>100): 20%
    Provider (>500): 5%
    Elite (>1000): 1%
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT successful_shards FROM peers WHERE peer_id = ? LIMIT 1",
            (peer_id,),
        ).fetchone()
        count = int(row["successful_shards"]) if row else 0
    finally:
        conn.close()

    if count < 100:
        return 1.0
    if count < 500:
        return 0.20
    if count < 1000:
        return 0.05
    return 0.01
