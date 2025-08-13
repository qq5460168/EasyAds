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

# 常量定义
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODING = "latin-1"
TMP_DIR_NAME = "tmp"


def read_file(file_path: Path) -> str:
    """
    读取文件内容，支持编码自动 fallback
    :param file_path: 文件路径
    :return: 文件内容字符串
    :raises FileNotFoundError: 文件不存在时抛出
    :raises IOError: 读取文件发生IO错误时抛出
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    for encoding in [DEFAULT_ENCODING, FALLBACK_ENCODING]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError(f"无法解码文件: {file_path}，已尝试 {DEFAULT_ENCODING} 和 {FALLBACK_ENCODING}")


def write_file(content: str, file_path: Path, encoding: str = DEFAULT_ENCODING) -> None:
    """
    写入内容到文件
    :param content: 要写入的内容
    :param file_path: 文件路径
    :param encoding: 编码方式
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def merge_files(pattern: str, output_file: Path, source_dir: Path = Path(TMP_DIR_NAME)) -> None:
    """
    合并匹配模式的文件到输出文件
    :param pattern: 文件名匹配模式（如 'adblock*.txt'）
    :param output_file: 输出文件路径
    :param source_dir: 源文件目录，默认 tmp 目录
    """
    try:
        files = sorted(source_dir.glob(pattern))
        if not files:
            logger.warning(f"未找到匹配 {pattern} 的文件")
            return

        content = []
        for file in files:
            try:
                content.append(read_file(file))
                logger.debug(f"已读取文件: {file.name}")
            except Exception as e:
                logger.error(f"读取文件 {file.name} 失败: {str(e)}")
                continue

        # 合并内容并添加换行分隔
        merged_content = "\n".join(content)
        write_file(merged_content, output_file)
        logger.info(f"已合并 {len(files)} 个文件到 {output_file}")
    except Exception as e:
        logger.error(f"合并文件失败: {str(e)}", exc_info=True)
        raise


def clean_rules(input_file: Path, output_file: Path) -> None:
    """
    清理规则文件：移除注释和无效行
    :param input_file: 输入文件路径
    :param output_file: 输出文件路径
    """
    try:
        content = read_file(input_file)
        
        # 移除注释行：
        # 1. 以 ! 开头的行（Adblock 风格注释）
        # 2. 以 # 开头且后面不是 ## 的行（排除 ## 开头的特殊标记）
        content = re.sub(r"^[!].*$\n?", "", content, flags=re.MULTILINE)
        content = re.sub(r"^#(?!\s*#).*$\n?", "", content, flags=re.MULTILINE)
        
        # 移除空行
        content = re.sub(r"\n{2,}", "\n", content).strip()
        
        write_file(content, output_file)
        logger.info(f"已清理规则，输出到 {output_file}")
    except Exception as e:
        logger.error(f"清理规则失败: {str(e)}", exc_info=True)
        raise


def extract_allow_lines(allow_file: Path, adblock_combined_file: Path, allow_output_file: Path) -> None:
    """
    提取允许规则（@ 开头的行）并去重排序
    :param allow_file: 允许规则源文件
    :param adblock_combined_file: 合并的广告规则文件
    :param allow_output_file: 提取后的允许规则输出文件
    """
    try:
        # 读取允许规则并追加到合并的广告规则文件
        allow_content = read_file(allow_file)
        with open(adblock_combined_file, "a", encoding=DEFAULT_ENCODING) as f:
            f.write(allow_content)
        logger.debug(f"已追加允许规则到 {adblock_combined_file}")
        
        # 提取所有 @ 开头的行
        combined_content = read_file(adblock_combined_file)
        allow_lines = [line for line in combined_content.splitlines() if line.startswith("@")]
        
        # 去重并排序
        unique_allow_lines = sorted(set(allow_lines))
        write_file("\n".join(unique_allow_lines), allow_output_file)
        logger.info(f"已提取 {len(unique_allow_lines)} 条允许规则到 {allow_output_file}")
    except Exception as e:
        logger.error(f"提取允许规则失败: {str(e)}", exc_info=True)
        raise


def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path) -> None:
    """
    将处理后的文件移动到目标目录
    :param adblock_file: 广告规则文件
    :param allow_file: 允许规则文件
    :param target_dir: 目标目录
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义目标路径
        adblock_target = target_dir / "adblock.txt"
        allow_target = target_dir / "allow.txt"
        
        # 移动文件（若目标存在则先删除）
        for src, dst in [(adblock_file, adblock_target), (allow_file, allow_target)]:
            if dst.exists():
                dst.unlink()
            src.rename(dst)
            logger.info(f"已移动文件: {src} -> {dst}")
    except Exception as e:
        logger.error(f"移动文件失败: {str(e)}", exc_info=True)
        raise


def deduplicate_txt_files(target_dir: Path) -> None:
    """
    移除目标目录中所有 txt 文件的重复行（保持顺序）
    :param target_dir: 目标目录
    """
    try:
        txt_files = list(target_dir.glob("*.txt"))
        if not txt_files:
            logger.warning(f"目标目录 {target_dir} 中未找到 txt 文件")
            return
        
        for file in txt_files:
            content = read_file(file)
            lines = content.splitlines()
            
            # 去重并保持顺序
            seen = set()
            unique_lines = []
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
            
            # 写回文件
            write_file("\n".join(unique_lines), file)
            logger.debug(f"已去重文件: {file.name}（原{len(lines)}行，去重后{len(unique_lines)}行）")
        
        logger.info(f"已完成 {len(txt_files)} 个 txt 文件的去重")
    except Exception as e:
        logger.error(f"文件去重失败: {str(e)}", exc_info=True)
        raise


def main() -> None:
    """主函数：执行规则合并、清理、提取、移动和去重流程"""
    try:
        # 计算路径（基于脚本所在位置）
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent  # 项目根目录
        tmp_dir = project_root / TMP_DIR_NAME
        rules_dir = project_root  # 目标目录为项目根目录
        
        # 确保目录存在
        tmp_dir.mkdir(parents=True, exist_ok=True)
        rules_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("开始合并广告规则...")
        merge_files("adblock*.txt", tmp_dir / "combined_adblock.txt")
        clean_rules(tmp_dir / "combined_adblock.txt", tmp_dir / "cleaned_adblock.txt")
        logger.info("广告规则合并完成")
        
        logger.info("开始合并允许规则...")
        merge_files("allow*.txt", tmp_dir / "combined_allow.txt")
        clean_rules(tmp_dir / "combined_allow.txt", tmp_dir / "cleaned_allow.txt")
        logger.info("允许规则合并完成")
        
        logger.info("开始提取允许规则...")
        extract_allow_lines(
            tmp_dir / "cleaned_allow.txt",
            tmp_dir / "combined_adblock.txt",
            tmp_dir / "allow.txt"
        )
        
        logger.info("开始移动文件到目标目录...")
        move_files_to_target(
            tmp_dir / "cleaned_adblock.txt",
            tmp_dir / "allow.txt",
            rules_dir
        )
        
        logger.info("开始文件去重...")
        deduplicate_txt_files(rules_dir)
        
        logger.info("所有流程执行完成！")
    except Exception as e:
        logger.critical(f"主流程执行失败: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()