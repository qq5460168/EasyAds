# data/python/rules_generator/loon.py
import sys
from pathlib import Path
import re

def extract_to_loon_rules(input_file: Path, output_file: Path):
    """提取规则并转换为Loon格式"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取域名规则（假设规则格式为 ||domain^ 或类似格式）
        pattern = r'\|\|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\^?'
        domains = re.findall(pattern, content)
        
        # 去重处理
        unique_domains = list(set(domains))
        total_count = len(unique_domains)
        
        # 生成Loon格式规则（DNS拦截）
        loon_rules = []
        for domain in unique_domains:
            loon_rules.append(f"DOMAIN,{domain},REJECT")
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Loon 广告拦截规则\n")
            f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 规则总数: {total_count}\n\n")
            f.write('\n'.join(loon_rules))
        
        print(f"生成成功! 规则总数: {total_count}")
        return True
        
    except Exception as e:
        print(f"生成失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 关键修复：输出文件名改为 Loon.conf 与工作流匹配
    input_file = Path("./dns.txt")
    output_file = Path("./Loon.conf")  # 修复文件名
    success = extract_to_loon_rules(input_file, output_file)
    sys.exit(0 if success else 1)