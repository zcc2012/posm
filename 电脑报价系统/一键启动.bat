@echo off
chcp 65001 >nul
title 报价系统
color 0A
echo ========================================
echo           报价系统启动器
echo ========================================
echo.
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