from __future__ import annotations

import shutil
from typing import Any

from .artifacts import build_command_artifact, build_failure_artifact, truncate_text


def validation_command(intent: str, arguments: dict[str, Any]) -> str:
    override = str(arguments.get("command") or "").strip()
    if override:
        return override
    if intent == "workspace.run_tests":
        if shutil.which("pytest"):
            return "pytest -q"
        return "python3 -m pytest -q"
    if intent == "workspace.run_lint":
        if shutil.which("ruff"):
            return "ruff check ."
        return "python3 -m ruff check ."
    if intent == "workspace.run_formatter":
        apply = bool(arguments.get("apply", False))
        if shutil.which("ruff"):
            return "ruff format ." if apply else "ruff format --check ."
        return "python3 -m ruff format ." if apply else "python3 -m ruff format --check ."
    raise ValueError(f"Unsupported validation intent: {intent}")


def render_validation_result(
    intent: str,
    *,
    command: str,
    cwd: str,
    runner_result: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    status = str(runner_result.get("status") or "")
    stdout = truncate_text(str(runner_result.get("stdout") or ""), limit=2400)
    stderr = truncate_text(str(runner_result.get("stderr") or ""), limit=1600)
    returncode = int(runner_result.get("returncode", 0) or 0)
    success = bool(runner_result.get("success", False)) and status == "executed"
    command_artifact = build_command_artifact(
        command=command,
        cwd=cwd,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        status=status or "executed",
        artifact_type="validation_output",
    )
    artifacts = [command_artifact]
    failure_summary = ""
    if returncode != 0:
        combined = "\n".join(part for part in (stderr, stdout) if part).splitlines()
        for raw_line in combined:
            line = " ".join(str(raw_line or "").split()).strip()
            if line:
                failure_summary = line[:260]
                break
        if failure_summary:
            artifacts.append(
                build_failure_artifact(
                    command=command,
                    cwd=cwd,
                    returncode=returncode,
                    stdout=stdout,
                    stderr=stderr,
                    summary=failure_summary,
                )
            )
    rendered = [f"{label} in `{cwd}`:", f"$ {command}", f"- Exit code: {returncode}"]
    if stdout:
        rendered.append(f"- Stdout:\n{stdout}")
    if stderr:
        rendered.append(f"- Stderr:\n{stderr}")
    return {
        "ok": success,
        "status": status or "executed",
        "response_text": "\n".join(rendered),
        "details": {
            "command": command,
            "cwd": cwd,
            "returncode": returncode,
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "artifacts": artifacts,
            "failure_summary": failure_summary,
        },
    }
