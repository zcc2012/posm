#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR=".venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PORT="${PORT:-5000}"
HOST="0.0.0.0"

if [ ! -d "$VENV_DIR" ]; then
  echo "正在创建 Python 虚拟环境：$VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "正在安装/更新依赖..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r requirements.txt

get_lan_ip() {
  local ip=""
  ip="$(ipconfig getifaddr en0 2>/dev/null || true)"
  if [ -z "$ip" ]; then
    ip="$(ipconfig getifaddr en1 2>/dev/null || true)"
  fi
  if [ -z "$ip" ]; then
    local iface=""
    iface="$(route get default 2>/dev/null | awk '/interface:/{print $2; exit}' || true)"
    if [ -n "$iface" ]; then
      ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
    fi
  fi
  echo "$ip"
}

LAN_IP="$(get_lan_ip)"

echo ""
echo "报价系统即将启动："
echo "本机访问：http://127.0.0.1:${PORT}"
if [ -n "$LAN_IP" ]; then
  echo "局域网访问：http://${LAN_IP}:${PORT}"
else
  echo "局域网访问：未自动识别 Mac 局域网 IP，请在 系统设置 > Wi-Fi/网络 中查看"
fi
echo ""

if command -v "$VENV_DIR/bin/gunicorn" >/dev/null 2>&1; then
  exec "$VENV_DIR/bin/gunicorn" -w "${GUNICORN_WORKERS:-2}" -b "${HOST}:${PORT}" app:app
fi

echo "未找到 gunicorn，将使用 python app.py 启动。"
exec "$VENV_DIR/bin/python" app.py
