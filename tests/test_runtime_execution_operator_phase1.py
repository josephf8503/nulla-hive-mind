from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.execution.validation_tools import runtime_validation_command, validation_command
from core.runtime_execution_tools import execute_runtime_tool


class RuntimeExecutionOperatorPhase1Tests(unittest.TestCase):
    def test_workspace_list_tree_and_symbol_search_are_grounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "src").mkdir(parents=True, exist_ok=True)
            (workspace / "src" / "app.py").write_text(
                "class Runner:\n    pass\n\n\ndef launch():\n    return Runner()\n",
                encoding="utf-8",
            )

            tree = execute_runtime_tool(
                "workspace.list_tree",
                {"path": ".", "limit": 20},
                source_context={"workspace": tmpdir},
            )
            assert tree is not None
            self.assertTrue(tree.ok)
            self.assertIn("src/", tree.response_text)
            self.assertIn("src/app.py", tree.response_text)
            self.assertEqual(tree.details["observation"]["intent"], "workspace.list_tree")

            symbol = execute_runtime_tool(
                "workspace.symbol_search",
                {"symbol": "launch", "path": "src"},
                source_context={"workspace": tmpdir},
            )
            assert symbol is not None
            self.assertTrue(symbol.ok)
            self.assertIn("[function_definition]", symbol.response_text)
            self.assertEqual(symbol.details["observation"]["matches"][0]["path"], "src/app.py")

    def test_workspace_apply_unified_diff_and_rollback_use_tracked_mutation_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "app.py").write_text("print('hello')\n", encoding="utf-8")
            patch_text = "\n".join(
                [
                    "--- a/app.py",
                    "+++ b/app.py",
                    "@@ -1 +1 @@",
                    "-print('hello')",
                    "+print('goodbye')",
                    "",
                ]
            )

            applied = execute_runtime_tool(
                "workspace.apply_unified_diff",
                {"patch": patch_text},
                source_context={"workspace": tmpdir, "session_id": "session-1"},
            )
            assert applied is not None
            self.assertTrue(applied.ok)
            self.assertIn("Applied unified diff", applied.response_text)
            self.assertEqual((workspace / "app.py").read_text(encoding="utf-8"), "print('goodbye')\n")

            rolled_back = execute_runtime_tool(
                "workspace.rollback_last_change",
                {},
                source_context={"workspace": tmpdir, "session_id": "session-1"},
            )
            assert rolled_back is not None
            self.assertTrue(rolled_back.ok)
            self.assertIn("restored `app.py`", rolled_back.response_text)
            self.assertEqual((workspace / "app.py").read_text(encoding="utf-8"), "print('hello')\n")

    def test_workspace_apply_unified_diff_has_python_fallback_when_shell_patchers_are_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "app.py").write_text("print('hello')\n", encoding="utf-8")
            patch_text = "\n".join(
                [
                    "--- a/app.py",
                    "+++ b/app.py",
                    "@@ -1 +1 @@",
                    "-print('hello')",
                    "+print('goodbye')",
                    "",
                ]
            )

            with mock.patch("core.execution.workspace_tools.shutil.which", return_value=None):
                applied = execute_runtime_tool(
                    "workspace.apply_unified_diff",
                    {"patch": patch_text},
                    source_context={"workspace": tmpdir, "session_id": "session-fallback"},
                )

            assert applied is not None
            self.assertTrue(applied.ok)
            self.assertEqual(applied.details["observation"]["engine"], "python_fallback")
            self.assertEqual((workspace / "app.py").read_text(encoding="utf-8"), "print('goodbye')\n")

    def test_workspace_git_status_and_diff_report_real_repo_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "tests@example.test"], cwd=workspace, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Tests"], cwd=workspace, check=True, capture_output=True)
            (workspace / "tracked.py").write_text("print('hello')\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.py"], cwd=workspace, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=workspace, check=True, capture_output=True)
            (workspace / "tracked.py").write_text("print('goodbye')\n", encoding="utf-8")

            status = execute_runtime_tool(
                "workspace.git_status",
                {},
                source_context={"workspace": tmpdir},
            )
            assert status is not None
            self.assertTrue(status.ok)
            self.assertIn("tracked.py", status.response_text)

            diff = execute_runtime_tool(
                "workspace.git_diff",
                {},
                source_context={"workspace": tmpdir},
            )
            assert diff is not None
            self.assertTrue(diff.ok)
            self.assertIn("-print('hello')", diff.response_text)
            self.assertIn("+print('goodbye')", diff.response_text)

    def test_workspace_run_tests_executes_validation_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "test_sample.py").write_text(
                "def test_truth():\n    assert 2 + 2 == 4\n",
                encoding="utf-8",
            )
            result = execute_runtime_tool(
                "workspace.run_tests",
                {"command": "python3 -m pytest -q test_sample.py"},
                source_context={"workspace": tmpdir},
            )
            assert result is not None
            self.assertTrue(result.ok)
            self.assertEqual(result.details["observation"]["intent"], "workspace.run_tests")
            self.assertEqual(result.details["observation"]["returncode"], 0)
            self.assertIn(sys.executable, result.details["observation"]["command"])

    def test_validation_command_defaults_are_honest(self) -> None:
        with mock.patch("core.execution.validation_tools.shutil.which") as which:
            which.side_effect = lambda name: "/usr/bin/" + name if name in {"pytest", "ruff"} else None
            self.assertEqual(validation_command("workspace.run_tests", {}), "pytest -q")
            self.assertEqual(validation_command("workspace.run_lint", {}), "ruff check .")
            self.assertEqual(validation_command("workspace.run_formatter", {}), "ruff format --check .")
            self.assertEqual(validation_command("workspace.run_formatter", {"apply": True}), "ruff format .")

    def test_runtime_validation_command_uses_current_interpreter_for_pytest_and_ruff(self) -> None:
        self.assertEqual(
            runtime_validation_command("python3 -m pytest -q test_sample.py"),
            f"{sys.executable} -m pytest -q test_sample.py",
        )
        self.assertEqual(
            runtime_validation_command("ruff check ."),
            f"{sys.executable} -m ruff check .",
        )


if __name__ == "__main__":
    unittest.main()
