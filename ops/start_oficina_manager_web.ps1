$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$srcDir = Join-Path $repoRoot "src"
$python = Join-Path $repoRoot ".venv\\Scripts\\python.exe"

$env:DATABASE_URL = "postgresql://postgres@localhost:55432/oficina_db"
$env:SECRET_KEY = "dev-local-key"
$env:PORT = "5000"
$env:FLASK_DEBUG = "0"
$env:FLASK_USE_RELOADER = "0"

Set-Location $srcDir
& $python -m waitress --host=127.0.0.1 --port=5000 app:app
