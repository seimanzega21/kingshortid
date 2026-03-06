@echo off
echo.
echo ============================================================================
echo   QUICK MITMPROXY TEST FOR ANDROID STUDIO EMULATOR
echo ============================================================================
echo.

:: Get emulator ID
echo [1/4] Detecting emulator...
for /f "tokens=1" %%i in ('adb devices ^| findstr emulator') do set EMULATOR_ID=%%i
echo     Emulator: %EMULATOR_ID% ✅
echo.

:: Get PC IP
echo [2/4] Getting PC IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set PC_IP=%%b
    goto :found_ip
)
:found_ip
echo     PC IP: %PC_IP% ✅
echo.

:: Start mitmproxy
echo [3/4] Starting mitmproxy with auto-save script...
echo     Segments will be saved to: captured_segments/
echo.
start "mitmproxy" cmd /k "mitmdump -s mitm_video_dumper.py"
timeout /t 3 /nobreak >nul
echo     mitmproxy running on port 8080 ✅
echo.

:: Configure emulator proxy
echo [4/4] Configuring emulator proxy...
adb -s %EMULATOR_ID% shell settings put global http_proxy %PC_IP%:8080
echo     Emulator proxy configured ✅
echo.

echo ============================================================================
echo   READY TO TEST!
echo ============================================================================
echo.
echo Next steps:
echo   1. In emulator browser, go to: http://mitm.it
echo   2. Download and install Android certificate
echo   3. Open GoodShort app
echo   4. Play any episode
echo   5. Watch mitmproxy terminal for saved segments!
echo.
echo Certificate installation:
echo   Settings ^> Security ^> Install from storage ^> Download folder
echo.
echo After test, press ENTER to cleanup...
pause >nul

:: Cleanup
echo.
echo Cleaning up...
adb -s %EMULATOR_ID% shell settings put global http_proxy :0
taskkill /F /IM mitmdump.exe 2>nul
echo.
echo ============================================================================
echo   Test complete! Check captured_segments/ folder
echo ============================================================================
pause
