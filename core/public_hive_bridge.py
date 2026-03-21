from __future__ import annotations

import contextlib
import os
import ssl
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from core import audit_logger
from core.brain_hive_models import (
    HivePostCreateRequest,
    HiveTopicClaimRequest,
    HiveTopicCreateRequest,
    HiveTopicDeleteRequest,
    HiveTopicStatusUpdateRequest,
    HiveTopicUpdateRequest,
)
from core.meet_and_greet_models import PresenceUpsertRequest
from core.privacy_guard import text_privacy_risks
from core.public_hive import PublicHiveBridgeConfig
from core.public_hive import bootstrap as public_hive_bootstrap
from core.public_hive import client as public_hive_client
from core.public_hive import config as public_hive_config
from core.public_hive import truth as public_hive_truth
from core.runtime_paths import CONFIG_HOME_DIR, PROJECT_ROOT, config_path
from network.signer import get_local_peer_id

_UNSET_SENTINEL = object()


class PublicHiveBridge:
    def __init__(
        self,
        config: PublicHiveBridgeConfig | None = None,
        *,
        urlopen: Any | None = None,
    ) -> None:
        self.config = config or load_public_hive_bridge_config()
        self._urlopen = urlopen or urllib.request.urlopen
        self._nullabook_token: str | None = _UNSET_SENTINEL
        self._client = public_hive_client.PublicHiveHttpClient(
            self.config,
            urlopen=self._urlopen,
            nullabook_token_fn=self._get_nullabook_token,
        )

    def _get_nullabook_token(self) -> str | None:
        if self._nullabook_token is _UNSET_SENTINEL:
            try:
                from core.nullabook_identity import load_local_token
                self._nullabook_token = load_local_token()
            except Exception:
                self._nullabook_token = None
        return self._nullabook_token

    def enabled(self) -> bool:
        return bool(self.config.enabled and self.config.meet_seed_urls)

    def auth_configured(self) -> bool:
        return public_hive_has_auth(self.config)

    def write_enabled(self) -> bool:
        return public_hive_write_enabled(self.config)

    def sync_presence(
        self,
        *,
        agent_name: str,
        capabilities: list[str],
        status: str = "idle",
        transport_mode: str = "nulla_agent",
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled", "posted_to": [], "errors": []}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth", "posted_to": [], "errors": ["public hive auth is not configured"]}

        request = self._presence_request(
            agent_name=agent_name,
            capabilities=capabilities,
            status=status,
            transport_mode=transport_mode,
        )
        return self._post_many(
            "/v1/presence/register",
            payload=request.model_dump(mode="json"),
            base_urls=self.config.meet_seed_urls,
        )

    def heartbeat_presence(
        self,
        *,
        agent_name: str,
        capabilities: list[str],
        status: str = "idle",
        transport_mode: str = "nulla_agent",
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled", "posted_to": [], "errors": []}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth", "posted_to": [], "errors": ["public hive auth is not configured"]}
        request = self._presence_request(
            agent_name=agent_name,
            capabilities=capabilities,
            status=status,
            transport_mode=transport_mode,
        )
        return self._post_many(
            "/v1/presence/heartbeat",
            payload=request.model_dump(mode="json"),
            base_urls=self.config.meet_seed_urls,
        )

    def list_public_topics(
        self,
        *,
        limit: int = 24,
        statuses: tuple[str, ...] = ("open", "researching", "disputed", "partial", "needs_improvement"),
    ) -> list[dict[str, Any]]:
        if not self.enabled() or not self.config.topic_target_url:
            return []
        try:
            result = self._get_json(
                str(self.config.topic_target_url),
                f"/v1/hive/topics?limit={max(1, min(int(limit), 100))}",
            )
        except Exception:
            return []
        wanted_statuses = {str(item or "").strip().lower() for item in statuses if str(item or "").strip()}
        rows = list(result if isinstance(result, list) else [])
        out: list[dict[str, Any]] = []
        for row in rows:
            status = str((row or {}).get("status") or "").strip().lower()
            if wanted_statuses and status not in wanted_statuses:
                continue
            out.append(_annotate_public_hive_truth(dict(row or {})))
        return out

    def get_public_topic(
        self,
        topic_id: str,
        *,
        include_flagged: bool = True,
    ) -> dict[str, Any] | None:
        clean_topic_id = str(topic_id or "").strip()
        if not clean_topic_id or not self.enabled() or not self.config.topic_target_url:
            return None
        route = f"/v1/hive/topics/{clean_topic_id}"
        if include_flagged:
            route = f"{route}?include_flagged=1"
        try:
            result = self._get_json(str(self.config.topic_target_url), route)
        except Exception:
            return None
        return _annotate_public_hive_truth(dict(result or {}))

    def list_public_research_queue(self, *, limit: int = 24) -> list[dict[str, Any]]:
        if not self.enabled() or not self.config.topic_target_url:
            return []
        try:
            result = self._get_json(
                str(self.config.topic_target_url),
                f"/v1/hive/research-queue?limit={max(1, min(int(limit), 100))}",
            )
        except Exception as exc:
            if _route_missing(exc):
                return self._build_research_queue_fallback(limit=max(1, min(int(limit), 100)))
            return []
        rows = [_annotate_public_hive_truth(dict(item or {})) for item in list(result or [])]
        if rows and any(not _research_queue_truth_complete(row) for row in rows):
            return self._overlay_research_queue_truth(rows, limit=max(1, min(int(limit), 100)))
        return rows

    def list_public_review_queue(self, *, object_type: str | None = None, limit: int = 24) -> list[dict[str, Any]]:
        if not self.enabled() or not self.config.topic_target_url:
            return []
        route = f"/v1/hive/review-queue?limit={max(1, min(int(limit), 100))}"
        if str(object_type or "").strip():
            route += f"&object_type={quote(str(object_type or '').strip())}"
        try:
            result = self._get_json(str(self.config.topic_target_url), route)
        except Exception:
            return []
        return [dict(item or {}) for item in list(result or [])]

    def get_public_research_packet(self, topic_id: str) -> dict[str, Any]:
        if not self.enabled() or not self.config.topic_target_url:
            return {}
        clean_topic_id = str(topic_id or "").strip()
        if not clean_topic_id:
            return {}
        try:
            result = self._get_json(
                str(self.config.topic_target_url),
                f"/v1/hive/topics/{clean_topic_id}/research-packet",
            )
        except Exception as exc:
            if _route_missing(exc):
                return self._build_research_packet_fallback(clean_topic_id)
            return {}
        packet = _annotate_public_hive_packet_truth(dict(result or {}))
        if not _research_packet_truth_complete(packet):
            return self._overlay_research_packet_truth(clean_topic_id, packet)
        return packet

    def _build_research_queue_fallback(self, *, limit: int) -> list[dict[str, Any]]:
        from core.brain_hive_research import build_research_queue_entry

        topics = self.list_public_topics(limit=max(32, int(limit) * 2))
        queue_rows: list[dict[str, Any]] = []
        for topic in topics:
            status = str(topic.get("status") or "").strip().lower()
            if status not in {"open", "researching", "disputed", "partial", "needs_improvement"}:
                continue
            topic_id = str(topic.get("topic_id") or "").strip()
            if not topic_id:
                continue
            posts = self._list_public_topic_posts(topic_id, limit=120)
            claims = self._list_public_topic_claims(topic_id, limit=48)
            row = build_research_queue_entry(topic=topic, posts=posts, claims=claims)
            row["claims"] = [dict(item or {}) for item in claims]
            row["updated_at"] = str(topic.get("updated_at") or "")
            row["created_at"] = str(topic.get("created_at") or "")
            row["compat_fallback"] = True
            queue_rows.append(_annotate_public_hive_truth(row))
        queue_rows.sort(
            key=lambda row: (
                float(row.get("research_priority") or 0.0),
                -int(row.get("active_claim_count") or 0),
                str(row.get("updated_at") or ""),
            ),
            reverse=True,
        )
        return queue_rows[: max(1, min(int(limit), 100))]

    def _build_research_packet_fallback(self, topic_id: str) -> dict[str, Any]:
        from core.brain_hive_research import build_topic_research_packet

        topic = self._get_public_topic(topic_id)
        if not topic:
            return {}
        posts = self._list_public_topic_posts(topic_id, limit=400)
        claims = self._list_public_topic_claims(topic_id, limit=200)
        packet = build_topic_research_packet(topic=topic, posts=posts, claims=claims)
        packet["compat_fallback"] = True
        return _annotate_public_hive_packet_truth(packet)

    def _overlay_research_queue_truth(self, rows: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
        fallback_rows = {
            str(item.get("topic_id") or "").strip(): dict(item)
            for item in self._build_research_queue_fallback(limit=limit)
            if str(item.get("topic_id") or "").strip()
        }
        merged_rows: list[dict[str, Any]] = []
        for row in rows:
            topic_id = str(row.get("topic_id") or "").strip()
            fallback = dict(fallback_rows.get(topic_id) or {})
            if fallback:
                merged = dict(fallback)
                merged.update({key: value for key, value in row.items() if value not in (None, "", [], {})})
                merged["truth_overlay"] = True
                merged_rows.append(_annotate_public_hive_truth(merged))
            else:
                merged_rows.append(row)
        return merged_rows[: max(1, min(int(limit), 100))]

    def _overlay_research_packet_truth(self, topic_id: str, direct_packet: dict[str, Any]) -> dict[str, Any]:
        fallback = self._build_research_packet_fallback(topic_id)
        if not fallback:
            return direct_packet
        merged = dict(fallback)
        merged.update({key: value for key, value in direct_packet.items() if value not in (None, "", [], {})})
        if dict(direct_packet.get("topic") or {}):
            topic = dict(fallback.get("topic") or {})
            topic.update({key: value for key, value in dict(direct_packet.get("topic") or {}).items() if value not in (None, "", [], {})})
            merged["topic"] = topic
        merged["truth_overlay"] = True
        return _annotate_public_hive_packet_truth(merged)

    def _get_public_topic(self, topic_id: str) -> dict[str, Any]:
        clean_topic_id = str(topic_id or "").strip()
        if not clean_topic_id or not self.config.topic_target_url:
            return {}
        try:
            result = self._get_json(
                str(self.config.topic_target_url),
                f"/v1/hive/topics/{clean_topic_id}",
            )
        except Exception:
            return {}
        return _annotate_public_hive_truth(dict(result or {}))

    def _list_public_topic_posts(self, topic_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        clean_topic_id = str(topic_id or "").strip()
        if not clean_topic_id or not self.config.topic_target_url:
            return []
        try:
            result = self._get_json(
                str(self.config.topic_target_url),
                f"/v1/hive/topics/{clean_topic_id}/posts?limit={max(1, min(int(limit), 400))}",
            )
        except Exception:
            return []
        return [dict(item or {}) for item in list(result or [])]

    def _list_public_topic_claims(self, topic_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        clean_topic_id = str(topic_id or "").strip()
        if not clean_topic_id or not self.config.topic_target_url:
            return []
        try:
            result = self._get_json(
                str(self.config.topic_target_url),
                f"/v1/hive/topics/{clean_topic_id}/claims?limit={max(1, min(int(limit), 400))}",
            )
        except Exception:
            return []
        return [dict(item or {}) for item in list(result or [])]

    def _topic_result_settlement_helpers(
        self,
        *,
        topic_id: str,
        claim_id: str,
    ) -> list[str]:
        claim_rows = self._list_public_topic_claims(topic_id, limit=200)
        clean_claim_id = str(claim_id or "").strip()
        if clean_claim_id:
            for row in claim_rows:
                if str(row.get("claim_id") or "").strip() != clean_claim_id:
                    continue
                agent_id = str(row.get("agent_id") or "").strip()
                if agent_id:
                    return [agent_id]
        helper_peer_ids: list[str] = []
        seen_helpers: set[str] = set()
        for row in claim_rows:
            claim_status = str(row.get("status") or "").strip().lower()
            if claim_status not in {"active", "completed"}:
                continue
            agent_id = str(row.get("agent_id") or "").strip()
            if not agent_id or agent_id in seen_helpers:
                continue
            seen_helpers.add(agent_id)
            helper_peer_ids.append(agent_id)
        return helper_peer_ids

    def search_public_artifacts(
        self,
        *,
        query_text: str,
        topic_id: str | None = None,
        limit: int = 24,
    ) -> list[dict[str, Any]]:
        if not self.enabled() or not self.config.topic_target_url:
            return []
        clean_query = " ".join(str(query_text or "").split()).strip()
        if not clean_query:
            return []
        route = f"/v1/hive/artifacts/search?q={quote(clean_query)}&limit={max(1, min(int(limit), 100))}"
        if str(topic_id or "").strip():
            route += f"&topic_id={quote(str(topic_id or '').strip())}"
        try:
            result = self._get_json(str(self.config.topic_target_url), route)
        except Exception:
            return []
        return [dict(item or {}) for item in list(result or [])]

    def submit_public_moderation_review(
        self,
        *,
        object_type: str,
        object_id: str,
        decision: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled() or not self.config.topic_target_url:
            return {"ok": False, "status": "disabled"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}
        payload = {
            "object_type": str(object_type or "").strip(),
            "object_id": str(object_id or "").strip(),
            "reviewer_agent_id": get_local_peer_id(),
            "decision": str(decision or "").strip(),
            "note": " ".join(str(note or "").split()).strip()[:512] or None,
        }
        result = self._post_json(str(self.config.topic_target_url), "/v1/hive/moderation/reviews", payload)
        return {"ok": True, **result}

    def get_public_review_summary(
        self,
        *,
        object_type: str,
        object_id: str,
    ) -> dict[str, Any]:
        if not self.enabled() or not self.config.topic_target_url:
            return {}
        clean_type = str(object_type or "").strip()
        clean_id = str(object_id or "").strip()
        if not clean_type or not clean_id:
            return {}
        route = (
            "/v1/hive/moderation/reviews"
            f"?object_type={quote(clean_type)}"
            f"&object_id={quote(clean_id)}"
        )
        try:
            result = self._get_json(str(self.config.topic_target_url), route)
        except Exception:
            return {}
        return dict(result or {})

    def update_public_topic_status(
        self,
        *,
        topic_id: str,
        status: str,
        note: str | None = None,
        claim_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled() or not self.config.topic_target_url:
            return {"ok": False, "status": "disabled"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}
        try:
            result = self._update_topic_status(
                topic_id=topic_id,
                status=status,
                note=note,
                claim_id=claim_id,
                idempotency_key=idempotency_key,
            )
        except (RuntimeError, ValueError) as exc:
            error_text = str(exc or "").strip()
            if "Unknown POST path" in error_text and "/v1/hive/topic-status" in error_text:
                return {"ok": False, "status": "route_unavailable", "error": error_text}
            if "Only the creating agent can update this Hive topic." in error_text:
                return {"ok": False, "status": "not_owner", "error": error_text}
            if "Only the claiming agent can finalize the claim via topic status update." in error_text:
                return {"ok": False, "status": "not_owner", "error": error_text}
            if "already claimed" in error_text.lower():
                return {"ok": False, "status": "already_claimed", "error": error_text}
            if "Unknown topic claim:" in error_text or "Topic claim does not belong" in error_text:
                return {"ok": False, "status": "invalid_claim", "error": error_text}
            if "Only active claims can drive Hive topic status updates." in error_text:
                return {"ok": False, "status": "invalid_claim", "error": error_text}
            if "Claim-backed Hive topic status updates only support" in error_text:
                return {"ok": False, "status": "invalid_status", "error": error_text}
            raise
        return {"ok": True, **result}

    def update_public_topic(
        self,
        *,
        topic_id: str,
        title: str | None = None,
        summary: str | None = None,
        topic_tags: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled() or not self.config.topic_target_url:
            return {"ok": False, "status": "disabled"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}
        combined = "\n".join(part for part in (str(title or "").strip(), str(summary or "").strip()) if part)
        if combined and text_privacy_risks(combined):
            return {"ok": False, "status": "privacy_blocked_topic"}
        request = HiveTopicUpdateRequest(
            topic_id=str(topic_id or "").strip(),
            updated_by_agent_id=get_local_peer_id(),
            title=" ".join(str(title or "").split()).strip()[:180] or None,
            summary=" ".join(str(summary or "").split()).strip()[:4000] or None,
            topic_tags=[str(item).strip()[:64] for item in list(topic_tags or []) if str(item).strip()][:16] or None,
            idempotency_key=str(idempotency_key or "").strip()[:128] or None,
        )
        try:
            result = self._post_json(
                str(self.config.topic_target_url),
                "/v1/hive/topic-update",
                request.model_dump(mode="json"),
            )
        except (RuntimeError, ValueError) as exc:
            error_text = str(exc or "").strip()
            if "Unknown POST path" in error_text and "/v1/hive/topic-update" in error_text:
                return {"ok": False, "status": "route_unavailable", "error": error_text}
            if "Only the creating agent can edit this Hive topic." in error_text:
                return {"ok": False, "status": "not_owner", "error": error_text}
            raise
        return {
            "ok": bool(result.get("topic_id")),
            "status": "updated" if result.get("topic_id") else "topic_update_failed",
            "topic_id": str(result.get("topic_id") or ""),
            "topic_result": result,
        }

    def delete_public_topic(
        self,
        *,
        topic_id: str,
        note: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled() or not self.config.topic_target_url:
            return {"ok": False, "status": "disabled"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}
        request = HiveTopicDeleteRequest(
            topic_id=str(topic_id or "").strip(),
            deleted_by_agent_id=get_local_peer_id(),
            note=" ".join(str(note or "").split()).strip()[:512] or None,
            idempotency_key=str(idempotency_key or "").strip()[:128] or None,
        )
        try:
            result = self._post_json(
                str(self.config.topic_target_url),
                "/v1/hive/topic-delete",
                request.model_dump(mode="json"),
            )
        except (RuntimeError, ValueError) as exc:
            error_text = str(exc or "").strip()
            if "Unknown POST path" in error_text and "/v1/hive/topic-delete" in error_text:
                return {"ok": False, "status": "route_unavailable", "error": error_text}
            if "Only the creating agent can delete this Hive topic." in error_text:
                return {"ok": False, "status": "not_owner", "error": error_text}
            if "already claimed" in error_text.lower():
                return {"ok": False, "status": "already_claimed", "error": error_text}
            if "Only open, unclaimed Hive topics can be deleted." in error_text:
                return {"ok": False, "status": "not_deletable", "error": error_text}
            raise
        return {
            "ok": bool(result.get("topic_id")),
            "status": "deleted" if result.get("topic_id") else "topic_delete_failed",
            "topic_id": str(result.get("topic_id") or ""),
            "topic_result": result,
        }

    def create_public_topic(
        self,
        *,
        title: str,
        summary: str,
        topic_tags: list[str] | None = None,
        status: str = "open",
        visibility: str = "read_public",
        evidence_mode: str = "candidate_only",
        linked_task_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled"}
        if not self.config.topic_target_url:
            return {"ok": False, "status": "missing_target"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}

        clean_title = " ".join(str(title or "").split()).strip()[:180]
        clean_summary = " ".join(str(summary or "").split()).strip()[:4000]
        if not clean_title or not clean_summary:
            return {"ok": False, "status": "empty_topic"}
        if text_privacy_risks(f"{clean_title}\n{clean_summary}"):
            return {"ok": False, "status": "privacy_blocked_topic"}

        display_name: str | None = None
        try:
            from core.nullabook_identity import get_profile
            profile = get_profile(get_local_peer_id())
            if profile and profile.handle:
                display_name = profile.handle.strip()[:64] or None
        except Exception:
            pass
        if not display_name:
            try:
                from core.agent_name_registry import get_agent_name
                display_name = (get_agent_name(get_local_peer_id()) or "")[:64] or None
            except Exception:
                pass

        request = HiveTopicCreateRequest(
            created_by_agent_id=get_local_peer_id(),
            creator_display_name=display_name,
            title=clean_title,
            summary=clean_summary,
            topic_tags=[str(item).strip()[:64] for item in list(topic_tags or []) if str(item).strip()][:16],
            status=str(status or "open").strip() or "open",
            visibility=str(visibility or "read_public").strip() or "read_public",
            evidence_mode=str(evidence_mode or "candidate_only").strip() or "candidate_only",
            linked_task_id=str(linked_task_id or "").strip()[:256] or None,
            idempotency_key=str(idempotency_key or "").strip()[:128] or None,
        )
        topic_result = self._post_json(
            str(self.config.topic_target_url),
            "/v1/hive/topics",
            request.model_dump(mode="json"),
        )
        topic_id = str(topic_result.get("topic_id") or "")
        return {
            "ok": bool(topic_id),
            "status": "created" if topic_id else "topic_failed",
            "topic_id": topic_id,
            "topic_result": topic_result,
        }

    def claim_public_topic(
        self,
        *,
        topic_id: str,
        note: str | None = None,
        capability_tags: list[str] | None = None,
        status: str = "active",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled"}
        if not self.config.topic_target_url:
            return {"ok": False, "status": "missing_target"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}

        clean_topic_id = str(topic_id or "").strip()
        clean_note = " ".join(str(note or "").split()).strip()[:512] or None
        if not clean_topic_id:
            return {"ok": False, "status": "missing_topic_id"}
        if clean_note and text_privacy_risks(clean_note):
            return {"ok": False, "status": "privacy_blocked_claim"}

        request = HiveTopicClaimRequest(
            topic_id=clean_topic_id,
            agent_id=get_local_peer_id(),
            status=str(status or "active").strip() or "active",
            note=clean_note,
            capability_tags=[str(item).strip()[:64] for item in list(capability_tags or []) if str(item).strip()][:16],
            idempotency_key=str(idempotency_key or "").strip()[:128] or None,
        )
        claim_result = self._post_json(
            str(self.config.topic_target_url),
            "/v1/hive/topic-claims",
            request.model_dump(mode="json"),
        )
        return {
            "ok": bool(claim_result.get("claim_id")),
            "status": "claimed" if claim_result.get("claim_id") else "claim_failed",
            "claim_id": str(claim_result.get("claim_id") or ""),
            "topic_id": clean_topic_id,
            "claim_result": claim_result,
        }

    def post_public_topic_progress(
        self,
        *,
        topic_id: str,
        body: str,
        progress_state: str = "working",
        claim_id: str | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled"}
        if not self.config.topic_target_url:
            return {"ok": False, "status": "missing_target"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}

        clean_topic_id = str(topic_id or "").strip()
        clean_body = str(body or "").strip()
        if not clean_topic_id or not clean_body:
            return {"ok": False, "status": "empty_progress"}
        if text_privacy_risks(clean_body):
            return {"ok": False, "status": "privacy_blocked_post"}

        refs = [
            {
                "kind": "task_event",
                "event_type": "progress_update",
                "progress_state": str(progress_state or "working").strip() or "working",
                "claim_id": str(claim_id or "").strip() or None,
            }
        ]
        refs.extend([dict(item) for item in list(evidence_refs or []) if isinstance(item, dict)])
        post_result = self._post_topic_update(
            topic_id=clean_topic_id,
            body=clean_body,
            post_kind="analysis",
            stance="support",
            evidence_refs=refs,
            idempotency_key=idempotency_key,
        )
        return {
            "ok": bool(post_result.get("post_id")),
            "status": "progress_posted" if post_result.get("post_id") else "progress_failed",
            "topic_id": clean_topic_id,
            "post_id": str(post_result.get("post_id") or ""),
            "post_result": post_result,
        }

    def submit_public_topic_result(
        self,
        *,
        topic_id: str,
        body: str,
        result_status: str = "solved",
        post_kind: str = "verdict",
        claim_id: str | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled"}
        if not self.config.topic_target_url:
            return {"ok": False, "status": "missing_target"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}

        clean_topic_id = str(topic_id or "").strip()
        clean_body = str(body or "").strip()
        clean_status = str(result_status or "solved").strip() or "solved"
        clean_post_kind = str(post_kind or "verdict").strip().lower() or "verdict"
        if clean_post_kind not in {"analysis", "evidence", "challenge", "summary", "verdict"}:
            clean_post_kind = "verdict"
        if not clean_topic_id or not clean_body:
            return {"ok": False, "status": "empty_result"}
        if text_privacy_risks(clean_body):
            return {"ok": False, "status": "privacy_blocked_post"}

        refs = [
            {
                "kind": "task_event",
                "event_type": "result_submitted",
                "result_status": clean_status,
                "claim_id": str(claim_id or "").strip() or None,
            }
        ]
        refs.extend([dict(item) for item in list(evidence_refs or []) if isinstance(item, dict)])
        post_result = self._post_topic_update(
            topic_id=clean_topic_id,
            body=clean_body,
            post_kind=clean_post_kind,
            stance="summarize",
            evidence_refs=refs,
            idempotency_key=(str(idempotency_key or "").strip() + ":post")[:128] if idempotency_key else None,
        )
        status_result = self._update_topic_status(
            topic_id=clean_topic_id,
            status=clean_status,
            note=clean_body[:240],
            claim_id=claim_id,
            idempotency_key=(str(idempotency_key or "").strip() + ":status")[:128] if idempotency_key else None,
        )
        credit_settlement: dict[str, Any] = {
            "ok": False,
            "status": "not_applicable",
            "topic_id": clean_topic_id,
            "settlements": [],
            "refunded_amount": 0.0,
        }
        if clean_status in {"solved", "partial"}:
            from core.credit_ledger import settle_hive_task_escrow

            credit_settlement = settle_hive_task_escrow(
                clean_topic_id,
                self._topic_result_settlement_helpers(
                    topic_id=clean_topic_id,
                    claim_id=str(claim_id or "").strip(),
                ),
                result_status=clean_status,
                receipt_prefix=f"hive_topic_settlement:{clean_topic_id}:{clean_status}",
            )
        return {
            "ok": bool(post_result.get("post_id")),
            "status": "result_submitted" if post_result.get("post_id") else "result_failed",
            "topic_id": clean_topic_id,
            "post_id": str(post_result.get("post_id") or ""),
            "post_result": post_result,
            "topic_result": status_result,
            "credit_settlement": credit_settlement,
        }

    def publish_public_task(
        self,
        *,
        task_id: str,
        task_summary: str,
        task_class: str,
        assistant_response: str,
        topic_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled"}
        if not self.config.topic_target_url:
            return {"ok": False, "status": "missing_target"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}

        redacted_summary = " ".join(str(task_summary or "").split()).strip()[:320]
        if not redacted_summary:
            return {"ok": False, "status": "empty_summary"}

        resolved_tags = _topic_tags(task_class=task_class, text=redacted_summary, extra=topic_tags)
        post_body = _public_post_body(assistant_response) or _fallback_public_post_body(
            task_summary=redacted_summary,
            task_class=task_class,
        )
        if post_body and not text_privacy_risks(post_body):
            related_topic = self._find_related_topic(
                task_summary=redacted_summary,
                task_class=task_class,
                topic_tags=resolved_tags,
            )
            if related_topic:
                try:
                    post_result = self._post_topic_update(
                        topic_id=str(related_topic.get("topic_id") or ""),
                        body=post_body,
                        post_kind="analysis",
                        stance="support",
                    )
                    return {
                        "ok": True,
                        "status": "joined_existing_topic",
                        "topic_id": str(related_topic.get("topic_id") or ""),
                        "post_id": str(post_result.get("post_id") or ""),
                        "topic_result": related_topic,
                        "post_result": post_result,
                    }
                except Exception as exc:
                    audit_logger.log(
                        "public_hive_existing_topic_join_error",
                        target_id=task_id,
                        target_type="task",
                        details={
                            "error": str(exc),
                            "topic_id": str(related_topic.get("topic_id") or ""),
                        },
                    )

        title = _task_title(redacted_summary)
        topic_summary = (
            f"Public-safe task thread opened by NULLA. "
            f"Requested work: {redacted_summary} "
            f"Classification: {str(task_class or 'unknown').strip()[:64] or 'unknown'}."
        )[:3000]
        if text_privacy_risks(f"{title}\n{topic_summary}"):
            return {"ok": False, "status": "privacy_blocked_topic"}

        topic = HiveTopicCreateRequest(
            created_by_agent_id=get_local_peer_id(),
            title=title,
            summary=topic_summary,
            topic_tags=resolved_tags,
            status="researching",
            visibility="read_public",
            evidence_mode="candidate_only",
            linked_task_id=str(task_id or "")[:256] or None,
        )
        topic_result = self._post_json(
            str(self.config.topic_target_url),
            "/v1/hive/topics",
            topic.model_dump(mode="json"),
        )
        topic_id = str(topic_result.get("topic_id") or "")
        if not topic_id:
            return {"ok": False, "status": "topic_failed", "result": topic_result}

        if post_body and not text_privacy_risks(post_body):
            try:
                post_result = self._post_topic_update(
                    topic_id=topic_id,
                    body=post_body,
                    post_kind="summary",
                    stance="summarize",
                )
            except Exception as exc:
                audit_logger.log(
                    "public_hive_post_publish_error",
                    target_id=task_id,
                    target_type="task",
                    details={"error": str(exc), "topic_id": topic_id},
                )
                return {"ok": True, "status": "topic_only", "topic_id": topic_id, "topic_result": topic_result}
            return {
                "ok": True,
                "status": "topic_and_post",
                "topic_id": topic_id,
                "post_id": str(post_result.get("post_id") or ""),
                "topic_result": topic_result,
                "post_result": post_result,
            }

        return {"ok": True, "status": "topic_only", "topic_id": topic_id, "topic_result": topic_result}

    def sync_nullabook_profile(
        self,
        *,
        peer_id: str,
        handle: str,
        bio: str = "",
        display_name: str = "",
        twitter_handle: str = "",
    ) -> dict[str, Any]:
        """Push NullaBook profile updates to the meet node."""
        if not self.enabled() or not self.config.topic_target_url:
            return {"ok": False, "status": "disabled"}
        base = str(self.config.topic_target_url)
        reg_payload: dict[str, Any] = {"peer_id": peer_id, "handle": handle, "bio": bio or ""}
        if twitter_handle:
            reg_payload["twitter_handle"] = twitter_handle
        if display_name:
            reg_payload["display_name"] = display_name
        try:
            result = self._post_json(base, "/v1/nullabook/register", reg_payload)
            return {"ok": True, "status": "synced", **result}
        except Exception as exc:
            return {"ok": False, "status": "sync_failed", "error": str(exc)}

    def sync_nullabook_post(
        self,
        *,
        peer_id: str,
        handle: str,
        bio: str,
        content: str,
        post_type: str = "social",
        twitter_handle: str = "",
        display_name: str = "",
    ) -> dict[str, Any]:
        """Push a NullaBook social post to the meet node so it appears in the public feed."""
        if not self.enabled() or not self.config.topic_target_url:
            return {"ok": False, "status": "disabled"}
        base = str(self.config.topic_target_url)
        reg_payload: dict[str, Any] = {"peer_id": peer_id, "handle": handle, "bio": bio or ""}
        if twitter_handle:
            reg_payload["twitter_handle"] = twitter_handle
        if display_name:
            reg_payload["display_name"] = display_name
        with contextlib.suppress(Exception):
            self._post_json(base, "/v1/nullabook/register", reg_payload)
        try:
            result = self._post_json(base, "/v1/nullabook/post", {
                "nullabook_peer_id": peer_id,
                "content": content,
                "post_type": post_type,
            })
            return {"ok": True, "status": "synced", **result}
        except Exception as exc:
            return {"ok": False, "status": "sync_failed", "error": str(exc)}

    def publish_agent_commons_update(
        self,
        *,
        topic: str,
        topic_kind: str,
        summary: str,
        public_body: str,
        topic_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled():
            return {"ok": False, "status": "disabled"}
        if not self.config.topic_target_url:
            return {"ok": False, "status": "missing_target"}
        if not self.write_enabled():
            return {"ok": False, "status": "missing_auth"}

        clean_topic = " ".join(str(topic or "").split()).strip()[:140]
        clean_summary = " ".join(str(summary or "").split()).strip()[:600]
        if not clean_topic or not clean_summary:
            return {"ok": False, "status": "empty_commons_update"}

        resolved_tags = _topic_tags(
            task_class="agent_commons",
            text=f"{clean_topic} {clean_summary}",
            extra=["agent_commons", "commons", "brainstorm", str(topic_kind or "").strip().lower(), *list(topic_tags or [])],
        )
        related_topic = self._find_agent_commons_topic(
            topic=clean_topic,
            topic_kind=topic_kind,
            topic_tags=resolved_tags,
        )
        body = _commons_post_body(topic=clean_topic, summary=clean_summary, public_body=public_body)
        if text_privacy_risks(body):
            return {"ok": False, "status": "privacy_blocked_post"}

        if related_topic:
            post_result = self._post_topic_update(
                topic_id=str(related_topic.get("topic_id") or ""),
                body=body,
                post_kind="analysis",
                stance="propose",
            )
            return {
                "ok": True,
                "status": "joined_existing_commons_topic",
                "topic_id": str(related_topic.get("topic_id") or ""),
                "post_id": str(post_result.get("post_id") or ""),
                "topic_result": related_topic,
                "post_result": post_result,
            }

        title = _commons_topic_title(clean_topic)
        topic_summary = _commons_topic_summary(topic=clean_topic, summary=clean_summary)
        if text_privacy_risks(f"{title}\n{topic_summary}"):
            return {"ok": False, "status": "privacy_blocked_topic"}

        topic_request = HiveTopicCreateRequest(
            created_by_agent_id=get_local_peer_id(),
            title=title,
            summary=topic_summary,
            topic_tags=resolved_tags,
            status="researching",
            visibility="read_public",
            evidence_mode="candidate_only",
            linked_task_id=None,
        )
        topic_result = self._post_json(
            str(self.config.topic_target_url),
            "/v1/hive/topics",
            topic_request.model_dump(mode="json"),
        )
        topic_id = str(topic_result.get("topic_id") or "")
        if not topic_id:
            return {"ok": False, "status": "topic_failed", "result": topic_result}
        post_result = self._post_topic_update(
            topic_id=topic_id,
            body=body,
            post_kind="summary",
            stance="summarize",
        )
        return {
            "ok": True,
            "status": "created_commons_topic",
            "topic_id": topic_id,
            "post_id": str(post_result.get("post_id") or ""),
            "topic_result": topic_result,
            "post_result": post_result,
        }

    def _presence_request(
        self,
        *,
        agent_name: str,
        capabilities: list[str],
        status: str,
        transport_mode: str,
    ) -> PresenceUpsertRequest:
        return PresenceUpsertRequest(
            agent_id=get_local_peer_id(),
            agent_name=str(agent_name or "").strip()[:64] or None,
            status=_normalize_presence_status(status),
            capabilities=[str(item).strip()[:64] for item in capabilities if str(item).strip()][:32],
            home_region=str(self.config.home_region or "global")[:64] or "global",
            current_region=str(self.config.home_region or "global")[:64] or "global",
            transport_mode=str(transport_mode or "nulla_agent")[:64] or "nulla_agent",
            trust_score=0.5,
            timestamp=datetime.now(timezone.utc),
            lease_seconds=300,
        )

    def _post_many(
        self,
        route: str,
        *,
        payload: dict[str, Any],
        base_urls: tuple[str, ...],
    ) -> dict[str, Any]:
        return self._client.post_many(route, payload=payload, base_urls=base_urls)

    def _get_json(self, base_url: str, route: str) -> Any:
        return self._client.get_json(base_url, route)

    def _post_json(self, base_url: str, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.post_json(base_url, route, payload)

    def _find_related_topic(
        self,
        *,
        task_summary: str,
        task_class: str,
        topic_tags: list[str],
    ) -> dict[str, Any] | None:
        best_topic: dict[str, Any] | None = None
        best_score = 0
        local_peer_id = get_local_peer_id()
        for topic in self.list_public_topics(limit=24):
            if str(topic.get("created_by_agent_id") or "") == local_peer_id:
                continue
            score = _topic_match_score(
                task_summary=task_summary,
                task_class=task_class,
                topic_tags=topic_tags,
                topic=topic,
            )
            if score > best_score:
                best_score = score
                best_topic = topic
        if best_score >= 3:
            return best_topic
        return None

    def _find_agent_commons_topic(
        self,
        *,
        topic: str,
        topic_kind: str,
        topic_tags: list[str],
    ) -> dict[str, Any] | None:
        best_topic: dict[str, Any] | None = None
        best_score = 0
        wanted_tokens = set(_content_tokens(topic))
        wanted_kind = str(topic_kind or "").strip().lower()
        for candidate in self.list_public_topics(limit=48, statuses=("open", "researching", "disputed", "solved")):
            tags = {
                str(item or "").strip().lower()
                for item in list(candidate.get("topic_tags") or [])
                if str(item or "").strip()
            }
            title = str(candidate.get("title") or "")
            summary = str(candidate.get("summary") or "")
            if "agent_commons" not in tags and "commons" not in tags and "agent commons" not in f"{title} {summary}".lower():
                continue
            score = 0
            if wanted_kind and wanted_kind in tags:
                score += 2
            if set(topic_tags) & tags:
                score += min(3, len(set(topic_tags) & tags))
            candidate_tokens = set(_content_tokens(title) + _content_tokens(summary))
            score += min(4, len(wanted_tokens & candidate_tokens))
            if title.lower() == _commons_topic_title(topic).lower():
                score += 3
            if score > best_score:
                best_score = score
                best_topic = candidate
        if best_score >= 3:
            return best_topic
        return None

    def _post_topic_update(
        self,
        *,
        topic_id: str,
        body: str,
        post_kind: str,
        stance: str,
        evidence_refs: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        post = HivePostCreateRequest(
            topic_id=str(topic_id or "").strip(),
            author_agent_id=get_local_peer_id(),
            post_kind=str(post_kind or "analysis").strip() or "analysis",
            stance=str(stance or "support").strip() or "support",
            body=str(body or "").strip(),
            evidence_refs=[dict(item) for item in list(evidence_refs or []) if isinstance(item, dict)],
            idempotency_key=str(idempotency_key or "").strip()[:128] or None,
        )
        return self._post_json(
            str(self.config.topic_target_url),
            "/v1/hive/posts",
            post.model_dump(mode="json"),
        )

    def _update_topic_status(
        self,
        *,
        topic_id: str,
        status: str,
        note: str | None = None,
        claim_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        request = HiveTopicStatusUpdateRequest(
            topic_id=str(topic_id or "").strip(),
            updated_by_agent_id=get_local_peer_id(),
            status=str(status or "researching").strip() or "researching",
            note=" ".join(str(note or "").split()).strip()[:512] or None,
            claim_id=str(claim_id or "").strip() or None,
            idempotency_key=str(idempotency_key or "").strip()[:128] or None,
        )
        return self._post_json(
            str(self.config.topic_target_url),
            "/v1/hive/topic-status",
            request.model_dump(mode="json"),
        )

    def _auth_token_for_url(self, url: str) -> str | None:
        return self._client.auth_token_for_url(url)

    def _write_grant_for_request(self, base_url: str, route: str) -> dict[str, Any] | None:
        return self._client.write_grant_for_request(base_url, route)

    def _ssl_context_for_url(self, url: str) -> ssl.SSLContext | None:
        return self._client.ssl_context_for_url(url)


def load_public_hive_bridge_config() -> PublicHiveBridgeConfig:
    return public_hive_config.load_public_hive_bridge_config(
        ensure_public_hive_agent_bootstrap_fn=ensure_public_hive_agent_bootstrap,
        load_json_file_fn=_load_json_file,
        load_agent_bootstrap_fn=_load_agent_bootstrap,
        discover_local_cluster_bootstrap_fn=_discover_local_cluster_bootstrap,
        split_csv_fn=_split_csv,
        json_env_object_fn=_json_env_object,
        merge_auth_tokens_by_base_url_fn=_merge_auth_tokens_by_base_url,
        json_env_write_grants_fn=_json_env_write_grants,
        merge_write_grants_by_base_url_fn=_merge_write_grants_by_base_url,
        clean_token_fn=_clean_token,
        config_path_fn=config_path,
        project_root=PROJECT_ROOT,
        env=os.environ,
    )


def ensure_public_hive_agent_bootstrap() -> Path | None:
    return public_hive_bootstrap.ensure_public_hive_agent_bootstrap(
        config_home_dir=CONFIG_HOME_DIR,
        project_root=PROJECT_ROOT,
        env=os.environ,
        split_csv_fn=_split_csv,
        clean_token_fn=_clean_token,
        json_env_object_fn=_json_env_object,
        json_env_write_grants_fn=_json_env_write_grants,
        load_agent_bootstrap_fn=_load_agent_bootstrap,
        discover_local_cluster_bootstrap_fn=_discover_local_cluster_bootstrap,
        merge_write_grants_by_base_url_fn=_merge_write_grants_by_base_url,
    )


def _load_agent_bootstrap(*, include_runtime: bool = True) -> dict[str, Any]:
    return public_hive_bootstrap.load_agent_bootstrap(
        include_runtime=include_runtime,
        agent_bootstrap_paths_fn=_agent_bootstrap_paths,
    )


def _agent_bootstrap_paths(*, include_runtime: bool) -> tuple[Path, ...]:
    return public_hive_bootstrap.agent_bootstrap_paths(
        include_runtime=include_runtime,
        config_path_fn=config_path,
    )


def write_public_hive_agent_bootstrap(
    *,
    target_path: Path | None = None,
    project_root: str | Path | None = None,
    meet_seed_urls: list[str] | tuple[str, ...] | None = None,
    auth_token: str | None = None,
    auth_tokens_by_base_url: dict[str, str] | None = None,
    write_grants_by_base_url: dict[str, dict[str, dict[str, Any]]] | None = None,
    home_region: str | None = None,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool | None = None,
) -> Path | None:
    return public_hive_bootstrap.write_public_hive_agent_bootstrap(
        target_path=target_path,
        project_root=project_root,
        meet_seed_urls=meet_seed_urls,
        auth_token=auth_token,
        auth_tokens_by_base_url=auth_tokens_by_base_url,
        write_grants_by_base_url=write_grants_by_base_url,
        home_region=home_region,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
        config_path_fn=config_path,
        project_root_default=PROJECT_ROOT,
        load_json_file_fn=_load_json_file,
        load_agent_bootstrap_fn=_load_agent_bootstrap,
        discover_local_cluster_bootstrap_fn=_discover_local_cluster_bootstrap,
        resolve_local_tls_ca_file_fn=_resolve_local_tls_ca_file,
        normalize_base_url_fn=_normalize_base_url,
        clean_token_fn=_clean_token,
        merge_write_grants_by_base_url_fn=_merge_write_grants_by_base_url,
    )


def sync_public_hive_auth_from_ssh(
    *,
    ssh_key_path: str,
    project_root: str | Path | None = None,
    watch_host: str = "",
    watch_user: str = "root",
    remote_config_path: str = "",
    target_path: Path | None = None,
    runner: Any | None = None,
) -> dict[str, Any]:
    return public_hive_bootstrap.sync_public_hive_auth_from_ssh(
        ssh_key_path=ssh_key_path,
        project_root=project_root,
        watch_host=watch_host,
        watch_user=watch_user,
        remote_config_path=remote_config_path,
        target_path=target_path,
        runner=runner or subprocess.run,
        clean_token_fn=_clean_token,
        write_public_hive_agent_bootstrap_fn=write_public_hive_agent_bootstrap,
    )


def _split_csv(value: str) -> list[str]:
    return public_hive_config._split_csv(value)


def _load_json_file(path: Path) -> dict[str, Any]:
    return public_hive_config._load_json_file(path)


def public_hive_has_auth(config: PublicHiveBridgeConfig | None = None, *, payload: dict[str, Any] | None = None) -> bool:
    return public_hive_config.public_hive_has_auth(config, payload=payload)


def public_hive_write_requires_auth(
    config: PublicHiveBridgeConfig | None = None,
    *,
    seed_urls: list[str] | tuple[str, ...] | None = None,
    topic_target_url: str | None = None,
) -> bool:
    return public_hive_config.public_hive_write_requires_auth(
        config,
        seed_urls=seed_urls,
        topic_target_url=topic_target_url,
    )


def public_hive_write_enabled(config: PublicHiveBridgeConfig | None = None) -> bool:
    return public_hive_config.public_hive_write_enabled(
        config,
        load_public_hive_bridge_config_fn=load_public_hive_bridge_config,
    )


def _annotate_public_hive_truth(row: dict[str, Any]) -> dict[str, Any]:
    return public_hive_truth.annotate_public_hive_truth(row)


def _annotate_public_hive_packet_truth(packet: dict[str, Any]) -> dict[str, Any]:
    return public_hive_truth.annotate_public_hive_packet_truth(packet)


def _research_queue_truth_complete(row: dict[str, Any]) -> bool:
    return public_hive_truth.research_queue_truth_complete(row)


def _research_packet_truth_complete(packet: dict[str, Any]) -> bool:
    return public_hive_truth.research_packet_truth_complete(packet)


def _resolve_local_tls_ca_file(tls_ca_file: str | None, *, project_root: str | Path | None = None) -> str | None:
    return public_hive_config._resolve_local_tls_ca_file(tls_ca_file, project_root=project_root or PROJECT_ROOT)


def find_public_hive_ssh_key(project_root: str | Path | None = None) -> Path | None:
    return public_hive_bootstrap.find_public_hive_ssh_key(
        project_root=project_root,
        project_root_default=PROJECT_ROOT,
        env=os.environ,
    )


def ensure_public_hive_auth(
    *,
    project_root: str | Path | None = None,
    target_path: Path | None = None,
    watch_host: str | None = None,
    watch_user: str = "root",
    remote_config_path: str = "",
    require_auth: bool = False,
) -> dict[str, Any]:
    return public_hive_bootstrap.ensure_public_hive_auth(
        project_root=project_root,
        target_path=target_path,
        watch_host=watch_host,
        watch_user=watch_user,
        remote_config_path=remote_config_path,
        require_auth=require_auth,
        env=os.environ,
        project_root_default=PROJECT_ROOT,
        config_home_dir=CONFIG_HOME_DIR,
        load_json_file_fn=_load_json_file,
        discover_local_cluster_bootstrap_fn=_discover_local_cluster_bootstrap,
        load_agent_bootstrap_fn=_load_agent_bootstrap,
        clean_token_fn=_clean_token,
        json_env_object_fn=_json_env_object,
        normalize_base_url_fn=_normalize_base_url,
        public_hive_has_auth_fn=public_hive_has_auth,
        public_hive_write_requires_auth_fn=public_hive_write_requires_auth,
        write_public_hive_agent_bootstrap_fn=write_public_hive_agent_bootstrap,
        find_public_hive_ssh_key_fn=find_public_hive_ssh_key,
        sync_public_hive_auth_from_ssh_fn=sync_public_hive_auth_from_ssh,
    )


def _discover_local_cluster_bootstrap(*, project_root: str | Path | None = None) -> dict[str, Any]:
    return public_hive_bootstrap.discover_local_cluster_bootstrap(
        project_root=project_root,
        project_root_default=PROJECT_ROOT,
        load_json_file_fn=_load_json_file,
        clean_token_fn=_clean_token,
        normalize_base_url_fn=_normalize_base_url,
    )


def _json_env_object(value: str) -> dict[str, str]:
    return public_hive_config._json_env_object(value)


def _json_env_write_grants(value: str) -> dict[str, dict[str, dict[str, Any]]]:
    return public_hive_config._json_env_write_grants(value)


def _merge_auth_tokens_by_base_url(raw: dict[str, Any]) -> dict[str, str]:
    return public_hive_config._merge_auth_tokens_by_base_url(raw)


def _merge_write_grants_by_base_url(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return public_hive_config._merge_write_grants_by_base_url(raw)


def _clean_token(value: str) -> str | None:
    return public_hive_config._clean_token(value)


def _url_requires_auth(url: str) -> bool:
    return public_hive_config._url_requires_auth(url)


def _normalize_base_url(url: str) -> str:
    return public_hive_config._normalize_base_url(url)


def _normalize_presence_status(value: str) -> str:
    return public_hive_truth.normalize_presence_status(value)


def _task_title(task_summary: str) -> str:
    return public_hive_truth.task_title(task_summary)


def _topic_tags(*, task_class: str, text: str, extra: list[str] | None = None) -> list[str]:
    return public_hive_truth.topic_tags(task_class=task_class, text=text, extra=extra)


def _public_post_body(response: str) -> str:
    return public_hive_truth.public_post_body(response)


def _fallback_public_post_body(*, task_summary: str, task_class: str) -> str:
    return public_hive_truth.fallback_public_post_body(task_summary=task_summary, task_class=task_class)


def _commons_topic_title(topic: str) -> str:
    return public_hive_truth.commons_topic_title(topic)


def _commons_topic_summary(*, topic: str, summary: str) -> str:
    return public_hive_truth.commons_topic_summary(topic=topic, summary=summary)


def _commons_post_body(*, topic: str, summary: str, public_body: str) -> str:
    return public_hive_truth.commons_post_body(topic=topic, summary=summary, public_body=public_body)


def _topic_match_score(
    *,
    task_summary: str,
    task_class: str,
    topic_tags: list[str],
    topic: dict[str, Any],
) -> int:
    return public_hive_truth.topic_match_score(
        task_summary=task_summary,
        task_class=task_class,
        topic_tags=topic_tags,
        topic=topic,
    )


def _content_tokens(text: str) -> list[str]:
    return public_hive_truth.content_tokens(text)


def _http_error_detail(exc: urllib.error.HTTPError, *, fallback: str) -> str:
    return public_hive_truth.http_error_detail(exc, fallback=fallback)


def _route_missing(exc: Exception) -> bool:
    return public_hive_truth.route_missing(exc)
