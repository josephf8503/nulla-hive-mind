from __future__ import annotations

from core.live_quote_contract import LiveQuoteResult, validate_live_quote_payload


def first_live_quote(notes: list[dict[str, object]]) -> LiveQuoteResult | None:
    for note in list(notes or []):
        payload = note.get("live_quote")
        if not isinstance(payload, dict):
            continue
        ok, _reason = validate_live_quote_payload(payload)
        if not ok:
            continue
        try:
            return LiveQuoteResult.from_payload(payload)
        except Exception:
            continue
    return None
