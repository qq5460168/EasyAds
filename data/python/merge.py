# -*- coding: utf-8 -*-
import re
from pathlib import Path
from typing import List, Set

def merge_files(pattern: str, output_file: Path):
    """合并文件并处理多种编码，同时进行去重"""
    files = sorted(Path('tmp').glob(pattern))
    seen_lines: Set[str] = set()  # 用于跟踪已出现的行内容
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for file in files:
            file_processed = False
            for encoding in ['utf-8', 'gbk', 'latin-1']:  # 增加编码尝试顺序
                try:
                    with open(file, 'r', encoding=encoding) as f:
                        for line in f:
                            # 标准化行：移除两端空白，但保留中间空格
                            normalized = line.strip()
                            
                            # 跳过空行和注释行（以#或!开头的行）
                            if not normalized or normalized.startswith(('#', '!')):
                                out.write(line)  # 保留原始格式的注释和空行
                                continue
                                
                            # 检查是否重复
                            if normalized not in seen_lines:
                                seen_lines.add(normalized)
                                out.write(line)  # 写入原始行（保留原始格式）
                    file_processed = True
                    break  # 成功处理文件后跳出编码尝试循环
                except UnicodeDecodeError:
                    continue
            
            if not file_processed:
                print(f"警告: {file} 无法解析，跳过")
            # 文件之间添加空行分隔
            out.write('\n')

def clean_rules(input_file: Path, output_file: Path):
    """清理注释和无效行（保持不变）"""
    content = ""
    # 尝试多种编码读取
    for encoding in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    # 移除注释（保留!开头的元信息但移除普通注释）
    content = re.sub(r'^#(?!\s*#).*$\n?', '', content, flags=re.MULTILINE)  # 移除#开头的注释
    content = re.sub(r'^![^Tt].*$\n', '', content, flags=re.MULTILINE)  # 保留! Title/Total等元信息

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_allow_lines(allow_file: Path, adblock_combined_file: Path, allow_output_file: Path):
    """提取白名单规则并去重（保持不变）"""
    # 读取白名单
    allow_lines = []
    for encoding in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(allow_file, 'r', encoding=encoding) as f:
                allow_lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue

    # 合并到广告规则（用于提取）
    with open(adblock_combined_file, 'a', encoding='utf-8') as out:
        out.writelines(allow_lines)

    # 提取@开头的白名单规则并去重（保持顺序）
    seen = set()
    unique_allow: List[str] = []
    for encoding in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(adblock_combined_file, 'r', encoding=encoding) as f:
                for line in f:
                    line_strip = line.strip()
                    if line_strip.startswith('@') and line_strip not in seen:
                        seen.add(line_strip)
                        unique_allow.append(line)
            break
        except UnicodeDecodeError:
            continue

    with open(allow_output_file, 'w', encoding='utf-8') as f:
        f.writelines(unique_allow)

def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path):
    """移动文件到目标目录（保持不变）"""
    target_dir.mkdir(parents=True, exist_ok=True)
    adblock_file.rename(target_dir / 'adblock.txt')
    allow_file.rename(target_dir / 'allow.txt')

def deduplicate_txt_files(target_dir: Path):
    """去重并保持首次出现顺序（保持不变）"""
    for file in target_dir.glob('*.txt'):
        seen = set()
        unique_lines: List[str] = []
        for encoding in ['utf-8', 'gbk', 'latin-1']:
            try:
                with open(file, 'r', encoding=encoding) as f:
                    for line in f:
                        line_strip = line.strip()
                        if line_strip and line_strip not in seen:
                            seen.add(line_strip)
                            unique_lines.append(line)
                break
            except UnicodeDecodeError:
                continue

        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(unique_lines)
        print(f"去重完成: {file}, 保留 {len(unique_lines)} 行")

def main():
    tmp_dir = Path('tmp')
    rules_dir = Path('data/rules')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)

    print("合并广告规则...")
    merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
    clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')

    print("合并白名单规则...")
    merge_files('allow*.txt', tmp_dir / 'combined_allow.txt')
    clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt')

    print("提取白名单规则...")
    extract_allow_lines(
        tmp_dir / 'cleaned_allow.txt',
        tmp_dir / 'combined_adblock.txt',
        tmp_dir / 'allow.txt'
    )

    print("移动文件到目标目录...")
    move_files_to_target(
        tmp_dir / 'cleaned_adblock.txt',
        tmp_dir / 'allow.txt',
        rules_dir
    )

    print("去重处理...")
    deduplicate_txt_files(rules_dir)
    print("处理完成")

if __name__ == '__main__':
    main()
