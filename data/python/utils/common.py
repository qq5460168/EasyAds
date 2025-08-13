# EasyAds/data/python/utils/common.py
import logging
from pathlib import Path
from typing import List, Union

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def read_file_safely(file_path: Union[Path, str], encoding: str = "utf-8") -> str:
    """安全读取文件内容，自动处理编码异常"""
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return ""
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        logger.debug(f"utf-8解码失败，尝试latin-1: {file_path}")
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件失败 {file_path}: {str(e)}")
        return ""

def write_file_safely(content: str, file_path: Union[Path, str], encoding: str = "utf-8") -> bool:
    """安全写入文件，先写临时文件再替换（防止文件损坏）"""
    file_path = Path(file_path)
    try:
        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # 写入临时文件
        temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
        with open(temp_path, "w", encoding=encoding) as f:
            f.write(content)
        # 原子替换
        temp_path.rename(file_path)
        return True
    except Exception as e:
        logger.error(f"写入文件失败 {file_path}: {str(e)}")
        return False

def get_unique_lines(lines: List[str], keep_order: bool = True) -> List[str]:
    """去重并保持顺序（规则文件顺序可能影响优先级）"""
    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return unique