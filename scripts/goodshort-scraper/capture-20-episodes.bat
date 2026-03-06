@echo off
echo.
echo ============================================================================
echo   Perfect Episode HLS Capture
echo   Taps each episode 1-20 to capture HLS URLs
echo ============================================================================
echo.

set /a DRAMA_X=540
set /a DRAMA_Y=800
set /a EPISODE_START_Y=1200
set /a EPISODE_SPACING=150

echo [1/3] Opening drama detail page...
adb shell input tap %DRAMA_X% %DRAMA_Y%
timeout /t 4 /nobreak >nul

echo [2/3] Scrolling to episode list...
adb shell input swipe 540 1500 540 500 300
timeout /t 2 /nobreak >nul

echo [3/3] Tapping episodes 1-20 to capture HLS...
echo.

for /L %%i in (1,1,20) do (
    echo ============================================================================
    echo   Episode %%i/20
    echo ============================================================================
    
    :: Tap episode at same position (episodes are in list)
    echo   [1/3] Tapping episode %%i...
    adb shell input tap 540 1200
    timeout /t 3 /nobreak >nul
    
    :: Wait for video player + HLS capture
    echo   [2/3] Waiting for HLS capture...
    timeout /t 2 /nobreak >nul
    
    :: Go back to episode list
    echo   [3/3] Returning to list...
    adb shell input keyevent KEYCODE_BACK
    timeout /t 1 /nobreak >nul
    
    :: Scroll down to next episode
    echo   [*] Scrolling to next episode...
    adb shell input swipe 540 1400 540 1200 200
    timeout /t 1 /nobreak >nul
    
    echo.
)

echo ============================================================================
echo   ✅ 20 Episodes Captured!
echo ============================================================================
echo.
echo Check Frida console for captured HLS URLs
echo.
pause
