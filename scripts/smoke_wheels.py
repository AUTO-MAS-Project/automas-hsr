from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import venv
import zipfile
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path


CORE_DISTRIBUTION = "automas-script-hsr"
ADAPTER_DISTRIBUTIONS = (
    "automas-hsr-adapter-sra",
    "automas-hsr-adapter-m7a",
)
WORKSPACE_DISTRIBUTIONS = frozenset({CORE_DISTRIBUTION, *ADAPTER_DISTRIBUTIONS})
ENTRY_POINTS = {
    CORE_DISTRIBUTION: (
        "automas_script_hsr",
        "automas_script_hsr.plugin:Plugin",
    ),
    "automas-hsr-adapter-sra": (
        "automas_hsr_adapter_sra",
        "automas_hsr_adapter_sra.plugin:Plugin",
    ),
    "automas-hsr-adapter-m7a": (
        "automas_hsr_adapter_m7a",
        "automas_hsr_adapter_m7a.plugin:Plugin",
    ),
}
SMOKE_MODES = ("local-adapter-resolution", "metadata-only")
_REQUIREMENT_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


@dataclass(frozen=True, slots=True)
class WheelMetadata:
    name: str
    version: str
    requires_dist: tuple[str, ...]


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _wheel_prefix(distribution: str) -> str:
    return re.sub(r"[-_.]+", "_", distribution).lower() + "-"


def _find_wheel(dist_dir: Path, distribution: str) -> Path:
    prefix = _wheel_prefix(distribution)
    matches = sorted(
        path
        for path in dist_dir.rglob("*.whl")
        if path.name.lower().startswith(prefix)
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one wheel for {distribution}, found {len(matches)}"
        )
    return matches[0]


def _read_wheel_metadata(wheel: Path) -> WheelMetadata:
    with zipfile.ZipFile(wheel) as archive:
        metadata_paths = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_paths) != 1:
            raise RuntimeError(
                f"expected exactly one METADATA file in {wheel.name}, "
                f"found {len(metadata_paths)}"
            )
        message = BytesParser().parsebytes(archive.read(metadata_paths[0]))
    name = str(message.get("Name") or "").strip()
    version = str(message.get("Version") or "").strip()
    if not name or not version:
        raise RuntimeError(f"wheel metadata is missing Name or Version: {wheel.name}")
    return WheelMetadata(
        name=name,
        version=version,
        requires_dist=tuple(message.get_all("Requires-Dist", [])),
    )


def _requirement_name(requirement: str) -> str:
    match = _REQUIREMENT_NAME_PATTERN.match(requirement)
    if match is None:
        raise RuntimeError(f"cannot parse Requires-Dist entry: {requirement!r}")
    return _canonical_name(match.group(1))


def _external_requirements(metadata: list[WheelMetadata]) -> tuple[str, ...]:
    requirements = {
        requirement
        for item in metadata
        for requirement in item.requires_dist
        if _requirement_name(requirement) not in WORKSPACE_DISTRIBUTIONS
    }
    return tuple(sorted(requirements, key=str.lower))


def _venv_python(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _expected_installation(
    wheels: dict[str, Path],
    distributions: tuple[str, ...],
) -> dict[str, dict[str, str]]:
    expected: dict[str, dict[str, str]] = {}
    for distribution in distributions:
        entry_name, entry_value = ENTRY_POINTS[distribution]
        metadata = _read_wheel_metadata(wheels[distribution])
        if _canonical_name(metadata.name) != distribution:
            raise RuntimeError(
                f"wheel name mismatch for {distribution}: {metadata.name!r}"
            )
        expected[distribution] = {
            "entry_name": entry_name,
            "entry_value": entry_value,
            "version": metadata.version,
        }
    return expected


def _inspect_installation(
    python: Path,
    expected: dict[str, dict[str, str]],
) -> None:
    check_code = """
import importlib.metadata
import importlib.util
import json
import sys

expected = json.loads(sys.argv[1])
for distribution, contract in expected.items():
    metadata = importlib.metadata.distribution(distribution)
    if metadata.version != contract["version"]:
        raise SystemExit(
            f"unexpected version for {distribution}: {metadata.version!r}"
        )
    entry_points = {
        item.name: item.value
        for item in metadata.entry_points
        if item.group == "auto_mas.plugins"
    }
    if entry_points.get(contract["entry_name"]) != contract["entry_value"]:
        raise SystemExit(
            f"invalid entry point for {distribution}: {entry_points!r}"
        )
    top_level_package = contract["entry_value"].partition(":")[0].partition(".")[0]
    if importlib.util.find_spec(top_level_package) is None:
        raise SystemExit(f"package module missing for {distribution}")
"""
    subprocess.run(
        [str(python), "-c", check_code, json.dumps(expected)],
        check=True,
    )


def _create_environment(root: Path) -> Path:
    environment = root / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    return _venv_python(environment)


def smoke_metadata_only(dist_dir: Path, distributions: tuple[str, ...]) -> None:
    wheels = {
        distribution: _find_wheel(dist_dir, distribution)
        for distribution in distributions
    }
    expected = _expected_installation(wheels, distributions)
    with tempfile.TemporaryDirectory(prefix="automas-hsr-metadata-smoke-") as temp_dir:
        python = _create_environment(Path(temp_dir))
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                *(str(wheels[distribution]) for distribution in distributions),
            ],
            check=True,
        )
        _inspect_installation(python, expected)


def smoke_local_adapter_resolution(
    dist_dir: Path,
    adapters: tuple[str, ...] = ADAPTER_DISTRIBUTIONS,
) -> None:
    invalid = [adapter for adapter in adapters if adapter not in ADAPTER_DISTRIBUTIONS]
    if invalid:
        raise ValueError(f"local dependency smoke only accepts adapters: {invalid}")

    required_distributions = (CORE_DISTRIBUTION, *adapters)
    wheels = {
        distribution: _find_wheel(dist_dir, distribution)
        for distribution in required_distributions
    }
    wheel_metadata = [
        _read_wheel_metadata(wheels[distribution])
        for distribution in required_distributions
    ]
    external_requirements = _external_requirements(wheel_metadata)

    with tempfile.TemporaryDirectory(prefix="automas-hsr-local-deps-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        dependency_wheelhouse = temp_root / "external-wheelhouse"
        dependency_wheelhouse.mkdir()
        if external_requirements:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    "--disable-pip-version-check",
                    "--only-binary=:all:",
                    "--dest",
                    str(dependency_wheelhouse),
                    *external_requirements,
                ],
                check=True,
            )

        for adapter in adapters:
            environment_root = temp_root / adapter
            python = _create_environment(environment_root)
            subprocess.run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-index",
                    "--find-links",
                    str(dependency_wheelhouse),
                    "--find-links",
                    str(wheels[CORE_DISTRIBUTION].parent),
                    "--find-links",
                    str(wheels[adapter].parent),
                    str(wheels[adapter]),
                ],
                check=True,
            )
            subprocess.run([str(python), "-m", "pip", "check"], check=True)
            expected = _expected_installation(
                wheels,
                (CORE_DISTRIBUTION, adapter),
            )
            _inspect_installation(python, expected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install and inspect built wheels")
    parser.add_argument("dist_dir", type=Path)
    parser.add_argument("--mode", required=True, choices=SMOKE_MODES)
    parser.add_argument(
        "--expected-package",
        action="append",
        choices=tuple(ENTRY_POINTS),
        dest="expected_packages",
    )
    args = parser.parse_args()
    dist_dir = args.dist_dir.resolve()

    if args.mode == "metadata-only":
        distributions = tuple(args.expected_packages or ENTRY_POINTS)
        smoke_metadata_only(dist_dir, distributions)
        print(f"metadata-only wheel smoke passed: {', '.join(distributions)}")
        return

    adapters = tuple(args.expected_packages or ADAPTER_DISTRIBUTIONS)
    smoke_local_adapter_resolution(dist_dir, adapters)
    print(
        "local adapter dependency resolution passed: "
        f"{', '.join(adapters)} -> {CORE_DISTRIBUTION}"
    )


if __name__ == "__main__":
    main()
