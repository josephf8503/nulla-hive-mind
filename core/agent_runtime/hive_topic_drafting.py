from __future__ import annotations

import re
from typing import Any


def clean_hive_title(raw: str) -> str:
    """Basic cleanup: strip command prefixes, fix common doubled chars, capitalize."""
    title = re.sub(
        r"^(?:create\s+(?:a\s+)?(?:hive\s+)?task\s*[-:—]*\s*)",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()
    title = re.sub(r"^[-:—]+\s*", "", title).strip()
    if title and title[0].islower():
        title = title[0].upper() + title[1:]
    return title or raw


def extract_hive_topic_create_draft(agent: Any, text: str) -> dict[str, Any] | None:
    clean = " ".join(str(text or "").split()).strip()
    lowered = clean.lower()
    if not agent._looks_like_hive_topic_create_request(lowered):
        return None

    sections = {
        "title": re.search(r"\b(?:name it|title|call it|called)\b\s*[:=-]?\s*(.+?)(?=(?:\bsummary\b\s*[:=-])|(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", clean, re.IGNORECASE),
        "task": re.search(r"\btask\b\s*[:=-]\s*(.+?)(?=(?:\b(?:goal|summary)\b\s*[:=-])|(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", clean, re.IGNORECASE),
        "goal": re.search(r"\bgoal\b\s*[:=-]\s*(.+?)(?=(?:\bsummary\b\s*[:=-])|(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", clean, re.IGNORECASE),
        "summary": re.search(r"\bsummary\b\s*[:=-]\s*(.+?)(?=(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", clean, re.IGNORECASE),
        "tags": re.search(r"\b(?:topic tags?|tags?)\b\s*[:=-]\s*(.+)$", clean, re.IGNORECASE),
    }
    title = ""
    if sections["title"] is not None:
        title = str(sections["title"].group(1) or "")
    elif sections["task"] is not None:
        title = str(sections["task"].group(1) or "")
    elif ":" in clean:
        title = clean.rsplit(":", 1)[-1]
    else:
        title = re.sub(r"^.*?\bhive\b[?!.,:;-]*\s*", "", clean, flags=re.IGNORECASE)
    title = re.sub(r"^(?:name it|title|call it|called)\b\s*[:=-]?\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(
        r"^(?:(?:ok\s+)?(?:lets?|let'?s|can you|please|pls|now)\s+)*"
        r"(?:create|make|start|open|add)\s+"
        r"(?:(?:a|the|new|hive|brain hive|this)\s+)*"
        r"(?:task|topic|thread)\s*"
        r"(?:(?:on|in|for|to|at)\s+(?:(?:the\s+)?(?:hive|hive mind|brain hive))\s*)?",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip().lstrip("-–—:;/.,!? ")
    if not title:
        for prefix in ("create task", "create new task", "create hive task", "new task", "add task"):
            if clean.lower().startswith(prefix):
                title = clean[len(prefix):].strip().lstrip("-:–/")
                break
    if re.match(r"^.{0,30}---+", title):
        title = re.sub(r"^.{0,30}---+\s*", "", title).strip()
    if " - " in title and len(title.split(" - ", 1)[1].strip()) > 15:
        title = title.split(" - ", 1)[1].strip()
    title = re.sub(r"^(?:task|goal|summary)\s*[:=-]\s*", "", title, flags=re.IGNORECASE).strip()
    title = agent._strip_wrapping_quotes(" ".join(title.split()).strip().strip("."))

    summary = ""
    if sections["summary"] is not None:
        summary = agent._strip_wrapping_quotes(" ".join(str(sections["summary"].group(1) or "").split()).strip().strip("."))
    elif sections["goal"] is not None:
        summary = agent._strip_wrapping_quotes(" ".join(str(sections["goal"].group(1) or "").split()).strip().strip("."))
    if not summary and title:
        summary = title

    topic_tags: list[str] = []
    if sections["tags"] is not None:
        raw_tags = str(sections["tags"].group(1) or "")
        topic_tags = [
            normalized
            for normalized in (
                agent._normalize_hive_topic_tag(item)
                for item in re.split(r"[,;|/]+", raw_tags)
            )
            if normalized
        ][:8]
    if not topic_tags and title:
        topic_tags = agent._infer_hive_topic_tags(title)

    return {
        "title": title[:180],
        "summary": summary[:4000],
        "topic_tags": topic_tags[:8],
        "auto_start_research": agent._wants_hive_create_auto_start(clean),
    }


def extract_original_hive_topic_create_draft(agent: Any, text: str) -> dict[str, Any] | None:
    raw = str(text or "").strip()
    compact = " ".join(raw.split()).strip()
    if not agent._looks_like_hive_topic_create_request(compact.lower()):
        return None
    sections = {
        "title": re.search(r"\b(?:name it|title|call it|called)\b\s*[:=-]?\s*(.+?)(?=(?:\bsummary\b\s*[:=-])|(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", compact, re.IGNORECASE),
        "task": re.search(r"\btask\b\s*[:=-]\s*(.+?)(?=(?:\b(?:goal|summary)\b\s*[:=-])|(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", compact, re.IGNORECASE),
        "goal": re.search(r"\bgoal\b\s*[:=-]\s*(.+?)(?=(?:\bsummary\b\s*[:=-])|(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", compact, re.IGNORECASE),
        "summary": re.search(r"\bsummary\b\s*[:=-]\s*(.+?)(?=(?:\b(?:topic tags?|tags?)\b\s*[:=-])|$)", compact, re.IGNORECASE),
        "tags": re.search(r"\b(?:topic tags?|tags?)\b\s*[:=-]\s*(.+)$", compact, re.IGNORECASE),
    }
    title = ""
    if sections["title"] is not None:
        title = str(sections["title"].group(1) or "")
    elif sections["task"] is not None:
        title = str(sections["task"].group(1) or "")
    elif ":" in compact:
        title = compact.rsplit(":", 1)[-1]
    title = re.sub(r"^(?:task|title|name it|call it|called)\s*[:=-]\s*", "", title, flags=re.IGNORECASE).strip()
    title = agent._strip_wrapping_quotes(" ".join(title.split()).strip().strip("."))
    summary = ""
    if sections["summary"] is not None:
        summary = agent._strip_wrapping_quotes(" ".join(str(sections["summary"].group(1) or "").split()).strip().strip("."))
    elif sections["goal"] is not None:
        summary = agent._strip_wrapping_quotes(" ".join(str(sections["goal"].group(1) or "").split()).strip().strip("."))
    if not summary and title:
        summary = title
    topic_tags: list[str] = []
    if sections["tags"] is not None:
        raw_tags = str(sections["tags"].group(1) or "")
        topic_tags = [
            normalized
            for normalized in (
                agent._normalize_hive_topic_tag(item)
                for item in re.split(r"[,;|/]+", raw_tags)
            )
            if normalized
        ][:8]
    if not topic_tags and title:
        topic_tags = agent._infer_hive_topic_tags(title)
    if not title:
        return None
    return {
        "title": title[:180],
        "summary": summary[:4000],
        "topic_tags": topic_tags[:8],
        "auto_start_research": agent._wants_hive_create_auto_start(compact),
    }


def check_hive_duplicate(agent: Any, title: str, summary: str) -> dict[str, Any] | None:
    """Check if a similar hive topic exists within the last 3 days."""
    try:
        from datetime import datetime, timedelta, timezone

        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
        topics = agent.public_hive_bridge.list_public_topics(limit=50)
        title_tokens = set(title.lower().split())
        summary_tokens = set(summary.lower().split()[:30])
        all_tokens = title_tokens | summary_tokens
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "to",
            "for",
            "on",
            "in",
            "of",
            "and",
            "or",
            "how",
            "what",
            "why",
            "create",
            "task",
            "new",
            "hive",
        }
        meaningful = all_tokens - stop_words
        if not meaningful:
            return None
        for topic in topics:
            topic_date = str(topic.get("updated_at") or topic.get("created_at") or "")
            if topic_date and topic_date < cutoff:
                continue
            t_title = str(topic.get("title") or "").lower()
            t_summary = str(topic.get("summary") or "").lower()
            t_tokens = set(t_title.split()) | set(t_summary.split()[:30])
            overlap = meaningful & t_tokens
            if len(overlap) >= max(2, len(meaningful) * 0.5):
                return topic
    except Exception:
        pass
    return None


def build_hive_create_pending_variants(
    agent: Any,
    *,
    raw_input: str,
    draft: dict[str, Any],
    task_id: str,
) -> dict[str, Any]:
    improved_title = agent._clean_hive_title(str(draft.get("title") or "").strip())
    improved_summary = str(draft.get("summary") or "").strip() or improved_title
    improved_copy = agent._prepare_public_hive_topic_copy(
        raw_input=raw_input,
        title=improved_title,
        summary=improved_summary,
        mode="improved",
    )
    if not bool(improved_copy.get("ok")):
        return improved_copy

    improved_variant = agent._normalize_hive_create_variant(
        title=str(improved_copy.get("title") or improved_title).strip() or improved_title,
        summary=str(improved_copy.get("summary") or improved_summary).strip() or improved_summary,
        topic_tags=[
            str(item).strip()
            for item in list(draft.get("topic_tags") or [])
            if str(item).strip()
        ][:8],
        auto_start_research=bool(draft.get("auto_start_research")),
        preview_note=str(improved_copy.get("preview_note") or ""),
    )

    original_variant: dict[str, Any] | None = None
    original_blocked_reason = ""
    original_draft = agent._extract_original_hive_topic_create_draft(raw_input)
    if original_draft is not None:
        same_title = str(original_draft.get("title") or "").strip() == str(improved_variant.get("title") or "").strip()
        same_summary = str(original_draft.get("summary") or "").strip() == str(improved_variant.get("summary") or "").strip()
        if not (same_title and same_summary):
            original_copy = agent._prepare_public_hive_topic_copy(
                raw_input=raw_input,
                title=str(original_draft.get("title") or "").strip(),
                summary=str(original_draft.get("summary") or "").strip()
                or str(original_draft.get("title") or "").strip(),
                mode="original",
            )
            if bool(original_copy.get("ok")):
                original_variant = agent._normalize_hive_create_variant(
                    title=str(original_copy.get("title") or "").strip(),
                    summary=str(original_copy.get("summary") or "").strip(),
                    topic_tags=[
                        str(item).strip()
                        for item in list(original_draft.get("topic_tags") or [])
                        if str(item).strip()
                    ][:8],
                    auto_start_research=bool(original_draft.get("auto_start_research")),
                    preview_note=str(original_copy.get("preview_note") or ""),
                )
            else:
                original_blocked_reason = str(original_copy.get("response") or "").strip()

    pending = {
        "title": str(improved_variant.get("title") or "").strip(),
        "summary": str(improved_variant.get("summary") or "").strip(),
        "topic_tags": list(improved_variant.get("topic_tags") or []),
        "task_id": str(task_id or "").strip(),
        "auto_start_research": bool(improved_variant.get("auto_start_research")),
        "default_variant": "improved",
        "variants": {"improved": improved_variant},
        "original_blocked_reason": original_blocked_reason,
    }
    if original_variant is not None:
        pending["variants"]["original"] = original_variant
    return {"ok": True, "pending": pending}


def normalize_hive_create_variant(
    agent: Any,
    *,
    title: str,
    summary: str,
    topic_tags: list[str],
    auto_start_research: bool,
    preview_note: str = "",
) -> dict[str, Any]:
    resolved_title = str(title or "").strip()[:180]
    resolved_summary = str(summary or "").strip()[:4000] or resolved_title
    resolved_tags = [
        str(item).strip()
        for item in list(topic_tags or [])[:8]
        if str(item).strip()
    ]
    if not resolved_tags and resolved_title:
        resolved_tags = agent._infer_hive_topic_tags(resolved_title)
    return {
        "title": resolved_title,
        "summary": resolved_summary,
        "topic_tags": resolved_tags[:8],
        "auto_start_research": bool(auto_start_research),
        "preview_note": str(preview_note or "").strip(),
    }


def wants_hive_create_auto_start(text: str) -> bool:
    compact = " ".join(str(text or "").split()).strip().lower()
    if not compact:
        return False
    return any(
        phrase in compact
        for phrase in (
            "start working on it",
            "start working on this",
            "start on it",
            "start on this",
            "start researching",
            "start research",
            "work on it",
            "work on this",
            "research it",
            "research this",
            "go ahead and start",
            "create it and start",
            "post it and start",
            "start there",
        )
    )


def looks_like_hive_topic_create_request(agent: Any, lowered: str) -> bool:
    text = str(lowered or "").strip().lower()
    if not text:
        return False
    if agent._looks_like_hive_topic_drafting_request(text):
        return False
    has_create = bool(
        re.search(r"\b(?:create|make|start)\b", text)
        or "new task" in text
        or "new topic" in text
        or "open a" in text
        or "open new" in text
    )
    has_target = any(marker in text for marker in ("task", "topic", "thread"))
    if not (has_create and has_target):
        return False
    if "hive" not in text and "topic" not in text and "create" not in text:
        return False
    return not any(
        marker in text
        for marker in (
            "claim task",
            "pull hive tasks",
            "open hive tasks",
            "open tasks",
            "show me",
            "what do we have",
            "any tasks",
            "list tasks",
            "ignore hive",
            "research complete",
            "status",
        )
    )


def looks_like_hive_topic_drafting_request(_: Any, lowered: str) -> bool:
    text = " ".join(str(lowered or "").split()).strip().lower()
    if not text:
        return False
    strong_drafting_markers = (
        "give me the perfect script",
        "create extensive script first",
        "write the script first",
        "draft it first",
        "before i push",
        "before i post",
        "before i send",
        "then i decide if i want to push",
        "then i check and decide",
        "if i want to push that to the hive",
        "if i want to send that to the hive",
        "improve the task first",
        "improve this task first",
    )
    if any(marker in text for marker in strong_drafting_markers):
        return True
    if any(token in text for token in ("script", "prompt", "outline", "template")):
        explicit_send_markers = (
            "create hive mind task",
            "create hive task",
            "create new hive task",
            "create task in hive",
            "add this to the hive",
            "post this to the hive",
            "send this to the hive",
            "push this to the hive",
            "put this on the hive",
        )
        if not any(marker in text for marker in explicit_send_markers):
            if any(
                marker in text
                for marker in (
                    "give me",
                    "write me",
                    "draft",
                    "improve",
                    "polish",
                    "rewrite",
                    "fix typos",
                    "help me",
                )
            ):
                return True
    return False
