from __future__ import annotations

import unittest

from automas_script_hsr import HSRCapabilitySnapshot, HSRRegistryService


class RegistryContractTests(unittest.TestCase):
    def test_record_resolver_returns_plugin_owned_duck_type(self) -> None:
        registry = HSRRegistryService()

        capability = registry.resolve_record_capability(
            {"SRA": {"Path": "C:/example/sra"}}
        )

        self.assertIsInstance(capability, HSRCapabilitySnapshot)
        self.assertFalse(capability.available)
        self.assertIsInstance(capability.supported_modes, tuple)
        self.assertEqual(capability.configured_engines, ("SRA",))
