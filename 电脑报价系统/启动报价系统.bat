@echo off
chcp 65001 >nul
echo 正在启动报价系统...
echo.
echo 系统将在浏览器中自动打开: http://127.0.0.1:5000
echo 如需停止服务，请按 Ctrl+C
echo.
python app.py
pause