import os
import time
from pathlib import Path
from typing import List

def extract_domains_from_dns(input_file: Path) -> List[str]:
    """从 dns.txt 提取域名"""
    domains = []
    if not input_file.exists():
        raise FileNotFoundError(f"DNS 规则文件不存在: {input_file}")
    
    with input_file.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line.startswith("||") and line.endswith("^"):
                domain = line[2:-1]
                if "." in domain:
                    domains.append(domain)
    return list(set(domains))

def generate_invizible_rules(domains: List[str], output_file: Path) -> None:
    """生成 Invizible 规则（兼容 Hosts 格式）"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with output_file.open('w', encoding='utf-8') as f:
        f.write("# EasyAds Invizible 去广告规则\n")
        f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}（北京时间）\n")
        f.write("# 来源: EasyAds 规则集\n")
        f.write("# 适配 Invizible 应用的 Hosts 格式\n\n")
        
        for domain in sorted(domains):
            # Invizible 直接使用 Hosts 格式（0.0.0.0 屏蔽）
            f.write(f"0.0.0.0 {domain}\n")
            f.write(f"0.0.0.0 www.{domain}\n")

if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    input_file = root_dir / "dns.txt"
    output_file = root_dir / "invizible_hosts.txt"
    
    try:
        domains = extract_domains_from_dns(input_file)
        generate_invizible_rules(domains, output_file)
        print(f"成功生成 Invizible 规则: {output_file}，共 {len(domains)} 条域名")
    except Exception as e:
        print(f"生成失败: {str(e)}")