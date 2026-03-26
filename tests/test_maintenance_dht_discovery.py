from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import mock

from core.discovery_index import (
    endpoint_for_peer,
    get_best_helpers,
    recent_peer_endpoint_candidates,
    record_bootstrap_presence,
    register_peer_endpoint,
    register_peer_endpoint_candidate,
)
from core.maintenance import MaintenanceConfig, MaintenanceLoop
from storage.db import get_connection
from storage.migrations import run_migrations


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clear_tables() -> None:
    conn = get_connection()
    try:
        existing_tables = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        for table in (
            "agent_capabilities",
            "peers",
            "peer_endpoints",
            "peer_endpoint_candidates",
            "presence_leases",
            "replica_table",
        ):
            if table in existing_tables:
                conn.execute(f"DELETE FROM {table}")
        conn.commit()
    finally:
        conn.close()


def test_get_best_helpers_prefers_fresher_capability_rows() -> None:
    run_migrations()
    _clear_tables()
    record_bootstrap_presence(
        peer_id="fresh-peer",
        status="idle",
        capabilities=["code"],
        capacity=2,
        trust_score=0.8,
    )
    record_bootstrap_presence(
        peer_id="stale-peer",
        status="idle",
        capabilities=["code"],
        capacity=2,
        trust_score=0.8,
    )
    stale_seen = (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE agent_capabilities SET last_seen_at = ? WHERE peer_id = ?",
            (stale_seen, "stale-peer"),
        )
        conn.commit()
    finally:
        conn.close()

    helpers = get_best_helpers(required_capabilities=["code"], limit=2)

    assert [item.peer_id for item in helpers[:2]] == ["fresh-peer", "stale-peer"]
    assert helpers[0].freshness_score > helpers[1].freshness_score


def test_recent_peer_endpoint_candidates_returns_candidate_rows_without_promoting_them() -> None:
    run_migrations()
    _clear_tables()
    register_peer_endpoint_candidate("candidate-peer", "198.51.100.55", 49555, source="dht")

    candidates = recent_peer_endpoint_candidates(limit=4)

    assert len(candidates) == 1
    assert (candidates[0].peer_id, candidates[0].host, candidates[0].port, candidates[0].source) == (
        "candidate-peer",
        "198.51.100.55",
        49555,
        "dht",
    )
    assert endpoint_for_peer("candidate-peer") is None


def test_maintenance_tick_uses_candidate_endpoints_when_verified_coverage_is_sparse() -> None:
    run_migrations()
    _clear_tables()
    register_peer_endpoint_candidate("candidate-peer", "198.51.100.60", 49560, source="dht")
    loop = MaintenanceLoop(
        config=MaintenanceConfig(
            bootstrap_topics=[],
            dht_discovery_min_nodes=20,
            dht_discovery_verified_limit=4,
            dht_discovery_candidate_limit=2,
            dht_discovery_min_verified_endpoints=1,
        )
    )

    with mock.patch("core.maintenance.publish_local_presence_snapshots"), mock.patch(
        "core.maintenance.sync_from_bootstrap_topics"
    ), mock.patch("core.maintenance.prune_stale_capabilities", return_value=0), mock.patch(
        "core.maintenance.prune_expired_presence",
        return_value=0,
    ), mock.patch("core.maintenance.prune_expired_holders", return_value=0), mock.patch(
        "core.maintenance.reap_stale_subtasks",
        return_value=0,
    ), mock.patch("core.maintenance.release_mature_pending_rewards", return_value=0), mock.patch(
        "core.maintenance.finalize_confirmed_rewards",
        return_value=0,
    ), mock.patch("core.maintenance.prune_expired_topic_files", return_value=0), mock.patch(
        "core.maintenance.initiate_random_hardware_challenge"
    ), mock.patch("core.maintenance.schedule_adaptation_autopilot_tick"), mock.patch(
        "core.maintenance.sync_control_plane_workspace",
        return_value={"ok": True, "writes": 0},
    ), mock.patch("network.signer.get_local_peer_id", return_value="local-peer"), mock.patch(
        "network.dht.get_routing_table",
        return_value=mock.Mock(nodes={}),
    ), mock.patch("network.assist_router.build_find_node_message", return_value=b"find-node"), mock.patch(
        "network.transport.send_message",
        return_value=True,
    ) as send_message:
        loop.run_tick()

    send_message.assert_called_once_with("198.51.100.60", 49560, b"find-node")
    assert endpoint_for_peer("candidate-peer") is None


def test_maintenance_tick_prefers_verified_endpoints_before_candidates() -> None:
    run_migrations()
    _clear_tables()
    register_peer_endpoint("verified-peer", "203.0.113.20", 49020, source="observed")
    register_peer_endpoint_candidate("candidate-peer", "198.51.100.61", 49561, source="dht")
    loop = MaintenanceLoop(
        config=MaintenanceConfig(
            bootstrap_topics=[],
            dht_discovery_min_nodes=20,
            dht_discovery_verified_limit=4,
            dht_discovery_candidate_limit=2,
            dht_discovery_min_verified_endpoints=1,
        )
    )

    with mock.patch("core.maintenance.publish_local_presence_snapshots"), mock.patch(
        "core.maintenance.sync_from_bootstrap_topics"
    ), mock.patch("core.maintenance.prune_stale_capabilities", return_value=0), mock.patch(
        "core.maintenance.prune_expired_presence",
        return_value=0,
    ), mock.patch("core.maintenance.prune_expired_holders", return_value=0), mock.patch(
        "core.maintenance.reap_stale_subtasks",
        return_value=0,
    ), mock.patch("core.maintenance.release_mature_pending_rewards", return_value=0), mock.patch(
        "core.maintenance.finalize_confirmed_rewards",
        return_value=0,
    ), mock.patch("core.maintenance.prune_expired_topic_files", return_value=0), mock.patch(
        "core.maintenance.initiate_random_hardware_challenge"
    ), mock.patch("core.maintenance.schedule_adaptation_autopilot_tick"), mock.patch(
        "core.maintenance.sync_control_plane_workspace",
        return_value={"ok": True, "writes": 0},
    ), mock.patch("network.signer.get_local_peer_id", return_value="local-peer"), mock.patch(
        "network.dht.get_routing_table",
        return_value=mock.Mock(nodes={}),
    ), mock.patch("network.assist_router.build_find_node_message", return_value=b"find-node"), mock.patch(
        "network.transport.send_message",
        return_value=True,
    ) as send_message:
        loop.run_tick()

    send_message.assert_called_once_with("203.0.113.20", 49020, b"find-node")
