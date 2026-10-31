# 本 Fork 说明

- 上游：[Nickszy/openlist-theme-workbench](https://github.com/Nickszy/openlist-theme-workbench)，基于 commit `a2bffd1`（2026-10-28）
- 本 Fork：[mercer08/openlist-theme-workbench](https://github.com/mercer08/openlist-theme-workbench)
- 使用环境：内网 Debian + Docker，OpenList v4.2.9（地址与容器名从略）

## 与上游的差异

1. 品牌名 `雪人投研` → `OpenList`
2. 移除写死的根目录自动跳转（`/雪人投研`）
3. PDF 预览改用浏览器内置阅读器（本机未部署 `/pdfjs`，避免 iframe 递归加载整站）
4. Excel 组件加载增加 `window.XLSX` 校验，避免把 SPA 返回的 HTML 当脚本执行
5. 移除 Word / PPT 的 `view.officeapps.live.com` 在线预览（不再把签名直链发给第三方），改为本地下载

## 新增功能（相对上游）

- **排序**：点击表头「名称 / 大小 / 修改时间」在升序、降序间切换；文件夹始终置顶；偏好存入 `localStorage.xhSort`。
- **文件管理**：新建文件夹、上传（`PUT /api/fs/put`，支持多选顺序上传）、重命名、删除、下载；行内悬停出现操作按钮。
- **离线下载**：调用 `POST /api/fs/add_offline_download`，工具列表取自 `/api/public/offline_download_tools?path=<当前目录>`；115 存储会以原生 `115 Open` 工具直接落到当前目录。
- **任务面板**：`/api/task/offline_download/{undone,done}`，展示进度、取消任务，打开时每 4 秒刷新。
- 所有请求均为同源 `/api/*`，没有新增外链；未登录时工具栏自动隐藏。

## 部署方式

后台 → 设置 → 全局 → 自定义头部，粘贴 `dist/workbench.html` 全文。

或用脚本（token 取自后台「设置 → 其他 → 令牌」）：

```bash
OPENLIST_URL=https://openlist.example.com \
OPENLIST_TOKEN=<token> \
./scripts/deploy.sh
```

验证：

```bash
curl -s https://openlist.example.com/ | grep -c xh-tree
```

## 当前线上版本

- sha256 `3355b5453294e15fa84f061f62f67af07c2ef5f151fafd02d68387d668f1021a`
- 旧值备份：`scripts/deploy.sh` 每次会写入 `/tmp/openlist-customize_head-<时间>.html`

## 回滚

清空「自定义头部」并保存，界面立刻恢复原生外观。

## 可选：反向代理加 CSP

注入式方案自身没有 CSP，建议在反向代理层补一层，限制外发通道：

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' data:; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://<文件源域名>; media-src 'self' blob: https://<文件源域名>; frame-src 'self' https://<文件源域名>; connect-src 'self' https://<文件源域名>; object-src 'none'; base-uri 'self'; form-action 'self'" always;
```

注意：

- `<文件源域名>` 换成实际直链域名（如 115 的 CDN），否则 PDF / 图片 / 视频预览会被拦；本仓库已无第三方预览，不需要放行任何预览服务。
- `script-src` 必须保留 `'unsafe-inline'`——主题与 OpenList 前端都靠内联脚本；`data:` 是 OpenList 做 `import.meta.resolve` 探测所需。
- 改完用浏览器控制台确认没有 `Content Security Policy` 报错，并实际点开一次 PDF / 图片预览。

## 升级上游前先查 diff

```bash
git fetch upstream
git diff main upstream/main -- dist/workbench.html \
  | grep -E '^\+' \
  | grep -E 'fetch|XMLHttpRequest|https?://|eval|Function|atob|script|localStorage|postMessage|token'
```

出现新的外链域名、动态脚本、token 读取，先停下来人工确认。

## 提交前自检

```bash
python3 scripts/check.py
```

检查项：内联脚本语法（`node --check`）、`eval` / `new Function` / `document.write` / `atob`、站外域名白名单（`res.oplist.org`、`*.115cdn.net`、`*.115.com`）、远程 `<script src>`。

同一脚本会在 GitHub Actions（`.github/workflows/validate.yml`，托管 runner、只读权限、无 secrets）里对 `push` 与 `pull_request` 自动执行；CI 只做校验，不接触任何内网资源，部署仍需手动执行。
