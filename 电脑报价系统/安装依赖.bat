@echo off
chcp 65001 >nul
title 安装报价系统依赖
color 0B
echo ========================================
echo         报价系统依赖安装器
echo ========================================
echo.
echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误：未找到Python环境！
    echo 请先安装Python 3.7或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

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
echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 现在您可以使用以下方式启动系统：
echo 1. 双击 "一键启动.bat" （推荐）
echo 2. 双击 "启动报价系统.bat"
echo.
echo 如需打包成exe文件，请运行：
echo pip install auto-py-to-exe
echo auto-py-to-exe
echo.
pause