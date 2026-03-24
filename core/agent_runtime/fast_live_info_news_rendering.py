from __future__ import annotations

import re
from typing import Any


def render_news_response(*, query: str, notes: list[dict[str, Any]]) -> str:
    topic = re.sub(
        r"^\s*(?:what's|what is|whats)\s+the\s+latest\s+on\s+|^\s*latest\s+(?:news\s+on|news\s+about|on|about)\s+",
        "",
        query,
        flags=re.IGNORECASE,
    ).strip(" ?.,!") or query.strip()
    lines = [f"Latest coverage on {topic}:"]
    for note in list(notes or [])[:3]:
        summary = " ".join(str(note.get("summary") or "").split()).strip()
        fallback_title = str(note.get("result_title") or "").strip()
        url = str(note.get("result_url") or "").strip()
        domain = str(note.get("origin_domain") or "").strip()
        parts = [part.strip() for part in summary.split("|") if part.strip()]
        source = parts[0] if len(parts) >= 1 else domain
        published = parts[1] if len(parts) >= 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[1]) else ""
        headline = parts[2] if len(parts) >= 3 else fallback_title or summary
        lead_parts = [item for item in (published, source) if item]
        lead = " | ".join(lead_parts)
        line = f"- {headline}"
        if lead:
            line = f"- {lead}: {headline}"
        if url:
            line += f" [{url}]"
        lines.append(line)
    return "\n".join(lines)
