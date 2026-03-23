from __future__ import annotations

from core.memory.entries import add_memory_fact
from core.memory.files import (
    conversation_log_path,
    memory_entries_path,
    memory_path,
    operator_dense_profile_path,
    session_summaries_path,
    user_heuristics_path,
)
from core.memory.learning import (
    load_operator_dense_profile,
    normalized_history,
    refresh_operator_dense_profile,
    update_session_summary,
)


def setup_function() -> None:
    for path in (
        memory_path(),
        conversation_log_path(),
        memory_entries_path(),
        session_summaries_path(),
        user_heuristics_path(),
        operator_dense_profile_path(),
    ):
        if path.exists():
            path.unlink()


def test_normalized_history_drops_invalid_items() -> None:
    history = normalized_history(
        [
            {"role": "user", "content": " keep this concise "},
            {"role": "assistant", "content": " ok "},
            {"role": "tool", "content": "ignored"},
            {"role": "user", "content": ""},
            "bad",
        ]
    )

    assert history == [
        {"role": "user", "content": "keep this concise"},
        {"role": "assistant", "content": "ok"},
    ]


def test_refresh_operator_dense_profile_reflects_memory_and_session_summary() -> None:
    add_memory_fact("Operator prefers concise answers.", session_id="dense-a")
    conversation_log_path().write_text(
        '{"session_id":"dense-a","user":"build telegram bot","assistant":"ok"}\n'
        '{"session_id":"dense-a","user":"keep answers concise","assistant":"stored"}\n',
        encoding="utf-8",
    )

    update_session_summary(
        session_id="dense-a",
        user_input="keep answers concise",
        assistant_output="stored",
    )

    profile = refresh_operator_dense_profile(session_id="dense-a")

    assert profile["share_scope"] == "local_only"
    assert "LOCAL_ONLY" in list(profile.get("policy_tags") or [])
    assert load_operator_dense_profile()["last_session_id"] == "dense-a"
    assert "Facts:" in str(profile.get("dense_summary") or "")
