@echo off
echo.
echo ============================================================================
echo   Automated Drama Browsing with Frida Capture
echo ============================================================================
echo.

REM Kill existing processes first
echo [Setup] Stopping existing processes...
taskkill /F /IM frida.exe 2>nul
adb shell am force-stop com.newreading.goodreels
timeout /t 2 /nobreak >nul

REM Start Frida in background
echo [1/3] Starting Frida capture...
start /B cmd /c "frida -U -f com.newreading.goodreels -l frida\production-scraper.js > frida-auto-capture.log 2>&1"

timeout /t 8 /nobreak
echo   [OK] Frida running

echo.
echo [2/3] Automated browsing - 10 dramas...
echo.

REM Wait for app to fully load
timeout /t 5 /nobreak

REM Browse 10 dramas
for /L %%i in (1,1,10) do (
    echo   [%%i/10] Processing drama %%i...
    
    REM Scroll to ensure drama is visible
    adb shell input swipe 500 1200 500 800 300
    timeout /t 1 /nobreak
    
    REM Tap drama card (approximate position)
    set /a y_pos=400 + (%%i * 180)
    if %%i GTR 5 (
        REM Scroll down if beyond screen
        adb shell input swipe 500 1200 500 600 300
        timeout /t 1 /nobreak
        set y_pos=600
    )
    
    echo     - Tapping drama...
    adb shell input tap 540 !y_pos!
    timeout /t 3 /nobreak
    
    REM Scroll episodes list
    echo     - Viewing episodes...
    adb shell input swipe 500 1200 500 600 200
    timeout /t 1 /nobreak
    adb shell input swipe 500 1200 500 600 200
    timeout /t 2 /nobreak
    
    REM Go back
    echo     - Returning to list...
    adb shell input keyevent 4
    timeout /t 2 /nobreak
    
    echo     [OK] Drama %%i captured
    echo.
)

echo.
echo [3/3] Pulling captured data...
timeout /t 3 /nobreak

adb pull /sdcard/goodshort_production_data.json scraped_data\goodshort_production_data_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%.json

if exist "scraped_data\goodshort_production_data_*.json" (
    echo.
    echo ✅ Success! Data saved to scraped_data\
    echo.
    
    REM Copy to standard location
    copy /Y scraped_data\goodshort_production_data_*.json scraped_data\goodshort_production_data.json >nul 2>&1
    
    echo Next steps:
    echo   1. python process_production_capture.py
    echo   2. python download_with_http_toolkit.py --drama-folder r2_ready\drama_name
    echo.
) else (
    echo.
    echo ⚠️  No data captured - check frida-auto-capture.log
    echo.
)

REM Stop Frida
taskkill /F /IM frida.exe 2>nul

pause
