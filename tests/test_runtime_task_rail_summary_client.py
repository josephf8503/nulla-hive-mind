from __future__ import annotations

import unittest

from core.runtime_task_rail_summary_client import (
    RUNTIME_TASK_RAIL_SUMMARY_CLIENT_SCRIPT,
)


class RuntimeTaskRailSummaryClientTests(unittest.TestCase):
    def test_summary_script_keeps_stage_and_receipt_contract(self) -> None:
        script = RUNTIME_TASK_RAIL_SUMMARY_CLIENT_SCRIPT
        self.assertIn("function buildSummary(session, events)", script)
        self.assertIn("received: false", script)
        self.assertIn("packet: false", script)
        self.assertIn("bundle: false", script)
        self.assertIn("result: false", script)
        self.assertIn("stopReason", script)
        self.assertIn("queryCompletedCount", script)
        self.assertIn("artifactRows", script)


if __name__ == "__main__":
    unittest.main()
