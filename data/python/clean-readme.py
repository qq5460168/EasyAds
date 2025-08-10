import re
from datetime import datetime
from pathlib import Path
import pytz

def update_readme() -> bool:
    """更新README.md中的规则计数和时间（纯Python实现，不依赖外部工具）"""
    rule_files = {
        'adblock': Path('./data/rules/adblock.txt'),
        'dns': Path('./data/rules/dns.txt'),
        'allow': Path('./data/rules/allow.txt')
    }
    
    # 验证文件存在
    for name, path in rule_files.items():
        if not path.exists():
            print(f"错误: {path} 不存在")
            return False
    
    # 提取规则计数（纯Python替代sed）
    counts: dict[str, str] = {}
    count_pattern = re.compile(r'^! Total count: (\d+)$', re.MULTILINE)  # 预编译正则
    for name, path in rule_files.items():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = count_pattern.search(content)
            if not match:
                raise ValueError(f"{path} 中未找到计数信息")
            counts[name] = match.group(1)
        except (UnicodeDecodeError, ValueError) as e:
            print(f"提取计数失败 {path}: {str(e)}")
            return False
    
    # 获取北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # 更新README
    readme_path = Path('README.md')
    if not readme_path.exists():
        print("错误: README.md 不存在")
        return False
    
    try:
        with open(readme_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            
            # 替换内容（使用预编译正则提高效率）
            replacements = {
                re.compile(r'更新时间:.*'): f'更新时间: {beijing_time} （北京时间）',
                re.compile(r'拦截规则数量.*'): f'拦截规则数量: {counts["adblock"]}',
                re.compile(r'DNS拦截规则数量.*'): f'DNS拦截规则数量: {counts["dns"]}',
                re.compile(r'白名单规则数量.*'): f'白名单规则数量: {counts["allow"]}'
            }
            
            for pattern, repl in replacements.items():
                content = pattern.sub(repl, content)
            
            f.seek(0)
            f.write(content)
            f.truncate()
        
        print("已成功更新README.md中的规则计数和时间")
        return True
        
    except Exception as e:
        print(f"更新失败: {str(e)}")
        return False