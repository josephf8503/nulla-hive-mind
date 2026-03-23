from __future__ import annotations

from typing import Any

from core import brain_hive_commons_promotion, brain_hive_queries, brain_hive_review_workflow
from core.agent_name_registry import get_agent_name
from core.brain_hive_guard import guard_post_submission, guard_topic_submission
from core.brain_hive_models import (
    BrainHiveStatsResponse,
    HiveAgentProfile,
    HiveClaimLinkRecord,
    HiveClaimLinkRequest,
    HiveCommonsCommentRecord,
    HiveCommonsCommentRequest,
    HiveCommonsEndorseRecord,
    HiveCommonsEndorseRequest,
    HiveCommonsPromotionActionRequest,
    HiveCommonsPromotionCandidateRecord,
    HiveCommonsPromotionCandidateRequest,
    HiveCommonsPromotionReviewRequest,
    HiveModerationReviewRecord,
    HiveModerationReviewRequest,
    HiveModerationReviewSummary,
    HivePostCreateRequest,
    HivePostRecord,
    HiveRegionStat,
    HiveTopicClaimRecord,
    HiveTopicClaimRequest,
    HiveTopicCreateRequest,
    HiveTopicDeleteRequest,
    HiveTopicRecord,
    HiveTopicStatusUpdateRequest,
    HiveTopicUpdateRequest,
)
from core.brain_hive_moderation import ModerationDecision, moderate_post_submission, moderate_topic_submission
from core.privacy_guard import assert_public_text_safe, assert_public_value_safe, text_privacy_risks
from core.runtime_continuity import load_hive_idempotent_result, store_hive_idempotent_result
from core.scoreboard_engine import get_peer_scoreboard
from storage.brain_hive_moderation_store import (
    apply_post_moderation,
    apply_topic_moderation,
)
from storage.brain_hive_store import (
    count_active_topic_claims,
    count_topic_posts,
    create_post,
    create_post_comment,
    create_topic,
    get_topic,
    get_topic_claim,
    list_claim_links,
    list_post_comments,
    list_post_endorsements,
    list_posts,
    list_topic_claims,
    list_topics,
    upsert_claim_link,
    upsert_post_endorsement,
    upsert_topic_claim,
)
from storage.brain_hive_store import (
    update_topic as store_update_topic,
)
from storage.brain_hive_store import (
    update_topic_status as store_update_topic_status,
)
from storage.db import get_connection

_PUBLIC_HIVE_VISIBILITIES = {"agent_public", "read_public"}


class BrainHiveService:
    _post_model_cls = HivePostRecord

    def create_topic(self, request: HiveTopicCreateRequest) -> HiveTopicRecord:
        cached = self._cached_result(request.idempotency_key, HiveTopicRecord)
        if cached is not None:
            return cached
        if request.creator_display_name:
            try:
                from core.agent_name_registry import claim_agent_name, get_agent_name
                if not get_agent_name(request.created_by_agent_id):
                    claim_agent_name(request.created_by_agent_id, request.creator_display_name)
            except Exception:
                pass
        public_topic = self._visibility_requires_public_guard(request.visibility)
        if public_topic:
            guard_topic_submission(request)
        moderation = moderate_topic_submission(request)
        if request.force_review_required and moderation.state == "approved":
            moderation = self._forced_review_decision(moderation)
        topic_id = create_topic(
            created_by_agent_id=request.created_by_agent_id,
            title=request.title,
            summary=request.summary,
            topic_tags=list(request.topic_tags),
            status=request.status,
            visibility=request.visibility,
            evidence_mode=request.evidence_mode,
            linked_task_id=request.linked_task_id,
        )
        apply_topic_moderation(
            topic_id=topic_id,
            agent_id=request.created_by_agent_id,
            moderation_state=moderation.state,
            moderation_score=moderation.score,
            reasons=moderation.reasons,
            metadata=moderation.metadata,
        )
        record = self.get_topic(topic_id, include_flagged=True)
        self._store_idempotent_result(request.idempotency_key, "hive.create_topic", record)
        return record

    def get_topic(self, topic_id: str, *, include_flagged: bool = False) -> HiveTopicRecord:
        row = get_topic(topic_id, visible_only=not include_flagged)
        if not row:
            raise KeyError(f"Unknown topic: {topic_id}")
        creator_display_name, creator_claim_label = self._display_fields(row["created_by_agent_id"])
        return HiveTopicRecord(
            **row,
            creator_display_name=creator_display_name,
            creator_claim_label=creator_claim_label,
        )

    def list_topics(self, *, status: str | None = None, limit: int = 100, include_flagged: bool = False) -> list[HiveTopicRecord]:
        rows = list_topics(status=status, limit=limit, visible_only=not include_flagged)
        out: list[HiveTopicRecord] = []
        for row in rows:
            creator_display_name, creator_claim_label = self._display_fields(row["created_by_agent_id"])
            out.append(
                HiveTopicRecord(
                    **row,
                    creator_display_name=creator_display_name,
                    creator_claim_label=creator_claim_label,
                )
            )
        return out

    def create_post(self, request: HivePostCreateRequest) -> HivePostRecord:
        cached = self._cached_result(request.idempotency_key, HivePostRecord)
        if cached is not None:
            return cached
        topic = self.get_topic(request.topic_id, include_flagged=True)
        if self._visibility_requires_public_guard(topic.visibility):
            guard_post_submission(request)
            assert_public_value_safe(request.evidence_refs, field_name="Hive evidence refs")
        moderation = moderate_post_submission(request)
        if request.force_review_required and moderation.state == "approved":
            moderation = self._forced_review_decision(moderation)
        post_id = create_post(
            topic_id=request.topic_id,
            author_agent_id=request.author_agent_id,
            post_kind=request.post_kind,
            stance=request.stance,
            body=request.body,
            evidence_refs=list(request.evidence_refs),
        )
        apply_post_moderation(
            post_id=post_id,
            agent_id=request.author_agent_id,
            moderation_state=moderation.state,
            moderation_score=moderation.score,
            reasons=moderation.reasons,
            metadata=moderation.metadata,
        )
        row = self._post_row(post_id)
        author_display_name, author_claim_label = self._display_fields(row["author_agent_id"])
        record = HivePostRecord(
            **row,
            author_display_name=author_display_name,
            author_claim_label=author_claim_label,
        )
        self._store_idempotent_result(request.idempotency_key, "hive.create_post", record)
        return record

    def endorse_post(self, request: HiveCommonsEndorseRequest) -> HiveCommonsEndorseRecord:
        cached = self._cached_result(request.idempotency_key, HiveCommonsEndorseRecord)
        if cached is not None:
            return cached
        post = self._require_commons_post(request.post_id)
        if self._post_requires_public_guard(post) and request.note is not None:
            assert_public_text_safe(request.note, field_name="Hive endorsement note")
        weight = self._reviewer_weight(request.agent_id)
        endorsement_id = upsert_post_endorsement(
            post_id=post["post_id"],
            agent_id=request.agent_id,
            endorsement_kind=request.endorsement_kind,
            note=request.note,
            weight=weight,
        )
        row = next(item for item in list_post_endorsements(post["post_id"], limit=200) if item["endorsement_id"] == endorsement_id)
        agent_display_name, agent_claim_label = self._display_fields(request.agent_id)
        record = HiveCommonsEndorseRecord(
            **row,
            agent_display_name=agent_display_name,
            agent_claim_label=agent_claim_label,
        )
        self._store_idempotent_result(request.idempotency_key, "hive.commons.endorse_post", record)
        return record

    def list_post_endorsements(self, post_id: str, *, limit: int = 200) -> list[HiveCommonsEndorseRecord]:
        self._require_commons_post(post_id)
        out: list[HiveCommonsEndorseRecord] = []
        for row in list_post_endorsements(post_id, limit=limit):
            agent_display_name, agent_claim_label = self._display_fields(str(row["agent_id"]))
            out.append(
                HiveCommonsEndorseRecord(
                    **row,
                    agent_display_name=agent_display_name,
                    agent_claim_label=agent_claim_label,
                )
            )
        return out

    def comment_on_post(self, request: HiveCommonsCommentRequest) -> HiveCommonsCommentRecord:
        cached = self._cached_result(request.idempotency_key, HiveCommonsCommentRecord)
        if cached is not None:
            return cached
        post = self._require_commons_post(request.post_id)
        mirror = HivePostCreateRequest(
            topic_id=str(post["topic_id"]),
            author_agent_id=request.author_agent_id,
            body=request.body,
            post_kind="analysis",
            stance="question",
            evidence_refs=[],
        )
        if self._post_requires_public_guard(post):
            guard_post_submission(mirror)
        moderation = moderate_post_submission(mirror)
        comment_id = create_post_comment(
            post_id=post["post_id"],
            author_agent_id=request.author_agent_id,
            body=request.body,
            moderation_state=moderation.state,
            moderation_score=moderation.score,
            moderation_reasons=moderation.reasons,
        )
        row = next(item for item in list_post_comments(post["post_id"], limit=200, visible_only=False) if item["comment_id"] == comment_id)
        author_display_name, author_claim_label = self._display_fields(request.author_agent_id)
        record = HiveCommonsCommentRecord(
            **row,
            author_display_name=author_display_name,
            author_claim_label=author_claim_label,
        )
        self._store_idempotent_result(request.idempotency_key, "hive.commons.comment_post", record)
        return record

    def list_post_comments(self, post_id: str, *, limit: int = 200, include_flagged: bool = False) -> list[HiveCommonsCommentRecord]:
        self._require_commons_post(post_id)
        out: list[HiveCommonsCommentRecord] = []
        for row in list_post_comments(post_id, limit=limit, visible_only=not include_flagged):
            author_display_name, author_claim_label = self._display_fields(str(row["author_agent_id"]))
            out.append(
                HiveCommonsCommentRecord(
                    **row,
                    author_display_name=author_display_name,
                    author_claim_label=author_claim_label,
                )
            )
        return out

    def evaluate_promotion_candidate(self, request: HiveCommonsPromotionCandidateRequest) -> HiveCommonsPromotionCandidateRecord:
        return brain_hive_commons_promotion.evaluate_promotion_candidate(self, request)

    def list_commons_promotion_candidates(self, *, limit: int = 100, status: str | None = None) -> list[HiveCommonsPromotionCandidateRecord]:
        return brain_hive_commons_promotion.list_candidates(self, limit=limit, status=status)

    def review_promotion_candidate(self, request: HiveCommonsPromotionReviewRequest) -> HiveCommonsPromotionCandidateRecord:
        return brain_hive_commons_promotion.review_promotion_candidate(self, request)

    def promote_commons_candidate(self, request: HiveCommonsPromotionActionRequest) -> HiveTopicRecord:
        return brain_hive_commons_promotion.promote_commons_candidate(self, request)

    def claim_topic(self, request: HiveTopicClaimRequest) -> HiveTopicClaimRecord:
        cached = self._cached_result(request.idempotency_key, HiveTopicClaimRecord)
        if cached is not None:
            return cached
        topic = self.get_topic(request.topic_id, include_flagged=True)
        if self._visibility_requires_public_guard(topic.visibility) and request.note is not None:
            assert_public_text_safe(request.note, field_name="Hive claim note")
        claim_id = upsert_topic_claim(
            topic_id=request.topic_id,
            agent_id=request.agent_id,
            status=request.status,
            note=request.note,
            capability_tags=list(request.capability_tags),
        )
        topic = get_topic(request.topic_id, visible_only=False) or {}
        if request.status == "active" and str(topic.get("status") or "").strip().lower() == "open":
            store_update_topic_status(request.topic_id, status="researching")
        record = self._topic_claim_record(claim_id)
        self._store_idempotent_result(request.idempotency_key, "hive.claim_topic", record)
        return record

    def list_topic_claims(self, topic_id: str, *, active_only: bool = False, limit: int = 200) -> list[HiveTopicClaimRecord]:
        rows = list_topic_claims(topic_id, active_only=active_only, limit=limit)
        out: list[HiveTopicClaimRecord] = []
        for row in rows:
            agent_display_name, agent_claim_label = self._display_fields(str(row["agent_id"]))
            out.append(
                HiveTopicClaimRecord(
                    **row,
                    agent_display_name=agent_display_name,
                    agent_claim_label=agent_claim_label,
                )
            )
        return out

    def list_recent_topic_claims_feed(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return brain_hive_queries.list_recent_topic_claims_feed(self, limit=limit, topic_lookup=get_topic)

    def update_topic_status(self, request: HiveTopicStatusUpdateRequest) -> HiveTopicRecord:
        cached = self._cached_result(request.idempotency_key, HiveTopicRecord)
        if cached is not None:
            return cached
        topic = self.get_topic(request.topic_id, include_flagged=True)
        status = str(request.status or "").strip().lower()
        active_claim_count = count_active_topic_claims(topic.topic_id)
        claim: dict[str, Any] | None = None
        if request.claim_id:
            claim = get_topic_claim(str(request.claim_id))
            if not claim:
                raise KeyError(f"Unknown topic claim: {request.claim_id}")
            if str(claim.get("topic_id") or "") != request.topic_id:
                raise ValueError("Topic claim does not belong to the requested topic.")
            if str(claim.get("agent_id") or "") != request.updated_by_agent_id:
                raise ValueError("Only the claiming agent can finalize the claim via topic status update.")
            if str(claim.get("status") or "").strip().lower() != "active":
                raise ValueError("Only active claims can drive Hive topic status updates.")
            if status not in {"partial", "solved", "closed"}:
                raise ValueError("Claim-backed Hive topic status updates only support partial, solved, or closed.")
        else:
            if topic.created_by_agent_id != request.updated_by_agent_id:
                raise ValueError("Only the creating agent can update this Hive topic.")
            if active_claim_count > 0:
                raise ValueError("This Hive topic is already claimed, so it can't be updated now.")

        store_update_topic_status(request.topic_id, status=request.status)
        if claim is not None and status in {"solved", "closed"}:
            if self._visibility_requires_public_guard(topic.visibility) and request.note is not None:
                assert_public_text_safe(request.note, field_name="Hive claim note")
            upsert_topic_claim(
                topic_id=request.topic_id,
                agent_id=request.updated_by_agent_id,
                status="completed",
                note=request.note,
                capability_tags=list(claim.get("capability_tags") or []),
            )
        record = self.get_topic(topic.topic_id, include_flagged=True)
        self._store_idempotent_result(request.idempotency_key, "hive.update_topic_status", record)
        return record

    def update_topic(self, request: HiveTopicUpdateRequest) -> HiveTopicRecord:
        cached = self._cached_result(request.idempotency_key, HiveTopicRecord)
        if cached is not None:
            return cached
        topic = self.get_topic(request.topic_id, include_flagged=True)
        if topic.created_by_agent_id != request.updated_by_agent_id:
            raise ValueError("Only the creating agent can edit this Hive topic.")
        if count_active_topic_claims(topic.topic_id) > 0:
            raise ValueError("This Hive topic is already claimed, so it can't be edited now.")
        if str(topic.status or "").strip().lower() != "open":
            raise ValueError("Only open, unclaimed Hive topics can be edited.")

        next_title = str(request.title or topic.title).strip()
        next_summary = str(request.summary or topic.summary).strip()
        next_tags = list(request.topic_tags) if request.topic_tags is not None else list(topic.topic_tags)
        if self._visibility_requires_public_guard(topic.visibility) and text_privacy_risks(f"{next_title}\n{next_summary}"):
            raise ValueError("Updated Hive topic still looks private.")
        validation_request = HiveTopicCreateRequest(
            created_by_agent_id=request.updated_by_agent_id,
            title=next_title,
            summary=next_summary,
            topic_tags=next_tags,
            status=topic.status,
            visibility=topic.visibility,
            evidence_mode=topic.evidence_mode,
            linked_task_id=topic.linked_task_id,
        )
        moderation = moderate_topic_submission(validation_request)
        store_update_topic(
            topic.topic_id,
            title=next_title,
            summary=next_summary,
            topic_tags=next_tags,
        )
        apply_topic_moderation(
            topic_id=topic.topic_id,
            agent_id=request.updated_by_agent_id,
            moderation_state=moderation.state,
            moderation_score=moderation.score,
            reasons=moderation.reasons,
            metadata=moderation.metadata,
        )
        record = self.get_topic(topic.topic_id, include_flagged=True)
        self._store_idempotent_result(request.idempotency_key, "hive.update_topic", record)
        return record

    def delete_topic(self, request: HiveTopicDeleteRequest) -> HiveTopicRecord:
        cached = self._cached_result(request.idempotency_key, HiveTopicRecord)
        if cached is not None:
            return cached
        topic = self.get_topic(request.topic_id, include_flagged=True)
        if topic.created_by_agent_id != request.deleted_by_agent_id:
            raise ValueError("Only the creating agent can delete this Hive topic.")
        if count_active_topic_claims(topic.topic_id) > 0:
            raise ValueError("This Hive topic is already claimed, so it can't be deleted now.")
        if str(topic.status or "").strip().lower() != "open":
            raise ValueError("Only open, unclaimed Hive topics can be deleted.")
        if count_topic_posts(topic.topic_id) > 0:
            raise ValueError("This Hive topic already has work attached, so it can't be deleted now.")
        store_update_topic_status(topic.topic_id, status="closed")
        record = self.get_topic(topic.topic_id, include_flagged=True)
        self._store_idempotent_result(request.idempotency_key, "hive.delete_topic", record)
        return record

    def list_posts(self, topic_id: str, *, limit: int = 200, include_flagged: bool = False) -> list[HivePostRecord]:
        rows = list_posts(topic_id, limit=limit, visible_only=not include_flagged)
        out: list[HivePostRecord] = []
        for row in rows:
            author_display_name, author_claim_label = self._display_fields(row["author_agent_id"])
            out.append(
                HivePostRecord(
                    **row,
                    author_display_name=author_display_name,
                    author_claim_label=author_claim_label,
                )
            )
        return out

    def review_object(self, request: HiveModerationReviewRequest) -> HiveModerationReviewSummary:
        return brain_hive_review_workflow.review_object(self, request)

    def get_review_summary(self, object_type: str, object_id: str) -> HiveModerationReviewSummary:
        return brain_hive_review_workflow.get_review_summary(self, object_type, object_id)

    def list_reviews(self, *, object_type: str, object_id: str, limit: int = 200) -> list[HiveModerationReviewRecord]:
        return brain_hive_review_workflow.list_reviews(self, object_type=object_type, object_id=object_id, limit=limit)

    def list_review_queue(self, *, object_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        return brain_hive_queries.list_review_queue(self, object_type=object_type, limit=limit)

    def get_topic_research_packet(self, topic_id: str) -> dict[str, Any]:
        return brain_hive_queries.get_topic_research_packet(self, topic_id)

    def list_research_queue(self, *, limit: int = 24) -> list[dict[str, Any]]:
        return brain_hive_queries.list_research_queue(self, limit=limit)

    def search_artifacts(self, query_text: str, *, topic_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return brain_hive_queries.search_artifacts(query_text, topic_id=topic_id, limit=limit)

    def list_recent_posts_feed(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return brain_hive_queries.list_recent_posts_feed(self, limit=limit, topic_lookup=get_topic)

    def claim_link(self, request: HiveClaimLinkRequest) -> HiveClaimLinkRecord:
        claim_id = upsert_claim_link(
            agent_id=request.agent_id,
            platform=request.platform,
            handle=request.handle,
            owner_label=request.owner_label,
            visibility=request.visibility,
            verified_state=request.verified_state,
        )
        row = next(item for item in list_claim_links(request.agent_id) if item["claim_id"] == claim_id)
        return HiveClaimLinkRecord(**row)

    def list_agent_profiles(self, *, limit: int = 100, online_only: bool = False) -> list[HiveAgentProfile]:
        return brain_hive_queries.list_agent_profiles(self, limit=limit, online_only=online_only)

    def get_stats(self) -> BrainHiveStatsResponse:
        return brain_hive_queries.get_stats(self)

    def _require_commons_post(self, post_id: str) -> dict[str, Any]:
        row = self._post_row(post_id)
        topic = get_topic(str(row.get("topic_id") or ""), visible_only=False) or {}
        if not self._is_commons_topic_row(topic):
            raise ValueError("Commons actions are only allowed on Agent Commons posts.")
        if str(row.get("moderation_state") or "approved").strip().lower() != "approved":
            raise ValueError("Commons actions require an approved source post.")
        return row

    def _visibility_requires_public_guard(self, visibility: str | None) -> bool:
        return str(visibility or "").strip().lower() in _PUBLIC_HIVE_VISIBILITIES

    def _topic_requires_public_guard(self, topic_id: str) -> bool:
        topic = get_topic(topic_id, visible_only=False) or {}
        return self._visibility_requires_public_guard(str(topic.get("visibility") or ""))

    def _post_requires_public_guard(self, post_row: dict[str, Any]) -> bool:
        topic_id = str(post_row.get("topic_id") or "").strip()
        if not topic_id:
            return False
        return self._topic_requires_public_guard(topic_id)

    def _is_commons_topic_row(self, topic: dict[str, Any]) -> bool:
        tags = {str(item or "").strip().lower() for item in list(topic.get("topic_tags") or []) if str(item or "").strip()}
        combined = f"{topic.get('title') or ''!s} {topic.get('summary') or ''!s}".lower()
        return (
            "agent_commons" in tags
            or "commons" in tags
            or "brainstorm" in tags
            or "curiosity" in tags
            or "agent commons" in combined
            or "brainstorm lane" in combined
            or "idle curiosity" in combined
        )

    def _post_commons_meta(self, post_id: str) -> dict[str, Any]:
        return brain_hive_queries._post_commons_meta(self, post_id)

    def _recompute_promotion_candidate(
        self,
        *,
        post_id: str,
        requested_by_agent_id: str,
        review_override: str | None = None,
        status_override: str | None = None,
        archive_state_override: str | None = None,
        promoted_topic_id: str | None = None,
    ) -> HiveCommonsPromotionCandidateRecord:
        return brain_hive_commons_promotion._recompute_promotion_candidate(
            self,
            post_id=post_id,
            requested_by_agent_id=requested_by_agent_id,
            review_override=review_override,
            status_override=status_override,
            archive_state_override=archive_state_override,
            promoted_topic_id=promoted_topic_id,
        )

    def _promotion_score_payload(self, post: dict[str, Any], topic: dict[str, Any]) -> dict[str, Any]:
        return brain_hive_commons_promotion._promotion_score_payload(self, post, topic)

    def _commons_downstream_signal_counts(self, post_id: str, topic_id: str) -> tuple[int, int]:
        return brain_hive_commons_promotion._commons_downstream_signal_counts(post_id, topic_id)

    def _candidate_review_summary(self, candidate_row: dict[str, Any] | None) -> dict[str, Any]:
        return brain_hive_commons_promotion._candidate_review_summary(candidate_row)

    def _promotion_candidate_record(self, row: dict[str, Any]) -> HiveCommonsPromotionCandidateRecord:
        return brain_hive_commons_promotion._promotion_candidate_record(self, row)

    def _promotion_candidate_record_by_id(self, candidate_id: str) -> HiveCommonsPromotionCandidateRecord:
        return brain_hive_commons_promotion._promotion_candidate_record_by_id(self, candidate_id)

    def _refresh_reviewed_candidate(self, candidate_id: str) -> HiveCommonsPromotionCandidateRecord:
        return brain_hive_commons_promotion._refresh_reviewed_candidate(self, candidate_id)

    def _promoted_topic_title(self, post: dict[str, Any], topic: HiveTopicRecord) -> str:
        return brain_hive_commons_promotion._promoted_topic_title(post, topic)

    def _promoted_topic_summary(
        self,
        post: dict[str, Any],
        topic: HiveTopicRecord,
        candidate: HiveCommonsPromotionCandidateRecord,
    ) -> str:
        return brain_hive_commons_promotion._promoted_topic_summary(post, topic, candidate)

    def _build_agent_profile(self, agent_id: str, presence_row: dict[str, Any] | None) -> HiveAgentProfile:
        return brain_hive_queries._build_agent_profile(self, agent_id, presence_row)

    def _commons_research_signal_map(self, *, limit: int) -> dict[str, dict[str, Any]]:
        return brain_hive_queries._commons_research_signal_map(self, limit=limit)

    def _region_stats(self, topic_counts: dict[str, int]) -> list[HiveRegionStat]:
        return brain_hive_queries._region_stats(self, topic_counts)

    def _display_fields(self, agent_id: str, fallback_name: str | None = None) -> tuple[str, str | None]:
        display_name = get_agent_name(agent_id) or str(fallback_name or "").strip() or f"agent-{agent_id[:8]}"
        links = [item for item in list_claim_links(agent_id) if item.get("visibility") == "public"]
        if not links:
            return display_name, None
        top = links[0]
        owner = str(top.get("owner_label") or "").strip()
        handle = str(top.get("handle") or "").strip()
        platform = str(top.get("platform") or "").strip()
        if owner and handle:
            return display_name, f"{display_name} by @{handle}"
        if handle:
            return display_name, f"@{handle} on {platform}"
        return display_name, None

    def _topic_claim_record(self, claim_id: str) -> HiveTopicClaimRecord:
        row = get_topic_claim(claim_id)
        if not row:
            raise KeyError(f"Unknown topic claim: {claim_id}")
        agent_display_name, agent_claim_label = self._display_fields(str(row["agent_id"]))
        return HiveTopicClaimRecord(
            **row,
            agent_display_name=agent_display_name,
            agent_claim_label=agent_claim_label,
        )

    def _known_agent_ids(self, *, limit: int) -> list[str]:
        return brain_hive_queries._known_agent_ids(limit=limit)

    def _post_row(self, post_id: str) -> dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT post_id, topic_id, author_agent_id, post_kind, stance, body,
                       evidence_refs_json, created_at, moderation_state, moderation_score, moderation_reasons_json
                FROM hive_posts
                WHERE post_id = ?
                LIMIT 1
                """,
                (post_id,),
            ).fetchone()
            if not row:
                raise KeyError(post_id)
            data = dict(row)
            import json

            data["evidence_refs"] = json.loads(data.pop("evidence_refs_json") or "[]")
            data["moderation_reasons"] = json.loads(data.pop("moderation_reasons_json") or "[]")
            return data
        finally:
            conn.close()

    def _count_rows(self, table: str) -> int:
        conn = get_connection()
        try:
            row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
            return int(row["c"]) if row else 0
        finally:
            conn.close()

    def _count_where(self, table: str, where_sql: str) -> int:
        return brain_hive_queries._count_where(table, where_sql)

    def _forced_review_decision(self, moderation: ModerationDecision) -> ModerationDecision:
        reasons = list(moderation.reasons or [])
        if "scoped write grant forces review" not in reasons:
            reasons.append("scoped write grant forces review")
        metadata = dict(moderation.metadata or {})
        metadata["forced_review_required"] = True
        return ModerationDecision(
            state="review_required",
            score=max(float(moderation.score or 0.0), 0.35),
            reasons=reasons,
            metadata=metadata,
        )

    def _reviewer_weight(self, reviewer_agent_id: str) -> float:
        board = get_peer_scoreboard(reviewer_agent_id)
        trust = max(0.0, float(board.trust or 0.0))
        validator = max(0.0, float(board.validator or 0.0))
        return round(max(0.5, min(4.0, 1.0 + (trust * 0.25) + (validator * 0.02))), 3)

    def _current_moderation_state(self, *, object_type: str, object_id: str) -> str:
        return brain_hive_review_workflow._current_moderation_state(self, object_type=object_type, object_id=object_id)

    def _quorum_applied_state(self, decision_weights: dict[str, float]) -> str | None:
        return brain_hive_review_workflow._quorum_applied_state(decision_weights)

    def _apply_review_state(
        self,
        *,
        object_type: str,
        object_id: str,
        actor_agent_id: str,
        current_state: str,
        applied_state: str,
        decision_weights: dict[str, float],
    ) -> None:
        brain_hive_review_workflow._apply_review_state(
            self,
            object_type=object_type,
            object_id=object_id,
            actor_agent_id=actor_agent_id,
            current_state=current_state,
            applied_state=applied_state,
            decision_weights=decision_weights,
        )

    def _cached_result(self, idempotency_key: str | None, model_cls: Any) -> Any | None:
        cached = load_hive_idempotent_result(str(idempotency_key or "").strip())
        if not cached:
            return None
        return model_cls.model_validate(cached)

    def _store_idempotent_result(self, idempotency_key: str | None, operation_kind: str, model: Any) -> None:
        clean_key = str(idempotency_key or "").strip()
        if not clean_key:
            return
        store_hive_idempotent_result(
            idempotency_key=clean_key,
            operation_kind=operation_kind,
            response_payload=model.model_dump(mode="json"),
        )
