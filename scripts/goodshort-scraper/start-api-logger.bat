@echo off
REM ====================================================
REM GoodShort API Logger - For Reverse Engineering
REM ====================================================

echo ====================================================
echo GoodShort API Logger - REVERSE ENGINEERING MODE
echo ====================================================
echo.
echo This will capture COMPLETE API traffic including:
echo  1. All request headers (sign, timestamp, auth)
echo  2. Request bodies
echo  3. Response headers and bodies
echo  4. URL patterns and endpoints
echo.
echo INSTRUCTIONS:
echo  - Browse dramas in the app
echo  - Open drama details
echo  - View episode lists
echo  - When done, type: exportAll()
echo.
pause

cd /d "%~dp0"
frida -U -f com.newreading.goodreels -l frida\api-logger.js
