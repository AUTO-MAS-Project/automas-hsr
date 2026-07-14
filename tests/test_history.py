from __future__ import annotations

import unittest
from pathlib import Path

from automas_script_hsr.runtime.history import (
    HSR_SUCCESS_LOG_STATUSES,
    general_log_result,
)


class HistoryResultTests(unittest.TestCase):
    def test_all_hsr_success_statuses_use_generic_success_result(self) -> None:
        self.assertGreater(len(HSR_SUCCESS_LOG_STATUSES), 0)
        for status in HSR_SUCCESS_LOG_STATUSES:
            with self.subTest(status=status):
                self.assertEqual(general_log_result(status), "Success!")

    def test_failure_status_is_preserved(self) -> None:
        status = "HSR 运行异常: example"
        self.assertEqual(general_log_result(status), status)

    def test_manager_uses_only_generic_history_writer(self) -> None:
        manager = (
            Path(__file__).resolve().parents[1]
            / "packages"
            / "automas_script_hsr"
            / "src"
            / "automas_script_hsr"
            / "runtime"
            / "manager.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Config.save_general_log", manager)
        self.assertNotIn("Config.save_hsr_log", manager)
