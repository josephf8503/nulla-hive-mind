from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .artifacts import build_file_diff_artifact, record_workspace_mutation

_SYMBOL_DEFINITION_TEMPLATES = (
    ("function_definition", r"^\s*def\s+{symbol}\b"),
    ("class_definition", r"^\s*class\s+{symbol}\b"),
    ("assignment", r"^\s*{symbol}\s*="),
    ("javascript_function", r"^\s*(?:export\s+)?function\s+{symbol}\b"),
    ("javascript_const", r"^\s*(?:export\s+)?(?:const|let|var)\s+{symbol}\b"),
)
_PATCH_TARGET_RE = re.compile(r"^(?:\+\+\+|---)\s+(?P<path>.+)$", re.MULTILINE)


def resolve_workspace_path(raw_path: str | None, *, workspace_root: Path) -> Path:
    raw = str(raw_path or "").strip()
    if not raw:
        return workspace_root
    candidate = Path(raw)
    candidate = (workspace_root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if candidate != workspace_root and workspace_root not in candidate.parents:
        raise ValueError("Path escapes the active workspace.")
    return candidate


def relative_path(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root)) or "."
    except Exception:
        return str(path)


def is_probably_text(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:4096]
    except Exception:
        return False
    return b"\x00" not in sample


def iter_workspace_files(
    target: Path,
    *,
    workspace_root: Path,
    glob_pattern: str,
    limit: int,
) -> list[Path]:
    if target.is_file():
        return [target]
    matches: list[Path] = []
    for path in sorted(target.rglob("*")):
        if len(matches) >= limit:
            break
        if not path.is_file():
            continue
        relative = relative_path(path, workspace_root=workspace_root)
        if any(part.startswith(".") for part in Path(relative).parts):
            continue
        if glob_pattern not in {"", "*", "**", "**/*"} and not fnmatch.fnmatch(relative, glob_pattern) and not fnmatch.fnmatch(path.name, glob_pattern):
            continue
        matches.append(path)
    return matches


def list_tree_workspace(arguments: dict[str, Any], *, workspace_root: Path) -> dict[str, Any]:
    target = resolve_workspace_path(arguments.get("path"), workspace_root=workspace_root)
    limit = max(1, min(int(arguments.get("limit") or 60), 240))
    rows: list[dict[str, Any]] = []
    if target.is_file():
        rows.append({"path": relative_path(target, workspace_root=workspace_root), "kind": "file"})
    else:
        root_relative = relative_path(target, workspace_root=workspace_root)
        for path in sorted(target.rglob("*")):
            if len(rows) >= limit:
                break
            rel = relative_path(path, workspace_root=workspace_root)
            if any(part.startswith(".") for part in Path(rel).parts):
                continue
            rows.append({"path": rel, "kind": "directory" if path.is_dir() else "file"})
        if root_relative == "." and not rows:
            rows = []
    if not rows:
        return {
            "ok": True,
            "status": "no_results",
            "response_text": f"No files or directories matched inside `{relative_path(target, workspace_root=workspace_root)}`.",
            "details": {"path": relative_path(target, workspace_root=workspace_root), "entries": [], "truncated": False},
        }
    rendered = [f"Workspace tree under `{relative_path(target, workspace_root=workspace_root)}`:"]
    for row in rows:
        marker = "/" if row["kind"] == "directory" else ""
        rendered.append(f"- {row['path']}{marker}")
    return {
        "ok": True,
        "status": "executed",
        "response_text": "\n".join(rendered),
        "details": {
            "path": relative_path(target, workspace_root=workspace_root),
            "entries": rows,
            "truncated": len(rows) >= limit,
        },
    }


def symbol_search_workspace(arguments: dict[str, Any], *, workspace_root: Path) -> dict[str, Any]:
    symbol = str(arguments.get("symbol") or arguments.get("query") or "").strip()
    if not symbol:
        return {
            "ok": False,
            "status": "invalid_arguments",
            "response_text": "workspace.symbol_search needs a non-empty `symbol`.",
            "details": {"symbol": "", "matches": []},
        }
    target = resolve_workspace_path(arguments.get("path"), workspace_root=workspace_root)
    glob_pattern = str(arguments.get("glob") or "**/*").strip() or "**/*"
    limit = max(1, min(int(arguments.get("limit") or 20), 100))
    escaped = re.escape(symbol)
    patterns = [(kind, re.compile(template.format(symbol=escaped))) for kind, template in _SYMBOL_DEFINITION_TEMPLATES]
    matches: list[dict[str, Any]] = []
    for path in iter_workspace_files(target, workspace_root=workspace_root, glob_pattern=glob_pattern, limit=500):
        if not is_probably_text(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for index, line in enumerate(lines, start=1):
            kind = ""
            for candidate_kind, pattern in patterns:
                if pattern.search(line):
                    kind = candidate_kind
                    break
            if not kind and symbol not in line:
                continue
            if not kind:
                kind = "reference"
            rel = relative_path(path, workspace_root=workspace_root)
            matches.append({"path": rel, "line": index, "kind": kind, "snippet": line.strip()[:220]})
            if len(matches) >= limit:
                break
        if len(matches) >= limit:
            break
    if not matches:
        return {
            "ok": True,
            "status": "no_results",
            "response_text": f'No symbol matches for "{symbol}" were found in the workspace.',
            "details": {"symbol": symbol, "matches": []},
        }
    rendered = [f'Symbol matches for "{symbol}":']
    for row in matches:
        rendered.append(f"- {row['path']}:{row['line']} [{row['kind']}] {row['snippet']}")
    return {
        "ok": True,
        "status": "executed",
        "response_text": "\n".join(rendered),
        "details": {"symbol": symbol, "matches": matches, "match_count": len(matches)},
    }


def apply_unified_diff_workspace(
    arguments: dict[str, Any],
    *,
    workspace_root: Path,
    session_id: str | None,
) -> dict[str, Any]:
    patch_text = str(arguments.get("patch") or arguments.get("diff") or "").strip()
    if not patch_text:
        return {
            "ok": False,
            "status": "invalid_arguments",
            "response_text": "workspace.apply_unified_diff needs a non-empty `patch`.",
            "details": {"paths": []},
        }
    touched_paths = _extract_patch_paths(patch_text)
    if not touched_paths:
        return {
            "ok": False,
            "status": "invalid_arguments",
            "response_text": "No patch targets were found in the supplied unified diff.",
            "details": {"paths": []},
        }
    snapshots: list[dict[str, Any]] = []
    for relative in touched_paths:
        target = resolve_workspace_path(relative, workspace_root=workspace_root)
        existed_before = target.exists()
        before_text = target.read_text(encoding="utf-8", errors="replace") if existed_before and target.is_file() else ""
        snapshots.append({"path": relative_path(target, workspace_root=workspace_root), "existed_before": existed_before, "before_text": before_text})

    applied_with = ""
    errors: list[str] = []
    git_available = shutil.which("git")
    if git_available:
        git_cmd = [git_available, "-C", str(workspace_root), "apply", "--whitespace=nowarn", "--recount", "-"]
        git_result = subprocess.run(git_cmd, input=patch_text, text=True, capture_output=True)
        if git_result.returncode == 0:
            applied_with = "git_apply"
        else:
            errors.append((git_result.stderr or git_result.stdout or "").strip())
    if not applied_with:
        patch_available = shutil.which("patch")
        if patch_available:
            strip = "1" if "/dev/null" in patch_text or " a/" in patch_text or " b/" in patch_text or "\na/" in patch_text else "0"
            patch_cmd = [patch_available, f"-p{strip}", "-d", str(workspace_root), "--forward", "--batch"]
            patch_result = subprocess.run(patch_cmd, input=patch_text, text=True, capture_output=True)
            if patch_result.returncode == 0:
                applied_with = "patch"
            else:
                errors.append((patch_result.stderr or patch_result.stdout or "").strip())
    if not applied_with:
        error_text = "; ".join(item for item in errors if item) or "No supported patch engine was available."
        return {
            "ok": False,
            "status": "apply_failed",
            "response_text": f"I could not apply the unified diff: {error_text}",
            "details": {"paths": touched_paths, "errors": errors},
        }

    artifacts: list[dict[str, Any]] = []
    mutation_changes: list[dict[str, Any]] = []
    for snapshot in snapshots:
        target = resolve_workspace_path(snapshot["path"], workspace_root=workspace_root)
        exists_after = target.exists()
        after_text = target.read_text(encoding="utf-8", errors="replace") if exists_after and target.is_file() else ""
        if exists_after and snapshot["before_text"].endswith("\n") and after_text and not after_text.endswith("\n"):
            after_text = after_text + "\n"
            target.write_text(after_text, encoding="utf-8")
        action = "updated"
        if not snapshot["existed_before"] and exists_after:
            action = "created"
        elif snapshot["existed_before"] and not exists_after:
            action = "deleted"
        artifacts.append(
            build_file_diff_artifact(
                path=snapshot["path"],
                action=action,
                before=snapshot["before_text"],
                after=after_text,
                extra={"engine": applied_with},
            )
        )
        mutation_changes.append(
            {
                "path": snapshot["path"],
                "action": action,
                "existed_before": bool(snapshot["existed_before"]),
                "existed_after": bool(exists_after),
                "before_text": snapshot["before_text"],
                "after_text": after_text,
            }
        )
    mutation_record = record_workspace_mutation(
        session_id=session_id,
        workspace_root=workspace_root,
        intent="workspace.apply_unified_diff",
        changes=mutation_changes,
    )
    rendered = ["Applied unified diff:"]
    for path in touched_paths:
        rendered.append(f"- {path}")
    return {
        "ok": True,
        "status": "executed",
        "response_text": "\n".join(rendered),
        "details": {
            "paths": touched_paths,
            "artifacts": artifacts,
            "engine": applied_with,
            "mutation_record": {
                "mutation_id": str(mutation_record.get("mutation_id") or "").strip(),
                "session_key": str(mutation_record.get("session_key") or "").strip(),
            },
        },
    }


def _extract_patch_paths(patch_text: str) -> list[str]:
    candidates: list[str] = []
    for match in _PATCH_TARGET_RE.finditer(str(patch_text or "")):
        raw = str(match.group("path") or "").strip()
        if not raw or raw == "/dev/null":
            continue
        clean = raw
        if clean.startswith("a/") or clean.startswith("b/"):
            clean = clean[2:]
        if clean not in candidates:
            candidates.append(clean)
    return candidates
