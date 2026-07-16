from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from automas_hsr_adapter_m7a.stages import load_m7a_stage_options
from automas_hsr_adapter_sra.stages import load_sra_stage_options
from automas_script_hsr.runtime.stage_provider import (
    M7A_INSTANCE_TYPE_CALYX_GOLDEN,
)


class _ScriptConfig:
    def __init__(self, **paths: str) -> None:
        self._paths = paths

    def get(self, section: str, key: str) -> str:
        if key != "Path":
            return ""
        return self._paths.get(section, "")


class CurrentStageProviderContractTests(unittest.TestCase):
    def test_current_m7a_provider_payload_normalizes_to_public_dto(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            assets = root / "assets" / "config"
            assets.mkdir(parents=True)
            (assets / "instance_names.json").write_text(
                json.dumps(
                    {
                        M7A_INSTANCE_TYPE_CALYX_GOLDEN: {
                            "Test Stage": "Test Detail",
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (assets / "instance_drops.json").write_text("{}", encoding="utf-8")

            categories = load_m7a_stage_options(_ScriptConfig(M7A=str(root)))

        self.assertEqual(len(categories), 1)
        option = categories[0].options[0]
        self.assertEqual(option.label, "Test Stage")
        self.assertEqual(option.detail, "Test Detail")
        self.assertEqual(
            option.native_payload["m7a"],
            {
                "instanceType": M7A_INSTANCE_TYPE_CALYX_GOLDEN,
                "instanceName": "Test Stage",
            },
        )

    def test_current_sra_provider_payload_normalizes_to_public_dto(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / "tasks" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "trailblaze_power.toml").write_text(
                """
[subtasks.calyx_golden]
name = "Test Category"
cost = 10
max_count = 24
levels = ["Test Stage"]
results = ["Test Detail"]
""".strip(),
                encoding="utf-8",
            )

            categories = load_sra_stage_options(_ScriptConfig(SRA=str(root)))

        self.assertEqual(len(categories), 1)
        option = categories[0].options[0]
        self.assertEqual(option.label, "Test Stage")
        self.assertEqual(option.detail, "Test Detail")
        self.assertEqual(option.cost, 10)
        self.assertEqual(option.max_count, 24)
        self.assertEqual(option.native_payload["sra"], {"id": "calyx_golden", "level": 1})
