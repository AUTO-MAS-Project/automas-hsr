from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "automas_script_hsr": {
        "name": "automas-script-hsr",
        "entry_point": "automas_script_hsr.plugin:Plugin",
        "dependencies": {"pydantic>=2"},
    },
    "automas_hsr_adapter_sra": {
        "name": "automas-hsr-adapter-sra",
        "entry_point": "automas_hsr_adapter_sra.plugin:Plugin",
        "dependencies": {"automas-script-hsr>=0.1.0,<0.2.0"},
    },
    "automas_hsr_adapter_m7a": {
        "name": "automas-hsr-adapter-m7a",
        "entry_point": "automas_hsr_adapter_m7a.plugin:Plugin",
        "dependencies": {"automas-script-hsr>=0.1.0,<0.2.0", "PyYAML>=6"},
    },
}


class PackageMetadataTests(unittest.TestCase):
    def test_package_metadata_and_entry_points(self) -> None:
        for directory, expected in PACKAGES.items():
            with self.subTest(package=directory):
                pyproject = ROOT / "packages" / directory / "pyproject.toml"
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                project = data["project"]
                self.assertEqual(project["name"], expected["name"])
                self.assertEqual(
                    project["entry-points"]["auto_mas.plugins"][directory],
                    expected["entry_point"],
                )
                self.assertTrue(
                    expected["dependencies"].issubset(set(project.get("dependencies", [])))
                )
