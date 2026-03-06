@echo off
setlocal enabledelayedexpansion
echo.
echo ============================================================================
echo   FULL AUTO VIDEO CAPTURE - NO MANUAL PLAY NEEDED
echo   Captures complete episodes with all segments automatically
echo ============================================================================
echo.

:: Configuration
set EPISODES_TO_CAPTURE=3
set PLAYBACK_DURATION=90
set CENTER_X=540
set CENTER_Y=1400

echo [*] Configuration:
echo     Episodes to capture: %EPISODES_TO_CAPTURE%
echo     Playback duration: %PLAYBACK_DURATION% seconds per episode
echo.

:: Step 1: Clean storage
echo [1/6] Cleaning device storage...
adb shell "rm -rf /sdcard/goodshort_segments/*"
adb shell "mkdir -p /sdcard/goodshort_segments"
echo     Done.
echo.

:: Step 2: Start Frida interceptor in background
echo [2/6] Starting Frida video segment interceptor...
start "Frida Video Saver" frida -U -n "GoodShort" -l frida\video-segment-saver.js
timeout /t 5 /nobreak >nul
echo     Frida running.
echo.

:: Step 3: Navigate to drama
echo [3/6] Preparing to capture...
echo     Make sure app is on DRAMA DETAIL page
echo     Script will auto-play episodes in 10 seconds
timeout /t 10 /nobreak >nul
echo.

:: Step 4: Auto-play episodes
echo [4/6] Auto-playing and capturing episodes...
echo.

for /L %%i in (1,1,%EPISODES_TO_CAPTURE%) do (
    echo ============================================================================
    echo   Episode %%i/%EPISODES_TO_CAPTURE%
    echo ============================================================================
    
    echo   [1/5] Finding episode card...
    adb shell input swipe %CENTER_X% 1500 %CENTER_X% 1000 300
    timeout /t 1 /nobreak >nul
    
    echo   [2/5] Opening player...
    set /a EP_Y=800 + %%i * 50
    adb shell input tap %CENTER_X% !EP_Y!
    timeout /t 4 /nobreak >nul
    
    echo   [3/5] Starting playback...
    adb shell input tap %CENTER_X% %CENTER_Y%
    timeout /t 2 /nobreak >nul
    
    echo   [4/5] Capturing segments - waiting %PLAYBACK_DURATION% seconds...
    echo        Frida is saving .ts segments in background...
    timeout /t %PLAYBACK_DURATION% /nobreak >nul
    
    echo   [5/5] Returning to episode list...
    adb shell input keyevent KEYCODE_BACK
    timeout /t 2 /nobreak >nul
    
    echo.
)

echo ============================================================================
echo   Capture Complete!
echo ============================================================================
echo.

:: Step 5: Pull segments
echo [5/6] Pulling segments from device...
if not exist "captured_segments" mkdir captured_segments
adb pull /sdcard/goodshort_segments/ captured_segments/
echo     Done.
echo.

:: Step 6: Organize and upload
echo [6/6] Organizing segments and uploading to R2...
python organize_segments.py
echo.

echo ============================================================================
echo   ALL DONE! Videos uploaded to R2
echo ============================================================================
echo.
echo Check output at: r2_complete_videos/
echo.
pause
