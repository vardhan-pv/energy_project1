@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo                IREOS / CEOS - Local Teardown Script
echo ===============================================================================

echo Stopping local backend (port 5000) and dashboard (port 5173)...
powershell -NoProfile -Command ^
    "$ports = @(5000, 5001, 5173); foreach ($port in $ports) { $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; foreach ($c in $connections) { Write-Host '  Terminated process PID' $c.OwningProcess 'on port' $port; Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } }"

echo.
echo All IREOS local processes stopped successfully.
echo ===============================================================================
