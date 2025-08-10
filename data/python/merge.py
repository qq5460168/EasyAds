import re
from pathlib import Path
from typing import List, Iterable

def read_file_safely(file_path: Path, encoding: str = 'utf-8') -> str:
    """��ȫ��ȡ�ļ����Զ�����������"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"��ȡ�ļ�ʧ�� {file_path}: {e}")

def merge_files(pattern: str, output_file: Path) -> None:
    """�ϲ�ƥ��ģʽ���ļ�������ļ�"""
    files = sorted(Path('tmp').glob(pattern))
    with open(output_file, 'w', encoding='utf-8') as out:
        for file in files:
            out.write(read_file_safely(file))
            out.write('\n')

def clean_rules(input_file: Path, output_file: Path) -> None:
    """��������Ƴ�ע�ͺͿ��У�"""
    content = read_file_safely(input_file)
    
    # �Ƴ�ע���кͿ���
    content = re.sub(r'^[!#](?!\s*#).*$\n?', '', content, flags=re.MULTILINE)  # ����##ע��
    content = re.sub(r'^\s*$\n', '', content, flags=re.MULTILINE)  # �Ƴ�����
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def get_unique_lines(lines: Iterable[str]) -> List[str]:
    """ȥ�ز�����ԭʼ˳��Python 3.7+ �ֵ�����"""
    seen = dict()
    return [seen.setdefault(line, line) for line in lines if line not in seen]

def extract_allow_lines(allow_file: Path, adblock_combined_file: Path, allow_output_file: Path) -> None:
    """��ȡ���������������"""
    # ��ȡ��������׷�ӵ��ϲ��ļ�
    allow_content = read_file_safely(allow_file)
    with open(adblock_combined_file, 'a', encoding='utf-8') as out:
        out.write(allow_content)
    
    # ��ȡ@��ͷ�Ĺ���ȥ��
    combined_content = read_file_safely(adblock_combined_file)
    allow_lines = [line for line in combined_content.splitlines(keepends=True) if line.startswith('@')]
    unique_allow_lines = get_unique_lines(allow_lines)
    
    with open(allow_output_file, 'w', encoding='utf-8') as f:
        f.writelines(unique_allow_lines)

def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path) -> None:
    """�ƶ��ļ���Ŀ��Ŀ¼"""
    target_dir.mkdir(parents=True, exist_ok=True)
    adblock_file.rename(target_dir / 'adblock.txt')
    allow_file.rename(target_dir / 'allow.txt')

def deduplicate_txt_files(target_dir: Path) -> None:
    """ȥ��Ŀ��Ŀ¼�µ�����TXT�ļ�������˳��"""
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
        print("�ϲ�adblock����...")
        merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
        clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')
        
        print("�ϲ�allow����...")
        merge_files('allow*.txt', tmp_dir / 'combined_allow.txt')
        clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt')
        
        print("��ȡ����������...")
        extract_allow_lines(
            tmp_dir / 'cleaned_allow.txt',
            tmp_dir / 'combined_adblock.txt',
            tmp_dir / 'allow.txt'
        )
        
        print("�ƶ��ļ���Ŀ��Ŀ¼...")
        move_files_to_target(
            tmp_dir / 'cleaned_adblock.txt',
            tmp_dir / 'allow.txt',
            rules_dir
        )
        
        print("ȥ���ļ�...")
        deduplicate_txt_files(rules_dir)
        print("�������")
        
    except Exception as e:
        print(f"����ʧ��: {str(e)}")

if __name__ == '__main__':
    main()