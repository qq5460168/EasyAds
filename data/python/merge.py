import re
from pathlib import Path
from typing import List, Iterable

def read_file_safely(file_path: Path, encoding: str = 'utf-8') -> str:
    """安全读取文件（自动处理编码错误）"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"读取文件失败 {file_path}: {e}")

def merge_files(pattern: str, output_file: Path) -> None:
    """合并匹配模式的文件到输出文件"""
    files = sorted(Path('tmp').glob(pattern))
    with open(output_file, 'w', encoding='utf-8') as out:
        for file in files:
            out.write(read_file_safely(file))
            out.write('\n')

def clean_rules(input_file: Path, output_file: Path) -> None:
    """清理规则（移除注释和空行）"""
    content = read_file_safely(input_file)
    
    # 移除注释行和空行
    content = re.sub(r'^[!#](?!\s*#).*$\n?', '', content, flags=re.MULTILINE)  # 保留##注释
    content = re.sub(r'^\s*$\n', '', content, flags=re.MULTILINE)  # 移除空行
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def get_unique_lines(lines: Iterable[str]) -> List[str]:
    """去重并保持原始顺序（Python 3.7+ 字典有序）"""
    seen = dict()
    return [seen.setdefault(line, line) for line in lines if line not in seen]

def extract_allow_lines(allow_file: Path, adblock_combined_file: Path, allow_output_file: Path) -> None:
    """提取并处理白名单规则"""
    # 读取白名单并追加到合并文件
    allow_content = read_file_safely(allow_file)
    with open(adblock_combined_file, 'a', encoding='utf-8') as out:
        out.write(allow_content)
    
    # 提取@开头的规则并去重
    combined_content = read_file_safely(adblock_combined_file)
    allow_lines = [line for line in combined_content.splitlines(keepends=True) if line.startswith('@')]
    unique_allow_lines = get_unique_lines(allow_lines)
    
    with open(allow_output_file, 'w', encoding='utf-8') as f:
        f.writelines(unique_allow_lines)

def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path) -> None:
    """移动文件到目标目录"""
    target_dir.mkdir(parents=True, exist_ok=True)
    adblock_file.rename(target_dir / 'adblock.txt')
    allow_file.rename(target_dir / 'allow.txt')

def deduplicate_txt_files(target_dir: Path) -> None:
    """去重目标目录下的所有TXT文件（保持顺序）"""
    for file in target_dir.glob('*.txt'):
        content = read_file_safely(file)
        lines = content.splitlines(keepends=True)
        unique_lines = get_unique_lines(lines)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(unique_lines)

def main() -> None:
    tmp_dir = Path('tmp')
    rules_dir = Path('data/rules')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)

    try:
        print("合并adblock规则...")
        merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
        clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')
        
        print("合并allow规则...")
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
        
        print("去重文件...")
        deduplicate_txt_files(rules_dir)
        print("处理完成")
        
    except Exception as e:
        print(f"处理失败: {str(e)}")

if __name__ == '__main__':
    main()