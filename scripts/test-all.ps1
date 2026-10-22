[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Invoke-TestPhase {
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter(Mandatory)] [scriptblock] $Action
    )

    Write-Host "[$Name] START"
    & $Action
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[$Name] FAIL"
        exit $LASTEXITCODE
    }
    Write-Host "[$Name] PASS"
}

Push-Location (Join-Path $repositoryRoot "frontend")
try {
    Invoke-TestPhase -Name "FRONTEND" -Action { npm run test -- --run }
}
finally {
    Pop-Location
}

$requiredValues = @{
    AI_BAP_TEST_MODE = "true"
    AI_BAP_TEST_DATABASE_CONFIRMATION = "isolated-postgresql-acknowledged"
    POSTGRES_HOST = "127.0.0.1"
    POSTGRES_PORT = "55432"
    POSTGRES_DB = "ai_bap_test"
    POSTGRES_USER = "ai_bap_test_user"
}
$missingOrUnsafe = @(
    $requiredValues.GetEnumerator() | Where-Object {
        [Environment]::GetEnvironmentVariable($_.Key) -ne $_.Value
    }
)
$testPassword = [Environment]::GetEnvironmentVariable("AI_BAP_TEST_POSTGRES_PASSWORD")
$configuredPassword = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")

if ($missingOrUnsafe.Count -gt 0 -or [string]::IsNullOrWhiteSpace($testPassword) -or $configuredPassword -ne $testPassword) {
    Write-Host "[BACKEND INTEGRATION] SKIPPED: an explicitly confirmed isolated PostgreSQL test environment is required."
    Write-Host "Follow docs/isolated-test-database.md, set the documented test-only environment variables, and rerun this script."
    exit 2
}

Push-Location (Join-Path $repositoryRoot "backend")
try {
    Invoke-TestPhase -Name "BACKEND INTEGRATION" -Action { uv run --no-sync pytest -q --tb=short }
}
finally {
    Pop-Location
}

Write-Host "[TEST-ALL] PASS"
