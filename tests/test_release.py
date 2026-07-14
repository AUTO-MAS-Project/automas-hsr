from __future__ import annotations

import unittest

from scripts.release import PACKAGE_CONFIG, project_version, resolve_release


class ReleaseTargetTests(unittest.TestCase):
    def _version(self, package: str) -> str:
        package_dir, _ = PACKAGE_CONFIG[package]
        return project_version(package_dir)

    def test_manual_first_release_must_run_from_main(self) -> None:
        with self.assertRaisesRegex(ValueError, "main branch"):
            resolve_release(
                event_name="workflow_dispatch",
                ref="refs/heads/feature/test",
                manual_package="automas-script-hsr",
                manual_version="0.1.0",
            )

    def test_manual_release_version_must_match_project(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match"):
            resolve_release(
                event_name="workflow_dispatch",
                ref="refs/heads/main",
                manual_package="automas-script-hsr",
                manual_version="999.0.0",
            )

    def test_supported_tags_resolve_to_their_package(self) -> None:
        for package in PACKAGE_CONFIG:
            with self.subTest(package=package):
                version = self._version(package)
                target = resolve_release(
                    event_name="push",
                    ref=f"refs/tags/{package}-v{version}",
                )
                self.assertEqual(target.package, package)
                self.assertEqual(target.version, version)

    def test_unknown_tag_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported release tag"):
            resolve_release(
                event_name="push",
                ref="refs/tags/v0.1.0",
            )
