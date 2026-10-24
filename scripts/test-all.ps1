[CmdletBinding()]
param(
    [ValidateSet("isolated-test", "disposable-regression")]
    [string] $Target = "isolated-test"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot

if ($Target -cnotin @("isolated-test", "disposable-regression")) {
    Write-Host "[BACKEND INTEGRATION] SKIPPED: the requested database target is not approved."
    exit 2
}

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
}

if ($Target -eq "disposable-regression") {
    $requiredValues.AI_BAP_TEST_TARGET = "disposable-regression"
    $requiredValues.AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION = "disposable-regression-postgresql-acknowledged"
    $requiredValues.POSTGRES_HOST = "127.0.0.1"
    $requiredValues.POSTGRES_PORT = "55435"
    $requiredValues.POSTGRES_DB = "ai_bap_regression_20261024"
    $requiredValues.POSTGRES_USER = "ai_bap_regression_user_20261024"
    $testPasswordName = "AI_BAP_DISPOSABLE_TEST_POSTGRES_PASSWORD"
    $alembicTarget = [Environment]::GetEnvironmentVariable("AI_BAP_ALEMBIC_TARGET")
    if ($null -eq $alembicTarget) { $alembicTarget = "" }
    if ($alembicTarget -cnotin @("", "disposable-regression")) {
        Write-Host "[BACKEND INTEGRATION] SKIPPED: conflicting test and Alembic targets are not allowed."
        exit 2
    }
}
else {
    $requiredValues.AI_BAP_TEST_DATABASE_CONFIRMATION = "isolated-postgresql-acknowledged"
    $requiredValues.POSTGRES_HOST = "127.0.0.1"
    $requiredValues.POSTGRES_PORT = "55432"
    $requiredValues.POSTGRES_DB = "ai_bap_test"
    $requiredValues.POSTGRES_USER = "ai_bap_test_user"
    $testPasswordName = "AI_BAP_TEST_POSTGRES_PASSWORD"
    $testTarget = [Environment]::GetEnvironmentVariable("AI_BAP_TEST_TARGET")
    $alembicTarget = [Environment]::GetEnvironmentVariable("AI_BAP_ALEMBIC_TARGET")
    if ($null -eq $testTarget) { $testTarget = "" }
    if ($null -eq $alembicTarget) { $alembicTarget = "" }
    if ($testTarget -cnotin @("", "isolated-test") -or
        $alembicTarget -cnotin @("", "isolated-test")) {
        Write-Host "[BACKEND INTEGRATION] SKIPPED: conflicting test target selectors are not allowed."
        exit 2
    }
}

$missingOrUnsafe = @(
    $requiredValues.GetEnumerator() | Where-Object {
        [Environment]::GetEnvironmentVariable($_.Key) -cne $_.Value
    }
)
$testPassword = [Environment]::GetEnvironmentVariable($testPasswordName)
$configuredPassword = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")

if ($missingOrUnsafe.Count -gt 0 -or [string]::IsNullOrWhiteSpace($testPassword) -or $configuredPassword -cne $testPassword -or
    [Environment]::GetEnvironmentVariable("DATABASE_URL")) {
    Write-Host "[BACKEND INTEGRATION] SKIPPED: an explicitly confirmed isolated PostgreSQL test environment is required."
    Write-Host "Follow docs/isolated-test-database.md, select one documented target, and set its process-scoped test variables."
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
