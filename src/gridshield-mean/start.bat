@echo off
title GridShield MEAN Stack
color 0A
echo.
echo  ====================================================
echo   GridShield MEAN Stack Launcher
echo   MongoDB + Express + Angular + Node.js
echo  ====================================================
echo.

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODEVER=%%i
echo  Node.js: %NODEVER%

:: Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 ( echo  ERROR: npm not found. & pause & exit /b 1 )

set "ROOT=%~dp0"
set "BACK=%ROOT%backend"
set "FRONT=%ROOT%frontend"

echo.
echo  [1/4] Installing backend dependencies...
cd /d "%BACK%"
call npm install --silent
if %errorlevel% neq 0 ( echo  ERROR: Backend npm install failed. & pause & exit /b 1 )

echo  [2/4] Installing frontend dependencies...
cd /d "%FRONT%"
call npm install --silent
if %errorlevel% neq 0 ( echo  ERROR: Frontend npm install failed. & pause & exit /b 1 )

echo.
echo  [3/4] Seeding database (running full pipeline)...
cd /d "%BACK%"
:: Copy env.example to .env.local if no .env.local exists
if not exist ".env.local" (
    copy env.example .env.local >nul
    echo  Created .env.local from env.example
)
node src/pipeline/seed.js
if %errorlevel% neq 0 (
    echo  WARNING: Seed failed - MongoDB may not be running.
    echo  Start MongoDB first, then run seed manually:
    echo    cd backend ^& node src/pipeline/seed.js
)

echo.
echo  [4/4] Starting servers...
echo.
echo  Backend API  : http://localhost:3000
echo  Frontend App : http://localhost:4200
echo.
echo  Starting backend in background...
start "GridShield Backend" cmd /k "cd /d "%BACK%" && npm run dev"

timeout /t 3 /nobreak >nul

echo  Starting Angular dev server...
cd /d "%FRONT%"
call npm start

pause
