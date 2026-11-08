"""更新 README.md 中的规则统计区块。

历史问题：旧版用 `sed -n "s/^! Total count: //p"` 取数量，但 adblock.txt
由 title.py 写入的头部是 `! 有效规则数量: N 条`，永远匹配不到，导致
ValueError 被捕获后只打印"更新失败"仍以 0 退出——README 从此再没更新过。
本版改为直接解析文件内容/头部，并把结果写进固定的 STATS 区块。
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import pytz

ROOT = Path(__file__).resolve().parent.parent.parent.parent
README = ROOT / "README.md"
STATS_BEGIN = "<!-- STATS:BEGIN -->"
STATS_END = "<!-- STATS:END -->"
ANCHOR = '<h2 id="a">'


def beijing_time() -> str:
    return datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


def _header_count(path: Path) -> int:
    """优先读取规则文件头部的数量声明。"""
    text = path.read_text(encoding="utf-8", errors="ignore")
    head = "\n".join(text.splitlines()[:12])
    for pattern in (r"!\s*有效规则数量:\s*(\d+)\s*条", r"#\s*规则总数:\s*(\d+)"):
        m = re.search(pattern, head)
        if m:
            return int(m.group(1))
    return -1


def count_rules(path: Path, counter) -> int:
    """头部没有数量时按行统计。"""
    if not path.exists():
        raise FileNotFoundError(f"规则文件缺失: {path.name}")
    n = _header_count(path)
    return n if n >= 0 else counter(path)


def _count_adblock_rules(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.lstrip().startswith(("!", "#", "["))
    )


def _count_dns_rules(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip().startswith("||") and line.strip().endswith("^")
    )


def _count_hosts_rules(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip().startswith("0.0.0.0 ")
    )


def build_stats_block(counts: dict) -> str:
    lines = [
        STATS_BEGIN,
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 更新时间 | {beijing_time()}（北京时间） |",
        f"| 拦截规则数量 | {counts['adblock']} |",
        f"| DNS 拦截规则数量 | {counts['dns']} |",
        f"| 白名单规则数量 | {counts['allow']} |",
        f"| Hosts 规则数量 | {counts['hosts']} |",
        STATS_END,
    ]
    return "\n".join(lines)


def update_readme(block: str) -> str:
    content = README.read_text(encoding="utf-8")
    if STATS_BEGIN in content and STATS_END in content:
        head, _, rest = content.partition(STATS_BEGIN)
        _, _, tail = rest.partition(STATS_END)
        new_content = head + block + tail
    elif ANCHOR in content:
        new_content = content.replace(ANCHOR, block + "\n\n" + ANCHOR, 1)
    else:
        raise ValueError('README 中既没有 STATS 标记，也找不到 <h2 id="a"> 锚点')

    if new_content != content:
        README.write_text(new_content, encoding="utf-8")
        return "updated"
    return "unchanged"


def main() -> None:
    try:
        counts = {
            "adblock": count_rules(ROOT / "adblock.txt", _count_adblock_rules),
            "dns": count_rules(ROOT / "dns.txt", _count_dns_rules),
            "allow": count_rules(ROOT / "allow.txt", _count_adblock_rules),
            "hosts": count_rules(ROOT / "hosts.txt", _count_hosts_rules),
        }
        for name, value in counts.items():
            if value <= 0:
                raise ValueError(f"{name} 规则数量异常: {value}")
        result = update_readme(build_stats_block(counts))
        print(f"README 统计区块已处理（{result}）: {counts}")
    except Exception as e:
        print(f"::error::更新 README 失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
