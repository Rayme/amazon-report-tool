@echo off
chcp 65001 >nul
echo ============================================
echo   Amazon Sales Report Analyzer
echo ============================================
echo.
echo Choose action:
echo.
echo  1. Auto detect and generate report
echo  2. Show help
echo.
echo  0. Exit
echo.
set /p choice=Enter option: 

if "%choice%"=="1" goto auto
if "%choice%"=="2" goto help
if "%choice%"=="0" exit
goto end

:auto
python run.py
pause
goto end

:help
echo.
echo ============================================
echo How to use:
echo ============================================
echo.
echo 1. Put report folders in amazon/ subfolder
echo 2. Run: python run.py
echo.
echo For more info see README.md
echo.
pause
goto end

:end
