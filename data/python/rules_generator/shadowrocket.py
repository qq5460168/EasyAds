import re
from pathlib import Path
from datetime import datetime

def generate_shadowrocket_rules():
    """生成Shadowrocket规则（DOMAIN-SUFFIX格式）"""
    input_path = Path("./adblock.txt")
    output_path = Path("./Shadowrocket.conf")  # 输出文件名为Shadowrocket.conf
    
    if not input_path.exists():
        raise FileNotFoundError(f"源文件不存在: {input_path}")
    
    # 匹配Adblock中的域名规则（||domain.com^）
    domain_pattern = re.compile(r'^\|\|([a-zA-Z0-9.-]+)\^.*$', re.MULTILINE)
    
    with input_path.open('r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 提取并去重域名
    domains = set(domain_pattern.findall(content))
    total = len(domains)
    
    with output_path.open('w', encoding='utf-8') as f:
        f.write(f"# Shadowrocket规则 - 自动生成\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 规则总数: {total}\n\n")
        for domain in sorted(domains):
            # 按照指定格式生成规则，使用Reject（首字母大写）
            f.write(f"DOMAIN-SUFFIX,{domain},Reject\n")
    
    print(f"Shadowrocket规则生成完成，输出到 {output_path}，共 {total} 条")

if __name__ == "__main__":
    generate_shadowrocket_rules()