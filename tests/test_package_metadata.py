from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "automas_script_hsr": {
        "name": "automas-script-hsr",
        "entry_point": "automas_script_hsr.plugin:Plugin",
        "dependencies": {"jinja2>=3.1", "pydantic>=2"},
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
                self.assertEqual(project["authors"], [{"name": "AUTO-MAS Team"}])
                self.assertEqual(project["license"], "AGPL-3.0-or-later")
                self.assertEqual(project["license-files"], ["LICENSE"])
                package_license = pyproject.parent / "LICENSE"
                self.assertIn(
                    "GNU AFFERO GENERAL PUBLIC LICENSE",
                    package_license.read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    project["urls"],
                    {
                        "Homepage": "https://github.com/AUTO-MAS-Project/automas-hsr",
                        "Repository": "https://github.com/AUTO-MAS-Project/automas-hsr",
                        "Documentation": "https://doc.auto-mas.top/",
                        "Issues": "https://github.com/AUTO-MAS-Project/automas-hsr/issues",
                    },
                )

    def test_repository_contains_agpl_license_and_lockfile(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", license_text)
        self.assertTrue((ROOT / "uv.lock").is_file())
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn("uv.lock", gitignore.splitlines())

    def test_core_does_not_depend_on_host_script_record_type(self) -> None:
        registry = (
            ROOT
            / "packages"
            / "automas_script_hsr"
            / "src"
            / "automas_script_hsr"
            / "registry.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("app.core.script_types", registry)
        self.assertNotIn("ScriptRecordCapability", registry)
        self.assertIn(
            ") -> HSRCapabilitySnapshot:",
            registry,
        )

    def test_new_config_and_login_contracts_are_strictly_named(self) -> None:
        core = ROOT / "packages" / "automas_script_hsr" / "src" / "automas_script_hsr"
        schema = (core / "schema.py").read_text(encoding="utf-8")
        models = (core / "runtime" / "models.py").read_text(encoding="utf-8")
        autoproxy = (core / "runtime" / "autoproxy.py").read_text(encoding="utf-8")
        manager = (core / "runtime" / "manager.py").read_text(encoding="utf-8")
        log_detect = (core / "runtime" / "log_detect.py").read_text(encoding="utf-8")
        self.assertIn('ConfigDict(extra="forbid")', schema)
        self.assertNotIn('ConfigDict(extra="allow")', schema)
        self.assertIn("m7a_current_account", models)
        self.assertIn("m7a_current_account", autoproxy)
        self.assertNotIn("m7a_fallback", models)
        self.assertNotIn("m7a_fallback", autoproxy)
        self.assertNotIn("_m7a_only_skip_reason", manager)
        self.assertNotIn("M7A-only 只执行", manager)
        self.assertNotIn("MemoryOfChaos", log_detect)
