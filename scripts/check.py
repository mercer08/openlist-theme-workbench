#!/usr/bin/env python3
"""检查 dist/workbench.html：语法 + 供应链特征。

用法：
    python3 scripts/check.py [文件]

退出码：0 = 通过，1 = 发现必须修复的问题。
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "workbench.html"

# 允许出现在主题里的站外域名（文件源与图标）。
# 新增域名必须人工确认后写进这里，否则 CI 直接失败。
ALLOWED_HOSTS = {
    "res.oplist.org",
    "*.115cdn.net",
    "*.115.com",
}

ERROR_PATTERNS = [
    (r"\beval\s*\(", "eval()"),
    (r"new\s+Function\s*\(", "new Function()"),
    (r"document\.write\s*\(", "document.write()"),
    (r"\batob\s*\(", "atob()"),
    (r"String\.fromCharCode", "String.fromCharCode()"),
]

WARN_PATTERNS = [
    (r"createElement\(['\"]script['\"]\)", "动态插入 <script>"),
    (r"localStorage(\.getItem|\.setItem)", "读写 localStorage"),
    (r"postMessage\s*\(", "postMessage"),
    (r"window\.open\s*\(", "window.open"),
]


def host_allowed(host: str) -> bool:
    host = host.lower()
    if host in ALLOWED_HOSTS:
        return True
    for pattern in ALLOWED_HOSTS:
        if pattern.startswith("*.") and host.endswith(pattern[1:]):
            return True
    return False


def main() -> int:
    if not TARGET.is_file() or TARGET.stat().st_size == 0:
        print(f"✗ 找不到或文件为空: {TARGET}")
        return 1

    raw = TARGET.read_text(encoding="utf-8")
    size = len(raw.encode("utf-8"))
    print(f"文件: {TARGET.relative_to(ROOT) if TARGET.is_relative_to(ROOT) else TARGET}")
    print(f"大小: {size} 字节 / {len(raw)} 字符")

    errors: list[str] = []
    warnings: list[str] = []

    # 1. 内联脚本语法检查（主题与 OpenList 一样靠内联脚本运行）
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", raw, re.S)
    print(f"内联脚本: {len(scripts)} 段")
    if not scripts:
        errors.append("没有找到内联 <script>，文件可能不完整")
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            tmp = Path(fh.name)
            fh.write("\n;\n".join(scripts))
        try:
            proc = subprocess.run(
                ["node", "--check", str(tmp)], capture_output=True, text=True
            )
            if proc.returncode != 0:
                errors.append("JS 语法错误：\n" + (proc.stderr.strip() or proc.stdout.strip()))
        except FileNotFoundError:
            warnings.append("未找到 node，跳过语法检查")
        finally:
            tmp.unlink(missing_ok=True)

    # 2. 危险执行 / 编码特征
    for pattern, label in ERROR_PATTERNS:
        hits = len(re.findall(pattern, raw))
        if hits:
            errors.append(f"出现 {label} × {hits}")
    for pattern, label in WARN_PATTERNS:
        hits = len(re.findall(pattern, raw))
        if hits:
            warnings.append(f"{label} × {hits}")

    # 3. 站外域名白名单
    hosts = sorted({m.group(1).lower() for m in re.finditer(r"https?://([^/\"'\s>]+)", raw)})
    foreign = [h for h in hosts if not host_allowed(h)]
    print(f"站外域名: {', '.join(hosts) if hosts else '(无)'}")
    for host in foreign:
        errors.append(f"未在白名单中的站外域名: {host}")

    # 4. 远程脚本
    for match in re.finditer(r"<script[^>]+src=[\"']([^\"']+)[\"']", raw, re.I):
        src = match.group(1)
        if src.startswith(("http://", "https://", "//")):
            errors.append(f"引用了远程脚本: {src}")

    for item in warnings:
        print(f"⚠ {item}")
    for item in errors:
        print(f"✗ {item}")

    if errors:
        print(f"\n结果: 失败（{len(errors)} 个问题）")
        return 1
    print("\n结果: 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
