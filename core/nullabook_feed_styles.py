from __future__ import annotations

from core.nullabook_feed_base_styles import NULLABOOK_FEED_BASE_STYLES
from core.nullabook_feed_overlay_styles import NULLABOOK_FEED_OVERLAY_STYLES
from core.nullabook_feed_search_styles import NULLABOOK_FEED_SEARCH_STYLES
from core.nullabook_feed_sidebar_styles import NULLABOOK_FEED_SIDEBAR_STYLES


def render_nullabook_feed_document_styles() -> str:
    return (
        NULLABOOK_FEED_BASE_STYLES
        + NULLABOOK_FEED_SIDEBAR_STYLES
        + NULLABOOK_FEED_SEARCH_STYLES
        + NULLABOOK_FEED_OVERLAY_STYLES
    )
