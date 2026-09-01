param([string]$Installer = ".\dist\PaleoRigor-Setup.exe")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Installer = (Resolve-Path $Installer).Path
if ((Split-Path $Installer -Leaf) -ne "PaleoRigor-Setup.exe") { throw "Expected PaleoRigor-Setup.exe" }
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Output = Join-Path $Root "paleorigor\windows"
$SmokeRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$Install = Join-Path $SmokeRoot ("pr-" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
$InstallLog = Join-Path $env:TEMP ("PaleoRigor-install-" + [Guid]::NewGuid().ToString("N") + ".log")
New-Item -ItemType Directory -Force $Output | Out-Null
$Checks = [ordered]@{ installer = $false; seven_tools = $false; backend_health = $false; uninstall = $false }
$Backend = $null

try {
    $InstallArguments = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/DIR=`"$Install`"", "/LOG=`"$InstallLog`"")
    $InstallProcess = Start-Process $Installer -ArgumentList $InstallArguments -Wait -PassThru
    if ($InstallProcess.ExitCode -ne 0 -or -not (Test-Path (Join-Path $Install "PaleoRigor.exe"))) {
        $LogTail = if (Test-Path $InstallLog) { (Get-Content $InstallLog -Tail 30) -join " | " } else { "installer log missing" }
        throw "Silent install failed (exit $($InstallProcess.ExitCode)): $LogTail"
    }
    $Checks.installer = $true

    $ToolRoot = Join-Path $Install "backend\_internal\research_agent\tools"
    $Tools = @("fastqc", "multiqc", "seqkit", "seqtk", "samtools", "bwa", "bowtie2")
    foreach ($Tool in $Tools) {
        if (-not (Test-Path (Join-Path $ToolRoot "bin\$Tool.cmd"))) { throw "Missing tool wrapper: $Tool" }
    }
    $Checks.seven_tools = $true

    $Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $Listener.Start(); $Port = ([System.Net.IPEndPoint]$Listener.LocalEndpoint).Port; $Listener.Stop()
    $Token = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    $TokenFile = Join-Path $Install "smoke.token"
    [IO.File]::WriteAllText($TokenFile, $Token)
    $BackendPath = Join-Path $Install "backend\PaleoRigorBackend.exe"
    $Backend = Start-Process $BackendPath -ArgumentList "--no-browser", "--port", "$Port", "--session-token-file", $TokenFile -PassThru
    $Headers = @{ "X-PaleoRigor-Token" = $Token }
    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 120; $Attempt++) {
        try { if ((Invoke-WebRequest "http://127.0.0.1:$Port/api/health" -Headers $Headers -UseBasicParsing).StatusCode -eq 200) { $Ready = $true; break } } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $Ready) { throw "backend_health check failed" }
    $Checks.backend_health = $true
    Stop-Process -Id $Backend.Id -Force; $Backend = $null

    $Uninstaller = Join-Path $Install "unins000.exe"
    $UninstallProcess = Start-Process $Uninstaller -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART" -Wait -PassThru
    if ($UninstallProcess.ExitCode -ne 0) { throw "Uninstall failed" }
    $Checks.uninstall = $true
}
finally {
    if ($null -ne $Backend -and -not $Backend.HasExited) { Stop-Process -Id $Backend.Id -Force }
    $Report = [ordered]@{ platform = "windows-x64"; passed = -not ($Checks.Values -contains $false); checks = $Checks }
    $Report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Output "verification.json")
    $Hash = (Get-FileHash -Algorithm SHA256 $Installer).Hash.ToLowerInvariant()
    "$Hash  PaleoRigor-Setup.exe" | Set-Content -Encoding ASCII (Join-Path $Output "SHA256SUMS.txt")
}

if ($Checks.Values -contains $false) { exit 1 }
Write-Host "Windows release-gate checks passed."
