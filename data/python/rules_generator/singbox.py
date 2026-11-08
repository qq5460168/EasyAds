import json
import re
from pathlib import Path
from datetime import datetime
import pytz


def get_beijing_time():
    """北京时间（UTC+8）。Actions 运行环境默认 UTC，统一在脚本内换算，避免时间标注错位"""
    return datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

def generate_singbox_rules():
    """生成Singbox规则（domain: 域名, policy: reject）"""
    input_path = Path("./adblock.txt")
    output_path = Path("./Singbox.srs")  # 修改输出文件名为Singbox.srs

    if not input_path.exists():
        raise FileNotFoundError(f"源文件不存在: {input_path}")

    domain_pattern = re.compile(r'^\|\|([a-zA-Z0-9.-]+)\^.*$', re.MULTILINE)

    with input_path.open('r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    domains = set(domain_pattern.findall(content))
    total = len(domains)

    with output_path.open('w', encoding='utf-8') as f:
        f.write(f"# Singbox规则 - 自动生成\n")
        f.write(f"# 更新时间: {get_beijing_time()}（北京时间）\n")
        f.write(f"# 规则总数: {total}\n")
        f.write(f"# 注意：本文件为旧版文本格式，sing-box 请使用 Singbox.json\n\n")
        for domain in sorted(domains):
            f.write(f"domain: {domain}, policy: reject\n")  # 保持Singbox标准格式

    # 旧版 .srs 是自定义文本格式，sing-box 实际无法加载（.srs 应为二进制规则集）。
    # 这里保留原文件以兼容既有订阅链接，同时额外生成合法的 JSON 规则集。
    json_path = Path("./Singbox.json")
    payload = {"version": 1, "rules": [{"domain_suffix": sorted(domains)}]}
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))

    print(f"Singbox规则生成完成：{output_path}（兼容文本）与 {json_path}（JSON 规则集），共 {total} 条")

if __name__ == "__main__":
    generate_singbox_rules()
