@echo off
chcp 65001 >nul
title 报价系统（便携版）
color 0A
echo ========================================
echo           报价系统启动器（便携版）
echo ========================================
echo.

REM 检查venv目录是否存在
if not exist venv (
    echo 未找到便携式Python环境，正在创建...
    echo 这可能需要几分钟时间，请耐心等待。
    echo.
    
    REM 检查是否已安装virtualenv
    pip show virtualenv >nul 2>&1
    if errorlevel 1 (
        echo 正在安装virtualenv...
        pip install virtualenv
        if errorlevel 1 (
            echo 安装virtualenv失败！
            echo 请确保已安装Python并添加到PATH。
            pause
            exit /b 1
        )
    )
    
    echo 正在创建虚拟环境...
    virtualenv venv
    if errorlevel 1 (
        echo 创建虚拟环境失败！
        pause
        exit /b 1
    )
    
    echo 正在安装依赖...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 安装依赖失败！
        pause
        exit /b 1
    )
    
    echo 便携式环境创建完成！
    echo.
)

echo 正在启动报价系统服务...
echo.

REM 启动Python服务（后台运行）
start /B venv\Scripts\python app.py

REM 等待服务启动
echo 等待服务启动中...
timeout /t 3 /nobreak >nul

REM 自动打开浏览器
echo 正在打开浏览器...
start http://127.0.0.1:5000

echo.
echo ========================================
echo 报价系统已启动！
echo 访问地址: http://127.0.0.1:5000
echo ========================================
echo.
echo 提示：
echo - 关闭此窗口将停止报价系统服务
echo - 如需重启系统，请关闭此窗口后重新运行
echo.
echo 按任意键退出并停止服务...
pause >nul

REM 结束Python进程
taskkill /f /im python.exe >nul 2>&1
echo 服务已停止。