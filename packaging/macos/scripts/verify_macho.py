#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


SYSTEM_PREFIXES = ("/usr/lib/", "/System/Library/")
RELATIVE_PREFIXES = ("@loader_path/", "@executable_path/", "@rpath/")


def is_allowed_dependency(dependency: str) -> bool:
    return dependency.startswith(SYSTEM_PREFIXES + RELATIVE_PREFIXES)


def is_macho(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    result = subprocess.run(
        ["/usr/bin/file", "-b", str(path)], capture_output=True, text=True, check=False
    )
    return "Mach-O" in result.stdout


def architectures(path: Path) -> set[str]:
    result = subprocess.run(
        ["/usr/bin/lipo", "-archs", str(path)], capture_output=True, text=True, check=True
    )
    return set(result.stdout.split())


def dependencies(path: Path) -> list[str]:
    result = subprocess.run(
        ["/usr/bin/otool", "-L", str(path)], capture_output=True, text=True, check=True
    )
    return [line.strip().split(" (", 1)[0] for line in result.stdout.splitlines()[1:] if line.strip()]


def verify_tree(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if not is_macho(path):
            continue
        archs = architectures(path)
        if "arm64" not in archs or archs - {"arm64"}:
            errors.append(f"{path}: expected arm64 only, found {sorted(archs)}")
        for dependency in dependencies(path):
            if not is_allowed_dependency(dependency):
                errors.append(f"{path}: non-portable dependency {dependency}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    errors = verify_tree(args.root.resolve())
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Mach-O verification passed: {args.root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
