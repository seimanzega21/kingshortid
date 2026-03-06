@echo off
echo.
echo ============================================================================
echo   MAXIMUM VIDEO CAPTURE STRATEGY
echo   Capture complete episodes with all video segments
echo ============================================================================
echo.

echo [*] Starting Frida video segment interceptor...
echo.

:: Kill any existing Frida processes
taskkill /F /IM frida.exe 2>nul

:: Clean device storage
echo [1/5] Cleaning device storage...
adb shell "rm -rf /sdcard/goodshort_segments/*"
adb shell "mkdir -p /sdcard/goodshort_segments"
echo     Done.
echo.

:: Start Frida interceptor in background
echo [2/5] Starting Frida interceptor...
start "Frida Video Saver" frida -U -n "GoodShort" -l frida\video-segment-saver.js
timeout /t 3 /nobreak >nul
echo     Frida running in background.
echo.

echo [3/5] Ready to capture! Manual steps:
echo.
echo     1. Open GoodShort app
echo     2. Go to a drama
echo     3. Play Episode 1 (let it buffer completely)
echo     4. Wait for "Episode complete" message
echo     5. Play Episode 2, etc.
echo.
echo [*] Segments will be saved to: /sdcard/goodshort_segments/
echo.

pause

echo.
echo [4/5] Pulling segments from device...
adb pull /sdcard/goodshort_segments/ captured_segments/
echo.

echo [5/5] Organizing segments...
python organize_segments.py
echo.

echo ============================================================================
echo   Capture complete! Check captured_segments/ folder
echo ============================================================================
echo.
pause
