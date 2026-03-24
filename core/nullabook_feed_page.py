from __future__ import annotations

from core.nullabook_feed_document import render_nullabook_page_document


def render_nullabook_page_html(
    *,
    api_base: str = "",
    og_title: str = "",
    og_description: str = "",
    og_url: str = "",
    initial_tab: str = "feed",
    current_view: str = "",
    canonical_url: str = "",
) -> str:
    return render_nullabook_page_document(
        api_base=api_base,
        og_title=og_title,
        og_description=og_description,
        og_url=og_url,
        initial_tab=initial_tab,
        current_view=current_view,
        canonical_url=canonical_url,
    )
