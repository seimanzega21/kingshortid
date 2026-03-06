@echo off
echo.
echo ============================================================================
echo   Simple Episode Capture - Logcat Method
echo   Captures network traffic while tapping episodes
echo ============================================================================
echo.

:: Clear logcat
echo [1/4] Clearing logcat...
adb logcat -c

:: Start logcat capture in background
echo [2/4] Starting logcat capture...
start /B adb logcat *:I ^| findstr "m3u8" > episode_urls.txt

:: Wait a bit
timeout /t 2 /nobreak >nul

:: Run episode tapping
echo [3/4] Tapping 5 episodes to test...
echo.

set /a DRAMA_Y=800

:: Open drama
adb shell input tap 540 %DRAMA_Y%
timeout /t 4 /nobreak >nul

:: Scroll to episodes
adb shell input swipe 540 1500 540 500 300
timeout /t 2 /nobreak >nul

:: Tap 5 episodes
for /L %%i in (1,1,5) do (
    echo Episode %%i: Tapping...
    adb shell input tap 540 1200
    timeout /t 3 /nobreak >nul
    
    echo Episode %%i: Captured HLS
    adb shell input keyevent KEYCODE_BACK
    timeout /t 1 /nobreak >nul
    
    adb shell input swipe 540 1400 540 1200 200
    timeout /t 1 /nobreak >nul
)

echo.
echo [4/4] Stopping logcat...
taskkill /F /IM adb.exe /FI "WINDOWTITLE eq *logcat*" >nul 2>&1

echo.
echo ============================================================================
echo   Capture Complete!
echo ============================================================================
echo.
echo Check episode_urls.txt for HLS URLs
echo.
pause
