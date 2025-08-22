import re
from pathlib import Path
from datetime import datetime

def generate_hosts_rules():
    """生成Hosts规则（0.0.0.0 域名格式）"""
    input_path = Path("./adblock.txt")
    output_path = Path("./hosts.txt")
    
    if not input_path.exists():
        raise FileNotFoundError(f"源文件不存在: {input_path}")
    
    domain_pattern = re.compile(r'^\|\|([a-zA-Z0-9.-]+)\^.*$', re.MULTILINE)
    
    with input_path.open('r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    domains = set(domain_pattern.findall(content))
    total = len(domains)
    
    with output_path.open('w', encoding='utf-8') as f:
        f.write(f"# Hosts规则 - 自动生成\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 规则总数: {total}\n\n")
        for domain in sorted(domains):
            f.write(f"0.0.0.0 {domain}\n")  # Hosts标准格式
    
    print(f"Hosts规则生成完成，输出到 {output_path}，共 {total} 条")

if __name__ == "__main__":
    generate_hosts_rules()