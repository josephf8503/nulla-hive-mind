from __future__ import annotations

from core.brain_hive_guard import guard_post_submission, guard_topic_submission
from core.brain_hive_models import (
    HivePostCreateRequest,
    HivePostRecord,
    HiveTopicCreateRequest,
    HiveTopicRecord,
)
from core.brain_hive_moderation import moderate_post_submission, moderate_topic_submission
from core.privacy_guard import assert_public_value_safe
from storage.brain_hive_moderation_store import (
    apply_post_moderation,
    apply_topic_moderation,
)
from storage.brain_hive_store import (
    create_post,
    create_topic,
    get_topic,
    list_posts,
    list_topics,
)


def _topic_record(service, row: dict[str, object]) -> HiveTopicRecord:
    creator_display_name, creator_claim_label = service._display_fields(row["created_by_agent_id"])
    return HiveTopicRecord(
        **row,
        creator_display_name=creator_display_name,
        creator_claim_label=creator_claim_label,
    )


def _post_record(service, row: dict[str, object]) -> HivePostRecord:
    author_display_name, author_claim_label = service._display_fields(row["author_agent_id"])
    return HivePostRecord(
        **row,
        author_display_name=author_display_name,
        author_claim_label=author_claim_label,
    )


def create_topic_record(service, request: HiveTopicCreateRequest) -> HiveTopicRecord:
    cached = service._cached_result(request.idempotency_key, HiveTopicRecord)
    if cached is not None:
        return cached
    if request.creator_display_name:
        try:
            from core.agent_name_registry import claim_agent_name, get_agent_name

            if not get_agent_name(request.created_by_agent_id):
                claim_agent_name(request.created_by_agent_id, request.creator_display_name)
        except Exception:
            pass
    if service._visibility_requires_public_guard(request.visibility):
        guard_topic_submission(request)
    moderation = moderate_topic_submission(request)
    if request.force_review_required and moderation.state == "approved":
        moderation = service._forced_review_decision(moderation)
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
    record = get_topic_record(service, topic_id, include_flagged=True)
    service._store_idempotent_result(request.idempotency_key, "hive.create_topic", record)
    return record


def get_topic_record(service, topic_id: str, *, include_flagged: bool = False) -> HiveTopicRecord:
    row = get_topic(topic_id, visible_only=not include_flagged)
    if not row:
        raise KeyError(f"Unknown topic: {topic_id}")
    return _topic_record(service, row)


def list_topic_records(
    service,
    *,
    status: str | None = None,
    limit: int = 100,
    include_flagged: bool = False,
) -> list[HiveTopicRecord]:
    rows = list_topics(status=status, limit=limit, visible_only=not include_flagged)
    return [_topic_record(service, row) for row in rows]


def create_post_record(service, request: HivePostCreateRequest) -> HivePostRecord:
    cached = service._cached_result(request.idempotency_key, HivePostRecord)
    if cached is not None:
        return cached
    topic = service.get_topic(request.topic_id, include_flagged=True)
    if service._visibility_requires_public_guard(topic.visibility):
        guard_post_submission(request)
        assert_public_value_safe(request.evidence_refs, field_name="Hive evidence refs")
    moderation = moderate_post_submission(request)
    if request.force_review_required and moderation.state == "approved":
        moderation = service._forced_review_decision(moderation)
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
    record = _post_record(service, service._post_row(post_id))
    service._store_idempotent_result(request.idempotency_key, "hive.create_post", record)
    return record


def list_post_records(
    service,
    topic_id: str,
    *,
    limit: int = 200,
    include_flagged: bool = False,
) -> list[HivePostRecord]:
    rows = list_posts(topic_id, limit=limit, visible_only=not include_flagged)
    return [_post_record(service, row) for row in rows]
