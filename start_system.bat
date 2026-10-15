@echo off
SETLOCAL

REM ==========================================
REM Retails System startup script for Windows
REM ==========================================

REM Base directories
cd /d C:\Retails-System || (
    echo [ERROR] Base folder not found!
    pause
    exit /b 1
)

:: Make sure log folder exists
if not exist C:\Retails-System mkdir C:\Retails-System

:: Define log files
set MAINLOG=C:\Retails-System\startup_log.txt
set BACKENDLOG=C:\Retails-System\backend_log.txt
set FRONTENDLOG=C:\Retails-System\frontend_log.txt

:: Main log header
echo ============================== >> %MAINLOG%
echo Startup run at %date% %time% >> %MAINLOG%
echo ============================== >> %MAINLOG%

echo 1. Activating Python virtual environment
if exist env\Scripts\activate.bat (
    call env\Scripts\activate.bat
    if errorlevel 1 (
        echo [ERROR] Failed to activate virtual environment! >> %MAINLOG%
        pause
        exit /b 1
    )
    echo Python virtual environment activated. >> %MAINLOG%
) else (
    echo [ERROR] Virtual environment not found! >> %MAINLOG%
    pause
    exit /b 1
)

echo.
echo 2. Checking internet connection
ping -n 1 github.com >nul 2>&1
if errorlevel 1 (
    echo No internet connection detected. Skipping Git pull... >> %MAINLOG%
) else (
    echo Internet OK. Pulling latest changes from Git... >> %MAINLOG%
    for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set BRANCH=%%i
    if not defined BRANCH (
        echo [WARNING] Not a Git repository. Skipping Git pull... >> %MAINLOG%
    ) else (
        echo Current branch: %BRANCH% >> %MAINLOG%
        git pull origin %BRANCH% >> %MAINLOG% 2>&1
        if errorlevel 1 (
            echo [ERROR] Git pull failed! Running local version instead... >> %MAINLOG%
        )
    )
)

echo.
echo 3. Installing Python requirements
if exist requirements.txt (
    pip install -r requirements.txt >> %MAINLOG% 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install Python requirements >> %MAINLOG%
    )
) else (
    echo [WARNING] requirements.txt not found >> %MAINLOG%
)

echo.
echo 4. Running database migrations
if exist run.py (
    flask db upgrade >> %MAINLOG% 2>&1
    if errorlevel 1 (
        echo [ERROR] Database migration failed >> %MAINLOG%
    )
) else (
    echo [WARNING] run.py not found. Skipping migrations >> %MAINLOG%
)

echo.
echo 5. Starting Flask backend
if exist run.py (
    start "Flask Backend" cmd /k "python run.py >> %BACKENDLOG% 2>&1"
    echo Flask backend started. Logs at %BACKENDLOG% >> %MAINLOG%
) else (
    echo [ERROR] run.py not found >> %MAINLOG%
)

echo.
echo 6. Switching to Node.js 20
nvm use 20 >> %MAINLOG% 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to switch Node version >> %MAINLOG%
)

echo.
echo 7. Starting frontend
if exist retail-service-shop-frontend\package.json (
    pushd retail-service-shop-frontend
    start "Frontend" cmd /k "npm run dev >> %FRONTENDLOG% 2>&1"
    popd
    echo Frontend started. Logs at %FRONTENDLOG% >> %MAINLOG%
) else (
    echo [ERROR] Frontend folder or package.json missing >> %MAINLOG%
)

echo.
echo ============================== >> %MAINLOG%
echo System startup completed at %time% >> %MAINLOG%
echo ============================== >> %MAINLOG%

pause