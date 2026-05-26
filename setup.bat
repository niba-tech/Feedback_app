@echo off
echo ============================================
echo  Store Marketing App - First Time Setup
echo ============================================
echo.
echo Step 1: Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is installed and added to PATH.
    echo Download Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo.
echo Step 2: Installing browser for web crawling...
playwright install chromium
if %errorlevel% neq 0 (
    echo ERROR: Playwright install failed.
    pause
    exit /b 1
)
echo.
echo ============================================
echo  Setup complete!
echo ============================================
echo.
echo NEXT STEP: Open the .env file in Notepad and
echo paste your Claude API key where it says:
echo   ANTHROPIC_API_KEY=your-api-key-here
echo.
echo Get your API key at: https://console.anthropic.com
echo.
echo After that, double-click start_app.bat to use the app.
echo.
pause
