import os
import time
from pathlib import Path
from typing import List

def extract_domains_from_dns(input_file: Path) -> List[str]:
    """从 dns.txt 提取域名（适配 AdBlock 格式规则）"""
    domains = []
    if not input_file.exists():
        raise FileNotFoundError(f"DNS 规则文件不存在: {input_file}")
    
    with input_file.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            # 匹配 ||domain^ 格式的 AdBlock 规则
            if line.startswith("||") and line.endswith("^"):
                domain = line[2:-1]  # 提取 || 和 ^ 之间的域名
                if "." in domain:  # 过滤无效域名
                    domains.append(domain)
    return list(set(domains))  # 去重

def generate_hosts_rules(domains: List[str], output_file: Path) -> None:
    """生成 Hosts 格式规则"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with output_file.open('w', encoding='utf-8') as f:
        f.write("# EasyAds Hosts 去广告规则\n")
        f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}（北京时间）\n")
        f.write("# 来源: EasyAds 规则集\n\n")
        
        for domain in sorted(domains):
            f.write(f"0.0.0.0 {domain}\n")
            f.write(f"0.0.0.0 www.{domain}\n")  # 补充 www 子域

if __name__ == "__main__":
    # 路径适配代码库结构（根目录的 dns.txt 作为输入）
    root_dir = Path(__file__).parent.parent.parent  # 项目根目录
    input_file = root_dir / "dns.txt"
    output_file = root_dir / "hosts.txt"
    
    try:
        domains = extract_domains_from_dns(input_file)
        generate_hosts_rules(domains, output_file)
        print(f"成功生成 Hosts 规则: {output_file}，共 {len(domains)} 条域名")
    except Exception as e:
        print(f"生成失败: {str(e)}")