from __future__ import annotations

import re
from typing import Any

from core.user_preferences import load_preferences


def maybe_attach_workflow(
    agent: Any,
    response: str,
    workflow_summary: str,
    *,
    source_context: dict[str, object] | None = None,
) -> str:
    prefs = load_preferences()
    if not getattr(prefs, "show_workflow", False):
        return str(response or "")
    summary = str(workflow_summary or "").strip()
    if not summary:
        return str(response or "")
    if not should_show_workflow_summary(
        response=response,
        workflow_summary=summary,
        source_context=source_context,
    ):
        return str(response or "")
    return f"Workflow:\n{summary}\n\n{str(response or '').strip()}".strip()


def should_attach_hive_footer(
    agent: Any,
    result: Any,
    *,
    source_context: dict[str, object] | None,
) -> bool:
    surface = str((source_context or {}).get("surface", "") or "").strip().lower()
    if surface not in {"channel", "openclaw", "api"}:
        return False
    if result.response_class == agent.ResponseClass.TASK_SELECTION_CLARIFICATION:
        return True
    if result.response_class != agent.ResponseClass.APPROVAL_REQUIRED:
        return False
    lowered = str(result.text or "").strip().lower()
    if "ready to post this to the public hive" in lowered or "confirm? (yes / no)" in lowered:
        return False
    return not ("reply with:" in lowered and "approve " in lowered)


def fast_path_response_class(agent: Any, *, reason: str, response: str) -> Any:
    response_class = agent.ResponseClass
    if reason in {"smalltalk_fast_path", "startup_sequence_fast_path"}:
        return response_class.SMALLTALK
    if reason in {
        "date_time_fast_path",
        "direct_math_fast_path",
        "ui_command_fast_path",
        "credit_status_fast_path",
        "memory_command",
        "user_preference_command",
        "live_info_fast_path",
        "capability_truth_query",
        "builder_capability_gap",
        "builder_controller_direct_response",
    }:
        return response_class.UTILITY_ANSWER
    if reason == "help_fast_path":
        return response_class.TASK_SELECTION_CLARIFICATION
    if reason == "evaluative_conversation_fast_path":
        return response_class.GENERIC_CONVERSATION
    if reason == "runtime_resume_missing":
        return response_class.SYSTEM_ERROR_USER_SAFE
    if reason == "hive_activity_command":
        return classify_hive_text_response(agent, response)
    if reason == "hive_research_followup":
        lowered = str(response or "").lower()
        if lowered.startswith("started hive research on") or lowered.startswith("autonomous research on"):
            return response_class.TASK_STARTED
        if lowered.startswith("research follow-up:") or lowered.startswith("research result:"):
            return response_class.RESEARCH_PROGRESS
        if "multiple real hive tasks open" in lowered or "pick one by name" in lowered:
            return response_class.TASK_SELECTION_CLARIFICATION
        if "couldn't map that follow-up" in lowered or "couldn't find an open hive task" in lowered:
            return response_class.TASK_SELECTION_CLARIFICATION
        return response_class.TASK_FAILED_USER_SAFE
    if reason == "hive_status_followup":
        return response_class.TASK_STATUS
    return response_class.GENERIC_CONVERSATION


def classify_hive_text_response(agent: Any, response: str) -> Any:
    lowered = str(response or "").strip().lower()
    response_class = agent.ResponseClass
    if (
        lowered.startswith("hive watcher is not configured")
        or lowered.startswith("i couldn't reach the hive watcher")
        or lowered.startswith("i couldn't reach hive")
        or lowered.startswith("public hive is not enabled")
    ):
        return response_class.TASK_FAILED_USER_SAFE
    if lowered.startswith("available hive tasks right now"):
        return response_class.TASK_LIST
    if lowered.startswith("i couldn't reach the live hive watcher just now, but these are the real hive tasks i already had in session"):
        return response_class.TASK_LIST
    if lowered.startswith("i couldn't reach the live hive watcher, but i can still pull public hive tasks"):
        return response_class.TASK_LIST
    if lowered.startswith("live hive watcher is not configured here, but i can still pull public hive tasks"):
        return response_class.TASK_LIST
    if lowered.startswith("online now:"):
        return response_class.TASK_LIST
    if "pick one by name" in lowered or "point at the task name" in lowered:
        return response_class.TASK_SELECTION_CLARIFICATION
    if lowered.startswith("no open hive tasks"):
        return response_class.TASK_STATUS
    return response_class.TASK_STATUS


def action_response_class(
    agent: Any,
    *,
    reason: str,
    success: bool,
    task_outcome: str | None,
    response: str,
) -> Any:
    lowered = str(response or "").lower()
    response_class = agent.ResponseClass
    if task_outcome == "pending_approval":
        return response_class.APPROVAL_REQUIRED
    if not success:
        return response_class.TASK_FAILED_USER_SAFE
    if "started hive research on" in lowered or lowered.startswith("autonomous research on"):
        return response_class.TASK_STARTED
    if reason.startswith("model_tool_intent_"):
        return response_class.RESEARCH_PROGRESS
    if reason.startswith("hive_topic_create_"):
        return response_class.TASK_STATUS
    return response_class.GENERIC_CONVERSATION


def grounded_response_class(agent: Any, *, gate: Any) -> Any:
    if bool(getattr(gate, "requires_user_approval", False)) or str(getattr(gate, "mode", "") or "").lower() in {
        "approval_required",
        "tool_preview",
    }:
        return agent.ResponseClass.APPROVAL_REQUIRED
    return agent.ResponseClass.GENERIC_CONVERSATION


def should_show_workflow_summary(
    *,
    response: str,
    workflow_summary: str,
    source_context: dict[str, object] | None,
) -> bool:
    surface = str((source_context or {}).get("surface", "") or "").strip().lower()
    response_text = str(response or "").strip()
    if surface not in {"channel", "openclaw", "api"}:
        return True
    if "recognized operator action" in workflow_summary:
        return True
    if "classified task as `research`" in workflow_summary:
        return True
    if "classified task as `integration_orchestration`" in workflow_summary:
        return True
    if "classified task as `system_design`" in workflow_summary:
        return True
    if "classified task as `debugging`" in workflow_summary:
        return True
    if "classified task as `code_" in workflow_summary:
        return True
    if "curiosity/research lane: `executed`" in workflow_summary:
        return True
    if "execution posture: `tool_" in workflow_summary:
        return True
    return len(response_text) >= 280


def tool_intent_direct_message(structured_output: Any) -> str | None:
    if not isinstance(structured_output, dict):
        return None
    intent = str(structured_output.get("intent") or "").strip().lower()
    if intent not in {"respond.direct", "none", "no_tool"}:
        return None
    arguments = structured_output.get("arguments") or {}
    if not isinstance(arguments, dict):
        return None
    message = str(arguments.get("message") or arguments.get("response") or "").strip()
    return message or None


def append_tool_result_to_source_context(
    agent: Any,
    source_context: dict[str, Any] | None,
    *,
    execution: Any,
    tool_name: str,
) -> dict[str, Any]:
    updated = dict(source_context or {})
    history = list(updated.get("conversation_history") or [])
    observation_message = tool_history_observation_message(
        agent,
        execution=execution,
        tool_name=tool_name,
    )
    if history and history[-1] == observation_message:
        updated["conversation_history"] = history[-12:]
        return updated
    history.append(observation_message)
    updated["conversation_history"] = history[-12:]
    return updated


def normalize_tool_history_message(agent: Any, item: dict[str, Any]) -> dict[str, str]:
    role = str(item.get("role") or "").strip().lower()
    content = str(item.get("content") or "").strip()
    if role != "assistant" or not content.startswith("Real tool result from `"):
        return {"role": role, "content": content}
    match = re.match(r"^Real tool result from `([^`]+)`:\s*(.*)$", content, re.DOTALL)
    if not match:
        return {"role": role, "content": content}
    tool_name = str(match.group(1) or "").strip() or "tool"
    response_text = str(match.group(2) or "").strip()
    observation = {
        "schema": "tool_observation_v1",
        "intent": tool_name,
        "tool_surface": tool_surface_for_history(tool_name),
        "ok": True,
        "status": "executed",
        "response_preview": response_text[:1800] if response_text else "No tool output returned.",
    }
    return {
        "role": "user",
        "content": agent._tool_history_observation_prompt(observation),
    }


def tool_surface_for_history(tool_name: str) -> str:
    lowered = str(tool_name or "").strip().lower()
    if lowered.startswith("web.") or lowered.startswith("browser."):
        return "web"
    if lowered.startswith("workspace."):
        return "workspace"
    if lowered.startswith("sandbox."):
        return "sandbox"
    if lowered.startswith("operator."):
        return "local_operator"
    if lowered.startswith("hive."):
        return "hive"
    return "runtime_tool"


def tool_history_observation_payload(
    *,
    execution: Any,
    tool_name: str,
) -> dict[str, Any]:
    details = dict(getattr(execution, "details", {}) or {})
    observation = details.get("observation")
    if isinstance(observation, dict) and observation:
        payload = dict(observation)
    else:
        response_text = str(getattr(execution, "response_text", "") or "").strip()
        payload = {
            "schema": "tool_observation_v1",
            "intent": str(tool_name or getattr(execution, "tool_name", "") or "tool").strip() or "tool",
            "tool_surface": tool_surface_for_history(str(tool_name or getattr(execution, "tool_name", "") or "tool")),
            "ok": bool(getattr(execution, "ok", False)),
            "status": str(getattr(execution, "status", "") or "executed").strip() or "executed",
            "response_preview": response_text[:1800] if response_text else "No tool output returned.",
        }
    payload.setdefault("mode", str(getattr(execution, "mode", "") or "").strip())
    if not payload.get("response_preview"):
        response_text = str(getattr(execution, "response_text", "") or "").strip()
        if response_text:
            payload["response_preview"] = response_text[:1800]
    return payload


def tool_history_observation_message(
    agent: Any,
    *,
    execution: Any,
    tool_name: str,
) -> dict[str, str]:
    observation = tool_history_observation_payload(
        execution=execution,
        tool_name=tool_name,
    )
    return {
        "role": "user",
        "content": agent._tool_history_observation_prompt(observation),
    }


def append_footer(response: str, *, prefix: str, footer: str) -> str:
    clean_response = str(response or "").strip()
    clean_footer = str(footer or "").strip()
    if not clean_footer:
        return clean_response
    if clean_footer.lower().startswith(f"{str(prefix or '').strip().lower()}:"):
        return f"{clean_response}\n\n{clean_footer}".strip()
    return f"{clean_response}\n\n{prefix}:\n{clean_footer}".strip()
