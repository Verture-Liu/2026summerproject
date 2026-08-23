# PaleoRigor macOS Phase 2 Application Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. This plan is executed inline without subagents at the user's request.

**Goal:** Produce an unsigned Apple Silicon `PaleoRigor.app` and development `.dmg` that run without VS Code, Python, Conda, Homebrew, Java, or bioinformatics tools installed by the user.

**Architecture:** A native Swift launcher owns lifecycle, creates a per-launch token file, starts a PyInstaller onedir backend on `127.0.0.1`, waits for authenticated health, and opens the browser. The app embeds seven tools beneath the backend resource root, a minimal Java runtime for FastQC, and a standalone MultiQC executable. Build scripts stage, inspect, checksum, assemble, ad-hoc sign, and smoke-test every artifact.

**Tech Stack:** Swift 6, Python 3.13, PyInstaller, FastAPI/Uvicorn, shell build scripts, `jlink`, `otool`, `install_name_tool`, `codesign`, and `hdiutil`.

## Global Constraints

- Target `arm64`, macOS 13.0 or later.
- Development artifacts are ad-hoc signed only; Developer ID signing and notarization belong to Phase 3.
- Bundle FastQC 0.12.1, MultiQC 1.35, SeqKit 2.13.0, SeqTk 1.5-r133, Samtools 1.23.1, BWA 0.7.19-r1273, and Bowtie2 2.5.5.
- Packaged execution must never use user `PATH`, Conda, Homebrew, or `PALEORIGOR_TOOL_ROOT`.
- Secrets must not appear in command-line arguments, logs, app resources, build manifests, or DMG contents.
- Do not modify manuscript, benchmark, raw-data, or user-result artifacts.

---

### Task 1: Reproducible packaging inventory and layout

**Files:**
- Create: `packaging/macos/tool-sources.json`
- Create: `packaging/macos/build_config.json`
- Create: `packaging/macos/scripts/audit_sources.py`
- Create: `tests/packaging/test_macos_packaging_contract.py`

**Interfaces:**
- `audit_sources.py --output <json>` records source path, version, architecture, SHA-256, and license source for every bundled component.
- App layout is `PaleoRigor.app/Contents/{MacOS,Resources,Frameworks}` with backend resources under `Contents/Resources/backend`.

- [ ] Write failing tests for exact versions, arm64 architecture, no credential-bearing paths, and required app layout fields.
- [ ] Implement inventory/config files and source audit.
- [ ] Run `pytest -q tests/packaging/test_macos_packaging_contract.py`.
- [ ] Commit `build: define macOS bundle inventory`.

### Task 2: Backend bundle and secure native-launch protocol

**Files:**
- Create: `packaging/macos/backend.spec`
- Create: `packaging/macos/backend_entry.py`
- Create: `packaging/macos/Launcher/main.swift`
- Modify: `src/research_agent/launcher.py`
- Modify: `tests/unit/test_launcher.py`
- Create: `tests/packaging/test_backend_bundle.py`

**Interfaces:**
- Backend accepts `--host 127.0.0.1`, `--port`, `--session-token-file`, and `--no-browser`.
- Token file must be mode `0600`, read once, deleted before serving, and never logged.
- Swift launcher selects a loopback port, writes the token file, launches the child, polls authenticated `/api/health`, opens `/#token=...`, and terminates the child on exit.

- [ ] Add failing launcher/token-file tests.
- [ ] Implement backend CLI and PyInstaller onedir spec.
- [ ] Implement and compile Swift launcher with deployment target 13.0.
- [ ] Verify backend starts from a temporary directory with empty `PATH`.
- [ ] Commit `build: add native launcher and frozen backend`.

### Task 3: Stage seven self-contained tools

**Files:**
- Create: `packaging/macos/scripts/stage_tools.py`
- Create: `packaging/macos/multiqc_entry.py`
- Create: `packaging/macos/multiqc.spec`
- Create: `packaging/macos/scripts/verify_macho.py`
- Create: `packaging/macos/licenses/README.md`
- Modify: `src/research_agent/resources/tool_manifest.json`
- Create: `tests/packaging/test_bundled_tools.py`

**Interfaces:**
- Tool commands live under `backend/_internal/research_agent/tools/bin`.
- FastQC wrapper uses bundled `tools/jre/bin/java` and bundled FastQC resources.
- MultiQC is a standalone PyInstaller executable.
- Mach-O validation rejects non-arm64 files and unresolved non-system dylibs.

- [ ] Add failing manifest, architecture, dylib, and wrapper tests.
- [ ] Stage SeqKit/SeqTk and tool-specific native executables/libraries.
- [ ] Build MultiQC and minimal Java runtime; stage FastQC.
- [ ] Generate checksums and license inventory.
- [ ] Run version and minimal fixture smokes with an empty `PATH`.
- [ ] Commit `build: bundle seven analysis tools`.

### Task 4: Assemble and ad-hoc sign `PaleoRigor.app`

**Files:**
- Create: `packaging/macos/Info.plist`
- Create: `packaging/macos/scripts/assemble_app.py`
- Create: `packaging/macos/scripts/sign_development.sh`
- Create: `tests/packaging/test_app_bundle.py`

**Interfaces:**
- Bundle identifier `org.paleorigor.app`; minimum system version `13.0`; executable `PaleoRigor`.
- Backend and tools are immutable app resources; user state remains in macOS Library directories.

- [ ] Add failing app-layout/plist/security tests.
- [ ] Assemble launcher, backend, tools, icons, licenses, and manifests.
- [ ] Ad-hoc sign nested Mach-O files from inside out and verify with `codesign --verify --deep --strict`.
- [ ] Launch from outside the repository with empty `PATH` and run authenticated About/config/tool checks.
- [ ] Commit `build: assemble development macOS application`.

### Task 5: Development DMG and release-gate smoke tests

**Files:**
- Create: `packaging/macos/scripts/create_dmg.sh`
- Create: `packaging/macos/scripts/smoke_app.py`
- Create: `packaging/macos/phase2-verification.json`
- Create: `tests/packaging/test_dmg_contents.py`

**Interfaces:**
- Output: `dist/macos/PaleoRigor.app` and `dist/macos/PaleoRigor-dev-arm64.dmg`.
- DMG contains the app and an Applications symlink; it contains no source tree, credentials, caches, or development paths.

- [ ] Build the DMG and mount it read-only.
- [ ] Verify bundle architecture, signatures, tool versions, checksums, loopback binding, lifecycle, and representative FASTQ/FASTA/BAM smokes.
- [ ] Scan app/DMG for API keys, session tokens, `.env`, `__pycache__`, absolute developer paths, and unexpected writable files.
- [ ] Record exact hashes, sizes, versions, tests, and deferred Phase 3 signing/notarization gates.
- [ ] Commit `build: create Apple Silicon development DMG`.

## Completion Gate

- [ ] All source and packaging tests pass.
- [ ] Seven tools report pinned versions and pass minimal offline smokes.
- [ ] `PaleoRigor.app` launches from `/Applications`-like temporary path with no development environment.
- [ ] Browser opens only after authenticated health succeeds and quitting terminates the backend.
- [ ] Ad-hoc signature and app/DMG integrity checks pass.
- [ ] No secret, developer path, Conda/Homebrew dependency, or unbundled non-system dylib remains.
- [ ] Phase 3 signing/notarization is not started.
