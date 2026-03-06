@echo off
REM ============================================================================
REM GoodShort mitmproxy Auto-Scraper - FINAL SOLUTION
REM Tanpa root, tanpa Frida - hanya mitmproxy!
REM ============================================================================

echo.
echo ============================================================================
echo   GoodShort mitmproxy Auto-Scraper
echo   SOLUSI FINAL - Tanpa Root
echo ============================================================================
echo.

REM Check mitmproxy
where mitmdump >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] mitmproxy not installed
    echo.
    echo Installing mitmproxy...
    pip install mitmproxy
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install mitmproxy!
        pause
        exit /b 1
    )
)

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [OK] mitmproxy installed
echo.

REM Get local IP
echo [*] Finding your local IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP: =%
echo [OK] Your IP: %LOCAL_IP%
echo.

:menu
echo ============================================================================
echo   Select Mode:
echo ============================================================================
echo.
echo   1. Start Proxy Server (for capture)
echo   2. Process Captured Data (download + organize)
echo   3. Upload to R2
echo   4. Complete Pipeline (capture -^> process -^> upload)
echo   5. Show Setup Instructions
echo   6. Exit
echo.
set /p choice="Select [1-6]: "

if "%choice%"=="1" goto start_proxy
if "%choice%"=="2" goto process_data
if "%choice%"=="3" goto upload_r2
if "%choice%"=="4" goto complete
if "%choice%"=="5" goto setup_help
if "%choice%"=="6" goto end

echo Invalid choice!
goto menu

REM ============================================================================
:start_proxy
echo.
echo ============================================================================
echo   STEP 1: Start Proxy Server
echo ============================================================================
echo.
echo Proxy akan berjalan di port 8888
echo.
echo ============ SETUP ANDROID ============
echo 1. Buka Settings -^> WiFi -^> [Koneksi WiFi Anda]
echo 2. Tap "Modify network" atau "Edit"
echo 3. Show advanced options
echo 4. Proxy: Manual
echo 5. Proxy hostname: %LOCAL_IP%
echo 6. Proxy port: 8888
echo 7. Save
echo.
echo 8. Buka browser di Android: http://mitm.it
echo 9. Download dan install certificate Android
echo    (Settings -^> Security -^> Install from storage)
echo ========================================
echo.
echo Setelah setup, browse GoodShort app seperti biasa.
echo Data akan auto-capture.
echo.
echo Press Ctrl+C untuk stop.
echo.
pause

echo [*] Starting mitmproxy on port 8888...
echo.
mitmdump -s goodshort_mitmproxy.py -p 8888 --set confdir=.mitmproxy

echo.
echo [*] Proxy stopped.
echo [*] Data saved to mitm_capture/
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
echo Ini akan:
echo   - Download semua cover images
echo   - Download dan gabungkan video segments
echo   - Organize ke folder r2_ready/
echo.
pause

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
    echo [ERROR] Folder r2_ready tidak ditemukan!
    echo Jalankan Process Data terlebih dahulu.
    pause
    goto menu
)

python upload_r2_ready.py

echo.
pause
goto menu

REM ============================================================================
:complete
echo.
echo ============================================================================
echo   COMPLETE PIPELINE
echo ============================================================================
echo.
echo Pipeline:
echo   1. Start Proxy -^> Browse app untuk capture
echo   2. Process Data -^> Download ^& organize
echo   3. Upload R2 -^> Upload ke cloud storage
echo.
echo Mulai dari Step 1?
pause
goto start_proxy

REM ============================================================================
:setup_help
echo.
echo ============================================================================
echo   SETUP INSTRUCTIONS
echo ============================================================================
echo.
echo === WINDOWS (PC ini) ===
echo 1. Pastikan PC dan Android di WiFi yang sama
echo 2. Jalankan script ini, pilih "Start Proxy"
echo.
echo === ANDROID ===
echo 1. Settings -^> WiFi -^> tap koneksi aktif
echo 2. Modify network -^> Advanced options
echo 3. Proxy: Manual
echo 4. Hostname: %LOCAL_IP%
echo 5. Port: 8888
echo 6. Save
echo.
echo === INSTALL CERTIFICATE ===
echo 1. Buka browser Android: http://mitm.it
echo 2. Download "Android" certificate
echo 3. Settings -^> Security -^> Install from storage
echo 4. Pilih file certificate, beri nama "mitmproxy"
echo.
echo === CAPTURE DATA ===
echo 1. Buka GoodShort app
echo 2. Browse drama, klik detail, scroll episodes
echo 3. Play beberapa episode (agar video URL tercapture)
echo 4. Tekan Ctrl+C di PC untuk stop capture
echo 5. Jalankan "Process Data"
echo.
echo === EMULATOR (ALTERNATIF) ===
echo Jika pakai emulator (LDPlayer/BlueStacks/NOX):
echo 1. Start emulator
echo 2. Set proxy seperti di atas (IP: 10.0.2.2 untuk Android Studio,
echo    atau IP PC asli untuk emulator lain)
echo.
pause
goto menu

:end
echo.
echo Goodbye!
exit /b 0
