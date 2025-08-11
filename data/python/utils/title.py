import datetime
import pytz
from pathlib import Path
from typing import Set
import shutil

HEADER_TEMPLATE = """[Adblock Plus 2.0]
! Title: EasyAds
! Homepage: https://github.com/045200/EasyAds
! Expires: 12 Hours
! Version: {timestamp}（北京时间）
! Description: 适用于AdGuard的去广告规则，合并优质上游规则并去重整理排列
! Total count: {line_count}
"""

def get_beijing_time() -> str:
    """获取当前北京时间（简化实现）"""
    return datetime.datetime.now(
        pytz.timezone('Asia/Shanghai')
    ).strftime('%Y-%m-%d %H:%M:%S')

def process_rule_files(target_files: Set[str], rules_dir: Path) -> None:
    """处理规则文件，添加标准头信息（优化版）"""
    beijing_time = get_beijing_time()
    
    # 显式遍历目标文件而非全局匹配，避免处理无关文件
    for file_name in target_files:
        file_path = rules_dir / file_name
        if not file_path.exists():
            print(f"警告: 跳过不存在的文件 - {file_path.name}")
            continue
            
        try:
            # 读取文件内容
            with file_path.open('r', encoding='utf-8') as file:
                lines = file.readlines()
                
            # 精确计数：排除注释行（!和#开头）、空行，保留有效规则
            valid_lines = [
                line for line in lines 
                if line.strip() 
                and not line.lstrip().startswith(('!', '#'))  # 允许行首有空格的规则
            ]
            line_count = len(valid_lines)
            
            # 过滤原文件中的旧头部（避免重复添加）
            content_lines = []
            header_started = False
            for line in lines:
                # 检测并跳过已存在的Adblock头部
                if line.strip().startswith('[Adblock Plus'):
                    header_started = True
                    continue
                if header_started:
                    # 跳过头部区域的注释行
                    if line.lstrip().startswith('!'):
                        continue
                    # 头部结束，保留剩余内容
                    header_started = False
                content_lines.append(line)
            content = ''.join(content_lines).lstrip()  # 移除头部后的多余空行
            
            # 生成新内容
            new_content = HEADER_TEMPLATE.format(
                timestamp=beijing_time,
                line_count=line_count
            ) + content
            
            # 先写入临时文件，成功后替换原文件（防止文件损坏）
            temp_path = file_path.with_suffix('.tmp')
            with temp_path.open('w', encoding='utf-8') as file:
                file.write(new_content)
            # 原子操作替换原文件
            shutil.move(temp_path, file_path)
                
            print(f"已处理 {file_path.name}，有效规则: {line_count} 条")
                
        except IOError as e:
            print(f"处理 {file_path.name} 出错: {e}")
        except Exception as e:
            print(f"意外错误（{file_path.name}）: {str(e)}")

if __name__ == "__main__":
    target_files = {'adblock.txt', 'allow.txt', 'dns.txt', 'adblock-filtered.txt'}
    
    # 统一路径计算方式（与其他脚本保持一致）
    script_dir = Path(__file__).parent
    rules_dir = script_dir.parent.parent  # 确保指向项目根目录（EasyAds/）
    
    # 路径验证与日志
    print(f"规则处理目录: {rules_dir.resolve()}")
    print(f"目标文件列表: {sorted(target_files)}")
    
    if not rules_dir.exists():
        raise FileNotFoundError(f"规则目录不存在: {rules_dir}")
    
    process_rule_files(target_files, rules_dir)
