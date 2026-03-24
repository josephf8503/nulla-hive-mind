from __future__ import annotations

import unittest

from core.runtime_task_rail_assets import (
    RUNTIME_TASK_RAIL_SHELL_HTML,
    RUNTIME_TASK_RAIL_STYLE_BLOCK,
)
from core.runtime_task_rail_shell import RUNTIME_TASK_RAIL_SHELL_HTML as RUNTIME_TASK_RAIL_SHELL_FRAGMENT
from core.runtime_task_rail_styles import RUNTIME_TASK_RAIL_STYLE_BLOCK as RUNTIME_TASK_RAIL_STYLE_FRAGMENT


class RuntimeTaskRailAssetsTests(unittest.TestCase):
    def test_assets_facade_reexports_style_and_shell_fragments(self) -> None:
        self.assertIs(RUNTIME_TASK_RAIL_SHELL_HTML, RUNTIME_TASK_RAIL_SHELL_FRAGMENT)
        self.assertIs(RUNTIME_TASK_RAIL_STYLE_BLOCK, RUNTIME_TASK_RAIL_STYLE_FRAGMENT)

    def test_style_and_shell_fragments_keep_trace_workbench_contract(self) -> None:
        self.assertIn(".trace-workbench", RUNTIME_TASK_RAIL_STYLE_BLOCK)
        self.assertIn(".trace-raw-panel", RUNTIME_TASK_RAIL_STYLE_BLOCK)
        self.assertIn("NULLA Task Rail", RUNTIME_TASK_RAIL_SHELL_HTML)
        self.assertIn("Selected-step center", RUNTIME_TASK_RAIL_SHELL_HTML)


if __name__ == "__main__":
    unittest.main()
