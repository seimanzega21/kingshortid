@echo off
REM GoodShort Production Scraping System
REM Complete pipeline to capture metadata + covers

echo.
echo ============================================================================
echo   GoodShort Production Scraping System
echo ============================================================================
echo.

REM Check Frida
where frida >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Frida not found!
    echo.
    echo Install: pip install frida-tools
    echo.
    pause
    exit /b 1
)

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Check device
echo [*] Checking device...
adb devices | findstr "emulator device" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No device/emulator found!
    echo.
    echo Start your emulator first!
    pause
    exit /b 1
)

echo [OK] Device connected
echo.

REM Menu
:menu
echo ============================================================================
echo   Select Mode:
echo ============================================================================
echo.
echo   1. Extract Tokens Only (first time setup)
echo   2. Capture Metadata + Covers (main scraping)
echo   3. Process Data + Download Covers (after capture)
echo   4. Complete Pipeline (all steps)
echo   5. Exit
echo.
set /p choice="Select [1-5]: "

if "%choice%"=="1" goto extract_tokens
if "%choice%"=="2" goto capture_metadata
if "%choice%"=="3" goto process_data
if "%choice%"=="4" goto complete_pipeline
if "%choice%"=="5" goto end

echo Invalid choice!
goto menu

REM ============================================================================
REM Extract Tokens
REM ============================================================================
:extract_tokens
echo.
echo ============================================================================
echo   Step 1: Extract Authentication Tokens
echo ============================================================================
echo.
echo This will:
echo   - Launch GoodReels app with Frida
echo   - Auto-extract tokens (userToken, GAID, Android ID)
echo   - Save to /sdcard/goodshort_tokens.json
echo.
echo Instructions:
echo   1. App will open automatically
echo   2. Login if needed
echo   3. Browse a few dramas
echo   4. Type: status() to check
echo   5. Type: save() to force save
echo   6. Press Ctrl+C to stop
echo.
pause

echo.
echo [*] Starting token extractor...
frida -U -f com.newreading.goodreels -l frida\auto-token-extractor.js

echo.
echo [*] Pulling tokens from device...
adb pull /sdcard/goodshort_tokens.json .

if exist goodshort_tokens.json (
    echo [OK] Tokens extracted successfully!
) else (
    echo [WARNING] Tokens file not found
)

echo.
pause
goto menu

REM ============================================================================
REM Capture Metadata
REM ============================================================================
:capture_metadata
echo.
echo ============================================================================
echo   Step 2: Capture Metadata + Covers
echo ============================================================================
echo.
echo This will:
echo   - Launch GoodReels with production scraper
echo   - Capture titles, covers, descriptions, episodes
echo   - Auto-save to /sdcard/goodshort_production_data.json
echo.
echo Instructions:
echo   1. Browse dramas in app
echo   2. Tap dramas to see details
echo   3. Scroll episode lists
echo   4. Type: status() to check progress
echo   5. Type: list() to see captured dramas
echo   6. Type: save() to force save
echo   7. Press Ctrl+C when done
echo.
pause

echo.
echo [*] Starting production scraper...
frida -U -f com.newreading.goodreels -l frida\production-scraper.js

echo.
echo [*] Pulling data from device...
adb pull /sdcard/goodshort_production_data.json .

if exist goodshort_production_data.json (
    echo [OK] Data captured successfully!
) else (
    echo [ERROR] Data file not found!
)

echo.
pause
goto menu

REM ============================================================================
REM Process Data
REM ============================================================================
:process_data
echo.
echo ============================================================================
echo   Step 3: Process Data + Download Covers
echo ============================================================================
echo.

if not exist goodshort_production_data.json (
    echo [ERROR] No data file found!
    echo.
    echo Run "Capture Metadata" first!
    pause
    goto menu
)

echo [*] Running production processor...
python production_processor.py

echo.
if exist production_output\final_metadata.json (
    echo [OK] Processing complete!
    echo.
    echo Output:
    echo   - production_output\final_metadata.json
    echo   - production_output\covers\
    echo   - production_output\database_import.sql
) else (
    echo [ERROR] Processing failed!
)

echo.
pause
goto menu

REM ============================================================================
REM Complete Pipeline
REM ============================================================================
:complete_pipeline
echo.
echo ============================================================================
echo   Complete Pipeline - All Steps
echo ============================================================================
echo.
echo This will run:
echo   1. Token extraction
echo   2. Metadata capture
echo   3. Data processing
echo.
echo Press Ctrl+C at any time to stop
echo.
pause

REM Step 1
call :extract_tokens

REM Step 2  
call :capture_metadata

REM Step 3
call :process_data

echo.
echo ============================================================================
echo   COMPLETE! Ready for production
echo ============================================================================
echo.
pause
goto menu

:end
echo.
echo Goodbye!
echo.
exit /b 0
