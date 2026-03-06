@echo off
echo.
echo ============================================================================
echo   Start Frida Metadata Capture
echo ============================================================================
echo.
echo Starting GoodShort with Frida production scraper...
echo.
echo INSTRUCTIONS:
echo   1. App akan launch otomatis
echo   2. Browse dramas (scroll, tap detail, view episodes)
echo   3. Data auto-save ke /sdcard/goodshort_production_data.json
echo   4. Press Ctrl+C untuk stop
echo.
echo ============================================================================
echo.

frida -U -f com.newreading.goodreels -l frida\production-scraper.js

echo.
echo ============================================================================
echo.
echo Frida stopped. Pulling captured data...
echo.

adb pull /sdcard/goodshort_production_data.json scraped_data\

if exist "scraped_data\goodshort_production_data.json" (
    echo.
    echo ✅ Data captured successfully!
    echo.
    echo Next: python process_production_capture.py
    echo.
) else (
    echo.
    echo ⚠️  No data file found
    echo    Browse some dramas next time!
    echo.
)

pause
