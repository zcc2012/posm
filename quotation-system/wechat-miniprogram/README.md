# 明邦报价系统微信小程序 Demo

这个目录是报价系统的微信小程序前端 Demo。

现有网页版保持不变；小程序只新增一套适合手机操作的界面。两端共用同一个 Flask 后端接口和同一个 SQLite 数据库。

## 项目目录

```text
/Users/zmv/Documents/New project 2/posm/quotation-system/wechat-miniprogram
```

## 当前接口

小程序接口地址在 `utils/api.js`：

```text
https://posm.mingbang.net/quote
```

当前会读取：

- `/api/material_categories`
- `/api/materials`
- `/api/processes`
- `/api/pricing_standards/match`

## 用微信开发者工具打开

1. 打开微信开发者工具。
2. 使用你的微信扫码登录。
3. 选择“导入项目”。
4. 项目目录选择：

```text
/Users/zmv/Documents/New project 2/posm/quotation-system/wechat-miniprogram
```

5. AppID 可以先用测试号/游客模式；如果要绑定正式小程序，请把 `project.config.json` 里的 `appid` 改成你的正式 AppID。

## Codex 浏览器预览

为了方便 Codex 和你一起改手机界面，这里额外提供了一个浏览器预览页：

```text
preview/index.html
```

启动本地预览服务：

```bash
cd "/Users/zmv/Documents/New project 2/posm/quotation-system/wechat-miniprogram"
python3 -m http.server 8091
```

浏览器打开：

```text
http://127.0.0.1:8091/preview/index.html
```

这个预览页只用于快速看手机 UI，不会修改数据库，也不会影响正式网页版。确认界面方向后，再把样式同步到小程序的 `pages/**/*.wxml` 和 `pages/**/*.wxss`。

## 正式上线前必须设置

到微信公众平台的小程序后台配置“request 合法域名”：

```text
https://posm.mingbang.net
```

开发工具里当前为了 Demo 打开了 `urlCheck: false`，方便本地调试。真机预览和发布时必须配置合法域名。

## 当前 Demo 页面

- 首页：手机端报价入口。
- 报价：从电脑网页版后台维护好的材料、工艺、分类中选择项目，填写尺寸和数量后自动计算。

材料、工艺、分类、判定标准等基础资料维护不放在小程序里，继续使用电脑网页版后台。

后续可以继续补：

- 登录权限。
- 客户选择与保存报价单。
- 报价明细页。
- 把所有核心报价公式统一迁移到后端，确保网页和小程序计算永远一致。
