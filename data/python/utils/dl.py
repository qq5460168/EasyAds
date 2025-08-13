import requests
import re
import requests
from pathlib import Path
from typing import List, Set

# 白名单规则来源链接（包含备注）
WHITELIST_URLS = [
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",  # 白名单
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt",  # 茯苓白名单
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt",  # 测试hosts（含部分白名单）
]

def fetch_url_content(url: str) -> str:
    """拉取网络文件内容，处理编码和连接错误"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # 尝试常见编码解析
        for encoding in ['utf-8', 'latin-1', 'gbk']:
            try:
                return response.content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return response.text  # 最后尝试默认编码
    except Exception as e:
        print(f"拉取 {url} 失败: {e}")
        return ""

def extract_whitelist_rules(content: str) -> List[str]:
    """从内容中提取白名单规则（AdBlock格式：以@@开头或!注释）"""
    rules = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # 保留白名单规则（@@开头）和注释（!开头）
        if line.startswith(('@@', '!')):
            rules.append(line)
    return rules

def deduplicate_rules(rules: List[str]) -> List[str]:
    """移除重复规则，保留顺序和注释"""
    seen: Set[str] = set()
    unique_rules = []
    for rule in rules:
        # 注释行不去重（可能有重复说明），规则行去重
        if rule.startswith('!'):
            unique_rules.append(rule)
        else:
            if rule not in seen:
                seen.add(rule)
                unique_rules.append(rule)
    return unique_rules

def generate_whitelist(output_path: str = "EasyAds/data/mod/whitelist.txt"):
    """生成最终白名单文件"""
    all_rules = []
    
    # 1. 拉取并提取所有来源的白名单规则
    for url in WHITELIST_URLS:
        content = fetch_url_content(url)
        if content:
            rules = extract_whitelist_rules(content)
            all_rules.extend(rules)
            print(f"从 {url} 提取 {len(rules)} 条规则")
    
    # 2. 去重处理
    unique_rules = deduplicate_rules(all_rules)
    print(f"去重后保留 {len(unique_rules)} 条规则")
    
    # 3. 写入最终文件（保留注释和规则结构）
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 添加文件头部说明
        f.write("! 自动生成的合并白名单规则\n")
        f.write("! 来源: 多个公开白名单规则集合\n\n")
        # 写入规则
        f.write('\n'.join(unique_rules))
    
    print(f"白名单文件已生成: {output_path}")

if __name__ == "__main__":
    generate_whitelist()
