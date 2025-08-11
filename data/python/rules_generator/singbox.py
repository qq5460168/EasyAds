import re
from pathlib import Path
from datetime import datetime

def generate_singbox_rules():
    """生成Singbox规则（domain: 域名, policy: reject）"""
    input_path = Path("./adblock.txt")
    output_path = Path("./singbox.txt")
    
    if not input_path.exists():
        raise FileNotFoundError(f"源文件不存在: {input_path}")
    
    domain_pattern = re.compile(r'^\|\|([a-zA-Z0-9.-]+)\^.*$', re.MULTILINE)
    
    with input_path.open('r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    domains = set(domain_pattern.findall(content))
    total = len(domains)
    
    with output_path.open('w', encoding='utf-8') as f:
        f.write(f"# Singbox规则 - 自动生成\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 规则总数: {total}\n\n")
        for domain in sorted(domains):
            f.write(f"domain: {domain}, policy: reject\n")  # Singbox标准格式
    
    print(f"Singbox规则生成完成，输出到 {output_path}，共 {total} 条")

if __name__ == "__main__":
    generate_singbox_rules()