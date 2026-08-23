# PaleoRigor macOS Apple Silicon Application Design

**Date:** 2026-08-23

**Status:** Approved design for implementation planning

**Target:** Apple Silicon Macs (M-series), macOS 13 Ventura or later

**Distribution:** Signed and notarized `.dmg`

## 1. Objective

Package the existing PaleoRigor research agent as a beginner-friendly macOS application. A user must be able to download a disk image, drag `PaleoRigor.app` into Applications, launch it by double-clicking, enter an API key, and run supported analyses without installing VS Code, Python, Conda, Homebrew, Java, or command-line bioinformatics tools.

The application remains local-first. Uploaded research data, generated workflows, intermediate outputs, final outputs, and audit records stay on the user's Mac. Only the text and metadata required for workflow planning are sent to the configured model API under the existing planner behavior.

## 2. User Experience

1. The user downloads and opens `PaleoRigor.dmg`.
2. The user drags `PaleoRigor.app` into Applications.
3. On first launch, the application displays the macOS-standard trust and privacy prompts associated with a signed and notarized application.
4. PaleoRigor starts its backend on `127.0.0.1` using an available ephemeral port.
5. The default browser opens the local PaleoRigor interface automatically.
6. The first-run page asks for the model API base URL, model identifier, and API key.
7. The API key is stored in macOS Keychain. It is never written to `.env`, logs, exported records, crash reports, or workflow JSON.
8. The user uploads files, enters a natural-language request, reviews the proposed workflow, chooses a result destination, and starts local execution.
9. Progress is shown for planning, validation, execution steps, export, and completion.
10. Closing PaleoRigor stops the local backend. The application does not remain as a hidden background service.

## 3. Architecture

### 3.1 Native launcher

A small macOS launcher owns the application lifecycle. It performs the following duties:

- establishes application-specific writable directories;
- loads non-secret preferences;
- retrieves secrets from macOS Keychain;
- starts the bundled PaleoRigor backend as a child process;
- waits for a successful local health check;
- opens the browser only after the backend is ready;
- displays a clear native error if startup fails;
- terminates the backend when the application exits.

The launcher binds the backend only to `127.0.0.1`. It must not expose the service on the local network.

### 3.2 Bundled backend

The existing FastAPI application, workflow planner, validator, executor, exporter, Skills registry, and web assets are packaged with an isolated Python runtime. PyInstaller is the initial packaging mechanism because it can preserve the existing Python application while producing a self-contained executable for Apple Silicon.

No runtime code may assume the repository layout, current working directory, Conda prefix, Homebrew prefix, or developer `.venv`. Resource discovery must resolve paths relative to the signed application bundle and writable user-data directory.

### 3.3 Browser interface

The existing HTML, CSS, and JavaScript interface remains the primary user interface. The native application opens a URL such as `http://127.0.0.1:<ephemeral-port>/`. A random session token is required for browser-to-backend requests so that unrelated local pages cannot invoke the backend merely by guessing its port.

The interface must provide:

- first-run API configuration;
- API connection test with redacted errors;
- file upload and detected file-type summary;
- natural-language task entry;
- workflow review and explicit execution approval;
- step-level progress and failure status;
- result-folder selection;
- links for final outputs, step outputs, and audit records;
- Chinese and English language selection;
- an About page with version, license, GitHub link, and bundled-tool versions.

### 3.4 Application data

Writable application state is stored outside the signed `.app` bundle:

- preferences and non-secret configuration: `~/Library/Application Support/PaleoRigor/`;
- logs: `~/Library/Logs/PaleoRigor/`;
- temporary task data: `~/Library/Caches/PaleoRigor/`;
- secrets: macOS Keychain;
- user-selected analysis results: the destination chosen in the interface.

Temporary task data is retained after a successful run only when required for audit records or when the user requests retention. Failed installation or startup attempts must not create analysis-result folders.

## 4. Bundled Analysis Tools

The first release includes native Apple Silicon builds or compatible self-contained distributions of:

1. FastQC;
2. MultiQC;
3. SeqKit;
4. SeqTk;
5. Samtools;
6. BWA;
7. Bowtie2.

A minimal Java runtime required by FastQC is included. Every bundled executable, shared library, license, version, and upstream source URL is recorded in a machine-readable tool manifest and displayed in the About page.

Tool execution uses explicit absolute paths supplied by the application tool resolver. It must not depend on the user's `PATH`, active shell, Conda environment, or Homebrew installation. Child processes receive a controlled environment and write only inside the current task workspace or selected output destination.

Tools not included in the first release, including mapDamage, Kraken2, MetaPhlAn, and MEGAHIT, remain available through existing Skills where applicable. Before planning or execution, PaleoRigor reports that the external tool is unavailable, identifies the required version or command, and provides installation guidance. The application does not silently install these tools.

## 5. Output Contract

Each successful run creates one timestamped result directory in the user-selected destination:

```text
PaleoRigor_Result_<timestamp>_<task-id>/
├── final_outputs/
├── step_outputs/
└── PaleoRigor Records/
```

- `final_outputs/` contains only files explicitly requested by the user or designated as final workflow outputs.
- `step_outputs/` contains intermediate files grouped by workflow step.
- `PaleoRigor Records/` contains the workflow, validation result, parameters, tool versions, file checksums, execution status, warnings, errors, and provenance needed to audit the run.

If local execution fails before producing a valid final result, the selected destination must not contain a misleading final result directory. Failure diagnostics remain in the application log and recoverable task cache, with an explicit option to export a diagnostic bundle.

## 6. Security and Privacy

- Bind only to the loopback interface.
- Require a random per-launch session token.
- Store API keys only in macOS Keychain.
- Redact credentials, authorization headers, and sensitive configuration values from logs and exports.
- Validate uploaded paths and generated output paths against allowed roots.
- Execute only registered Skills and declared bundled tools.
- Preserve the existing workflow review and explicit local-execution approval step.
- Do not add telemetry in the first release.
- Do not upload research files to a PaleoRigor-controlled server.

## 7. Packaging and Distribution

The build pipeline produces an `arm64` application bundle and disk image. It performs these stages:

1. create a clean, pinned Python build environment;
2. build or acquire pinned Apple Silicon tool artifacts;
3. verify tool checksums and licenses;
4. package the Python backend and static web assets with PyInstaller;
5. assemble the native launcher, backend, tools, Java runtime, manifests, icons, and licenses into `PaleoRigor.app`;
6. codesign nested binaries and the application with hardened runtime enabled;
7. create `PaleoRigor.dmg`;
8. notarize the disk image with Apple;
9. staple the notarization ticket;
10. verify installation and launch on a clean Apple Silicon Mac account.

The initial release supports Apple Silicon Macs running macOS 13 Ventura or later. This minimum deployment version is written into the build configuration, release notes, and application metadata and is covered by the compatibility test matrix.

## 8. Error Handling

Errors are divided into user-correctable and application failures.

User-correctable errors include invalid API credentials, unsupported input formats, missing required files, unavailable non-bundled tools, insufficient disk space, and unwritable output destinations. They receive a plain-language message and a concrete corrective action.

Application failures include backend startup failure, corrupted bundled resources, failed tool-integrity checks, and unexpected executor exceptions. They receive a stable error identifier, a redacted explanation, and an option to export a diagnostic bundle. Tracebacks and secrets are not displayed in the browser.

## 9. Verification and Release Gates

The first public Mac build is releasable only when all of the following pass:

- existing unit and integration tests;
- Skills registry and workflow-validation tests;
- executable discovery tests with an empty user `PATH`;
- version checks for all seven bundled tools and Java;
- FastQC and MultiQC smoke test on the existing minimal FASTQ fixture;
- SeqKit and SeqTk smoke tests on a minimal FASTA fixture;
- Samtools smoke test on a minimal BAM fixture;
- BWA and Bowtie2 indexing and alignment smoke tests on minimal fixtures;
- API-key create, retrieve, replace, and delete tests against macOS Keychain;
- browser session-token rejection tests;
- output-directory success and failure-cleanup tests;
- first-launch, repeated-launch, port-conflict, and shutdown tests;
- Chinese and English interface checks;
- Gatekeeper assessment, codesign verification, notarization verification, and clean-account installation test;
- manual end-to-end run of representative FASTQ, FASTA, and peptide CSV workflows.

## 10. Scope Boundaries

The first release does not include:

- Intel Mac support;
- Windows support;
- cloud execution or server-side data storage;
- automatic installation of missing large tools;
- automatic updates;
- multi-user accounts;
- telemetry or usage analytics;
- a native replacement for the browser interface.

Windows packaging will reuse the agent core, Skills, web interface, workflow contracts, fixtures, and most tests. It will have a separate launcher, credential-store adapter, bundled executable set, installer, code-signing process, and platform-specific QA plan.

## 11. Acceptance Criteria

The design is satisfied when a new Apple Silicon Mac user can install the signed application, configure an API key, run a supported workflow using bundled tools, inspect progress, receive the documented output structure, quit cleanly, and repeat the process without installing any development or command-line environment.
