@echo off
echo.
echo ============================================================================
echo   GoodShort Complete Scraping - Auto Workflow
echo ============================================================================
echo.

:: Check if Frida data already pulled
if not exist "scraped_data\goodshort_production_data.json" (
    echo [1/3] Checking for captured data on device...
    
    :: Try to pull from device
    adb pull /sdcard/goodshort_production_data.json scraped_data\
    
    if not exist "scraped_data\goodshort_production_data.json" (
        echo.
        echo WARNING: No captured data found!
        echo.
        echo Please run Frida capture first:
        echo   frida -U -f com.newreading.goodreels -l frida\production-scraper.js --no-pause
        echo.
        echo Then browse dramas in the app and try again.
        echo.
        pause
        exit /b 1
    )
    
    echo   [OK] Data pulled from device
) else (
    echo [1/3] Using existing captured data
)

echo.
echo [2/3] Processing captured data...
python process_production_capture.py

if errorlevel 1 (
    echo.
    echo ERROR: Processing failed
    pause
    exit /b 1
)

echo.
echo [3/3] Organizing for R2 upload...
echo   [OK] Output ready in: r2_ready\
echo.

echo ============================================================================
echo   Processing Complete!
echo ============================================================================
echo.
echo Next steps:
echo   1. Check output: r2_ready\
echo   2. (Optional) Download videos using HTTP Toolkit headers
echo   3. Upload to R2: python upload_to_r2.py
echo.
pause
