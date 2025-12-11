# LLM Agent Lab - Windows Setup Script
# Usage: .\scripts\setup.ps1
# Requires: PowerShell 5.1+ (comes with Windows 10/11)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

Write-Success "LLM Agent Lab - Initial Setup (Windows)"
Write-Host "========================================"

# Check prerequisites
Write-Warning "Checking prerequisites..."

# Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python is not installed or not in PATH."
    Write-Error "Please install Python 3.10+ from https://www.python.org/downloads/"
    Write-Error "Make sure to check 'Add Python to PATH' during installation."
    exit 1
}
$pythonVersion = python --version 2>&1
Write-Host "  Python: $pythonVersion"

# Check Python version is 3.10+
$versionMatch = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
$major, $minor = $versionMatch -split '\.'
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
    Write-Error "Python 3.10+ is required. Current version: $pythonVersion"
    exit 1
}

# Node.js
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error "Node.js is not installed or not in PATH."
    Write-Error "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
}
$nodeVersion = node --version
Write-Host "  Node.js: $nodeVersion"

# npm
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    Write-Error "npm is not installed."
    exit 1
}
$npmVersion = npm --version
Write-Host "  npm: $npmVersion"

# Docker (optional)
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    $dockerVersion = docker --version
    Write-Host "  Docker: $dockerVersion"
} else {
    Write-Warning "  Docker: Not installed (optional - required for PostgreSQL/Redis)"
}

Write-Host ""
Write-Warning "Setting up backend..."

# Navigate to backend directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$backendDir = Join-Path $rootDir "backend"

Push-Location $backendDir

try {
    # Create virtual environment
    if (-not (Test-Path "venv")) {
        Write-Host "Creating Python virtual environment..."
        python -m venv venv
    }

    # Activate virtual environment
    $activateScript = Join-Path $backendDir "venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        Write-Host "Activating virtual environment..."
        & $activateScript
    } else {
        Write-Error "Virtual environment activation script not found."
        exit 1
    }

    # Upgrade pip and install dependencies
    Write-Host "Installing Python dependencies..."
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements/development.txt --quiet

    # Create .env file if it doesn't exist
    $envFile = Join-Path $backendDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Host "Creating .env file..."
        $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
        @"
DJANGO_SECRET_KEY=$secretKey
DEBUG=True
USE_SQLITE=true
CELERY_EAGER=true
"@ | Out-File -FilePath $envFile -Encoding utf8
    }

    # Create directories
    Write-Host "Creating required directories..."
    $dirs = @("static", "media", "staticfiles")
    foreach ($dir in $dirs) {
        $dirPath = Join-Path $backendDir $dir
        if (-not (Test-Path $dirPath)) {
            New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        }
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Warning "Setting up frontend..."

$frontendDir = Join-Path $rootDir "frontend"
Push-Location $frontendDir

try {
    # Install npm dependencies
    Write-Host "Installing npm dependencies..."
    npm install --silent
}
finally {
    Pop-Location
}

Write-Host ""
Write-Warning "Creating documentation directory..."
$docsDir = Join-Path $rootDir "docs"
if (-not (Test-Path $docsDir)) {
    New-Item -ItemType Directory -Path $docsDir -Force | Out-Null
}

Write-Host ""
Write-Success "Setup complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review backend\.env and update settings as needed"
Write-Host "  2. Run '.\scripts\dev.ps1' to start the development servers"
Write-Host "  3. Open http://localhost:3000 in your browser"
Write-Host ""
Write-Host "For production setup, see docs\DEPLOYMENT.md"
Write-Host ""
Write-Info "Note: If you encounter any PowerShell execution policy issues, run:"
Write-Info "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
