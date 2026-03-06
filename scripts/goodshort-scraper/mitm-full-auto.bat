@echo off
echo.
echo ============================================================================
echo   MITM VIDEO DUMPER - Full Automation
echo   Combines mitmproxy + ADB auto-play
echo ============================================================================
echo.

:: Step 1: Check mitmproxy installed
echo [1/5] Checking mitmproxy...
python -c "import mitmproxy" 2>nul
if errorlevel 1 (
    echo     Not installed. Installing...
    pip install mitmproxy
) else (
    echo     Already installed ✅
)
echo.

:: Step 2: Start mitmproxy in background
echo [2/5] Starting MITM proxy...
start "mitmproxy Video Dumper" mitmdump -s mitm_video_dumper.py
timeout /t 5 /nobreak >nul
echo     mitmproxy running on port 8080 ✅
echo.

:: Step 3: Configure Android proxy
echo [3/5] Configuring Android to use proxy...
for /f "tokens=*" %%a in ('powershell -command "(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias Ethernet).IPAddress"') do set PC_IP=%%a
echo     PC IP: %PC_IP%

adb shell settings put global http_proxy %PC_IP%:8080
echo     Android proxy configured ✅
echo.

echo [4/5] Installing mitmproxy certificate on Android...
echo     1. On Android, open browser
echo     2. Go to: http://mitm.it
echo     3. Download Android certificate
echo     4. Install it (Settings > Security > Install from storage)
echo.
echo Press any key when certificate is installed...
pause
echo.

:: Step 5: Run ADB automation
echo [5/5] Starting ADB auto-play automation...
echo.
echo     Automation will:
echo     - Play 20 episodes automatically
echo     - mitmproxy saves .ts files in background
echo     - You can monitor progress in mitmproxy window
echo.
timeout /t 5 /nobreak >nul

:: Use simplified automation
for /L %%i in (1,1,20) do (
    echo ============================================================================
    echo   Episode %%i/20
    echo ============================================================================
    
    echo   [1/4] Opening episode...
    set /a EP_Y=800 + %%i * 50
    adb shell input tap 540 !EP_Y!
    timeout /t 4 /nobreak >nul
    
    echo   [2/4] Playing video...
    adb shell input tap 540 1400
    timeout /t 3 /nobreak >nul
    
    echo   [3/4] Buffering (90s) - mitmproxy is saving segments...
    timeout /t 90 /nobreak >nul
    
    echo   [4/4] Back to list...
    adb shell input keyevent KEYCODE_BACK
    timeout /t 2 /nobreak >nul
    
    echo.
)

:: Cleanup
echo.
echo ============================================================================
echo   Capture Complete!
echo ============================================================================
echo.
echo Stopping mitmproxy...
taskkill /F /IM mitmdump.exe 2>nul

echo Removing Android proxy...
adb shell settings put global http_proxy :0

echo.
echo 📁 Segments saved to: captured_segments/
echo.
echo Next steps:
echo   1. Check captured_segments/ folder
echo   2. Organize segments: python organize_segments.py
echo   3. Upload to R2: python upload_to_r2.py
echo.
pause
