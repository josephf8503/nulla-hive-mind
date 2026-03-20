from __future__ import annotations

from core.task_router import classify, evaluate_word_math_request, looks_like_live_recency_lookup


def test_word_math_request_classifies_as_chat_conversation() -> None:
    result = classify(
        "I have 3 tasks. Task A takes 17 minutes, Task B takes twice Task A minus 4 minutes, Task C takes 11 minutes. What is the total? Show the steps."
    )

    assert result["task_class"] == "chat_conversation"


def test_evaluate_word_math_request_solves_task_duration_prompt() -> None:
    response = evaluate_word_math_request(
        "I have 3 tasks. Task A takes 17 minutes, Task B takes twice Task A minus 4 minutes, Task C takes 11 minutes. What is the total? Show the steps."
    )

    assert response is not None
    assert "Task B = 2 * 17 - 4 = 30." in response
    assert response.endswith("= 58.")


def test_live_recency_lookup_classifies_as_research() -> None:
    prompt = "What happened five minutes ago in global markets?"

    assert looks_like_live_recency_lookup(prompt) is True
    result = classify(prompt)
    assert result["task_class"] == "research"
