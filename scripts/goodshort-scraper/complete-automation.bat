@echo off
echo.
echo ============================================================================
echo   GOODSHORT COMPLETE AUTOMATION - HTTP Toolkit + ADB
echo ============================================================================
echo.
echo This script will:
echo   1. Start HTTP Toolkit in background
echo   2. Play 20 episodes via ADB automation  
echo   3. HTTP Toolkit captures all .ts segments
echo   4. Export HAR file
echo   5. Download all segments with anti-blocking
echo   6. Organize into R2 structure
echo.

set DEVICE=emulator-5554
set EPISODES=20

echo [1/6] Checking emulator...
adb devices | findstr %DEVICE% >nul
if errorlevel 1 (
    echo ❌ Emulator not running!
    echo Please start Android Studio emulator first.
    pause
    exit /b 1
)
echo ✅ Emulator connected: %DEVICE%
echo.

echo [2/6] HTTP Toolkit Setup
echo.
echo MANUAL STEP REQUIRED:
echo   1. Open HTTP Toolkit
echo   2. Click "Android Device via ADB"
echo   3. Wait for "Intercepting Android device"
echo   4. Press ENTER here to continue...
pause

echo.
echo [3/6] Playing %EPISODES% episodes with ADB...
echo.

:: Episode playback loop
for /L %%i in (1,1,%EPISODES%) do (
    echo Episode %%i/%EPISODES%:
    
    :: Navigate to episode (adjust coordinates for your emulator)
    echo   - Navigating to episode %%i...
    adb -s %DEVICE% shell input tap 540 800
    timeout /t 2 /nobreak >nul
    
    :: Tap play button
    echo   - Playing episode...
    adb -s %DEVICE% shell input tap 540 1400
    
    :: Wait for episode duration (3 minutes = 180 seconds)
    echo   - Buffering... (waiting 180s for capture)
    timeout /t 180 /nobreak >nul
    
    :: Navigate back
    adb -s %DEVICE% shell input keyevent KEYCODE_BACK
    timeout /t 2 /nobreak >nul
    
    :: Next episode
    adb -s %DEVICE% shell input swipe 540 1200 540 400 300
    timeout /t 2 /nobreak >nul
    
    echo   ✅ Episode %%i complete
    echo.
)

echo.
echo [4/6] Playback complete!
echo.
echo MANUAL STEP REQUIRED:
echo   1. In HTTP Toolkit, export HAR file
echo   2. File → Export (or Ctrl+S)
echo   3. Save as: goodshort_capture.har
echo   4. Save location: %CD%
echo   5. Press ENTER when done...
pause

echo.
echo [5/6] Downloading segments...
echo.

python ultimate_capture.py goodshort_capture.har

if errorlevel 1 (
    echo ❌ Download failed!
    pause
    exit /b 1
)

echo.
echo [6/6] Organizing for R2...
echo.

:: TODO: Add R2 organization script
echo Captured videos are in: captured_complete/
echo.

echo ============================================================================
echo   COMPLETE! 🎉
echo ============================================================================
echo.
echo Next steps:
echo   1. Review: captured_complete/
echo   2. Organize: python organize_for_r2.py
echo   3. Upload: python upload_to_r2.py
echo.
pause
