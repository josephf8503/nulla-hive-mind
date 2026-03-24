from __future__ import annotations

import re
from typing import Any


def render_weather_response(*, query: str, notes: list[dict[str, Any]]) -> str:
    location = re.sub(
        r"\b(?:what\s+is\s+(?:the\s+)?|how\s+is\s+(?:the\s+)?|weather\s+(?:like\s+)?(?:in|for|at)\s+|"
        r"weather\s+in\s+|now\??|right\s+now\??|today\??|current(?:ly)?)\b",
        "",
        query,
        flags=re.IGNORECASE,
    )
    location = re.sub(r"\bforecast\b", " ", location, flags=re.IGNORECASE)
    location = " ".join(location.split()).strip(" ?.,!") or "your location"
    primary = dict(next((note for note in list(notes or []) if isinstance(note, dict)), {}))
    summary = " ".join(str(primary.get("summary") or "").split()).strip()
    url = str(primary.get("result_url") or "").strip()
    domain = str(primary.get("origin_domain") or "").strip()
    if summary:
        if location.lower() in summary.lower():
            line = summary
        else:
            line = f"Weather in {location}: {summary}"
    else:
        line = f"I searched for weather in {location} but couldn't extract conditions from the results."
    if url:
        line += f" Source: [{domain or 'source'}]({url})."
    return line
