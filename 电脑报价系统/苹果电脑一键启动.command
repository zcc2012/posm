#!/bin/bash
set -e

APP_NAME="电脑报价系统"
APP_URL="http://127.0.0.1:5000"
VENV_DIR=".venv"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "        $APP_NAME - Mac 一键启动"
echo "========================================"
echo ""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "没有找到 Python 3。"
    echo "请先安装 Python 3，然后重新双击本文件。"
    echo "下载地址：https://www.python.org/downloads/macos/"
    osascript -e 'display dialog "没有找到 Python 3，请先安装 Python 3。" buttons {"好"} default button "好"' >/dev/null 2>&1 || true
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "首次运行：正在创建本地运行环境..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

PYTHON_BIN="$SCRIPT_DIR/$VENV_DIR/bin/python"
INSTALL_MARK="$SCRIPT_DIR/$VENV_DIR/.requirements-installed"

if [ ! -f "$INSTALL_MARK" ] || [ "$SCRIPT_DIR/requirements.txt" -nt "$INSTALL_MARK" ]; then
    echo "正在安装/更新依赖..."
    "$PYTHON_BIN" -m pip install -r requirements.txt
    date > "$INSTALL_MARK"
fi

if lsof -ti tcp:5000 >/dev/null 2>&1; then
    echo "系统已经在运行，正在打开浏览器..."
    open "$APP_URL"
    echo ""
    echo "访问地址：$APP_URL"
    read -n 1 -s -r -p "按任意键关闭窗口..."
    exit 0
fi

echo "正在启动系统..."
echo "访问地址：$APP_URL"
echo "关闭此窗口即可停止系统。"
echo ""

(
    sleep 2
    open "$APP_URL"
) &

"$PYTHON_BIN" app.py
