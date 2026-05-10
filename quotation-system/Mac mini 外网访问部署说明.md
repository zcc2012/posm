# Mac mini 外网访问部署说明

本文档适用于本项目的 Flask 报价系统。项目入口文件为 `app.py`，默认监听 `0.0.0.0:5000`，可用于局域网访问和 Cloudflare Tunnel 转发。

## 一、首次部署

进入项目目录：

```bash
cd /path/to/posm/quotation-system
```

启动报价系统：

```bash
chmod +x start_mac.sh
./start_mac.sh
```

脚本会自动创建或复用 `.venv` 虚拟环境，安装 `requirements.txt` 依赖，并优先使用 gunicorn 启动：

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

启动成功后，终端会显示：

```text
本机访问：http://127.0.0.1:5000
局域网访问：http://Mac局域网IP:5000
```

## 二、三种访问方式

### 1. 局域网访问

Mac mini 和手机、平板、其他电脑在同一个 Wi-Fi 下时，可以通过下面地址访问：

```text
http://Mac局域网IP:5000
```

如果脚本没有自动显示局域网 IP，可在 Mac mini 终端执行：

```bash
ipconfig getifaddr en0
```

也可以在系统设置的 Wi-Fi 或网络详情里查看 IP 地址。

### 2. Cloudflare Tunnel

Cloudflare Tunnel 适合临时给客户、同事从外网访问演示，不需要路由器端口转发。

先在一个终端启动报价系统：

```bash
./start_mac.sh
```

再打开另一个终端启动 Cloudflare Tunnel：

```bash
chmod +x start_cloudflare_tunnel_mac.sh
./start_cloudflare_tunnel_mac.sh
```

如果提示未安装 `cloudflared`，执行：

```bash
brew install cloudflared
```

启动成功后，复制终端里生成的 `https://xxxx.trycloudflare.com` 地址给别人访问。

### 3. Tailscale

Tailscale 适合自己或内部员工安全访问，不公开到公网。

在 Mac mini 和手机、电脑上都安装并登录 Tailscale 后，查看 Mac mini 的 Tailscale IP，通常是 `100.x.x.x`。然后访问：

```text
http://100.x.x.x:5000
```

## 三、数据库备份

当前系统使用 SQLite 数据库：

```text
quotation_system.db
```

手动备份：

```bash
chmod +x backup_db_mac.sh
./backup_db_mac.sh
```

备份文件会保存到：

```text
~/Documents/quotation_system_backups
```

文件名示例：

```text
quotation_system_20260510_153000.db
```

建议每天备份数据库。备份目录不要提交到 GitHub。

## 四、Mac mini 防睡眠

为了让报价系统长期运行，建议关闭系统睡眠。可在终端执行：

```bash
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
sudo pmset -a displaysleep 30
```

也建议在系统设置里确认 Mac mini 接通电源时不会自动睡眠。

## 五、安全提醒

1. 不建议长期裸露公开访问报价系统。
2. Cloudflare Tunnel 适合临时演示或短期分享。
3. 长期公网访问前，必须给系统增加登录密码或其他身份验证。
4. 不要把 API Key、客户资料、报价数据公开上传。
5. Mac mini 不要睡眠，否则外部访问会中断。
6. 建议每天备份数据库。
7. 如果 `quotation_system.db` 已包含正式业务数据，请不要上传到公开 GitHub 仓库。

## 六、故障检查

如果本机打不开 `http://127.0.0.1:5000`，检查报价系统终端是否仍在运行，依赖是否安装成功，或端口 5000 是否被占用。

如果局域网打不开，检查手机和 Mac mini 是否在同一个 Wi-Fi，访问地址是否使用 Mac mini 的局域网 IP，macOS 防火墙是否拦截 Python 或 gunicorn。

如果 Cloudflare Tunnel 打不开，检查报价系统是否先启动，`cloudflared tunnel --url http://127.0.0.1:5000` 是否正常输出 `trycloudflare.com` 地址。

如果 Tailscale 打不开，检查两台设备是否都在线，是否登录同一个 Tailscale 网络，以及是否使用 Mac mini 的 `100.x.x.x` 地址。
