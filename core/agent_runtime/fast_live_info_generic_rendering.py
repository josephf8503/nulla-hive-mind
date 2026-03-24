from __future__ import annotations

from typing import Any

from core.agent_runtime.fast_live_info_news_rendering import render_news_response
from core.agent_runtime.fast_live_info_quote_rendering import first_live_quote
from core.agent_runtime.fast_live_info_weather_rendering import render_weather_response


def render_live_info_response(*, query: str, notes: list[dict[str, Any]], mode: str) -> str:
    if mode == "weather":
        return render_weather_response(query=query, notes=notes)
    if mode == "news":
        return render_news_response(query=query, notes=notes)
    live_quote = first_live_quote(notes)
    if mode == "fresh_lookup" and live_quote is not None:
        return live_quote.answer_text()
    label = {
        "news": "Live news results",
        "fresh_lookup": "Live web results",
    }.get(mode, "Live web results")
    lines = [f"{label} for `{query}`:"]
    browser_used = False
    for note in list(notes or [])[:3]:
        title = str(note.get("result_title") or note.get("origin_domain") or "Source").strip()
        domain = str(note.get("origin_domain") or "").strip()
        snippet = " ".join(str(note.get("summary") or "").split()).strip()
        url = str(note.get("result_url") or "").strip()
        line = f"- {title}"
        if domain and domain.lower() not in title.lower():
            line += f" ({domain})"
        if snippet:
            line += f": {snippet[:220]}"
        if url:
            line += f" [{url}]"
        lines.append(line)
        browser_used = browser_used or bool(note.get("used_browser"))
    if browser_used:
        lines.append("Browser rendering was used for at least one source when plain fetch was too thin.")
    return "\n".join(lines)
