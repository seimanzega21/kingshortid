@echo off
echo ============================================================
echo   GoodShort Batch Downloader
echo ============================================================
echo.

if not exist "captured-episodes.json" (
    echo [ERROR] captured-episodes.json not found!
    echo.
    echo Run start-capture.bat first to capture episode URLs
    pause
    exit /b
)

echo [1] Checking captured data...
for /f %%a in ('type captured-episodes.json ^| findstr /c:"bookId"') do (
    echo     Found drama entries
)

echo.
echo [2] Starting download...
echo.

:: Update PATH for ffmpeg
set PATH=%PATH%;C:\ProgramData\chocolatey\bin

call npx ts-node src/batch-download.ts captured-episodes.json

echo.
echo ============================================================
echo   Download complete! Check the 'downloads' folder
echo ============================================================
pause
