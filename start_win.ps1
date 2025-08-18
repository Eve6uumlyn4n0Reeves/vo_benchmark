param(
  [switch]$UseMirror
)

# VO-Benchmark Quick Start Script
Write-Host "VO-Benchmark Quick Start" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# Check directories
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'

Write-Host "Checking directories..." -ForegroundColor Cyan
if (-not (Test-Path $Backend)) {
  Write-Host "ERROR: Backend directory not found: $Backend" -ForegroundColor Red
  Read-Host "Press Enter to exit"
  exit 1
}
if (-not (Test-Path $Frontend)) {
  Write-Host "ERROR: Frontend directory not found: $Frontend" -ForegroundColor Red
  Read-Host "Press Enter to exit"
  exit 1
}
Write-Host "OK: Project structure is correct" -ForegroundColor Green

# Check and install Python
Write-Host "Checking Python..." -ForegroundColor Cyan
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
  Write-Host "Python not found. Attempting to install..." -ForegroundColor Yellow

  # Try to install Python via winget
  $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
  if ($wingetCheck) {
    Write-Host "Installing Python via winget..." -ForegroundColor Yellow
    try {
      winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
      Write-Host "Python installation completed. Please restart this script." -ForegroundColor Green
      Read-Host "Press Enter to exit"
      exit 0
    } catch {
      Write-Host "Failed to install Python via winget." -ForegroundColor Red
    }
  }

  # Manual installation guide
  Write-Host "Please manually install Python:" -ForegroundColor Yellow
  Write-Host "1. Visit: https://www.python.org/downloads/" -ForegroundColor White
  Write-Host "2. Download Python 3.8+ for Windows" -ForegroundColor White
  Write-Host "3. Run installer and CHECK 'Add Python to PATH'" -ForegroundColor White
  Write-Host "4. Restart this script after installation" -ForegroundColor White
  Start-Process "https://www.python.org/downloads/"
  Read-Host "Press Enter to exit"
  exit 1
}
$pythonVersion = python --version 2>&1
Write-Host "OK: $pythonVersion" -ForegroundColor Green

# Check and install Node.js
Write-Host "Checking Node.js..." -ForegroundColor Cyan
$nodeCheck = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCheck) {
  Write-Host "Node.js not found. Attempting to install..." -ForegroundColor Yellow

  # Try to install Node.js via winget
  $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
  if ($wingetCheck) {
    Write-Host "Installing Node.js via winget..." -ForegroundColor Yellow
    try {
      winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
      Write-Host "Node.js installation completed. Please restart this script." -ForegroundColor Green
      Read-Host "Press Enter to exit"
      exit 0
    } catch {
      Write-Host "Failed to install Node.js via winget." -ForegroundColor Red
    }
  }

  # Manual installation guide
  Write-Host "Please manually install Node.js:" -ForegroundColor Yellow
  Write-Host "1. Visit: https://nodejs.org/" -ForegroundColor White
  Write-Host "2. Download LTS version for Windows" -ForegroundColor White
  Write-Host "3. Run installer (npm is included)" -ForegroundColor White
  Write-Host "4. Restart this script after installation" -ForegroundColor White
  Start-Process "https://nodejs.org/"
  Read-Host "Press Enter to exit"
  exit 1
}
$nodeVersion = node --version 2>&1
Write-Host "OK: Node $nodeVersion" -ForegroundColor Green

# Check npm (should be included with Node.js)
Write-Host "Checking npm..." -ForegroundColor Cyan
$npmCheck = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCheck) {
  Write-Host "ERROR: npm not found even though Node.js is installed" -ForegroundColor Red
  Write-Host "Please reinstall Node.js from https://nodejs.org/" -ForegroundColor Yellow
  Start-Process "https://nodejs.org/"
  Read-Host "Press Enter to exit"
  exit 1
}
$npmVersion = npm --version 2>&1
Write-Host "OK: npm v$npmVersion" -ForegroundColor Green

# Install backend dependencies
Write-Host "Checking backend dependencies..." -ForegroundColor Cyan
Set-Location $Backend
$flaskTest = python -c "import flask; print('OK')" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
  pip install -r requirements.txt
  if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install backend dependencies" -ForegroundColor Red
    Set-Location $Root
    Read-Host "Press Enter to exit"
    exit 1
  }
} else {
  Write-Host "OK: Backend dependencies satisfied" -ForegroundColor Green
}
Set-Location $Root

# Install frontend dependencies
Write-Host "Checking frontend dependencies..." -ForegroundColor Cyan
Set-Location $Frontend
if (-not (Test-Path 'node_modules')) {
  Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
  npm install
  if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install frontend dependencies" -ForegroundColor Red
    Set-Location $Root
    Read-Host "Press Enter to exit"
    exit 1
  }
} else {
  Write-Host "OK: Frontend dependencies exist" -ForegroundColor Green
}
Set-Location $Root

Write-Host "Starting services..." -ForegroundColor Green

# Start backend
Write-Host "Starting backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; python start_server.py"
Write-Host "OK: Backend started in new window" -ForegroundColor Green

# Start frontend
Write-Host "Starting frontend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Frontend'; npm run dev"
Write-Host "OK: Frontend started in new window" -ForegroundColor Green

Write-Host ""
Write-Host "All done!" -ForegroundColor Green
Write-Host "Backend: http://localhost:5000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000 (or auto-assigned port)" -ForegroundColor Yellow
Write-Host ""

# Wait for services to start, then open browser
Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "Opening browser..." -ForegroundColor Cyan
try {
  # Try to open the frontend URL in default browser
  Start-Process "http://localhost:3000"
  Write-Host "OK: Browser opened to frontend" -ForegroundColor Green
} catch {
  Write-Host "Could not auto-open browser. Please manually visit: http://localhost:3000" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
