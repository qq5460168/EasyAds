#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则合并工具：合并、清洗并处理广告拦截规则和白名单规则
"""
import re
import logging
from pathlib import Path
from typing import List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def merge_files(pattern: str, output_file: Path, input_dir: Path = Path('tmp')) -> None:
    """
    合并匹配模式的文件到输出文件，支持编码自动检测
    
    Args:
        pattern: 文件名匹配模式
        output_file: 输出文件路径
        input_dir: 输入文件所在目录
    """
    try:
        files = sorted(input_dir.glob(pattern))
        if not files:
            logger.warning(f"未找到匹配 {pattern} 的文件")
            return

        with open(output_file, 'w', encoding='utf-8') as out_f:
            for file in files:
                content = read_file_with_fallback(file)
                if content is not None:
                    out_f.write(content)
                    out_f.write('\n')  # 确保文件间有分隔
            logger.info(f"已合并 {len(files)} 个文件到 {output_file}")
    except Exception as e:
        logger.error(f"合并文件失败: {str(e)}", exc_info=True)
        raise

def read_file_with_fallback(file_path: Path) -> Optional[str]:
    """
    读取文件，支持编码自动 fallback
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容字符串，失败时返回 None
    """
    encodings = ['utf-8', 'latin-1', 'gbk', 'gb2312']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.warning(f"读取文件 {file_path} 失败: {str(e)}")
            return None
    logger.error(f"所有编码均无法解析文件 {file_path}")
    return None

def clean_rules(input_file: Path, output_file: Path) -> None:
    """
    清洗规则：移除注释和无效行
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
    """
    try:
        content = read_file_with_fallback(input_file)
        if content is None:
            logger.error(f"无法读取规则文件 {input_file}")
            return

        # 移除注释行（!开头或#开头的非##行）
        content = re.sub(r'^[!].*$\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^#(?!\s*#).*$\n?', '', content, flags=re.MULTILINE)
        
        # 移除空行和多余空白
        content = re.sub(r'\n+', '\n', content).strip()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            f.write('\n')  # 确保文件末尾有换行
        logger.info(f"已清洗规则到 {output_file}")
    except Exception as e:
        logger.error(f"清洗规则失败: {str(e)}", exc_info=True)
        raise

def extract_allow_lines(
    allow_file: Path,
    adblock_combined_file: Path,
    allow_output_file: Path
) -> None:
    """
    提取允许规则（@开头的行）并处理
    
    Args:
        allow_file: 允许规则文件
        adblock_combined_file: 合并的广告规则文件
        allow_output_file: 输出的允许规则文件
    """
    try:
        # 读取允许规则
        allow_lines = read_file_with_fallback(allow_file)
        if allow_lines is None:
            logger.error(f"无法读取允许规则文件 {allow_file}")
            return
        allow_lines = allow_lines.splitlines()

        # 追加到合并的广告规则
        with open(adblock_combined_file, 'a', encoding='utf-8') as out_f:
            out_f.write('\n'.join(allow_lines))
            out_f.write('\n')

        # 提取@开头的行
        combined_content = read_file_with_fallback(adblock_combined_file)
        if combined_content is None:
            logger.error(f"无法读取合并的广告规则 {adblock_combined_file}")
            return
        
        # 去重并排序
        allow_rules = sorted(
            {line.strip() for line in combined_content.splitlines() 
             if line.strip().startswith('@')}
        )

        # 写入结果
        with open(allow_output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(allow_rules))
            f.write('\n')
        logger.info(f"已提取 {len(allow_rules)} 条允许规则到 {allow_output_file}")
    except Exception as e:
        logger.error(f"提取允许规则失败: {str(e)}", exc_info=True)
        raise

def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path) -> None:
    """
    移动处理后的文件到目标目录
    
    Args:
        adblock_file: 广告规则文件
        allow_file: 允许规则文件
        target_dir: 目标目录
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        adblock_target = target_dir / 'adblock.txt'
        allow_target = target_dir / 'allow.txt'
        
        adblock_file.rename(adblock_target)
        allow_file.rename(allow_target)
        
        logger.info(f"已移动文件到 {target_dir}")
        logger.info(f"广告规则: {adblock_target}")
        logger.info(f"允许规则: {allow_target}")
    except Exception as e:
        logger.error(f"移动文件失败: {str(e)}", exc_info=True)
        raise

def deduplicate_txt_files(target_dir: Path) -> None:
    """
    移除目标目录中所有txt文件的重复行
    
    Args:
        target_dir: 目标目录
    """
    try:
        for file in target_dir.glob('*.txt'):
            content = read_file_with_fallback(file)
            if content is None:
                continue
                
            # 去重并保持顺序
            seen = set()
            unique_lines: List[str] = []
            for line in content.splitlines():
                stripped = line.strip()
                if stripped and stripped not in seen:
                    seen.add(stripped)
                    unique_lines.append(line)
            
            # 写回文件
            with open(file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(unique_lines))
                f.write('\n')
            
            logger.info(f"已去重 {file}，原行数: {len(content.splitlines())}, 新行数: {len(unique_lines)}")
    except Exception as e:
        logger.error(f"去重文件失败: {str(e)}", exc_info=True)
        raise

def main() -> None:
    """主函数：执行规则合并流程"""
    try:
        # 初始化目录
        tmp_dir = Path('tmp')
        rules_dir = Path('data/rules')
        tmp_dir.mkdir(parents=True, exist_ok=True)
        rules_dir.mkdir(parents=True, exist_ok=True)
        logger.info("初始化目录完成")

        # 合并广告规则
        logger.info("开始合并广告规则...")
        merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
        clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')
        logger.info("广告规则合并完成")

        # 合并允许规则
        logger.info("开始合并允许规则...")
        merge_files('allow*.txt', tmp_dir / 'combined_allow.txt')
        clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt')
        logger.info("允许规则合并完成")

        # 提取允许规则
        logger.info("开始提取允许规则...")
        extract_allow_lines(
            tmp_dir / 'cleaned_allow.txt',
            tmp_dir / 'combined_adblock.txt',
            tmp_dir / 'allow.txt'
        )

        # 移动文件到目标目录
        logger.info("开始移动文件到目标目录...")
        move_files_to_target(
            tmp_dir / 'cleaned_adblock.txt',
            tmp_dir / 'allow.txt',
            rules_dir
        )

        # 去重处理
        logger.info("开始去重处理...")
        deduplicate_txt_files(rules_dir)
        
        logger.info("所有流程执行完成")
    except Exception as e:
        logger.critical(f"执行失败: {str(e)}", exc_info=True)
        raise SystemExit(1)

if __name__ == '__main__':
    main()