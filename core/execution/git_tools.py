from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .artifacts import build_command_artifact, truncate_text


def git_status_workspace(arguments: dict[str, Any], *, workspace_root: Path) -> dict[str, Any]:
    target = _git_target(arguments, workspace_root=workspace_root)
    result = _run_git(["status", "--short", "--branch"], cwd=target)
    if result["status"] == "not_git_repo":
        return {
            "ok": False,
            "status": "not_git_repo",
            "response_text": f"`{target}` is not inside a git repository.",
            "details": {"cwd": str(target), "stdout": "", "stderr": ""},
        }
    stdout = truncate_text(result["stdout"], limit=2400)
    stderr = truncate_text(result["stderr"], limit=1600)
    rendered = stdout or "Git working tree is clean."
    return {
        "ok": True,
        "status": "executed",
        "response_text": f"Git status for `{target}`:\n{rendered}",
        "details": {
            "cwd": str(target),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": int(result["returncode"]),
            "artifacts": [
                build_command_artifact(
                    command="git status --short --branch",
                    cwd=str(target),
                    returncode=int(result["returncode"]),
                    stdout=stdout,
                    stderr=stderr,
                    status="executed",
                    artifact_type="git_status",
                )
            ],
        },
    }


def git_diff_workspace(arguments: dict[str, Any], *, workspace_root: Path) -> dict[str, Any]:
    target = _git_target(arguments, workspace_root=workspace_root)
    command = ["diff"]
    if bool(arguments.get("cached", False)):
        command.append("--cached")
    path = str(arguments.get("path") or "").strip()
    if path:
        command.extend(["--", path])
    result = _run_git(command, cwd=target)
    if result["status"] == "not_git_repo":
        return {
            "ok": False,
            "status": "not_git_repo",
            "response_text": f"`{target}` is not inside a git repository.",
            "details": {"cwd": str(target), "stdout": "", "stderr": ""},
        }
    stdout = truncate_text(result["stdout"], limit=3200)
    stderr = truncate_text(result["stderr"], limit=1600)
    rendered = stdout or "No unstaged git diff is present."
    return {
        "ok": True,
        "status": "executed",
        "response_text": f"Git diff for `{target}`:\n{rendered}",
        "details": {
            "cwd": str(target),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": int(result["returncode"]),
            "artifacts": [
                build_command_artifact(
                    command="git " + " ".join(command),
                    cwd=str(target),
                    returncode=int(result["returncode"]),
                    stdout=stdout,
                    stderr=stderr,
                    status="executed",
                    artifact_type="git_diff",
                )
            ],
        },
    }


def _git_target(arguments: dict[str, Any], *, workspace_root: Path) -> Path:
    raw = str(arguments.get("cwd") or "").strip()
    if not raw:
        return workspace_root
    candidate = Path(raw)
    return (workspace_root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()


def _run_git(argv: list[str], *, cwd: Path) -> dict[str, Any]:
    probe = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        return {"status": "not_git_repo", "returncode": probe.returncode, "stdout": "", "stderr": probe.stderr}
    result = subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True, text=True)
    return {
        "status": "executed",
        "returncode": result.returncode,
        "stdout": result.stdout or "",
        "stderr": result.stderr or "",
    }
