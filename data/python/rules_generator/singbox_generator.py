import os
import time
import json
from pathlib import Path
from typing import List, Dict

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

def generate_singbox_rules(domains: List[str], output_file: Path) -> None:
    """生成 SingBox 格式规则（JSON）"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 构建 SingBox 路由配置
    singbox_config: Dict = {
        "version": "1.0.0",
        "route": {
            "rules": [
                {
                    "domain_set": ["ads"],
                    "outbound": "block"
                }
            ],
            "domain_set": {
                "ads": sorted(domains)  # 广告域名集合
            },
            "outbounds": [
                {
                    "type": "block",
                    "tag": "block"
                }
            ]
        },
        "log": {
            "level": "info"
        }
    }
    
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(singbox_config, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent.parent
    input_file = root_dir / "dns.txt"
    output_file = root_dir / "singbox_rules.json"
    
    try:
        domains = extract_domains_from_dns(input_file)
        generate_singbox_rules(domains, output_file)
        print(f"成功生成 SingBox 规则: {output_file}，共 {len(domains)} 条域名")
    except Exception as e:
        print(f"生成失败: {str(e)}")