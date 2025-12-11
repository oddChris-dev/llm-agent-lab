# LLM Agent Lab - Windows Development Script
# Usage: .\scripts\dev.ps1
# Starts both backend and frontend with hot reload

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

Write-Success "Starting LLM Agent Lab Development Environment"
Write-Host "================================================"

# Check if required tools are installed
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error "Node.js is not installed or not in PATH."
    exit 1
}

# Get script and project directories
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$backendDir = Join-Path $rootDir "backend"
$frontendDir = Join-Path $rootDir "frontend"

# Start PostgreSQL if Docker is available (optional)
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    Write-Warning "Checking PostgreSQL..."
    $containerRunning = docker ps --filter "name=agent-lab-postgres" --format "{{.Names}}" 2>$null
    if (-not $containerRunning) {
        Write-Host "Starting PostgreSQL container..."
        docker run -d `
            --name agent-lab-postgres `
            -e POSTGRES_DB=agent_lab `
            -e POSTGRES_USER=postgres `
            -e POSTGRES_PASSWORD=postgres `
            -p 5432:5432 `
            postgres:15-alpine 2>$null

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not start PostgreSQL container. Using SQLite instead."
        } else {
            Start-Sleep -Seconds 3
        }
    }
}

# Backend setup
Write-Warning "Setting up backend..."
Push-Location $backendDir

try {
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..."
        python -m venv venv
    }

    # Activate virtual environment
    $activateScript = Join-Path $backendDir "venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
    } else {
        Write-Error "Virtual environment activation script not found. Run setup.ps1 first."
        exit 1
    }

    # Install dependencies (quietly)
    Write-Host "Checking dependencies..."
    python -m pip install -q -r requirements/development.txt

    # Run migrations
    Write-Host "Running migrations..."
    python manage.py migrate --noinput

    # Create superuser if it doesn't exist
    $createSuperuser = @"
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin')
    print('Created superuser: admin/admin')
"@
    python -c $createSuperuser 2>$null
}
finally {
    Pop-Location
}

# Store process references for cleanup
$jobs = @()

# Register cleanup handler
$cleanup = {
    Write-Host ""
    Write-Warning "Shutting down..."
    Get-Job | Where-Object { $_.State -eq 'Running' } | Stop-Job
    Get-Job | Remove-Job -Force
}

# Register Ctrl+C handler
[Console]::TreatControlCAsInput = $false
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $cleanup

try {
    # Start Django development server
    Write-Success "Starting Django server on http://localhost:8000"
    $djangoJob = Start-Job -ScriptBlock {
        param($backendDir)
        Set-Location $backendDir
        & "$backendDir\venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
    } -ArgumentList $backendDir
    $jobs += $djangoJob

    # Give Django a moment to start
    Start-Sleep -Seconds 2

    # Frontend setup
    Write-Warning "Setting up frontend..."
    Push-Location $frontendDir
    try {
        # Install npm dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing npm packages..."
            npm install --silent
        }
    }
    finally {
        Pop-Location
    }

    # Start webpack dev server
    Write-Success "Starting Webpack Dev Server on http://localhost:3000"
    $webpackJob = Start-Job -ScriptBlock {
        param($frontendDir)
        Set-Location $frontendDir
        npm run dev
    } -ArgumentList $frontendDir
    $jobs += $webpackJob

    Write-Host ""
    Write-Success "Development environment is ready!"
    Write-Host "================================================"
    Write-Info "Frontend:    http://localhost:3000"
    Write-Info "Backend API: http://localhost:8000/api/v1/"
    Write-Info "API Docs:    http://localhost:8000/api/docs/"
    Write-Info "Admin:       http://localhost:8000/admin/ (admin/admin)"
    Write-Host "================================================"
    Write-Host "Press Ctrl+C to stop all services"
    Write-Host ""

    # Monitor jobs and display output
    while ($true) {
        foreach ($job in $jobs) {
            $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
            if ($output) {
                Write-Host $output
            }

            if ($job.State -eq 'Failed') {
                Write-Error "A service has failed. Check the output above."
                & $cleanup
                exit 1
            }
        }
        Start-Sleep -Milliseconds 500
    }
}
catch {
    Write-Error "An error occurred: $_"
}
finally {
    & $cleanup
}
