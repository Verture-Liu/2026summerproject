#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGING = ROOT / "packaging/macos"
LICENSE_SOURCES = {
    "fastqc": Path("/opt/homebrew/Cellar/fastqc/0.12.1/LICENSE"),
    "multiqc": Path("/opt/miniconda3/pkgs/multiqc-1.35-pyhdfd78af_1/info/licenses/LICENSE"),
    "seqkit": Path("/opt/miniconda3/pkgs/seqkit-2.13.0-hd5f1084_0/info/licenses/LICENSE"),
    "seqtk": Path("/opt/miniconda3/pkgs/seqtk-1.5-hba9b596_1/info/licenses/LICENSE"),
    "samtools": Path("/opt/miniconda3/pkgs/samtools-1.23.1-hc612e98_0/info/licenses/LICENSE"),
    "bwa": Path("/opt/miniconda3/pkgs/bwa-0.7.19-hba9b596_1/info/licenses/COPYING"),
    "bowtie2": Path("/opt/miniconda3/pkgs/bowtie2-2.5.5-h9e91881_0/info/licenses/LICENSE"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_command_link(tool_root: Path, command: str, target: str) -> Path:
    bin_dir = tool_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    link = bin_dir / command
    link.unlink(missing_ok=True)
    link.symlink_to(Path("../") / target)
    return link


def copy_executable(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def macho_dependencies(path: Path) -> list[str]:
    result = subprocess.run(
        ["/usr/bin/otool", "-L", str(path)], capture_output=True, text=True, check=True
    )
    return [line.strip().split(" (", 1)[0] for line in result.stdout.splitlines()[1:] if line.strip()]


def is_macho(path: Path) -> bool:
    result = subprocess.run(
        ["/usr/bin/file", "-b", str(path)], capture_output=True, text=True, check=False
    )
    return "Mach-O" in result.stdout


def bundleable_dependency_name(dependency: str, source_lib: Path) -> str | None:
    if dependency.startswith(("@rpath/", "@loader_path/", "@executable_path/")):
        return Path(dependency).name
    if dependency.startswith(str(source_lib)) or dependency.startswith("/opt/miniconda3/"):
        return Path(dependency).name
    return None


def copy_library_closure(seeds: list[Path], source_lib: Path, destination_lib: Path) -> None:
    destination_lib.mkdir(parents=True, exist_ok=True)
    queue = list(seeds)
    copied: set[str] = set()
    while queue:
        binary = queue.pop()
        if not is_macho(binary):
            continue
        for dependency in macho_dependencies(binary):
            name = bundleable_dependency_name(dependency, source_lib)
            if name is None:
                continue
            if name not in copied:
                source = source_lib / name
                if not source.exists():
                    raise FileNotFoundError(f"Missing dependency {name} for {binary} in {source_lib}")
                resolved = source.resolve()
                real_destination = destination_lib / resolved.name
                shutil.copy2(resolved, real_destination)
                real_destination.chmod(real_destination.stat().st_mode | stat.S_IWUSR)
                if name != resolved.name:
                    (destination_lib / name).symlink_to(resolved.name)
                copied.add(name)
                copied.add(resolved.name)
                queue.append(real_destination)
            relative = f"@loader_path/{name}" if binary.parent == destination_lib else f"@loader_path/../lib/{name}"
            if dependency != relative:
                binary.chmod(binary.stat().st_mode | stat.S_IWUSR)
                subprocess.run(
                    ["/usr/bin/install_name_tool", "-change", dependency, relative, str(binary)],
                    check=True,
                )


def patch_perl_shebang(path: Path) -> None:
    text = path.read_text()
    if text.startswith("#!/usr/bin/env perl"):
        path.write_text(text.replace("#!/usr/bin/env perl", "#!/usr/bin/perl", 1))
        path.chmod(0o755)


def stage_native_component(tool_root: Path, tool: str, source: Path, environment: Path) -> None:
    component = tool_root / "components" / tool
    executable = component / "bin" / tool
    copy_executable(source, executable)
    copy_library_closure([executable], environment / "lib", component / "lib")
    create_command_link(tool_root, tool, f"components/{tool}/bin/{tool}")


def stage_bowtie2(tool_root: Path, environment: Path) -> None:
    component = tool_root / "components/bowtie2"
    binaries: list[Path] = []
    for source in sorted((environment / "bin").glob("bowtie2*")):
        destination = component / "bin" / source.name
        copy_executable(source, destination)
        if destination.read_bytes()[:2] == b"#!":
            patch_perl_shebang(destination)
        binaries.append(destination)
    copy_library_closure(binaries, environment / "lib", component / "lib")
    create_command_link(tool_root, "bowtie2", "components/bowtie2/bin/bowtie2")


def stage_fastqc(tool_root: Path, source: Path, java_home: Path) -> None:
    component = tool_root / "components/fastqc"
    shutil.copytree(source, component, symlinks=True)
    subprocess.run(
        [
            str(java_home / "bin/jlink"),
            "--add-modules", "java.base,java.desktop,java.scripting,java.sql",
            "--strip-debug", "--no-man-pages", "--no-header-files", "--compress=2",
            "--output", str(component / "jre"),
        ],
        check=True,
    )
    (component / "fastqc").chmod(0o755)
    create_command_link(tool_root, "fastqc", "components/fastqc/fastqc")


def stage_multiqc(tool_root: Path, distribution: Path) -> None:
    component = tool_root / "components/multiqc"
    shutil.copytree(distribution, component, symlinks=True)
    (component / "multiqc").chmod(0o755)
    create_command_link(tool_root, "multiqc", "components/multiqc/multiqc")


def write_manifest(tool_root: Path, sources: dict) -> None:
    entries = []
    for name, metadata in sources.items():
        if name == "java":
            continue
        command = tool_root / "bin" / name
        entries.append({
            "id": name,
            "version": metadata["version"],
            "command": f"bin/{name}",
            "resolved_sha256": sha256(command.resolve()),
            "upstream": metadata["upstream"],
            "license_file": f"licenses/{name}.txt",
        })
    (tool_root / "manifest.json").write_text(json.dumps({"tools": entries}, indent=2) + "\n")


def adhoc_sign_native_components(tool_root: Path) -> None:
    for component_name in ("seqtk", "samtools", "bwa", "bowtie2"):
        component = tool_root / "components" / component_name
        machos = [path for path in component.rglob("*") if path.is_file() and not path.is_symlink() and is_macho(path)]
        for path in sorted(machos, key=lambda item: len(item.parts), reverse=True):
            subprocess.run(
                ["/usr/bin/codesign", "--force", "--sign", "-", str(path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def stage(destination: Path, multiqc_distribution: Path) -> None:
    sources = json.loads((PACKAGING / "tool-sources.json").read_text())
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    fastqc = sources["fastqc"]
    stage_fastqc(destination, Path(fastqc["source"]), Path(sources["java"]["source"]))
    stage_multiqc(destination, multiqc_distribution)

    seqkit_component = destination / "components/seqkit/bin/seqkit"
    copy_executable(Path(sources["seqkit"]["source"]), seqkit_component)
    create_command_link(destination, "seqkit", "components/seqkit/bin/seqkit")

    stage_native_component(destination, "seqtk", Path(sources["seqtk"]["source"]), Path("/opt/miniconda3"))
    for tool in ("samtools", "bwa"):
        item = sources[tool]
        stage_native_component(destination, tool, Path(item["source"]), Path(item["environment"]))
    stage_bowtie2(destination, Path(sources["bowtie2"]["source"]))

    license_dir = destination / "licenses"
    license_dir.mkdir()
    for tool, source in LICENSE_SOURCES.items():
        shutil.copy2(source, license_dir / f"{tool}.txt")
    shutil.copy2(PACKAGING / "licenses/README.md", license_dir / "README.md")
    adhoc_sign_native_components(destination)
    write_manifest(destination, sources)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--multiqc-distribution", type=Path, required=True)
    args = parser.parse_args()
    stage(args.destination.resolve(), args.multiqc_distribution.resolve())
    print(f"Staged seven tools at {args.destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
