$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ensureScript = Join-Path $repoRoot "ops\\ensure_oficina_manager.ps1"
$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ensureScript`""
$startupDir = [Environment]::GetFolderPath("Startup")
$startupLauncher = Join-Path $startupDir "OficinaManager-Ensure.cmd"
$launcherContent = @(
    "@echo off",
    "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File ""$ensureScript"""
)

Set-Content -LiteralPath $startupLauncher -Value $launcherContent -Encoding ASCII
schtasks /Create /F /SC MINUTE /MO 5 /TN "OficinaManager-Ensure-Recurring" /TR $taskCommand | Out-Null

Write-Output "Automacoes locais criadas:"
Write-Output "- OficinaManager-Ensure-Recurring"
Write-Output "- Startup: $startupLauncher"
