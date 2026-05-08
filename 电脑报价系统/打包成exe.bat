@echo off
chcp 65001 >nul
title 报价系统打包工具
color 0B
echo ========================================
echo         报价系统打包工具
echo ========================================
echo.

REM 检查是否已安装pyinstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 安装PyInstaller失败！
        echo 请确保已安装Python并添加到PATH。
        pause
        exit /b 1
    )
)

echo.
echo 开始打包报价系统...
echo 这可能需要几分钟时间，请耐心等待。
echo.

REM 创建输出目录
if not exist dist mkdir dist

REM 执行打包命令
pyinstaller --onefile --add-data "templates;templates" --add-data "quotation_system.db;." --name "报价系统" app.py

if errorlevel 1 (
    echo.
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置: %CD%\dist\报价系统.exe
echo.
echo 使用方法：
echo 1. 将生成的exe文件复制到目标电脑
echo 2. 双击运行exe文件
echo 3. 在浏览器中访问 http://127.0.0.1:5000
echo.
echo 注意：
echo - 首次运行可能需要允许通过防火墙
echo - 数据库文件会在exe所在目录创建
echo.
pause