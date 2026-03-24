from __future__ import annotations

from typing import Any

from core.task_router import (
    looks_like_explicit_lookup_request,
    looks_like_live_recency_lookup,
    looks_like_public_entity_lookup_request,
)

from .fast_live_info_mode_markers import (
    _CLOCK_AND_DATE_MARKERS,
    _FRESH_LOOKUP_MARKERS,
    _LATEST_DOMAIN_MARKERS,
    _LIVE_LOOKUP_HINT_MARKERS,
    _NEWS_MARKERS,
    _WEATHER_MARKERS,
)


def live_info_mode(agent: Any, text: str, *, interpretation: Any) -> str:
    lowered = " ".join(str(text or "").strip().lower().split())
    if not lowered:
        return ""
    if agent._looks_like_builder_request(lowered):
        return ""
    if any(marker in lowered for marker in _CLOCK_AND_DATE_MARKERS):
        return ""

    lowered_padded = f" {lowered} "
    if any(marker in lowered_padded for marker in _WEATHER_MARKERS):
        return "weather"
    if any(marker in lowered for marker in _NEWS_MARKERS):
        return "news"
    if looks_like_live_recency_lookup(lowered):
        return "fresh_lookup"
    if looks_like_explicit_lookup_request(lowered) or looks_like_public_entity_lookup_request(lowered):
        return "fresh_lookup"
    if any(marker in lowered for marker in _LIVE_LOOKUP_HINT_MARKERS):
        return "fresh_lookup"
    if any(marker in lowered for marker in _FRESH_LOOKUP_MARKERS):
        return "fresh_lookup"
    if any(marker in lowered for marker in ("latest", "newest", "recent", "just released")) and any(
        marker in lowered for marker in _LATEST_DOMAIN_MARKERS
    ):
        return "fresh_lookup"

    hints = {str(item).lower() for item in getattr(interpretation, "topic_hints", []) or []}
    if "weather" in hints:
        return "weather"
    if "news" in hints:
        return "news"
    if "web" in hints and agent._wants_fresh_info(lowered, interpretation=interpretation):
        return "fresh_lookup"
    return ""
