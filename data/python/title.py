import datetime
import pytz
from pathlib import Path
from typing import Set

HEADER_TEMPLATE = """[Adblock Plus 2.0]
! Title: EasyAds
! Homepage: https://github.com/045200/EasyAds
! Expires: 12 Hours
! Version: {timestamp}（北京时间）
! Description: 适用于AdGuard的去广告规则，合并优质上游规则并去重整理排列
! Total count: {line_count}
"""

def get_beijing_time() -> str:
    """获取当前北京时间"""
    utc_time = datetime.datetime.now(pytz.timezone('UTC'))
    return utc_time.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

def process_rule_files(target_files: Set[str], rules_dir: Path) -> None:
    """处理规则文件，添加标准头信息"""
    beijing_time = get_beijing_time()
    
    for file_path in rules_dir.glob('*.txt'):
        if file_path.name not in target_files:
            continue
            
        try:
            with file_path.open('r', encoding='utf-8') as file:
                lines = file.readlines()
                line_count = len([line for line in lines if line.strip() and not line.startswith('!')])
                content = ''.join(lines)
            
            new_content = HEADER_TEMPLATE.format(
                timestamp=beijing_time,
                line_count=line_count
            ) + content
            
            with file_path.open('w', encoding='utf-8') as file:
                file.write(new_content)
                
            print(f"Processed {file_path.name} with {line_count} rules")
                
        except IOError as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    target_files = {'adblock.txt', 'allow.txt', 'dns.txt'}
    
    # 规则目录改为根目录
    script_dir = Path(__file__).parent
    rules_dir = script_dir.parent.parent  # 项目根目录
    
    print(f"Looking for rules directory at: {rules_dir}")
    print(f"Absolute rules directory path: {rules_dir.absolute()}")
    
    if not rules_dir.exists():
        raise FileNotFoundError(f"Rules directory not found: {rules_dir}")
    
    process_rule_files(target_files, rules_dir)