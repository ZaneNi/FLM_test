# Setup script for Windows
# This script sets up the Python virtual environment and installs dependencies for FLM testing

param(
    [switch]$Force
)

Write-Host "Setting up FLM test environment for Windows..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
} catch {
    Write-Host "Error: Python is not installed or not in PATH. Please install Python 3.8 or higher from https://python.org" -ForegroundColor Red
    exit 1
}

# Extract version number
$versionMatch = $pythonVersion | Select-String -Pattern "Python (\d+)\.(\d+)"
if (-not $versionMatch) {
    Write-Host "Error: Could not determine Python version." -ForegroundColor Red
    exit 1
}

$major = [int]$versionMatch.Matches[0].Groups[1].Value
$minor = [int]$versionMatch.Matches[0].Groups[1].Value

if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
    Write-Host "Error: Python 3.8 or higher is required. Current version: $pythonVersion" -ForegroundColor Red
    exit 1
}

Write-Host "Using $pythonVersion"

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} elseif (-not $Force) {
    Write-Host "Virtual environment already exists. Use -Force to recreate." -ForegroundColor Yellow
} else {
    Write-Host "Removing existing virtual environment..."
    Remove-Item -Recurse -Force venv
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to upgrade pip." -ForegroundColor Yellow
}

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python packages from requirements.txt..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install requirements." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Warning: requirements.txt not found. Skipping package installation." -ForegroundColor Yellow
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in future sessions, run:" -ForegroundColor Cyan
Write-Host "& .\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To run tests, make sure the FLM server is running and use:" -ForegroundColor Cyan
Write-Host "python main.py --help"