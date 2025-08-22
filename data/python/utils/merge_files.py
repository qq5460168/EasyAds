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

def merge_files(pattern: str, output_file: Path, encoding_fallback: str = 'latin-1') -> None:
    """
    合并匹配模式的文件到单个输出文件，支持编码自动 fallback
    
    :param pattern: 用于匹配文件的 glob 模式
    :param output_file: 输出文件路径
    :param encoding_fallback: 当 utf-8 解码失败时使用的备用编码
    """
    try:
        # 获取并排序匹配的文件
        files: List[Path] = sorted(Path('tmp').glob(pattern))
        
        if not files:
            logger.warning(f"未找到匹配模式 '{pattern}' 的文件")
            return
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 合并文件内容
        with output_file.open('w', encoding='utf-8') as out_f:
            for file in files:
                content: Optional[str] = None
                
                # 尝试用 utf-8 编码读取
                try:
                    with file.open('r', encoding='utf-8') as in_f:
                        content = in_f.read()
                    logger.debug(f"成功用 utf-8 读取 {file.name}")
                except UnicodeDecodeError:
                    # 尝试备用编码
                    try:
                        with file.open('r', encoding=encoding_fallback) as in_f:
                            content = in_f.read()
                        logger.debug(f"成功用 {encoding_fallback} 读取 {file.name}")
                    except UnicodeDecodeError as e:
                        logger.error(f"无法解码文件 {file.name}: {str(e)}，已跳过")
                        continue
                
                if content is not None:
                    out_f.write(content)
                    out_f.write('\n')  # 在文件间添加分隔符
        
        logger.info(f"已合并 {len(files)} 个文件到 {output_file.name}")
        
    except IOError as e:
        logger.error(f"文件操作错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"合并文件时发生意外错误: {str(e)}", exc_info=True)

def clean_rules(input_file: Path, output_file: Path, encoding_fallback: str = 'latin-1') -> None:
    """
    清理规则文件，移除注释和无效行
    
    :param input_file: 输入规则文件路径
    :param output_file: 清理后的输出文件路径
    :param encoding_fallback: 当 utf-8 解码失败时使用的备用编码
    """
    try:
        # 读取文件内容
        content: Optional[str] = None
        
        try:
            with input_file.open('r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with input_file.open('r', encoding=encoding_fallback) as f:
                    content = f.read()
            except UnicodeDecodeError as e:
                logger.error(f"无法解码文件 {input_file.name}: {str(e)}", exc_info=True)
                return
        
        if content is None:
            logger.error(f"未读取到 {input_file.name} 的内容")
            return
        
        # 移除注释行（!开头或#开头且不是##的行）
        # 保留##开头的行（可能是特殊标记）
        content = re.sub(r'^[!].*$\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'^#(?!\s*#).*$\n?', '', content, flags=re.MULTILINE)
        
        # 移除空行和多余空白
        content = re.sub(r'\n+', '\n', content).strip()
        
        # 写入清理后的内容
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open('w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"已清理规则: {input_file.name} -> {output_file.name}")
        
    except IOError as e:
        logger.error(f"文件操作错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"清理规则时发生意外错误: {str(e)}", exc_info=True)

def extract_allow_lines(
    allow_file: Path, 
    adblock_combined_file: Path, 
    allow_output_file: Path,
    encoding_fallback: str = 'latin-1'
) -> None:
    """
    从合并文件中提取允许规则（@开头的行）
    
    :param allow_file: 允许规则文件路径
    :param adblock_combined_file: 合并的广告拦截规则文件路径
    :param allow_output_file: 提取后的允许规则输出路径
    :param encoding_fallback: 当 utf-8 解码失败时使用的备用编码
    """
    try:
        # 读取允许规则并追加到合并文件
        allow_lines: List[str] = []
        try:
            with allow_file.open('r', encoding='utf-8') as f:
                allow_lines = f.readlines()
        except UnicodeDecodeError:
            with allow_file.open('r', encoding=encoding_fallback) as f:
                allow_lines = f.readlines()
        
        with adblock_combined_file.open('a', encoding='utf-8') as out_f:
            out_f.writelines(allow_lines)
        logger.debug(f"已将 {len(allow_lines)} 行允许规则追加到合并文件")
        
        # 提取所有@开头的规则
        lines: List[str] = []
        try:
            with adblock_combined_file.open('r', encoding='utf-8') as f:
                lines = [line for line in f if line.startswith('@')]
        except UnicodeDecodeError:
            with adblock_combined_file.open('r', encoding=encoding_fallback) as f:
                lines = [line for line in f if line.startswith('@')]
        
        # 去重并排序
        unique_lines = sorted(set(lines))
        
        # 写入结果
        allow_output_file.parent.mkdir(parents=True, exist_ok=True)
        with allow_output_file.open('w', encoding='utf-8') as f:
            f.writelines(unique_lines)
        
        logger.info(f"已提取 {len(unique_lines)} 条允许规则到 {allow_output_file.name}")
        
    except IOError as e:
        logger.error(f"文件操作错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"提取允许规则时发生意外错误: {str(e)}", exc_info=True)

def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path) -> None:
    """
    将处理后的文件移动到目标目录（根目录）
    
    :param adblock_file: 广告拦截规则文件路径
    :param allow_file: 允许规则文件路径
    :param target_dir: 目标目录路径
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        adblock_target = target_dir / 'adblock.txt'
        allow_target = target_dir / 'allow.txt'
        
        # 如果目标文件已存在，先删除
        if adblock_target.exists():
            adblock_target.unlink()
        if allow_target.exists():
            allow_target.unlink()
        
        # 移动文件
        adblock_file.rename(adblock_target)
        allow_file.rename(allow_target)
        
        logger.info(f"已移动文件到目标目录: {target_dir}")
        
    except IOError as e:
        logger.error(f"移动文件时发生IO错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"移动文件时发生意外错误: {str(e)}", exc_info=True)

def deduplicate_txt_files(target_dir: Path, encoding_fallback: str = 'latin-1') -> None:
    """
    移除目标目录中所有txt文件的重复行
    
    :param target_dir: 目标目录路径
    :param encoding_fallback: 当 utf-8 解码失败时使用的备用编码
    """
    try:
        for file in target_dir.glob('*.txt'):
            # 读取文件内容
            lines: List[str] = []
            try:
                with file.open('r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with file.open('r', encoding=encoding_fallback) as f:
                    lines = f.readlines()
            
            # 去重并保持顺序
            seen = set()
            unique_lines = []
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
            
            # 只在有变化时写入
            if len(unique_lines) != len(lines):
                with file.open('w', encoding='utf-8') as f:
                    f.writelines(unique_lines)
                logger.debug(f"已去重 {file.name}: 原{len(lines)}行 -> 现{len(unique_lines)}行")
            else:
                logger.debug(f"{file.name} 无重复行，无需处理")
        
        logger.info(f"已完成 {target_dir} 目录下所有TXT文件的去重")
        
    except IOError as e:
        logger.error(f"去重时发生IO错误: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"去重时发生意外错误: {str(e)}", exc_info=True)

def main() -> None:
    """主函数：执行规则合并流程"""
    try:
        # 路径配置
        tmp_dir = Path('tmp')
        rules_dir = Path('./')  # 根目录
        
        # 确保目录存在
        tmp_dir.mkdir(parents=True, exist_ok=True)
        rules_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("开始合并广告拦截规则...")
        merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
        clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')
        logger.info("广告拦截规则合并完成")

        logger.info("开始合并允许规则...")
        merge_files('allow*.txt', tmp_dir / 'combined_allow.txt')
        clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt')
        logger.info("允许规则合并完成")

        logger.info("开始提取允许规则...")
        extract_allow_lines(
            tmp_dir / 'cleaned_allow.txt',
            tmp_dir / 'combined_adblock.txt',
            tmp_dir / 'allow.txt'
        )

        logger.info("开始移动文件到目标目录...")
        move_files_to_target(
            tmp_dir / 'cleaned_adblock.txt',
            tmp_dir / 'allow.txt',
            rules_dir  # 根目录
        )

        logger.info("开始去重处理...")
        deduplicate_txt_files(rules_dir)  # 根目录去重
        logger.info("所有流程执行完成")

    except Exception as e:
        logger.critical(f"主流程执行失败: {str(e)}", exc_info=True)
        exit(1)

if __name__ == '__main__':
    main()