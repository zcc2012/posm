@echo off
chcp 65001 >nul
setlocal EnableExtensions

title 电脑报价系统
color 0A
cd /d "%~dp0"

set "APP_URL=http://127.0.0.1:5000"
set "VENV_DIR=.venv"
set "PY_CMD="

echo ========================================
echo          电脑报价系统 - Windows
echo ========================================
echo.

where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3"
)

if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo 没有找到 Python 3，正在尝试自动安装...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo.
        echo 当前电脑没有 Python 3，也没有 winget 自动安装工具。
        echo 请先安装 Python 3，然后重新双击本文件。
        echo 下载地址：https://www.python.org/downloads/windows/
        start https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )

    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo.
        echo Python 自动安装失败，请手动安装 Python 3 后重试。
        start https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
    set "PY_CMD=py -3"
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo 首次运行：正在创建本地运行环境...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo 创建运行环境失败。
        pause
        exit /b 1
    )
)

set "PYTHON_EXE=%CD%\%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%CD%\%VENV_DIR%\Scripts\python.exe -m pip"
set "INSTALL_MARK=%CD%\%VENV_DIR%\.requirements-installed"

if not exist "%INSTALL_MARK%" goto install_deps
for %%F in (requirements.txt) do for %%G in ("%INSTALL_MARK%") do if "%%~tF" GTR "%%~tG" goto install_deps
goto deps_ready

:install_deps
echo 正在安装/更新依赖...
%PIP_EXE% install -r requirements.txt
if errorlevel 1 (
    echo.
    echo 依赖安装失败，请检查网络连接后重试。
    pause
    exit /b 1
)
echo ok > "%INSTALL_MARK%"

:deps_ready
netstat -ano | findstr /R /C:":5000 .*LISTENING" >nul 2>nul
if not errorlevel 1 (
    echo 系统已经在运行，正在打开浏览器...
    start "" "%APP_URL%"
    pause
    exit /b 0
)

echo 正在启动系统...
echo 访问地址：%APP_URL%
echo 关闭本窗口即可停止系统。
echo.

start "" "%APP_URL%"
"%PYTHON_EXE%" app.py

echo.
echo 系统已停止。
pause
