# Mac mini 外网访问部署说明

本文档适用于本项目的 Flask 报价系统。项目入口文件为 `app.py`，默认监听 `0.0.0.0:5000`，可用于局域网访问和 Cloudflare Tunnel 转发。

最终目标是让用户只需要打开：

```text
https://quote.taodisplay.com
```

就可以像访问普通网站一样使用报价系统。

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

## 二、像网站一样访问的三种方式

### 1. 局域网访问：公司内部使用

适合 Mac mini 和访问设备在同一个公司 Wi-Fi 或同一个局域网内使用。

访问地址：

```text
http://Mac局域网IP:5000
```

示例：

```text
http://192.168.50.135:5000
```

这种方式最简单，不需要域名，不需要公网，也不需要 Cloudflare。

### 2. Cloudflare Tunnel：临时外网演示

适合临时给客户、同事从外网访问演示，不需要路由器端口转发。

访问地址类似：

```text
https://xxxx.trycloudflare.com
```

这种地址是临时地址，重启 Tunnel 后可能变化，不适合作为长期正式入口。

### 3. 正式域名：长期像网站一样使用

正式长期使用建议绑定域名：

```text
https://quote.taodisplay.com
```

用户最终只需要在浏览器打开这个地址，就可以像普通网站一样访问报价系统。正式域名访问前，必须启用登录保护，并建议配置 HTTPS。

## 三、三种访问方式的操作步骤

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

## 四、Nginx 反向代理方案

正式域名访问时，推荐让 Flask 只在本机 `127.0.0.1:5000` 或当前脚本的 `0.0.0.0:5000` 上运行，再由 Nginx 对外提供网站入口。

目标：

```text
https://quote.taodisplay.com
        ↓
Nginx
        ↓
http://127.0.0.1:5000
        ↓
Flask 报价系统
```

### 安装 Nginx

Mac mini 上安装 Homebrew 后执行：

```bash
brew install nginx
```

启动 Nginx：

```bash
brew services start nginx
```

查看配置目录：

```bash
brew --prefix nginx
```

常见配置文件位置：

```text
/opt/homebrew/etc/nginx/nginx.conf
```

### Nginx 配置示例

把下面配置加入 Nginx 的 `server` 配置中，或放到 Nginx include 的站点配置文件里：

```nginx
server {
    listen 80;
    server_name quote.taodisplay.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

检查配置：

```bash
nginx -t
```

重载 Nginx：

```bash
brew services restart nginx
```

### 域名解析

如果使用普通公网 IP 方式，需要在域名 DNS 中添加：

```text
quote.taodisplay.com  A  Mac mini 所在公网 IP
```

同时路由器需要把公网 80/443 端口转发到 Mac mini。家庭或办公室宽带公网 IP 可能变化，长期使用建议使用固定公网 IP，或改用 Cloudflare Named Tunnel。

如果使用 Cloudflare 正式 Tunnel，可以把 `quote.taodisplay.com` 绑定到 Cloudflare Tunnel，不需要路由器端口转发。这种方式更适合公司内网服务器长期对外提供 HTTPS 访问。

### HTTPS

正式访问目标是：

```text
https://quote.taodisplay.com
```

HTTPS 可以通过两种方式实现：

1. 域名接入 Cloudflare，由 Cloudflare 提供外层 HTTPS。
2. 在 Mac mini 的 Nginx 上配置证书，例如使用 `certbot` 或 Cloudflare Origin Certificate。

长期公网访问时，不建议只开放 HTTP。

## 五、登录保护

系统已增加简单登录入口：

```text
/login
```

退出登录：

```text
/logout
```

登录保护会在以下两个环境变量都存在时启用：

```bash
export QUOTE_ADMIN_USER="admin"
export QUOTE_ADMIN_PASSWORD="请换成强密码"
```

不要把密码写死在代码里，也不要把真实密码提交到 GitHub。

启动系统前设置环境变量：

```bash
cd /path/to/posm/quotation-system
export QUOTE_ADMIN_USER="admin"
export QUOTE_ADMIN_PASSWORD="请换成强密码"
export SECRET_KEY="请换成一串随机长字符串"
./start_mac.sh
```

启用后，未登录用户不能访问客户、材料、工艺、报价、判定标准页面，也不能直接调用对应 API。

如果没有配置 `QUOTE_ADMIN_USER` 和 `QUOTE_ADMIN_PASSWORD`，系统会保持原来的本地开发访问方式，不强制登录。正式公网访问前必须配置登录账号和密码。

## 六、开机自启动：macOS launchd 示例

Mac mini 长期运行时，可以用 launchd 让系统登录后自动启动报价系统。

建议把项目放到非 `Documents` 目录，例如：

```text
/Users/zmv/Services/posm/quotation-system
```

如果继续放在 `Documents` 目录，macOS 隐私权限可能阻止 launchd 执行，需要给 Terminal 或相关运行程序完整磁盘访问权限。

创建文件：

```text
~/Library/LaunchAgents/com.taodisplay.quote.plist
```

示例内容：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.taodisplay.quote</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/zmv/Services/posm/quotation-system/.venv/bin/gunicorn</string>
    <string>-w</string>
    <string>2</string>
    <string>-b</string>
    <string>127.0.0.1:5000</string>
    <string>app:app</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/zmv/Services/posm/quotation-system</string>

  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/Users/zmv/Services/posm/quotation-system/quotation_system.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/zmv/Services/posm/quotation-system/quotation_system.log</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>QUOTE_ADMIN_USER</key>
    <string>admin</string>
    <key>QUOTE_ADMIN_PASSWORD</key>
    <string>请换成强密码</string>
    <key>SECRET_KEY</key>
    <string>请换成一串随机长字符串</string>
  </dict>
</dict>
</plist>
```

加载服务：

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.taodisplay.quote.plist
launchctl kickstart -k gui/$(id -u)/com.taodisplay.quote
```

查看状态：

```bash
launchctl print gui/$(id -u)/com.taodisplay.quote
```

停止并卸载：

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.taodisplay.quote.plist
```

如果使用 Nginx 反向代理，launchd 中 gunicorn 建议监听：

```text
127.0.0.1:5000
```

如果还需要局域网直接访问，则继续监听：

```text
0.0.0.0:5000
```

## 七、最终访问效果

正式部署完成后：

1. Mac mini 开机或登录后自动启动 Flask 报价系统。
2. Nginx 接收 `quote.taodisplay.com` 的访问请求。
3. Nginx 把请求转发到 `http://127.0.0.1:5000`。
4. 用户打开 `https://quote.taodisplay.com`。
5. 未登录时进入 `/login`。
6. 登录成功后像普通网站一样使用报价系统。

用户最终只需要打开：

```text
https://quote.taodisplay.com
```

## 八、数据库备份

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

## 九、Mac mini 防睡眠

为了让报价系统长期运行，建议关闭系统睡眠。可在终端执行：

```bash
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
sudo pmset -a displaysleep 30
```

也建议在系统设置里确认 Mac mini 接通电源时不会自动睡眠。

## 十、安全提醒

1. 不建议长期裸露公开访问报价系统。
2. Cloudflare Tunnel 适合临时演示或短期分享。
3. 长期公网访问前，必须配置 `QUOTE_ADMIN_USER` 和 `QUOTE_ADMIN_PASSWORD`。
4. 不要把 API Key、客户资料、报价数据公开上传。
5. Mac mini 不要睡眠，否则外部访问会中断。
6. 建议每天备份数据库。
7. 如果 `quotation_system.db` 已包含正式业务数据，请不要上传到公开 GitHub 仓库。

## 十一、故障检查

如果本机打不开 `http://127.0.0.1:5000`，检查报价系统终端是否仍在运行，依赖是否安装成功，或端口 5000 是否被占用。

如果局域网打不开，检查手机和 Mac mini 是否在同一个 Wi-Fi，访问地址是否使用 Mac mini 的局域网 IP，macOS 防火墙是否拦截 Python 或 gunicorn。

如果 Cloudflare Tunnel 打不开，检查报价系统是否先启动，`cloudflared tunnel --url http://127.0.0.1:5000` 是否正常输出 `trycloudflare.com` 地址。

如果 Tailscale 打不开，检查两台设备是否都在线，是否登录同一个 Tailscale 网络，以及是否使用 Mac mini 的 `100.x.x.x` 地址。
