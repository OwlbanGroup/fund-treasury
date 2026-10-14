<#
.SYNOPSIS
    One-command runner for the Fund Treasury backend.

.DESCRIPTION
    Starts uvicorn with sensible dev defaults. Set -Test to run the test-suite
    instead of the server.

.EXAMPLE
    .\run.ps1          # start the API on http://127.0.0.1:8000
    .\run.ps1 -Test    # run pytest instead
#>
param(
    [switch]$Test,
    [string]$Port = "8000"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Dev defaults; copy .env.example to .env to override.
if (-not $env:KYRIBA_MODE)  { $env:KYRIBA_MODE  = "mock" }
if (-not $env:BANK_MODE)    { $env:BANK_MODE    = "mock" }
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = "sqlite:///./treasury.db" }

if ($Test) {
    python -m pytest
    exit $LASTEXITCODE
}

Write-Output "Starting Fund Treasury API on http://127.0.0.1:$Port (docs at /docs)"
python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
