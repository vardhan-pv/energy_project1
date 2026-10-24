@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo                IREOS / CEOS - Local Development Starter
echo ===============================================================================

set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "!PYTHON_EXE!" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    echo Falling back to system python...
    set "PYTHON_EXE=python"
)

:: Enforce strictly local SQLite database engine and port
set "IREOS_DB_ENGINE=sqlite"
set "IREOS_PORT=5000"

echo [1/4] Stopping any existing processes on ports 5000 and 5173...
powershell -NoProfile -Command ^
    "$ports = @(5000, 5173); foreach ($port in $ports) { $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; foreach ($c in $connections) { Write-Host '  Killing PID' $c.OwningProcess 'on port' $port; Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } }"

echo [2/4] Starting IREOS Local Backend on port 5000 (SQLite: ceos_database.db)...
start "IREOS Local Backend (Port 5000)" cmd /k "cd /d "%ROOT_DIR%" && set IREOS_DB_ENGINE=sqlite && set IREOS_PORT=5000 && "%PYTHON_EXE%" api_server.py"

echo [3/4] Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo [4/4] Starting IREOS Dashboard Dev Server (Vite)...
start "IREOS Dashboard Dev Server" cmd /k "cd /d "%ROOT_DIR%dashboard" && set VITE_API_BASE_URL=http://localhost:5000 && npm.cmd run dev"

echo.
echo ===============================================================================
echo  IREOS Local Setup is Running!
echo ===============================================================================
echo  Backend Health : http://localhost:5000/api/health
echo  Dashboard UI   : http://localhost:5173
echo  ESP32 Ingestion: http://10.111.223.150:5000
echo.
echo  To cleanly stop both services at any time, run: stop_local.bat
echo ===============================================================================
