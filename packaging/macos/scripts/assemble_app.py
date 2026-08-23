#!/usr/bin/env python3
import argparse
import shutil
import stat
from pathlib import Path


def copy_executable(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def assemble(destination: Path, launcher: Path, backend: Path, info_plist: Path) -> Path:
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    contents = destination / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    frameworks = contents / "Frameworks"
    macos.mkdir(parents=True)
    resources.mkdir()
    frameworks.mkdir()
    copy_executable(launcher.resolve(), macos / "PaleoRigor")
    shutil.copytree(backend.resolve(), resources / "backend", symlinks=True)
    backend_executable = resources / "backend/PaleoRigorBackend"
    backend_executable.chmod(backend_executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    shutil.copy2(info_plist.resolve(), contents / "Info.plist")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--info-plist", type=Path, required=True)
    args = parser.parse_args()
    result = assemble(args.destination, args.launcher, args.backend, args.info_plist)
    print(f"Assembled {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
