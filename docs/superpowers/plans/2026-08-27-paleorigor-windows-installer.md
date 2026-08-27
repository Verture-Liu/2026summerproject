# PaleoRigor Windows Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the source, automation and installer definition needed to produce a self-contained `PaleoRigor-Setup.exe` on Windows 10/11 x64 while retaining the existing macOS package.

**Architecture:** Make the shared runtime choose platform-correct user directories and credential storage, then create an isolated `packaging/windows` pipeline that freezes the backend, stages seven pinned tools, builds a small launcher, and compiles an Inno Setup installer. Platform-neutral contracts run on macOS; GitHub Actions and the user's Windows PC perform native build and release-gate checks.

**Tech Stack:** Python 3.13, pytest, PyInstaller, PowerShell, C#/.NET launcher, Inno Setup 6, GitHub Actions.

## Global Constraints

- Preserve `packaging/macos/` and `paleorigor/PaleoRigor-dev-arm64.dmg` unchanged.
- Target Windows 10/11 x64; defer Windows ARM64.
- Bundle FastQC, MultiQC, SeqKit, SeqTk, Samtools, BWA and Bowtie2 plus required runtimes.
- Do not require VS Code, Python, Conda, Java, WSL or internet downloads at first launch.
- Bind the backend only to `127.0.0.1`; never put API keys in source, installer, logs or command lines.
- Do not claim Windows compatibility until the native release gate succeeds.
- Do not commit downloaded archives or generated build trees.

---

### Task 1: Platform-correct runtime paths and secret-store selection

**Files:**
- Modify: `src/research_agent/runtime/paths.py`
- Modify: `src/research_agent/runtime/secrets.py`
- Modify: `src/research_agent/launcher.py`
- Modify: `tests/unit/test_runtime_paths.py`
- Modify: `tests/unit/test_secrets.py`
- Modify: `tests/unit/test_launcher.py`

**Interfaces:**
- Produces: `AppPaths.for_runtime(..., platform_name: str | None = None)`
- Produces: `WindowsCredentialSecretStore`
- Produces: `secret_store_for_platform(platform_name: str | None = None) -> SecretStore`

- [ ] Write failing tests for Windows LocalAppData paths, Credential Manager command contracts and launcher store selection.
- [ ] Run the three unit-test files and confirm failures are caused by missing Windows support.
- [ ] Implement platform selection without changing macOS defaults.
- [ ] Re-run tests and commit the passing runtime change.

### Task 2: Windows packaging contracts and manifests

**Files:**
- Create: `packaging/windows/build_config.json`
- Create: `packaging/windows/tool-sources.json`
- Create: `packaging/windows/licenses/README.md`
- Create: `tests/packaging/test_windows_packaging_contract.py`

**Interfaces:**
- Produces: pinned Windows build configuration consumed by all build scripts.
- Produces: seven-entry tool-source manifest with version, URL, archive name and checksum field.

- [ ] Write failing contract tests for architecture, application layout, seven tool IDs, HTTPS sources, checksum shape and absence of credentials.
- [ ] Run the contract test and observe missing-file failures.
- [ ] Add the minimal configuration and manifest.
- [ ] Re-run the test and commit.

### Task 3: Deterministic tool staging and verification

**Files:**
- Create: `packaging/windows/scripts/stage_tools.py`
- Create: `packaging/windows/scripts/verify_bundle.py`
- Create: `tests/packaging/test_windows_stage_tools.py`

**Interfaces:**
- Produces: `sha256(path: Path) -> str`
- Produces: `safe_extract_zip(archive: Path, destination: Path) -> None`
- Produces: `stage_from_cache(cache: Path, destination: Path, manifest: dict) -> Path`
- Produces: a normalized `tools/bin` command directory and `manifest.json`.

- [ ] Write failing tests using tiny fixture archives, including traversal rejection and missing-tool diagnostics.
- [ ] Run tests and confirm expected failures.
- [ ] Implement checksum checking, safe extraction, command staging and manifest generation.
- [ ] Re-run tests and commit.

### Task 4: Frozen backend and Windows launcher

**Files:**
- Create: `packaging/windows/backend_entry.py`
- Create: `packaging/windows/backend.spec`
- Create: `packaging/windows/launcher/PaleoRigorLauncher.cs`
- Create: `packaging/windows/launcher/PaleoRigorLauncher.csproj`
- Create: `tests/packaging/test_windows_launcher_contract.py`

**Interfaces:**
- Backend consumes `--session-token-file` and launches the existing loopback-only service.
- Launcher starts `backend/PaleoRigorBackend.exe`, waits for `/api/health`, opens the browser, and deletes temporary token material.

- [ ] Write failing source-contract tests for loopback binding, random token creation, AppData use, health timeout, process cleanup and shell-safe process arguments.
- [ ] Run tests and confirm missing source failures.
- [ ] Add the backend entry/spec and focused C# launcher.
- [ ] Re-run tests and commit.

### Task 5: Build scripts, installer and native verification

**Files:**
- Create: `packaging/windows/scripts/build.ps1`
- Create: `packaging/windows/scripts/smoke_test.ps1`
- Create: `packaging/windows/installer/PaleoRigor.iss`
- Create: `tests/packaging/test_windows_installer_contract.py`

**Interfaces:**
- `build.ps1` produces `dist/PaleoRigor-Setup.exe` from a clean checkout.
- `smoke_test.ps1` writes `verification.json` and `SHA256SUMS.txt` only after required checks pass.

- [ ] Write failing contract tests for per-user installation, shortcuts, uninstall behavior, no first-launch downloads and verification output.
- [ ] Run tests and confirm missing source failures.
- [ ] Implement deterministic PowerShell orchestration and Inno Setup definition.
- [ ] Re-run tests and commit.

### Task 6: CI, documentation and regression gate

**Files:**
- Create: `.github/workflows/windows-build.yml`
- Create: `packaging/windows/README.md`
- Modify: `paleorigor/README.md`
- Modify: `.gitignore`
- Create: `tests/packaging/test_windows_release_docs.py`

**Interfaces:**
- CI uploads an unsigned development installer artifact without publishing a release.
- Windows README provides exact clean-build and native verification commands.

- [ ] Write failing tests for documented prerequisites, SmartScreen disclosure, seven tools, build commands and retained macOS links.
- [ ] Run tests and confirm failures.
- [ ] Add CI, documentation and generated-output ignore rules.
- [ ] Run Windows packaging tests, runtime tests and the complete existing suite.
- [ ] Confirm macOS artifact checksum is unchanged.
- [ ] Commit and push only the scoped Windows/runtime/documentation changes.

## Native Windows handoff

After the repository is pulled on the user's Windows 10/11 x64 computer:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./packaging/windows/scripts/build.ps1
./packaging/windows/scripts/smoke_test.ps1 -Installer ./dist/PaleoRigor-Setup.exe
```

The Windows build is considered complete only when `smoke_test.ps1` exits with code 0 and produces a verification report covering installation, startup, seven tool identities, CSV workflow, FASTQ workflow, shutdown, cleanup and uninstall.
