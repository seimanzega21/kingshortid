@echo off
title GoodShort Metadata Capture v4
echo ========================================
echo  GoodShort Enhanced Metadata Capture
echo  Version 4.0 - Full Metadata + Covers
echo ========================================
echo.

:: Check if Frida is installed
where frida >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Frida not found! Install with: pip install frida-tools
    pause
    exit /b 1
)

echo [*] Starting GoodReels app with Frida injection...
echo [*] This will capture:
echo     - Cover images (all sizes)
echo     - Drama metadata (title, description, genre)
echo     - Episode lists
echo     - Video URLs
echo.
echo [!] INSTRUCTIONS:
echo     1. Browse Indonesian dramas in the app
echo     2. Click on drama details to capture metadata
echo     3. Watch episodes to capture video URLs
echo     4. Type 'status()' to see progress
echo     5. Type 'save()' to export JSON data
echo.
echo ========================================
echo.

cd /d "%~dp0"
frida -U -f com.newreading.goodreels -l frida\capture-metadata-enhanced.js --no-pause

echo.
echo [*] Capture session ended.
pause
