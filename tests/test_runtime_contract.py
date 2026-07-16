from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from automas_script_hsr.adapter_plugin import HSRAdapterPlugin
from automas_script_hsr.contracts import (
    HSRAdapterDescriptor,
    HSRRunResult,
)
from automas_script_hsr.registry import HSRRegistryService


DESCRIPTOR = HSRAdapterDescriptor(
    engine="SRA",
    display_name="SRA",
    version="test",
    tasks=(),
)


class _Catalog:
    descriptor = DESCRIPTOR

    def list_tasks(self):
        return ()

    def list_stage_options(self, **kwargs):
        _ = kwargs
        return ()


class _Controller:
    descriptor = DESCRIPTOR

    def probe(self, script_config):
        _ = script_config
        return True, ""

    def lock_paths(self, script_config):
        _ = script_config
        return ()

    async def open_session(self, **kwargs):
        _ = kwargs
        raise NotImplementedError


class _RetryableSession:
    def __init__(self) -> None:
        self.close_calls = 0

    async def close(self) -> None:
        self.close_calls += 1
        if self.close_calls == 1:
            raise RuntimeError("busy")


class RegistrySessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_close_remains_tracked_for_a_later_retry(self) -> None:
        registry = HSRRegistryService()
        registry.register_group(
            owner="adapter",
            task_catalog=_Catalog(),
            controller=_Controller(),
        )
        session = _RetryableSession()
        registry.track_session("SRA", session)

        first_errors = await registry.close_owner_sessions("adapter")
        second_errors = await registry.close_owner_sessions("adapter")
        third_errors = await registry.close_owner_sessions("adapter")

        self.assertEqual(first_errors, ("SRA: RuntimeError: busy",))
        self.assertEqual(second_errors, ())
        self.assertEqual(third_errors, ())
        self.assertEqual(session.close_calls, 2)


class _Logger:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def info(self, message: str) -> None:
        _ = message

    def error(self, message: str) -> None:
        self.errors.append(message)


class _LifecycleRegistry:
    def __init__(self) -> None:
        self.owner: str | None = None
        self.close_results: list[tuple[str, ...]] = []
        self.unregister_calls = 0

    def register_group(self, *, owner, task_catalog, controller) -> None:
        _ = task_catalog, controller
        self.owner = owner

    async def close_owner_sessions(self, owner: str) -> tuple[str, ...]:
        self.assert_owner(owner)
        return self.close_results.pop(0) if self.close_results else ()

    def unregister_owner(self, owner: str) -> None:
        self.assert_owner(owner)
        self.owner = None
        self.unregister_calls += 1

    def assert_owner(self, owner: str) -> None:
        if self.owner != owner:
            raise AssertionError(f"unexpected owner: {owner!r}")


class _Context:
    def __init__(self, registry: _LifecycleRegistry) -> None:
        self.instance_id = "adapter"
        self.registry = registry
        self.services: dict[str, Any] = {}
        self.logger = _Logger()

    def get(self, name: str):
        if name == "hsr.registry.v1":
            return self.registry
        return self.services.get(name)

    def set(self, name: str, value: Any) -> None:
        self.services[name] = value


class _Plugin(HSRAdapterPlugin):
    task_catalog_factory = _Catalog
    controller_factory = _Controller
    task_catalog_service = "hsr.catalog.test"
    controller_service = "hsr.controller.test"
    display_name = "test adapter"


class AdapterLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_stop_keeps_services_until_session_cleanup_can_retry(self) -> None:
        registry = _LifecycleRegistry()
        registry.close_results = [("SRA: busy",), ()]
        context = _Context(registry)
        plugin = _Plugin(context)
        await plugin.on_start()

        await plugin.on_stop("reload")

        self.assertIs(context.services[plugin.task_catalog_service], plugin.catalog)
        self.assertIs(context.services[plugin.controller_service], plugin.controller)
        self.assertEqual(registry.owner, context.instance_id)
        self.assertEqual(registry.unregister_calls, 0)

        await plugin.on_stop("retry")

        self.assertIsNone(context.services[plugin.task_catalog_service])
        self.assertIsNone(context.services[plugin.controller_service])
        self.assertIsNone(registry.owner)
        self.assertEqual(registry.unregister_calls, 1)


@dataclass(slots=True)
class _NativeResult:
    success: bool
    output: str = ""
    error: str = ""
    returncode: int = 0


class NativeResultTests(unittest.TestCase):
    def test_success_preserves_native_evidence(self) -> None:
        native = _NativeResult(success=True, output="done", returncode=7)

        result = HSRRunResult.from_native(
            native,
            default_summary="fallback",
            default_error="failed",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.summary, "done")
        self.assertEqual(result.completion_evidence, {"returncode": 7})
        self.assertIs(result.native_result, native)

    def test_failure_uses_default_without_losing_native_result(self) -> None:
        native = _NativeResult(success=False, returncode=3)

        result = HSRRunResult.from_native(
            native,
            default_summary="fallback",
            default_error="failed",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "failed")
        self.assertIs(result.native_result, native)


if __name__ == "__main__":
    unittest.main()
