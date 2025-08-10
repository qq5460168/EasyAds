#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则合并工具：合并、清洗并处理广告拦截规则和白名单规则
"""
import re
import logging
from pathlib import Path
from typing import List, Optional

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def read_file_with_encoding_fallback(file_path: Path) -> Optional[str]:
    """
    读取文件并处理编码问题，支持多种编码自动尝试
    
    Args:
        file_path: 要读取的文件路径
        
    Returns:
        文件内容字符串（已转换为UTF-8），失败时返回None
    """
    # 优先尝试GB18030（根据检测结果），再尝试其他常见编码
    encodings = ['gb18030', 'utf-8', 'latin-1', 'gbk', 'gb2312']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                # 确保内容以UTF-8编码返回
                return content.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.warning(f"读取文件 {file_path} 时出错: {str(e)}")
            return None
    logger.error(f"所有编码均无法解析文件 {file_path}")
    return None

def merge_files(pattern: str, output_file: Path, input_dir: Path = Path('tmp')) -> None:
    """
    合并匹配指定模式的文件到输出文件
    
    Args:
        pattern: 文件名匹配模式（如 'adblock*.txt'）
        output_file: 合并后的输出文件路径
        input_dir: 输入文件所在目录，默认是'tmp'目录
    """
    try:
        # 获取所有匹配的文件并按名称排序
        files = sorted(input_dir.glob(pattern))
        if not files:
            logger.warning(f"未找到匹配模式 '{pattern}' 的文件")
            return

        with open(output_file, 'w', encoding='utf-8') as out_f:
            for file in files:
                content = read_file_with_encoding_fallback(file)
                if content:
                    out_f.write(content)
                    out_f.write('\n')  # 确保文件间有换行分隔
            logger.info(f"已成功合并 {len(files)} 个文件到 {output_file}")
    except Exception as e:
        logger.error(f"合并文件失败: {str(e)}", exc_info=True)
        raise

def clean_rules(input_file: Path, output_file: Path) -> None:
    """
    清洗规则文件：移除注释和无效行
    
    Args:
        input_file: 原始规则文件路径
        output_file: 清洗后的输出文件路径
    """
    try:
        content = read_file_with_encoding_fallback(input_file)
        if not content:
            logger.error(f"无法读取规则文件 {input_file}，清洗失败")
            return

        # 移除注释行（!开头或非##开头的#行）
        content = re.sub(r'^[!].*$\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^#(?!\s*#).*$\n?', '', content, flags=re.MULTILINE)
        
        # 移除连续空行，只保留单个空行
        content = re.sub(r'\n+', '\n', content).strip()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            f.write('\n')  # 确保文件末尾有换行
        logger.info(f"规则清洗完成，输出到 {output_file}")
    except Exception as e:
        logger.error(f"清洗规则失败: {str(e)}", exc_info=True)
        raise

def extract_allow_lines(
    allow_file: Path,
    adblock_combined_file: Path,
    allow_output_file: Path
) -> None:
    """
    提取允许规则（@开头的行）并去重处理
    
    Args:
        allow_file: 原始允许规则文件
        adblock_combined_file: 合并后的广告规则文件
        allow_output_file: 提取后的允许规则输出文件
    """
    try:
        # 读取允许规则并追加到合并的广告规则
        allow_content = read_file_with_encoding_fallback(allow_file)
        if not allow_content:
            logger.error(f"无法读取允许规则文件 {allow_file}")
            return

        with open(adblock_combined_file, 'a', encoding='utf-8') as out_f:
            out_f.write(allow_content)
            out_f.write('\n')

        # 提取所有@开头的规则行
        combined_content = read_file_with_encoding_fallback(adblock_combined_file)
        if not combined_content:
            logger.error(f"无法读取合并的广告规则文件 {adblock_combined_file}")
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
    将处理后的规则文件移动到目标目录
    
    Args:
        adblock_file: 广告拦截规则文件
        allow_file: 允许规则文件
        target_dir: 目标目录路径
    """
    try:
        # 确保目标目录存在
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义目标文件路径
        adblock_target = target_dir / 'adblock.txt'
        allow_target = target_dir / 'allow.txt'
        
        # 移动文件（若目标文件已存在则覆盖）
        if adblock_target.exists():
            adblock_target.unlink()
        adblock_file.rename(adblock_target)
        
        if allow_target.exists():
            allow_target.unlink()
        allow_file.rename(allow_target)
        
        logger.info(f"文件已移动到目标目录: {target_dir}")
        logger.info(f"广告拦截规则: {adblock_target}")
        logger.info(f"允许规则: {allow_target}")
    except Exception as e:
        logger.error(f"移动文件失败: {str(e)}", exc_info=True)
        raise

def deduplicate_txt_files(target_dir: Path) -> None:
    """
    移除目标目录中所有TXT文件的重复行，保持原始顺序
    
    Args:
        target_dir: 目标目录路径
    """
    try:
        for file in target_dir.glob('*.txt'):
            content = read_file_with_encoding_fallback(file)
            if not content:
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
            
            logger.info(f"已去重 {file.name}，原行数: {len(content.splitlines())}, 新行数: {len(unique_lines)}")
    except Exception as e:
        logger.error(f"去重文件失败: {str(e)}", exc_info=True)
        raise

def main() -> None:
    """主函数：执行规则合并的完整流程"""
    try:
        # 初始化目录
        tmp_dir = Path('tmp')
        rules_dir = Path('data/rules')
        tmp_dir.mkdir(parents=True, exist_ok=True)
        rules_dir.mkdir(parents=True, exist_ok=True)
        logger.info("目录初始化完成")

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
