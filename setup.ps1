# Setup script for Windows using uv
# This script sets up the Python environment and installs dependencies for FLM testing
#
# Behavior:
# - If pyproject.toml exists, use the uv project workflow: `uv sync`
# - Else, if requirements.txt exists, create/use a virtual environment and sync it with `uv pip sync`
# - Supports -Force to recreate the environment

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up FLM test environment for Windows with uv..." -ForegroundColor Green

function Fail($Message) {
    Write-Host "Error: $Message" -ForegroundColor Red
    exit 1
}

function Warn($Message) {
    Write-Host "Warning: $Message" -ForegroundColor Yellow
}

# Check if uv is available
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    Fail "uv is not installed or not in PATH. Install it first, e.g. with 'winget install --id=astral-sh.uv -e' or the official PowerShell installer."
}

try {
    $uvVersion = uv --version
    Write-Host "Using $uvVersion"
} catch {
    Fail "uv was found, but 'uv --version' failed."
}

$projectFile = "pyproject.toml"
$requirementsFile = "requirements.txt"
$venvPath = "venv"

# Project-style workflow: prefer pyproject.toml if present
if (Test-Path $projectFile) {
    if ($Force -and (Test-Path $venvPath)) {
        Write-Host "Removing existing virtual environment at $venvPath..."
        Remove-Item -Recurse -Force $venvPath
    }

    Write-Host "Detected $projectFile. Syncing project environment with uv..."
    uv sync
    if ($LASTEXITCODE -ne 0) {
        Fail "uv sync failed."
    }

    Write-Host "Activating virtual environment..."
    & ".\$venvPath\Scripts\Activate.ps1"

    Write-Host "Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To activate the virtual environment in future sessions, run:" -ForegroundColor Cyan
    Write-Host ".\$venvPath\Scripts\Activate.ps1"
    Write-Host ""
    Write-Host "To run tests, use:" -ForegroundColor Cyan
    Write-Host "uv run python main.py --help"
    exit 0
}

# requirements.txt workflow
if (-not (Test-Path $requirementsFile)) {
    Warn "$projectFile and $requirementsFile were both not found. Creating an empty environment only."
}

if ($Force -and (Test-Path $venvPath)) {
    Write-Host "Removing existing virtual environment at $venvPath..."
    Remove-Item -Recurse -Force $venvPath
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment with uv..."
    uv venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to create virtual environment with uv."
    }
} else {
    Write-Host "Virtual environment already exists at $venvPath."
}

Write-Host "Activating virtual environment..."
& ".\$venvPath\Scripts\Activate.ps1"

if (Test-Path $requirementsFile) {
    Write-Host "Syncing Python packages from $requirementsFile..."
    uv pip sync $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to sync requirements from $requirementsFile."
    }
} else {
    Warn "$requirementsFile not found. Skipping package installation."
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in future sessions, run:" -ForegroundColor Cyan
Write-Host ".\$venvPath\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To run tests, use:" -ForegroundColor Cyan
Write-Host "python main.py --help"
