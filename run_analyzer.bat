@echo off
chcp 65001 >nul
echo ============================================
echo   Amazon Sales Report Analyzer
echo ============================================
echo.
echo 请选择操作:
echo.
echo  1. 交互式模式 (推荐)
echo  2. 使用默认参数运行
echo  3. 指定目录运行
echo  4. 显示帮助
echo.
echo  0. 退出
echo.
set /p choice=请输入选项 (0-4):

if "%choice%"=="1" goto interactive
if "%choice%"=="2" goto auto
if "%choice%"=="3" goto custom
if "%choice%"=="4" goto help
if "%choice%"=="0" exit
goto end

:interactive
echo.
echo ============================================
echo 交互式模式
echo ============================================
python amazon_report_analyzer.py -i
pause
goto end

:auto
echo.
echo 正在使用默认参数运行...
python run.py
pause
goto end

:custom
echo.
set /p dir=请输入报告目录 (默认: amazon):
if "%dir%"=="" set dir=amazon
echo.
set /p countries=请输入国家代码，用空格分隔 (直接回车分析全部):
echo.

if "%countries%"=="" (
    python -m amazon_report_analyzer --dir "%dir%"
) else (
    python -m amazon_report_analyzer --dir "%dir%" --countries %countries%
)
pause
goto end

:help
echo.
echo ============================================
echo 使用说明:
echo ============================================
echo.
echo 1. 将报告文件夹放到 amazon/ 子目录
echo 2. 运行 python run.py 启动交互式模式
echo.
echo 命令行用法:
echo   python amazon_report_analyzer.py --dir amazon
echo   python amazon_report_analyzer.py -d amazon -c DE UK
echo   python amazon_report_analyzer.py -d amazon -c DE FR -p "2026年2月"
echo.
echo 详细说明请查看 README.md
echo.
pause
goto end

:end
