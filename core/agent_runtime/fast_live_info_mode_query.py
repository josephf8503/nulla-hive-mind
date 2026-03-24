from __future__ import annotations


def normalize_live_info_query(text: str, *, mode: str) -> str:
    clean = " ".join(str(text or "").split()).strip()
    lowered = clean.lower()
    if mode == "weather" and "forecast" not in lowered and "weather" in lowered:
        return f"{clean} forecast"
    if mode == "news" and "latest" not in lowered and "news" in lowered:
        return f"latest {clean}"
    return clean
