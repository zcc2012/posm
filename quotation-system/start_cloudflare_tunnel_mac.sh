#!/usr/bin/env bash
set -euo pipefail

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "未检测到 cloudflared。"
  echo "请先安装 Homebrew，然后执行："
  echo "brew install cloudflared"
  exit 1
fi

echo "请确认报价系统已经在另一个终端启动："
echo "http://127.0.0.1:5000"
echo ""
echo "Cloudflare Tunnel 启动后，请复制终端里生成的 https://xxxx.trycloudflare.com 地址给别人访问。"
echo ""

exec cloudflared tunnel --url http://127.0.0.1:5000
