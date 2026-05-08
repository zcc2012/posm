@echo off
chcp 65001 >nul
title 报价系统一键安装启动
color 0A
echo ========================================
echo       报价系统一键安装启动工具
echo ========================================
echo.

REM 检查Python环境
echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误：未找到Python环境！
    echo 请先安装Python 3.7或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时请勾选「Add Python to PATH」选项
    pause
    exit /b 1
)

REM 安装依赖
echo.
echo 正在安装依赖包...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo 安装失败！请检查网络连接或Python环境
    pause
    exit /b 1
)

echo.
echo 依赖安装完成！
echo.

REM 启动系统
echo 正在启动报价系统服务...
echo.

REM 启动Python服务（后台运行）
start /B python app.py

REM 等待服务启动
echo 等待服务启动中...
timeout /t 3 /nobreak >nul

REM 自动打开浏览器
echo 正在打开浏览器...
start http://127.0.0.1:5000

echo.
echo ========================================
echo 报价系统已安装并启动！
echo 访问地址: http://127.0.0.1:5000
echo ========================================
echo.
echo 提示：
echo - 关闭此窗口将停止报价系统服务
echo - 如需重启系统，请关闭此窗口后重新运行
echo - 下次启动只需双击「一键启动.bat」即可
echo.
echo 按任意键退出并停止服务...
pause >nul

REM 结束Python进程
taskkill /f /im python.exe >nul 2>&1
echo 服务已停止。