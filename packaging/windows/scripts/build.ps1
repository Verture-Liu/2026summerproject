param(
    [string]$Python = "py",
    [string]$Iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Packaging = Join-Path $Root "packaging\windows"
$Build = Join-Path $Root "build\windows"
$Cache = Join-Path $Build "cache"
$Downloads = Join-Path $Cache "downloads"
$Built = Join-Path $Cache "built"
$AppStage = Join-Path $Build "app"
$Dist = Join-Path $Root "dist"
$StagePath = Join-Path $Root "windows-build-stage.txt"
$ManifestPath = Join-Path $Packaging "tool-sources.json"
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force $Downloads, $Built, $Dist | Out-Null
"running: Prepare pinned assets" | Set-Content -Encoding ASCII $StagePath

function Invoke-Native([string]$Label, [scriptblock]$Command) {
    Write-Host "==> $Label"
    "running: $Label" | Set-Content -Encoding ASCII $StagePath
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Command
        $ExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
    if ($null -ne $ExitCode -and $ExitCode -ne 0) {
        Write-Host "::error::$Label failed with exit code $ExitCode"
        throw "$Label failed with exit code $ExitCode"
    }
    "completed: $Label" | Set-Content -Encoding ASCII $StagePath
}

function Get-PinnedAsset($Name, $Item) {
    $Destination = Join-Path $Downloads $Item.archive
    if (-not (Test-Path $Destination)) {
        Write-Host "Downloading $Name $($Item.version)"
        Invoke-WebRequest -Uri $Item.url -OutFile $Destination
    }
    $Actual = (Get-FileHash -Algorithm SHA256 $Destination).Hash.ToLowerInvariant()
    if ($Actual -ne $Item.sha256) {
        throw "SHA-256 mismatch for $Name. Expected $($Item.sha256), got $Actual"
    }
}

foreach ($Property in $Manifest.tools.PSObject.Properties) {
    if ($Property.Value.strategy -ne "msys2-package") {
        Get-PinnedAsset $Property.Name $Property.Value
    }
}
foreach ($Property in $Manifest.runtimes.PSObject.Properties) { Get-PinnedAsset $Property.Name $Property.Value }

$Venv = Join-Path $Build "venv"
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    if ($Python -eq "py") {
        Invoke-Native "Create Python virtual environment" { & py -3.13 -m venv $Venv }
    } else {
        Invoke-Native "Create Python virtual environment" { & $Python -m venv $Venv }
    }
}
$VenvPython = Join-Path $Venv "Scripts\python.exe"
Invoke-Native "Upgrade pip" { & $VenvPython -m pip install --upgrade pip }
Invoke-Native "Install Python build dependencies" { & $VenvPython -m pip install $Root pyinstaller (Join-Path $Downloads $Manifest.tools.multiqc.archive) }

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Build "backend-dist"), (Join-Path $Build "multiqc-dist")
Invoke-Native "Freeze PaleoRigor backend" { & $VenvPython -m PyInstaller --noconfirm --clean --distpath (Join-Path $Build "backend-dist") --workpath (Join-Path $Build "backend-work") (Join-Path $Packaging "backend.spec") }
Invoke-Native "Freeze MultiQC" { & $VenvPython -m PyInstaller --noconfirm --clean --distpath (Join-Path $Build "multiqc-dist") --workpath (Join-Path $Build "multiqc-work") (Join-Path $Packaging "multiqc.spec") }
Copy-Item -Recurse -Force (Join-Path $Build "multiqc-dist\multiqc") (Join-Path $Built "multiqc")

$FastqcBuilt = Join-Path $Built "fastqc"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $FastqcBuilt
Expand-Archive -Force (Join-Path $Downloads $Manifest.tools.fastqc.archive) $FastqcBuilt
$FastqcCommand = Join-Path $FastqcBuilt "FastQC\fastqc.cmd"
'@echo off' + "`r`n" + 'set "HERE=%~dp0"' + "`r`n" + 'for /d %%D in ("%HERE%..\..\..\runtimes\java\*") do set "JAVA_HOME=%%~fD"' + "`r`n" + 'pushd "%HERE%"' + "`r`n" + '"%JAVA_HOME%\bin\java.exe" -Xmx250m -classpath ".;htsjdk.jar;jbzip2-0.9.jar;sam-1.103.jar;cisd-jhdf5.jar" uk.ac.babraham.FastQC.FastQCApplication %*' + "`r`n" + 'set "CODE=%ERRORLEVEL%"' + "`r`n" + 'popd' + "`r`n" + 'exit /b %CODE%' | Set-Content -Encoding ASCII $FastqcCommand

$BowtieBuilt = Join-Path $Built "bowtie2"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $BowtieBuilt
Expand-Archive -Force (Join-Path $Downloads $Manifest.tools.bowtie2.archive) $BowtieBuilt
$BowtieDirectory = Get-ChildItem $BowtieBuilt -Directory | Select-Object -First 1
'@echo off' + "`r`n" + 'call "%~dp0bowtie2.bat" %*' | Set-Content -Encoding ASCII (Join-Path $BowtieDirectory.FullName "bowtie2.cmd")

$MsysBash = "C:\msys64\usr\bin\bash.exe"
if (-not (Test-Path $MsysBash)) { throw "MSYS2 is required to prepare seqtk, bwa and samtools: $MsysBash" }
Invoke-Native "Build MSYS2 bioinformatics tools" { & $MsysBash (Join-Path $Packaging "scripts\build_msys2_tools.sh") $Cache }

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $AppStage
New-Item -ItemType Directory -Force $AppStage, (Join-Path $AppStage "backend") | Out-Null
Copy-Item -Recurse -Force (Join-Path $Build "backend-dist\PaleoRigorBackend\*") (Join-Path $AppStage "backend")
$ToolRoot = Join-Path $AppStage "backend\_internal\research_agent\tools"
Invoke-Native "Stage bundled tools" { & $VenvPython (Join-Path $Packaging "scripts\stage_tools.py") --cache $Cache --destination $ToolRoot --manifest $ManifestPath }

Invoke-Native "Publish Windows launcher" { & dotnet publish (Join-Path $Packaging "launcher\PaleoRigorLauncher.csproj") -c Release -o (Join-Path $Build "launcher") }
Copy-Item -Force (Join-Path $Build "launcher\PaleoRigor.exe") (Join-Path $AppStage "PaleoRigor.exe")

if (-not (Test-Path $Iscc)) { throw "Inno Setup 6 was not found at $Iscc" }
Invoke-Native "Compile Inno Setup installer" { & $Iscc "/DAppSource=$AppStage" "/DOutputDir=$Dist" (Join-Path $Packaging "installer\PaleoRigor.iss") }
$Installer = Join-Path $Dist "PaleoRigor-Setup.exe"
if (-not (Test-Path $Installer)) { throw "PaleoRigor-Setup.exe was not produced" }
Write-Host "Built $Installer"
