"""更新 README.md 中的规则统计区块。

设计要点：
1. 统计区块放在 ```text 代码块里，一行一项（如 `拦截规则数量: 160742`），
   和 666 仓库的样式保持一致：等宽显示、右上角带复制按钮。
   旧版是 markdown 表格，且紧贴 `<!-- STATS:BEGIN -->` 注释、中间没有空行，
   GitHub 会把它整段吞进 HTML 块并当纯文本渲染，于是出现满屏 `|` 的效果。
2. 代码块前后各留一个空行，确保注释标记不会把后面的 markdown 一起吞掉。
3. 代码块内的换行是字面换行，不会被 GitHub 折叠成一行。
"""

import json
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


def _iter_lines(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def _header_count(path: Path) -> int:
    """优先读取规则文件头部的数量声明。"""
    head = "\n".join(_iter_lines(path)[:12])
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
        for line in _iter_lines(path)
        if line.strip() and not line.lstrip().startswith(("!", "#", "["))
    )


def _count_dns_rules(path: Path) -> int:
    return sum(
        1
        for line in _iter_lines(path)
        if line.strip().startswith("||") and line.strip().endswith("^")
    )


def _count_hosts_rules(path: Path) -> int:
    return sum(
        1
        for line in _iter_lines(path)
        if line.strip().startswith("0.0.0.0 ")
    )


def _count_qx_rules(path: Path) -> int:
    return sum(
        1
        for line in _iter_lines(path)
        if line.strip().upper().startswith("DOMAIN,")
    )


def _count_singbox_rules(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    total = 0
    for rule in data.get("rules", []):
        for value in rule.values():
            if isinstance(value, list):
                total += len(value)
    return total


def client_count(filename: str, counter=None) -> int:
    """统计某个客户端规则文件的条数。

    优先用文件头部声明的数量；头部没有时用传入的 counter；
    adb.mrs 是二进制格式无法直接统计，改按其输入源 adblock-filtered.txt 计。
    """
    if filename == "adb.mrs":
        src = ROOT / "adblock-filtered.txt"
        if not src.exists():
            raise FileNotFoundError("规则文件缺失: adblock-filtered.txt")
        return sum(
            1
            for line in _iter_lines(src)
            if line.strip() and not line.lstrip().startswith(("!", "#", "["))
        )

    path = ROOT / filename
    if not path.exists():
        raise FileNotFoundError(f"规则文件缺失: {filename}")
    n = _header_count(path)
    if n >= 0:
        return n
    if counter is None:
        raise ValueError(f"无法统计 {filename} 的规则数量")
    return counter(path)


# (统计项名称, 文件名, 备用计数函数)
CLIENT_SPECS = [
    ("Quantumult X 规则数量", "qx.list", _count_qx_rules),
    ("Clash 规则数量", "Clash.yaml", None),
    ("Clash Meta 规则数量", "adb.mrs", None),
    ("Shadowrocket 规则数量", "Shadowrocket.conf", None),
    ("Singbox 规则数量", "Singbox.json", _count_singbox_rules),
    ("Invizible Pro 规则数量", "invizible.txt", None),
    ("AdClose 规则数量", "AdClose.rule", None),
]


def build_stats_block(counts: dict) -> str:
    rows = [
        ("拦截规则数量", counts["adblock"]),
        ("DNS拦截规则数量", counts["dns"]),
        ("白名单规则数量", counts["allow"]),
        ("Hosts规则数量", counts["hosts"]),
    ]
    for label, _, _ in CLIENT_SPECS:
        rows.append((label.replace(" 规则数量", "规则数量"), counts[label]))

    lines = [
        STATS_BEGIN,
        "",
        "```text",
        f"更新时间: {beijing_time()}（北京时间）",
        "",
    ]
    lines += [f"{name}: {value}" for name, value in rows]
    lines += [
        "```",
        "",
        STATS_END,
    ]
    return "\n".join(lines)


def update_readme(block: str) -> str:
    content = README.read_text(encoding="utf-8")
    if STATS_BEGIN in content and STATS_END in content:
        head, _, rest = content.partition(STATS_BEGIN)
        _, _, tail = rest.partition(STATS_END)
        new_content = (
            head.rstrip("\n") + "\n\n" + block + "\n\n" + tail.lstrip("\n")
        )
    elif ANCHOR in content:
        new_content = content.replace(ANCHOR, "\n" + block + "\n\n" + ANCHOR, 1)
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

        # 客户端条目单独容错：某个文件缺失/格式变动只降级成 DNS 规则数量，
        # 不让整个 README 更新失败。
        for label, filename, counter in CLIENT_SPECS:
            try:
                value = client_count(filename, counter)
                if value <= 0:
                    raise ValueError(f"数量异常: {value}")
                counts[label] = value
            except Exception as e:
                print(f"::warning::统计 {label} 失败（{e}），暂以 DNS 规则数量代替")
                counts[label] = counts["dns"]

        result = update_readme(build_stats_block(counts))
        print(f"README 统计区块已处理（{result}）: {counts}")
    except Exception as e:
        print(f"::error::更新 README 失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
