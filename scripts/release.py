from __future__ import annotations

import argparse
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_CONFIG = {
    "automas-script-hsr": (
        "packages/automas_script_hsr",
        "pypi-script-hsr",
    ),
    "automas-hsr-adapter-sra": (
        "packages/automas_hsr_adapter_sra",
        "pypi-adapter-sra",
    ),
    "automas-hsr-adapter-m7a": (
        "packages/automas_hsr_adapter_m7a",
        "pypi-adapter-m7a",
    ),
}


@dataclass(frozen=True, slots=True)
class ReleaseTarget:
    package: str
    package_dir: str
    environment: str
    version: str

    @property
    def artifact_name(self) -> str:
        return f"release-{self.package}-{self.version}"


def project_version(package_dir: str) -> str:
    pyproject = ROOT / package_dir / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _tag_target(ref: str) -> tuple[str, str]:
    prefix = "refs/tags/"
    if not ref.startswith(prefix):
        raise ValueError("tag release must run from refs/tags/<package>-v<version>")
    tag = ref.removeprefix(prefix)
    for package in PACKAGE_CONFIG:
        package_prefix = f"{package}-v"
        if tag.startswith(package_prefix):
            version = tag.removeprefix(package_prefix)
            if not version:
                break
            return package, version
    raise ValueError(f"unsupported release tag: {tag}")


def resolve_release(
    *,
    event_name: str,
    ref: str,
    manual_package: str = "",
    manual_version: str = "",
) -> ReleaseTarget:
    if event_name == "workflow_dispatch":
        if ref != "refs/heads/main":
            raise ValueError("manual first release must run from the main branch")
        package = manual_package.strip()
        version = manual_version.strip()
        if package not in PACKAGE_CONFIG:
            raise ValueError(f"unsupported package: {package}")
        if not version:
            raise ValueError("manual release version is required")
    elif event_name == "push":
        package, version = _tag_target(ref)
    else:
        raise ValueError(f"unsupported release event: {event_name}")

    package_dir, environment = PACKAGE_CONFIG[package]
    configured_version = project_version(package_dir)
    if version != configured_version:
        raise ValueError(
            f"release version {version!r} does not match {package} "
            f"project version {configured_version!r}"
        )
    return ReleaseTarget(
        package=package,
        package_dir=package_dir,
        environment=environment,
        version=version,
    )


def _write_github_outputs(target: ReleaseTarget, output_path: Path) -> None:
    values = {
        "package": target.package,
        "package_dir": target.package_dir,
        "environment": target.environment,
        "version": target.version,
        "artifact_name": target.artifact_name,
    }
    with output_path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve and validate a release target")
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--package", default="")
    parser.add_argument("--version", default="")
    args = parser.parse_args()

    target = resolve_release(
        event_name=args.event_name,
        ref=args.ref,
        manual_package=args.package,
        manual_version=args.version,
    )
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        _write_github_outputs(target, Path(github_output))
    else:
        print(
            f"{target.package} {target.version} "
            f"({target.package_dir}, {target.environment})"
        )


if __name__ == "__main__":
    main()
