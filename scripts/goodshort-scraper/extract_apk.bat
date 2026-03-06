@echo off
echo ========================================
echo GoodShort APK Extraction Script
echo ========================================
echo.

REM Check if adb is available
where adb >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: adb not found in PATH
    echo Please install Android SDK Platform Tools
    echo Download: https://developer.android.com/studio/releases/platform-tools
    pause
    exit /b 1
)

echo [1/4] Checking connected devices...
adb devices
echo.

echo [2/4] Finding GoodShort package...
adb shell pm list packages | findstr good
echo.

set PACKAGE=com.newreading.goodreels
echo Using package: %PACKAGE%
echo.

echo [3/4] Getting APK path...
for /f "tokens=2 delims=:" %%a in ('adb shell pm path %PACKAGE%') do set APK_PATH=%%a
set APK_PATH=%APK_PATH: =%
echo APK Path: %APK_PATH%
echo.

echo [4/4] Pulling APK...
adb pull %APK_PATH% goodshort.apk
echo.

if exist goodshort.apk (
    echo SUCCESS! APK saved as goodshort.apk
    dir goodshort.apk
    echo.
    echo Next steps:
    echo 1. Decompile with jadx: jadx -d goodshort_jadx goodshort.apk
    echo 2. Search for RSA key in assets/ or code
) else (
    echo FAILED to pull APK
)

pause
