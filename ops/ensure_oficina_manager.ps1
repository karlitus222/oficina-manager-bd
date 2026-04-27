$ErrorActionPreference = "Stop"

function Test-PortListening {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listener = netstat -ano | Select-String (":$Port")
    return [bool]$listener
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pgBinDir = "C:\\Program Files\\PostgreSQL\\18\\bin"
$initdb = Join-Path $pgBinDir "initdb.exe"
$pgctl = Join-Path $pgBinDir "pg_ctl.exe"
$psql = Join-Path $pgBinDir "psql.exe"
$pgData = Join-Path $repoRoot ".pgdata_dev"
$pgPort = 55432
$webPort = 5000

if (-not (Test-Path -LiteralPath $pgData)) {
    & $initdb -D $pgData -U postgres -A trust --encoding=UTF8 --no-instructions | Out-Null
}

if (-not (Test-PortListening -Port $pgPort)) {
    & $pgctl -D $pgData -o "-p $pgPort" -l (Join-Path $pgData "server.log") -w start | Out-Null
}

$databaseExists = (& $psql -p $pgPort -U postgres -d postgres -t -A -c "SELECT 1 FROM pg_database WHERE datname = 'oficina_db';").Trim()
if ($databaseExists -ne "1") {
    & $psql -p $pgPort -U postgres -d postgres -f (Join-Path $repoRoot "ddl\\00_create_database.sql") | Out-Null
    & $psql -p $pgPort -U postgres -d oficina_db -f (Join-Path $repoRoot "ddl\\01_create_schema.sql") | Out-Null
    & $psql -p $pgPort -U postgres -d oficina_db -f (Join-Path $repoRoot "dml\\01_seed_data.sql") | Out-Null
}

if (-not (Test-PortListening -Port $webPort)) {
    Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", (Join-Path $repoRoot "ops\\start_oficina_manager_web.ps1")
        ) `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden | Out-Null
}
