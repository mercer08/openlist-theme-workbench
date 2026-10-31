#!/usr/bin/env bash
# 把 dist/workbench.html 写入 OpenList 的「自定义头部」设置
set -euo pipefail

: "${OPENLIST_URL:?请设置 OPENLIST_URL，例如 https://openlist.example.com}"
: "${OPENLIST_TOKEN:?请设置 OPENLIST_TOKEN（后台 设置 → 其他 → 令牌）}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$ROOT/dist/workbench.html"

[ -f "$FILE" ] || { echo "找不到 $FILE" >&2; exit 1; }

python3 - "$OPENLIST_URL" "$OPENLIST_TOKEN" "$FILE" <<'PY'
import json, sys, time, urllib.request

base = sys.argv[1].rstrip("/")
token = sys.argv[2]
path = sys.argv[3]
html = open(path, encoding="utf-8").read()

def call(p, data=None):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        base + p, data=body, method="POST" if data is not None else "GET"
    )
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

item = call("/api/admin/setting/get?key=customize_head")["data"]
old = item.get("value") or ""

if old:
    backup = f"/tmp/openlist-customize_head-{time.strftime('%Y%m%d-%H%M%S')}.html"
    open(backup, "w", encoding="utf-8").write(old)
    print(f"旧值已备份：{backup}（{len(old)} 字符）")

item["value"] = html
res = call("/api/admin/setting/save", [item])
if res.get("code") != 200:
    print("保存失败：", res, file=sys.stderr)
    sys.exit(1)

print(f"已保存，接口返回 {res.get('code')}；写入 {len(html)} 字符")
PY

echo "验证：curl -s \"$OPENLIST_URL/\" | grep -c xh-tree"
