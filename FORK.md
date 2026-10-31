# 本 Fork 说明

- 上游：[Nickszy/openlist-theme-workbench](https://github.com/Nickszy/openlist-theme-workbench)，基于 commit `a2bffd1`（2026-10-28）
- 本 Fork：[mercer08/openlist-theme-workbench](https://github.com/mercer08/openlist-theme-workbench)
- 使用环境：内网 Debian + Docker，OpenList v4.2.9（地址与容器名从略）

## 与上游的差异

1. 品牌名 `雪人投研` → `OpenList`
2. 移除写死的根目录自动跳转（`/雪人投研`）
3. PDF 预览改用浏览器内置阅读器（本机未部署 `/pdfjs`，避免 iframe 递归加载整站）
4. Excel 组件加载增加 `window.XLSX` 校验，避免把 SPA 返回的 HTML 当脚本执行

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

- sha256 `be1e5063075089c58073e1ca2ecb7e5f5949448683e828c5ff89a5c42aabdd23`
- 旧值备份：`scripts/deploy.sh` 每次会写入 `/tmp/openlist-customize_head-<时间>.html`

## 回滚

清空「自定义头部」并保存，界面立刻恢复原生外观。

## 升级上游前先查 diff

```bash
git fetch upstream
git diff main upstream/main -- dist/workbench.html \
  | grep -E '^\+' \
  | grep -E 'fetch|XMLHttpRequest|https?://|eval|Function|atob|script|localStorage|postMessage|token'
```

出现新的外链域名、动态脚本、token 读取，先停下来人工确认。
