#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
PACKAGING = ROOT / "packaging/windows"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_member(name: str) -> bool:
    member = PurePosixPath(name.replace("\\", "/"))
    return not member.is_absolute() and ".." not in member.parts


def safe_extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as handle:
        for item in handle.infolist():
            if not _safe_member(item.filename):
                raise ValueError(f"unsafe archive member: {item.filename}")
        handle.extractall(destination)


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as handle:
        for item in handle.getmembers():
            if not _safe_member(item.name) or item.issym() or item.islnk():
                raise ValueError(f"unsafe archive member: {item.name}")
        handle.extractall(destination, filter="data")


def extract_archive(archive: Path, destination: Path) -> None:
    if zipfile.is_zipfile(archive):
        safe_extract_zip(archive, destination)
        return
    if tarfile.is_tarfile(archive):
        safe_extract_tar(archive, destination)
        return
    raise ValueError(f"unsupported archive format: {archive.name}")


def _find_command(component: Path, command_name: str) -> Path:
    matches = [path for path in component.rglob("*") if path.is_file() and path.name.lower() == command_name.lower()]
    if not matches:
        raise FileNotFoundError(f"command {command_name} was not found below {component}")
    return min(matches, key=lambda path: (len(path.parts), len(str(path))))


def _write_wrapper(bin_dir: Path, name: str, target: Path) -> Path:
    relative = os.path.relpath(target, bin_dir).replace("/", "\\")
    wrapper = bin_dir / f"{name}.cmd"
    wrapper.write_text(f'@echo off\r\n"%~dp0{relative}" %*\r\n', encoding="utf-8", newline="")
    wrapper.chmod(0o755)
    return wrapper


def _verified_archive(cache: Path, name: str, item: dict) -> Path:
    archive = cache / "downloads" / item["archive"]
    if not archive.is_file():
        raise FileNotFoundError(f"downloaded archive is missing for {name}: {archive}")
    actual = sha256(archive)
    if actual != item["sha256"]:
        raise ValueError(f"checksum mismatch for {name}: expected {item['sha256']}, got {actual}")
    return archive


def stage_from_cache(cache: Path, destination: Path, manifest: dict) -> Path:
    cache = Path(cache)
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    components = destination / "components"
    bin_dir = destination / "bin"
    components.mkdir(parents=True)
    bin_dir.mkdir()
    entries = []

    for name, item in manifest["tools"].items():
        component = components / name
        prebuilt = cache / "built" / name
        if prebuilt.is_dir():
            shutil.copytree(prebuilt, component)
        elif item["strategy"] in {"msys2-source", "msys2-package", "python-wheel"}:
            if not prebuilt.is_dir():
                raise FileNotFoundError(f"prebuilt component is missing for {name}: {prebuilt}")
        else:
            archive = _verified_archive(cache, name, item)
            extract_archive(archive, component)

        command = _find_command(component, item["command"])
        wrapper = _write_wrapper(bin_dir, name, command)
        entries.append(
            {
                "id": name,
                "version": item["version"],
                "command": f"bin/{wrapper.name}",
                "resolved_sha256": sha256(command),
                "upstream": item["url"],
                "license_file": f"licenses/{name}.txt",
            }
        )

    for name, item in manifest.get("runtimes", {}).items():
        archive = _verified_archive(cache, name, item)
        extract_archive(archive, destination / "runtimes" / name)

    license_source = PACKAGING / "licenses"
    if license_source.is_dir():
        shutil.copytree(license_source, destination / "licenses")
    (destination / "manifest.json").write_text(json.dumps({"tools": entries}, indent=2) + "\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage pinned PaleoRigor Windows tools.")
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=PACKAGING / "tool-sources.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    stage_from_cache(args.cache.resolve(), args.destination.resolve(), manifest)
    print(f"Staged Windows tools at {args.destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
