@echo off
REM Automated Drama Browser for Cover Capture
REM Runs while Frida captures cover URLs

echo.
echo ============================================================================
echo   Automated Cover Capture System
echo   ADB will auto-browse while Frida captures covers
echo ============================================================================
echo.

REM Get screen size
for /f "tokens=3" %%a in ('adb shell wm size ^| findstr "Physical"') do set SCREEN_SIZE=%%a

echo [*] Screen: %SCREEN_SIZE%
echo [*] Starting automated browsing...
echo.

REM Number of dramas to browse
set NUM_DRAMAS=10

REM Center coordinates (adjust based on screen)
set CENTER_X=540
set CENTER_Y=1200

for /L %%i in (1,1,%NUM_DRAMAS%) do (
    echo [Drama %%i/%NUM_DRAMAS%]
    
    REM Tap drama card
    echo   - Opening drama...
    adb shell input tap %CENTER_X% %CENTER_Y%
    timeout /t 3 /nobreak >nul
    
    REM Wait for cover to load
    echo   - Loading cover...
    timeout /t 2 /nobreak >nul
    
    REM Scroll to see more content
    adb shell input swipe 540 1600 540 1200 300
    timeout /t 1 /nobreak >nul
    
    REM Go back
    echo   - Returning to list...
    adb shell input keyevent KEYCODE_BACK
    timeout /t 2 /nobreak >nul
    
    REM Scroll to next drama
    echo   - Next drama...
    adb shell input swipe 540 1600 540 1000 300
    timeout /t 1 /nobreak >nul
    
    echo.
)

echo.
echo ============================================================================
echo   Browsing Complete!
echo ============================================================================
echo.
echo [*] Now check Frida console for captured covers
echo [*] Type: status()
echo [*] Then: exportData()
echo.
pause
