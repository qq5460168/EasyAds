"""规则文件头部处理工具"""
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 北京时区偏移（UTC+8）
BEIJING_TZ = timedelta(hours=8)
HEADER_TEMPLATE = """[Adblock Plus 2.0]
! 规则更新时间: {timestamp}
! 有效规则数量: {line_count} 条
! 项目地址: https://github.com/qq5460168/EasyAds
! 请不要删除此头部，用于规则识别和更新
\n"""

def get_beijing_time():
    """获取北京时区当前时间"""
    return (datetime.utcnow() + BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")

def process_rule_files(target_files: set, rules_dir: Path) -> None:
    """处理目标文件，添加标准头部并保留有效内容"""
    for file_name in target_files:
        file_path = rules_dir / file_name
        if not file_path.exists():
            print(f"警告: 跳过不存在的文件 - {file_name}")
            continue
        
        try:
            # 读取文件内容
            with file_path.open('r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f]
            
            # 统计有效规则（排除注释和空行）
            valid_lines = [
                line for line in lines
                if line.strip() and not line.lstrip().startswith(('!', '#'))
            ]
            line_count = len(valid_lines)
            
            # 过滤旧头部（保留其他注释）
            content_lines = []
            in_old_header = False
            for line in lines:
                # 检测旧Adblock头部开始
                if line.strip().startswith('[Adblock Plus'):
                    in_old_header = True
                    continue
                # 头部内的注释行跳过
                if in_old_header:
                    if line.lstrip().startswith('!'):
                        continue
                    # 头部结束，恢复正常收集
                    in_old_header = False
                content_lines.append(line)
            
            # 移除头部后的空行
            while content_lines and not content_lines[0].strip():
                content_lines.pop(0)
            content = '\n'.join(content_lines)
            
            # 生成新内容
            new_content = HEADER_TEMPLATE.format(
                timestamp=get_beijing_time(),
                line_count=line_count
            ) + content
            
            # 原子写入（避免文件损坏）
            temp_path = file_path.with_suffix('.tmp')
            with temp_path.open('w', encoding='utf-8') as f:
                f.write(new_content)
            shutil.move(temp_path, file_path)
            
            print(f"已处理 {file_name}，有效规则: {line_count} 条")
            
        except IOError as e:
            print(f"IO错误（{file_name}）: {e}")
        except Exception as e:
            print(f"意外错误（{file_name}）: {str(e)}")

# 示例调用（在主流程中使用）
if __name__ == '__main__':
    target_files = {'adblock.txt', 'allow.txt', 'clash.txt', 'shadowrocket.txt'}
    process_rule_files(target_files, Path('./'))