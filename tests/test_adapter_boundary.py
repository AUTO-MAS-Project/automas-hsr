from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "automas_script_hsr" / "src" / "automas_script_hsr"
ADAPTERS = (
    ROOT / "packages" / "automas_hsr_adapter_sra" / "src" / "automas_hsr_adapter_sra",
    ROOT / "packages" / "automas_hsr_adapter_m7a" / "src" / "automas_hsr_adapter_m7a",
)


class AdapterBoundaryTests(unittest.TestCase):
    def test_core_uses_the_host_manager_factory_contract(self) -> None:
        plugin = (CORE / "plugin.py").read_text(encoding="utf-8")

        self.assertIn("hooks_factory=None", plugin)
        self.assertIn("manager_factory=self._build_manager", plugin)
        self.assertIn("await super().on_start()", plugin)
        self.assertNotIn("provider.manager_factory =", plugin)

    def test_engine_adapters_share_the_atomic_lifecycle(self) -> None:
        self.assertTrue((CORE / "adapter_plugin.py").is_file())
        self.assertFalse((CORE / "adapter.py").exists())

        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter.name):
                plugin = (adapter / "plugin.py").read_text(encoding="utf-8")
                self.assertIn(
                    "from automas_script_hsr.adapter_plugin import HSRAdapterPlugin",
                    plugin,
                )
                self.assertIn("class Plugin(HSRAdapterPlugin):", plugin)

    def test_native_execution_contract_is_owned_by_the_core_package(self) -> None:
        contracts = (CORE / "contracts.py").read_text(encoding="utf-8")

        self.assertIn("class HSRNativeRunPlan", contracts)
        self.assertIn("class HSRNativeRunResult", contracts)

    def test_failed_session_cleanup_keeps_references_for_manager_retry(self) -> None:
        autoproxy = (CORE / "runtime" / "autoproxy.py").read_text(
            encoding="utf-8"
        )
        manager = (CORE / "runtime" / "manager.py").read_text(encoding="utf-8")
        manual_review = (CORE / "runtime" / "manual_review.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("self.runtime.sessions.clear()", autoproxy)
        self.assertIn("cleanup_errors = await self._close_runtime_sessions()", manager)
        self.assertIn("已停止后续用户", manager)

        close_start = manual_review.index("async def _close_sra_session")
        close_end = manual_review.index("async def _unsubscribe_broadcast", close_start)
        close_block = manual_review[close_start:close_end]
        self.assertLess(
            close_block.index("await session.close()"),
            close_block.index("self._sra_session = None"),
        )


if __name__ == "__main__":
    unittest.main()
