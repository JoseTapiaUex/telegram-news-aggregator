# Setup script for Windows to install Python dependencies robustly
# Usage: Open PowerShell as Administrator and run:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\scripts\setup_windows.ps1

$venvPip = Join-Path -Path $PSScriptRoot -ChildPath "..\.venv\Scripts\pip.exe"
if (-Not (Test-Path $venvPip)) {
    Write-Host "pip not found in .venv. Make sure virtualenv is created and activated or provide path to pip." -ForegroundColor Yellow
}
else {
    Write-Host "Upgrading pip, setuptools and wheel..."
    & $venvPip install --upgrade pip setuptools wheel
}

# Try to install from requirements, preferring binary wheels
Write-Host "Attempting to install requirements (prefer binary wheels)..."
try {
    if (Test-Path $venvPip) { 
        & $venvPip install --only-binary=:all: -r ..\requirements.txt
    } else {
        python -m pip install --only-binary=:all: -r ..\requirements.txt
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Requirements installed successfully (binary wheels)." -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Host "Binary-only install failed, will try fallback methods..." -ForegroundColor Yellow
}

# Fallback: try pip install normally (this will compile if needed)
Write-Host "Trying normal pip install (may require build tools)..."
if (Test-Path $venvPip) { 
    & $venvPip install -r ..\requirements.txt
} else {
    python -m pip install -r ..\requirements.txt
}
if ($LASTEXITCODE -eq 0) {
    Write-Host "Requirements installed successfully." -ForegroundColor Green
    exit 0
}

# Fallback: try pipwin to get prebuilt Windows wheels for packages like lxml
Write-Host "Attempting to install pipwin and use it to install problematic packages (e.g., lxml)..." -ForegroundColor Yellow
try {
    if (Test-Path $venvPip) { & $venvPip install pipwin } else { python -m pip install pipwin }
    if (Test-Path $venvPip) { & $venvPip install --upgrade pipwin } else { python -m pip install --upgrade pipwin }
    Write-Host "Installing lxml via pipwin..." -ForegroundColor Yellow
    python -m pipwin install lxml
    Write-Host "Now retrying requirements installation..." -ForegroundColor Yellow
    if (Test-Path $venvPip) { & $venvPip install -r ..\requirements.txt } else { python -m pip install -r ..\requirements.txt }
    if ($LASTEXITCODE -eq 0) { Write-Host "Requirements installed successfully via pipwin." -ForegroundColor Green; exit 0 }
} catch {
    Write-Host "pipwin fallback failed or pipwin not available." -ForegroundColor Yellow
}

# Final suggestion: ask user to install Visual C++ Build Tools
Write-Host "---" -ForegroundColor Cyan
Write-Host "All automated install attempts failed. To build some packages (like lxml) from source you need Microsoft C++ Build Tools." -ForegroundColor Red
Write-Host "You can install them with winget (requires Windows 10/11 and winget):" -ForegroundColor Cyan
Write-Host "  winget install --id Microsoft.VisualCppBuildTools -e" -ForegroundColor White
Write-Host "Or download and install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor White
Write-Host "After installing Build Tools, re-run this script or run:`n  .venv\Scripts\python.exe -m pip install -r requirements.txt`" -ForegroundColor Cyan
exit 1
