@echo off
echo.
echo ============================================================================
echo   Production Drama Scraping - 10 Dramas
echo   Automated browsing while Frida captures complete metadata
echo ============================================================================
echo.

:: Get screen dimensions
for /f "tokens=1" %%a in ('adb shell wm size ^| find "Physical"') do set SIZE=%%a
for /f "tokens=3 delims=x " %%a in ("%SIZE%") do set WIDTH=%%a
for /f "tokens=3 delims=x " %%a in ("%SIZE%") do set HEIGHT=%%a

echo [*] Screen: %WIDTH%x%HEIGHT%
echo [*] Capturing 10 dramas with complete metadata...
echo.

:: Drama list coordinates (center of cards)
set CENTER_X=540
set /a DRAMA_Y=800

for /L %%i in (1,1,10) do (
    echo ============================================================================
    echo   Drama %%i/10
    echo ============================================================================
    
    :: Tap drama card
    echo   [1/5] Opening drama detail...
    adb shell input tap %CENTER_X% %DRAMA_Y%
    timeout /t 4 /nobreak >nul
    
    :: Wait for detail page to load + API calls
    echo   [2/5] Waiting for metadata capture...
    timeout /t 3 /nobreak >nul
    
    :: Optional: Scroll down to trigger more API calls
    echo   [3/5] Scrolling to load episodes...
    adb shell input swipe %CENTER_X% 1500 %CENTER_X% 500 300
    timeout /t 2 /nobreak >nul
    
    :: Tap first episode to trigger HLS capture
    echo   [4/5] Loading video to capture HLS...
    adb shell input tap %CENTER_X% 1200
    timeout /t 3 /nobreak >nul
    
    :: Go back twice (from player, from detail)
    echo   [5/5] Returning to list...
    adb shell input keyevent KEYCODE_BACK
    timeout /t 1 /nobreak >nul
    adb shell input keyevent KEYCODE_BACK
    timeout /t 2 /nobreak >nul
    
    :: Scroll to next drama
    if %%i LSS 10 (
        echo   [*] Scrolling to next drama...
        adb shell input swipe %CENTER_X% 1400 %CENTER_X% 800 300
        timeout /t 1 /nobreak >nul
    )
    
    echo.
)

echo ============================================================================
echo   Capture Complete!
echo ============================================================================
echo.
echo [*] Check Frida console for captured data
echo [*] Next: Export data and run scraper
echo.
pause
