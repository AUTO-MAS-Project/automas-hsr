from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.smoke_wheels import (
    ADAPTER_DISTRIBUTIONS,
    CORE_DISTRIBUTION,
    META_DISTRIBUTION,
    WheelMetadata,
    _external_requirements,
    _read_wheel_metadata,
)


class WheelSmokeContractTests(unittest.TestCase):
    def test_workspace_dependencies_are_excluded_from_external_wheelhouse(self) -> None:
        requirements = _external_requirements(
            [
                WheelMetadata(
                    name="automas-script-hsr",
                    version="0.1.0",
                    requires_dist=("jinja2>=3.1", "pydantic>=2"),
                ),
                WheelMetadata(
                    name="automas-hsr-adapter-m7a",
                    version="0.1.0",
                    requires_dist=(
                        "automas-script-hsr<0.2.0,>=0.1.0",
                        "PyYAML>=6",
                    ),
                ),
            ]
        )

        self.assertEqual(
            requirements,
            ("jinja2>=3.1", "pydantic>=2", "PyYAML>=6"),
        )

    def test_wheel_metadata_reader_preserves_dependency_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / "example-1.2.3-py3-none-any.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr(
                    "example-1.2.3.dist-info/METADATA",
                    """Metadata-Version: 2.4
Name: example
Version: 1.2.3
Requires-Dist: automas-script-hsr>=0.1.0,<0.2.0
""",
                )

            metadata = _read_wheel_metadata(wheel)

        self.assertEqual(metadata.name, "example")
        self.assertEqual(metadata.version, "1.2.3")
        self.assertEqual(
            metadata.requires_dist,
            ("automas-script-hsr>=0.1.0,<0.2.0",),
        )

    def test_ci_and_publish_use_distinct_smoke_modes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        ci = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        publish = (root / ".github" / "workflows" / "publish.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("--mode local-adapter-resolution", ci)
        self.assertIn("--mode local-meta-resolution", ci)
        self.assertIn("--mode metadata-only", publish)
        self.assertEqual(
            ADAPTER_DISTRIBUTIONS,
            ("automas-hsr-adapter-sra", "automas-hsr-adapter-m7a"),
        )
        self.assertEqual(CORE_DISTRIBUTION, "automas-script-hsr")
        self.assertEqual(META_DISTRIBUTION, "automas-hsr")
