# Building PaleoRigor for Windows

This directory builds the unsigned PaleoRigor research prototype for Windows 10/11 x64. It does not modify or replace the Apple Silicon macOS package.

## What the installer contains

`PaleoRigor-Setup.exe` installs the local browser application, the Agent and Skills, Python runtime, Java runtime, and seven analysis tools:

- FastQC 0.12.1
- MultiQC 1.35
- SeqKit 2.13.0
- SeqTk 1.5-r133
- Samtools 1.23.1
- BWA 0.7.19-r1273
- Bowtie2 2.5.5

End users do not need Python, Conda, Java, VS Code, WSL or MSYS2. The following prerequisites are required only on the computer that builds the installer.

## Build-machine prerequisites

- Windows 10/11 x64
- Git
- Python 3.13 x64
- .NET 8 SDK
- MSYS2 installed at `C:\msys64`
- Inno Setup 6
- Internet access while downloading the pinned build assets

Open an MSYS2 UCRT64 terminal once and install the compiler packages:

```bash
pacman -Syu
pacman -S --needed base-devel mingw-w64-ucrt-x86_64-toolchain mingw-w64-ucrt-x86_64-zlib
```

## Build

From PowerShell in the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./packaging/windows/scripts/build.ps1
```

The build verifies every downloaded archive against `tool-sources.json`, freezes the backend and MultiQC, compiles the three tools without official Windows binaries under MSYS2, publishes the self-contained launcher, and invokes Inno Setup 6. The output is:

```text
dist/PaleoRigor-Setup.exe
```

## Native verification

Run the installer gate on the same Windows computer:

```powershell
./packaging/windows/scripts/smoke_test.ps1 -Installer ./dist/PaleoRigor-Setup.exe
```

The script installs into a temporary directory, checks the seven tools, starts the loopback-only backend, verifies its authenticated health endpoint, uninstalls the application, and writes:

```text
paleorigor/windows/verification.json
paleorigor/windows/SHA256SUMS.txt
```

After this automated gate, manually launch the installed application and run one small CSV workflow and one small FASTQ/FastQC workflow before distributing the installer.

## Unsigned-build warning

The development installer is not commercially code signed. Windows SmartScreen may report an unknown publisher. This is an expected limitation of the research prototype; do not disable SmartScreen globally. A public build should be downloaded only from this project's GitHub workflow artifact or an identified project release and checked against `SHA256SUMS.txt`.

The Windows build must not be described as verified until `verification.json` reports `"passed": true` on a native Windows machine.
