from __future__ import annotations


class ProceedIntentSupportMixin:
    _PROCEED_PATTERNS: frozenset[str] = frozenset({
        "proceed", "carry on", "continue", "do it", "do all", "go ahead",
        "start working", "yes", "yes proceed", "yes do it", "ok do it",
        "ok proceed", "ok go ahead", "deliver it", "submit it", "just do it",
        "yes pls", "yes please", "all good carry on", "proceed with next steps",
        "proceed with that", "all good", "no proceed",
    })

    def _looks_like_explicit_resume_request(self, text: str) -> bool:
        normalized = self._resume_request_key(text)
        return normalized in {
            "continue",
            "resume",
            "retry",
            "try again",
            "continue please",
            "resume please",
            "keep going",
            "go on",
            "pick up where you left off",
        }

    def _looks_like_resume_request(self, text: str) -> bool:
        return self._looks_like_explicit_resume_request(text) or self._is_proceed_message(text)

    def _resume_request_key(self, text: str) -> str:
        return " ".join(str(text or "").strip().lower().split())

    def _is_proceed_message(self, text: str) -> bool:
        compact = self._resume_request_key(text).strip(" \t\n\r?!.,")
        if compact in self._PROCEED_PATTERNS:
            return True
        padded = f" {compact} "
        if any(f" {phrase} " in padded for phrase in (
            "proceed",
            "carry on",
            "continue",
            "do it",
            "do all",
            "go ahead",
            "start working",
            "just do it",
        )):
            return True
        return bool(any(marker in compact for marker in (
            "do research",
            "start research",
            "run research",
            "deliver to hive",
            "deliver to the hive",
            "deliver it to hive",
            "deliver it to the hive",
            "submit to hive",
            "submit to the hive",
            "post to hive",
            "research and deliver",
            "research it",
            "do it properly",
        )))
