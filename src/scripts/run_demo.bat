@echo off
:: ============================================================
:: run_demo.bat
:: GridShield — Windows One-Click Launcher
:: IBM Bob AI Hackathon 2026
::
:: Double-click from Windows Explorer to:
::   1. Check Python is installed
::   2. Install required packages
::   3. Run the full data pipeline
::   4. Launch the Streamlit app
:: ============================================================

title GridShield — Power Grid Advisor
color 0A

echo.
echo  ==================================================
echo   GridShield — Civil-Engineering Grid Advisor
echo   IBM Bob AI Hackathon 2026
echo  ==================================================
echo.

:: --------------------------------------------------------
:: Step 0: Check Python is on PATH
:: --------------------------------------------------------
echo  [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python was not found on your PATH.
    echo.
    echo  Please install Python 3.9 or later from:
    echo    https://www.python.org/downloads/
    echo.
    echo  During installation, tick "Add Python to PATH"
    echo  then re-run this file.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Found: %PYVER%
echo.

:: --------------------------------------------------------
:: Step 1: Install / upgrade required packages
:: --------------------------------------------------------
echo  [2/5] Installing required packages (streamlit, pandas)...
python -m pip install --quiet --upgrade streamlit pandas
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: pip install failed.
    echo  Check your internet connection or proxy settings.
    echo.
    pause
    exit /b 1
)
echo  Packages ready.
echo.

:: --------------------------------------------------------
:: Step 2: Locate src directory relative to this .bat file
:: (run_demo.bat lives in src\scripts\; src\ is one level up)
:: --------------------------------------------------------
set "SCRIPT_DIR=%~dp0"
set "SRC_DIR=%SCRIPT_DIR%.."
set "DATA_DIR=%SRC_DIR%\data"

if not exist "%SRC_DIR%\app.py" (
    echo  ERROR: Could not find app.py in the src\ folder.
    echo  Expected: %SRC_DIR%\app.py
    echo  Make sure run_demo.bat is in the src\scripts\ folder.
    echo.
    pause
    exit /b 1
)

:: --------------------------------------------------------
:: Step 3: Generate synthetic data
:: --------------------------------------------------------
echo  [3/5] Generating synthetic data...
python "%DATA_DIR%\generate_data.py"
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Data generation failed.
    echo  See error message above for details.
    echo.
    pause
    exit /b 1
)
echo.

:: --------------------------------------------------------
:: Step 4: Run risk + priority + recommendation engines
:: --------------------------------------------------------
echo  [4/5] Running risk scoring engine...
python "%SRC_DIR%\scoring\risk_engine.py"
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Risk engine failed.
    echo  See error message above for details.
    echo.
    pause
    exit /b 1
)
echo.

echo  [4/5] Running priority engine...
python "%SRC_DIR%\scoring\priority_engine.py"
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Priority engine failed.
    echo  See error message above for details.
    echo.
    pause
    exit /b 1
)
echo.

echo  [4/5] Running recommendation engine...
python "%SRC_DIR%\recommendation\recommend.py"
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Recommendation engine failed.
    echo  See error message above for details.
    echo.
    pause
    exit /b 1
)
echo.

:: --------------------------------------------------------
:: Step 5: Launch Streamlit app
:: --------------------------------------------------------
echo  [5/5] Launching GridShield app...
echo.
echo  The app will open in your browser at:
echo    http://localhost:8501
echo.
echo  Press Ctrl+C in this window to stop the app.
echo.

cd /d "%SRC_DIR%"
python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Streamlit failed to start.
    echo  Try running manually:
    echo    cd "%SRC_DIR%"
    echo    python -m streamlit run app.py
    echo.
)

echo.
echo  GridShield has stopped.
pause
