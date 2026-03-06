@echo off
echo.
echo ============================================================================
echo   HTTP TOOLKIT - Quick Test Guide
echo ============================================================================
echo.

echo STEP-BY-STEP INSTRUCTIONS:
echo.
echo [1] Open HTTP Toolkit application
echo     - Should already be open
echo.
echo [2] Click "Android Device via ADB"
echo     - HTTP Toolkit will auto-detect emulator-5554
echo     - Certificate will be installed automatically
echo     - Wait for "Intercepting Android device" status
echo.
echo [3] Test in emulator:
echo     - Open GoodShort app
echo     - Navigate to any drama (e.g., "Jeratan Hati")
echo     - Tap Episode 1
echo     - Let video play for 30-60 seconds
echo.
echo [4] Check HTTP Toolkit window:
echo     - Filter by typing: .ts
echo     - Look for requests ending in .ts
echo     - Status should be: 200 OK
echo     - Size: ~500 KB each
echo.
echo [5] If .ts files appear = SUCCESS!
echo     - Export: File -^> Export -^> HAR format
echo     - Save as: captured_test.har
echo     - Run: python parse_toolkit_export.py captured_test.har
echo.
echo ============================================================================
echo   Waiting for your test...
echo ============================================================================
echo.
echo After testing, press any key to see next steps...
pause
echo.

echo What was the result?
echo.
echo A. .ts files appeared in HTTP Toolkit
echo B. No .ts files (only API calls)
echo C. Certificate error
echo.
set /p RESULT="Enter A, B, or C: "

if /i "%RESULT%"=="A" (
    echo.
    echo ============================================================================
    echo   SUCCESS! Ready for full automation
    echo ============================================================================
    echo.
    echo Next steps:
    echo   1. Export HAR file from HTTP Toolkit
    echo   2. Parse URLs: python parse_toolkit_export.py captured.har
    echo   3. Run automation to capture 20 episodes
    echo.
    echo Create automation script? (Y/N^)
    set /p AUTO="Enter choice: "
    if /i "!AUTO!"=="Y" (
        echo.
        echo Creating automation scripts...
        echo Done! Run: .\http-toolkit-auto-capture.bat
    )
) else if /i "%RESULT%"=="B" (
    echo.
    echo ============================================================================
    echo   No .ts files - App likely using SSL pinning
    echo ============================================================================
    echo.
    echo Solution: Disable SSL pinning with Frida
    echo   frida -U -n "GoodShort" --codeshare akabe1/frida-multiple-unpinning
    echo.
    echo Then retry HTTP Toolkit test
    echo.
) else if /i "%RESULT%"=="C" (
    echo.
    echo ============================================================================
    echo   Certificate error - Reinstall needed
    echo ============================================================================
    echo.
    echo Try:
    echo   1. In HTTP Toolkit, reconnect Android device
    echo   2. Restart GoodShort app
    echo   3. Retry test
    echo.
)

echo.
pause
