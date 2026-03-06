@echo off
REM Auto Browser for GoodReels
REM Uses ADB to simulate taps and scrolls

echo.
echo ============================================================================
echo   GoodReels Auto Browser
echo   Automatically scrolls and taps dramas while Frida captures
echo ============================================================================
echo.

REM Check ADB
where adb >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ADB not found!
    pause
    exit /b 1
)

echo [*] Make sure:
echo   1. GoodReels app is open
echo   2. Frida is running (capture-metadata.js)
echo   3. You're on the drama list screen
echo.
pause

echo.
echo [*] Starting auto-browse...
echo.

REM Get screen size for tap coordinates
for /f "tokens=*" %%a in ('adb shell wm size') do set size_output=%%a
echo Screen: %size_output%

REM Tap positions (adjust based on your screen)
REM Assuming 1080x2400 screen
set CENTER_X=540
set CENTER_Y=1200
set BOTTOM_Y=2000

REM Number of dramas to browse
set NUM_DRAMAS=10

echo [*] Will browse %NUM_DRAMAS% dramas
echo.

for /L %%i in (1,1,%NUM_DRAMAS%) do (
    echo [Drama %%i/%NUM_DRAMAS%]
    
    REM Scroll to make sure drama is visible
    echo   - Scrolling list...
    adb shell input swipe 540 1800 540 800 300
    timeout /t 1 /nobreak >nul
    
    REM Tap drama card
    echo   - Opening drama detail...
    adb shell input tap %CENTER_X% %CENTER_Y%
    timeout /t 3 /nobreak >nul
    
    REM Scroll episode list (if visible)
    echo   - Scrolling episodes...
    adb shell input swipe 540 1800 540 1200 300
    timeout /t 2 /nobreak >nul
    
    adb shell input swipe 540 1800 540 1200 300
    timeout /t 2 /nobreak >nul
    
    REM Go back to list
    echo   - Going back...
    adb shell input keyevent KEYCODE_BACK
    timeout /t 2 /nobreak >nul
    
    REM Scroll down to next drama
    echo   - Next drama...
    adb shell input swipe 540 1600 540 1000 300
    timeout /t 1 /nobreak >nul
    
    echo.
)

echo.
echo [✓] Browsing complete!
echo.
echo [*] Now check Frida console:
echo     Type: status()
echo     Type: exportData()
echo.
pause
