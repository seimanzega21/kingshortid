@echo off
REM ============================================================================
REM GoodShort Complete Scraper - mitmproxy + Frida SSL Bypass
REM SOLUSI LENGKAP untuk bypass SSL Pinning
REM ============================================================================

echo.
echo ============================================================================
echo   GoodShort Complete Scraper
echo   mitmproxy + Frida SSL Bypass
echo ============================================================================
echo.

REM Check dependencies
echo [*] Checking dependencies...

where frida >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Frida not installed. Installing...
    pip install frida-tools
)

where mitmdump >nul 2>nul  
if %ERRORLEVEL% NEQ 0 (
    echo [!] mitmproxy not installed. Installing...
    pip install mitmproxy
)

where adb >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ADB not found! Install Android SDK Platform Tools
    pause
    exit /b 1
)

echo [OK] All dependencies ready
echo.

REM Check device
echo [*] Checking Android device/emulator...
adb devices | findstr "device emulator" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No Android device/emulator connected!
    echo Start your emulator and try again.
    pause
    exit /b 1
)
echo [OK] Device connected
echo.

REM Clean old data
echo [*] Cleaning old capture data...
if exist mitm_capture rmdir /s /q mitm_capture
mkdir mitm_capture
echo [OK] Clean workspace ready
echo.

:menu
echo ============================================================================
echo   Select Mode:
echo ============================================================================
echo.
echo   1. Start Complete Capture (Frida + mitmproxy)
echo   2. Process Captured Data
echo   3. Upload to R2
echo   4. Full Pipeline (Capture + Process + Upload)
echo   5. Exit
echo.
set /p choice="Select [1-5]: "

if "%choice%"=="1" goto start_capture
if "%choice%"=="2" goto process_data
if "%choice%"=="3" goto upload_r2
if "%choice%"=="4" goto full_pipeline
if "%choice%"=="5" goto end

echo Invalid choice!
goto menu

REM ============================================================================
:start_capture
echo.
echo ============================================================================
echo   STEP 1: Start Capture (Frida + mitmproxy)
echo ============================================================================
echo.
echo This will:
echo   1. Start mitmproxy on port 8888
echo   2. Run Frida SSL unpinning on GoodShort
echo   3. Set Android proxy to mitmproxy
echo   4. Capture all traffic automatically
echo.
echo Instructions:
echo   - Browse dramas in the app
echo   - Click drama details (capture metadata)
echo   - Scroll episode list (capture episode order)
echo   - Play episodes (capture video URLs)
echo.
echo Press Ctrl+C to stop capture when done.
echo.
pause

REM Clean old data
if exist mitm_capture\goodshort_data.json del mitm_capture\goodshort_data.json

REM Start mitmproxy in background
echo [1/3] Starting mitmproxy...
start "mitmproxy" cmd /c "mitmdump -s goodshort_mitmproxy.py -p 8888 --set confdir=.mitmproxy 2>&1 | tee mitm_capture\proxy.log"

REM Wait for mitmproxy to start
timeout /t 3 /nobreak >nul

REM Set proxy on Android
echo [2/3] Setting Android proxy...
adb shell settings put global http_proxy 10.0.2.2:8888

REM Start Frida with SSL unpinning
echo [3/3] Starting Frida SSL unpinning...
echo.
echo ============================================================
echo   CAPTURE RUNNING - Browse GoodShort now!
echo   Press Ctrl+C when done browsing
echo ============================================================
echo.

frida -U -f com.newreading.goodreels -l frida\ssl_unpin_for_mitm.js --no-pause

REM Cleanup after Ctrl+C
echo.
echo [*] Stopping capture...
adb shell settings put global http_proxy :0

REM Kill mitmproxy
taskkill /FI "WINDOWTITLE eq mitmproxy" /F >nul 2>nul

echo [OK] Capture complete!
echo [*] Data saved to: mitm_capture\goodshort_data.json
echo.
pause
goto menu

REM ============================================================================
:process_data
echo.
echo ============================================================================
echo   STEP 2: Process Captured Data
echo ============================================================================
echo.

if not exist mitm_capture\goodshort_data.json (
    echo [ERROR] No capture data found!
    echo Run "Start Capture" first.
    pause
    goto menu
)

echo [*] Processing captured data...
python process_mitm_data.py

echo.
pause
goto menu

REM ============================================================================
:upload_r2
echo.
echo ============================================================================
echo   STEP 3: Upload to R2
echo ============================================================================
echo.

if not exist r2_ready (
    echo [ERROR] No processed data found!
    echo Run "Process Data" first.
    pause
    goto menu
)

echo [*] Uploading to R2...
python upload_r2_ready.py

echo.
pause
goto menu

REM ============================================================================
:full_pipeline
echo.
echo ============================================================================
echo   FULL PIPELINE - Capture + Process + Upload
echo ============================================================================
echo.
echo This will run the complete pipeline:
echo   1. Capture with Frida + mitmproxy
echo   2. Process and download videos
echo   3. Upload to R2
echo.
pause
call :start_capture
call :process_data
call :upload_r2
echo.
echo ============================================================================
echo   PIPELINE COMPLETE!
echo ============================================================================
echo.
pause
goto menu

:end
echo.
echo Goodbye!
exit /b 0
