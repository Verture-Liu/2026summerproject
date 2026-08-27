# PaleoRigor desktop research prototypes

PaleoRigor is a local, browser-based research agent for reproducible
paleomicrobiome and ancient-DNA data analysis. This folder contains the first
Apple Silicon development build. Windows 10/11 x64 packaging source is also
available; its installer remains a separate artifact so the macOS build is
preserved.

## Platforms

- macOS: `PaleoRigor-dev-arm64.dmg` for Apple Silicon and macOS 13 or later.
- Windows: `PaleoRigor-Setup.exe` for Windows 10/11 x64, produced by the
  native Windows build workflow after verification.

## Download

- `PaleoRigor-dev-arm64.dmg`
- Version: `0.2.0-dev`
- Target: Apple Silicon (M-series Macs), macOS 13 or later

## Install and open

1. Download and open `PaleoRigor-dev-arm64.dmg`.
2. Drag `PaleoRigor.app` into the Applications folder.
3. On first launch, Control-click the app, choose **Open**, and confirm **Open**
   again if macOS reports that the developer cannot be verified.
4. PaleoRigor starts its local backend and opens the browser interface.
5. Enter the model API configuration in the web interface. API keys are stored
   in macOS Keychain and are not included in this repository.

On Windows, the same local browser interface is opened from the Start-menu or
desktop shortcut. API keys are stored through Windows Credential Manager. See
`../packaging/windows/README.md` for the build and native verification guide.

## Bundled tools

- FastQC 0.12.1
- MultiQC 1.35
- SeqKit 2.13.0
- SeqTk 1.5-r133
- Samtools 1.23.1
- BWA 0.7.19-r1273
- Bowtie2 2.5.5

The application does not require users to install VS Code, Python, Conda,
Homebrew, Java, or these seven analysis tools.

## Verification

The development build passed the project test suite, strict ad-hoc signature
verification, read-only DMG mounting, authenticated local API checks, bundled
tool checks, and native launcher lifecycle checks. See
`../packaging/macos/phase2-verification.json` for the recorded release gate.

Verify the downloaded image with:

```bash
shasum -a 256 PaleoRigor-dev-arm64.dmg
```

The expected value is listed in `SHA256SUMS.txt`.

## Development-build limitation

This build is ad-hoc signed but is not yet signed with an Apple Developer ID or
notarized by Apple. It is suitable for local development and limited testing.
Formal public distribution requires Developer ID signing and notarization.

The Windows development installer is likewise unsigned and may trigger Windows
SmartScreen. Neither prototype should be described as a commercial release.
