# PaleoRigor Windows Installer Design

Date: 2026-08-27

## Objective

Add a Windows distribution of PaleoRigor while preserving the existing Apple Silicon macOS application. A Windows user should install PaleoRigor through `PaleoRigor-Setup.exe`, launch it from the Start menu or desktop, and use the existing local browser interface without separately installing Python, Conda, Java, Skills, or the seven supported command-line tools.

The first release is a research prototype for Windows 10/11 x64. It is not a signed commercial release and will not claim support until the native Windows verification checklist passes.

## Distribution layout

The existing macOS files remain unchanged. Windows sources and release files are isolated:

```text
packaging/
├── macos/                         # existing build
└── windows/
    ├── launcher/                  # Windows launcher source
    ├── installer/                 # Inno Setup definition
    ├── scripts/                   # staging, build and verification
    ├── licenses/                  # bundled-tool notices
    ├── backend.spec               # PyInstaller backend build
    ├── build_config.json          # versions and expected paths
    └── tool-sources.json          # provenance and checksums

paleorigor/
├── PaleoRigor-dev-arm64.dmg       # retained macOS artifact
├── windows/                       # Windows release output
│   ├── PaleoRigor-Setup.exe
│   ├── SHA256SUMS.txt
│   └── verification.json
└── README.md
```

Large generated build directories and downloaded archives remain excluded from Git. The installer may be published as a GitHub release asset if its size makes normal Git storage unsuitable.

## Runtime architecture

The Windows launcher will:

1. Locate the installed application resources.
2. Create a per-launch random authentication token in the user's local application-data directory.
3. Start the bundled PaleoRigor backend on the loopback interface only (`127.0.0.1`) using an available local port.
4. wait for the health endpoint;
5. open the existing browser interface;
6. stop the backend and remove temporary token material when the launcher exits.

User data, API configuration, logs and results remain outside `Program Files`. Secrets must use Windows Credential Manager or the existing encrypted/user-local abstraction; they must not be embedded in the executable, installer, repository or logs.

## Bundled analysis tools

The target bundle contains the same seven user-facing tools as the macOS research application:

- FastQC
- MultiQC
- SeqKit
- SeqTk
- Samtools
- BWA
- Bowtie2

Each tool must have an explicit Windows x64 source URL, version, license notice and SHA-256 digest. Native Windows releases are preferred. Where an upstream project does not publish a supported Windows binary, the build must use a documented compatible distribution or mark the tool unavailable; it must not silently substitute a different analysis. Tool discovery will prioritize bundled executables, then retain the current managed-environment fallback for developer runs.

The installer will not depend on VS Code, Python, Conda, Homebrew, WSL or a system Java installation. Any runtime required by a bundled tool must be staged inside the application directory.

## Installer

Inno Setup will generate `PaleoRigor-Setup.exe`. The installer will:

- install per user by default, avoiding administrator privileges where possible;
- create Start-menu and optional desktop shortcuts;
- include an uninstaller;
- preserve user-created results during uninstall;
- show the research-prototype status and third-party notices;
- install the application and tool bundle without downloading components at first launch.

The first release may trigger a Windows SmartScreen warning because it will not initially have a commercial code-signing certificate. This limitation must be stated in the README rather than bypassed programmatically.

## Error handling

Startup failures must produce a readable local diagnostic instead of a blank browser page. The launcher distinguishes at least:

- missing or damaged bundled resource;
- backend startup timeout;
- occupied or unusable port;
- browser-open failure;
- tool identity/version mismatch;
- unwritable local application-data directory.

The application must never automatically install missing software from the internet. Verification failures stop the affected workflow and identify the missing or invalid component.

## Build and test strategy

Development follows test-first implementation. Platform-neutral tests run on macOS and in the existing Python test suite. Windows-specific tests run on a native Windows 10/11 x64 machine or GitHub Actions Windows runner.

Mac-side checks:

- configuration/schema validation;
- path and quoting unit tests using Windows path fixtures;
- launcher contract and cleanup logic tests where platform neutral;
- installer/source manifest completeness;
- existing project regression suite;
- confirmation that macOS packaging files and artifact remain unchanged.

Windows release gate:

1. build the backend and launcher from a clean checkout;
2. stage and checksum all seven tools;
3. compile `PaleoRigor-Setup.exe` with Inno Setup;
4. install on Windows 10 or 11 x64 without Python, Conda, Java or VS Code;
5. launch from desktop and Start menu;
6. confirm loopback-only binding, health check and browser opening;
7. confirm all seven commands report the expected identity/version;
8. run a small CSV workflow and a small FASTQ/FastQC workflow;
9. verify result export, shutdown, token cleanup and uninstall behavior;
10. generate `verification.json` and `SHA256SUMS.txt`.

No final Windows compatibility claim is made from macOS-only checks. The installer is uploaded to Git only after the native Windows release gate succeeds.

## Deliverables

- Windows packaging source under `packaging/windows/`;
- automated Windows build workflow;
- test suite for launcher/configuration/build contracts;
- Windows build and verification guide for the user's PC;
- installer and checksum after native verification;
- README update showing macOS and Windows as separate retained distributions.

## Explicitly deferred

- Windows ARM64;
- Microsoft Store distribution;
- commercial EV/code-signing certificate;
- automatic updates;
- cloud execution or server hosting;
- unattended system-wide installation;
- replacing browser UI with a native desktop UI.
