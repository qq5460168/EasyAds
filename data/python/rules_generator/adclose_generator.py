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

def generate_adclose_rules(domains: List[str], output_file: Path) -> None:
    """生成 AdClose 规则（AdBlock 语法）"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with output_file.open('w', encoding='utf-8') as f:
        f.write("! EasyAds AdClose 去广告规则\n")
        f.write(f"! 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}（北京时间）\n")
        f.write("! 来源: EasyAds 规则集\n")
        f.write("! 适配 AdClose 应用的 AdBlock 格式\n\n")
        
        for domain in sorted(domains):
            # AdClose 支持标准 AdBlock 规则（||domain^）
            f.write(f"||{domain}^\n")
            # 补充广告路径过滤
            f.write(f"||{domain}/*ad*\n")
            f.write(f"||{domain}/*track*\n")

if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    input_file = root_dir / "dns.txt"
    output_file = root_dir / "adclose_rules.txt"
    
    try:
        domains = extract_domains_from_dns(input_file)
        generate_adclose_rules(domains, output_file)
        print(f"成功生成 AdClose 规则: {output_file}，共 {len(domains)} 条域名")
    except Exception as e:
        print(f"生成失败: {str(e)}")