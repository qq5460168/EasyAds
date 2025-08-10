# -*- coding: utf-8 -*-
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
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

def process_rule_files(target_files: Set[str], rules_dir: Path) -> None:
    """处理规则文件，添加标准头信息"""
    beijing_time = get_beijing_time()
    
    for file_path in rules_dir.glob('*.txt'):
        if file_path.name not in target_files:
            continue
            
        try:
            # 读取文件内容并计算有效行数（非空、非注释）
            lines = []
            for encoding in ['utf-8', 'gbk', 'latin-1']:
                try:
                    with file_path.open('r', encoding=encoding) as file:
                        lines = file.readlines()
                    break
                except UnicodeDecodeError:
                    continue

            # 过滤注释和空行
            valid_lines = [line for line in lines if line.strip() and not line.startswith('!')]
            line_count = len(valid_lines)
            
            # 生成新内容（移除旧头信息）
            new_content = HEADER_TEMPLATE.format(
                timestamp=beijing_time,
                line_count=line_count
            )
            # 跳过旧头信息（以!开头的行）
            for line in lines:
                if not line.strip().startswith('!') and line.strip():
                    new_content += line
            
            # 写回文件
            with file_path.open('w', encoding='utf-8') as file:
                file.write(new_content)
                
            print(f"处理完成: {file_path.name}，有效规则 {line_count} 条")
                
        except IOError as e:
            print(f"处理 {file_path.name} 失败: {e}")

if __name__ == "__main__":
    target_files = {'adblock.txt', 'allow.txt', 'dns.txt'}
    
    # 精确计算路径（避免相对路径问题）
    script_dir = Path(__file__).resolve().parent  # 当前脚本目录
    rules_dir = script_dir.parent / "rules"  # data/rules/
    
    if not rules_dir.exists():
        raise FileNotFoundError(f"规则目录不存在: {rules_dir}")
    
    process_rule_files(target_files, rules_dir)