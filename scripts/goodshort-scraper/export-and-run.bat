@echo off
echo.
echo ============================================================================
echo   STEP-BY-STEP: Export HAR from HTTP Toolkit
echo ============================================================================
echo.
echo STEP 1: In HTTP Toolkit window
echo   - Look for menu bar at top
echo   - Try these options:
echo.
echo   Option A: File menu
echo     1. Click "File"
echo     2. Click "Export" or "Save"
echo     3. Choose format: HAR
echo.
echo   Option B: Keyboard shortcut
echo     1. Press Ctrl+S or Ctrl+Shift+S
echo     2. Choose format: HAR
echo.
echo   Option C: Right-click
echo     1. Right-click in request list area
echo     2. Look for "Export" or "Save All"
echo.
echo STEP 2: Save the file
echo   Location: %CD%
echo   Filename: goodshort_capture.har
echo.
echo ============================================================================
echo.
echo Press ENTER after you've exported the HAR file...
pause

echo.
echo Checking for HAR file...
if exist "goodshort_capture.har" (
    echo ✅ HAR file found!
    echo.
    echo Running ultimate capture script...
    python ultimate_capture.py goodshort_capture.har
) else (
    echo ❌ HAR file not found!
    echo.
    echo Please make sure you saved it as: goodshort_capture.har
    echo In location: %CD%
    echo.
    echo Alternative: Copy URLs manually
    echo   1. In HTTP Toolkit, select all .ts requests
    echo   2. Copy URLs
    echo   3. Create file: segment_urls.txt
    echo   4. Paste URLs (one per line)
    echo   5. Run: python download_captured_segments.py
)

echo.
pause
