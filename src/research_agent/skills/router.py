from __future__ import annotations

import hashlib
import importlib.util
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml


PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FACTORY_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RoutedSkillDescriptor:
    name: str
    description: str
    input_formats: list[str]
    output_formats: list[str]
    resource_class: str
    parameter_schema: dict
    package_id: str
    package_version: str


def _package_checksum(package: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in package.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts:
            continue
        digest.update(str(path.relative_to(package)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class SkillRouter:
    def __init__(self, roots: Iterable[Path]):
        self._skills = {}
        self._metadata = {}
        self._packages = []
        self._diagnostics = []
        self._load([Path(root) for root in roots])

    def _error(self, package: Path, error: Exception | str) -> None:
        self._diagnostics.append(
            {"package": str(package), "error": str(error)}
        )

    def _load(self, roots: list[Path]) -> None:
        candidates = []
        for root in roots:
            if not root.is_dir():
                continue
            candidates.extend(
                path for path in sorted(root.iterdir())
                if path.is_dir() and not path.name.startswith(".")
            )
        loaded = []
        for package in candidates:
            try:
                manifest_path = package / "skill.yaml"
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                if not isinstance(manifest, dict):
                    raise ValueError("Manifest must be a mapping")
                if manifest.get("protocol_version") != "1.0":
                    raise ValueError("Unsupported protocol_version")
                package_id = manifest.get("package_id", "")
                if not PACKAGE_ID.fullmatch(package_id):
                    raise ValueError("Invalid package_id")
                if manifest.get("enabled", True) is not True:
                    continue
                factory_spec = manifest.get("factory", "")
                if ":" not in factory_spec:
                    raise ValueError("factory must use file.py:function format")
                relative_file, factory_name = factory_spec.split(":", 1)
                if Path(relative_file).is_absolute() or ".." in Path(relative_file).parts:
                    raise ValueError("Unsafe factory path")
                if not FACTORY_NAME.fullmatch(factory_name):
                    raise ValueError("Invalid factory function")
                adapter_path = (package / relative_file).resolve()
                if package.resolve() not in adapter_path.parents:
                    raise ValueError("Factory escapes package directory")
                if not adapter_path.is_file():
                    raise ValueError(f"Factory file does not exist: {relative_file}")
                module_name = (
                    f"research_agent_dynamic_{package_id.replace('-', '_')}_"
                    f"{_package_checksum(package)[:12]}"
                )
                spec = importlib.util.spec_from_file_location(module_name, adapter_path)
                if spec is None or spec.loader is None:
                    raise ValueError("Could not load adapter")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                factory = getattr(module, factory_name)
                skills = list(factory())
                if not skills:
                    raise ValueError("Factory returned no Skills")
                loaded.append(
                    (
                        package,
                        manifest,
                        skills,
                        _package_checksum(package),
                    )
                )
            except Exception as exc:
                self._error(package, exc)

        definitions = {}
        for package, manifest, skills, checksum in loaded:
            for skill in skills:
                definitions.setdefault(skill.name, []).append(
                    (package, manifest, skill, checksum)
                )
        for name, items in definitions.items():
            if len(items) > 1:
                packages = ", ".join(item[1]["package_id"] for item in items)
                for package, _, _, _ in items:
                    self._error(
                        package,
                        f"Duplicate skill name {name!r} in packages: {packages}",
                    )
                continue
            package, manifest, skill, checksum = items[0]
            self._skills[name] = skill
            self._metadata[name] = {
                "package_id": manifest["package_id"],
                "package_version": str(manifest.get("package_version", "0")),
                "checksum": checksum,
            }
        active_packages = {
            metadata["package_id"] for metadata in self._metadata.values()
        }
        for package, manifest, skills, checksum in loaded:
            if manifest["package_id"] in active_packages:
                self._packages.append(
                    {
                        "package_id": manifest["package_id"],
                        "package_version": str(manifest.get("package_version", "0")),
                        "path": str(package),
                        "checksum": checksum,
                        "skills": [
                            skill.name
                            for skill in skills
                            if skill.name in self._skills
                        ],
                    }
                )

    def get(self, name: str):
        if name not in self._skills:
            raise KeyError(f"Unknown skill: {name}")
        return self._skills[name]

    def catalog(self) -> list[RoutedSkillDescriptor]:
        return [
            RoutedSkillDescriptor(
                name=skill.name,
                description=skill.description,
                input_formats=sorted(skill.input_formats),
                output_formats=sorted(skill.output_formats),
                resource_class=skill.resource_class,
                parameter_schema=skill.parameter_schema,
                package_id=self._metadata[name]["package_id"],
                package_version=self._metadata[name]["package_version"],
            )
            for name, skill in self._skills.items()
        ]

    def packages(self) -> list[dict]:
        return list(self._packages)

    def diagnostics(self) -> list[dict]:
        return list(self._diagnostics)
