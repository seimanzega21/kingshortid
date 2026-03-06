@echo off
echo ====================================================
echo GoodShort API Logger - SIMPLE & STABLE
echo ====================================================
echo.
echo Browse dramas in app, then type: export()
echo.
pause

cd /d "%~dp0"
frida -U -f com.newreading.goodreels -l frida\api-logger-simple.js
