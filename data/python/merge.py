# -*- coding: utf-8 -*-
import re
from pathlib import Path
from typing import List

def merge_files(pattern: str, output_file: Path):
    """�ϲ��ļ���������ֱ���"""
    files = sorted(Path('tmp').glob(pattern))
    with open(output_file, 'w', encoding='utf-8') as out:
        for file in files:
            for encoding in ['utf-8', 'gbk', 'latin-1']:  # ���ӱ��볢��˳��
                try:
                    with open(file, 'r', encoding=encoding) as f:
                        out.write(f.read())
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"����: {file} �޷�����������")
            out.write('\n')

def clean_rules(input_file: Path, output_file: Path):
    """����ע�ͺ���Ч��"""
    content = ""
    # ���Զ��ֱ����ȡ
    for encoding in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    # �Ƴ�ע�ͣ�����!��ͷ��Ԫ��Ϣ���Ƴ���ͨע�ͣ�
    content = re.sub(r'^#(?!\s*#).*$\n?', '', content, flags=re.MULTILINE)  # �Ƴ�#��ͷ��ע��
    content = re.sub(r'^![^Tt].*$\n', '', content, flags=re.MULTILINE)  # ����! Title/Total��Ԫ��Ϣ

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_allow_lines(allow_file: Path, adblock_combined_file: Path, allow_output_file: Path):
    """��ȡ����������ȥ��"""
    # ��ȡ������
    allow_lines = []
    for encoding in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(allow_file, 'r', encoding=encoding) as f:
                allow_lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue

    # �ϲ���������������ȡ��
    with open(adblock_combined_file, 'a', encoding='utf-8') as out:
        out.writelines(allow_lines)

    # ��ȡ@��ͷ�İ���������ȥ�أ�����˳��
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
    """�ƶ��ļ���Ŀ��Ŀ¼"""
    target_dir.mkdir(parents=True, exist_ok=True)
    adblock_file.rename(target_dir / 'adblock.txt')
    allow_file.rename(target_dir / 'allow.txt')

def deduplicate_txt_files(target_dir: Path):
    """ȥ�ز������״γ���˳��"""
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
        print(f"ȥ�����: {file}, ���� {len(unique_lines)} ��")

def main():
    tmp_dir = Path('tmp')
    rules_dir = Path('data/rules')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)

    print("�ϲ�������...")
    merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
    clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')

    print("�ϲ�����������...")
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

    print("ȥ�ش���...")
    deduplicate_txt_files(rules_dir)
    print("�������")

if __name__ == '__main__':
    main()