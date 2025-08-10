#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
����ϲ����ߣ��ϲ�����ϴ�����������ع���Ͱ���������
"""
import re
import logging
from pathlib import Path
from typing import List, Optional

# ������־
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def merge_files(pattern: str, output_file: Path, input_dir: Path = Path('tmp')) -> None:
    """
    �ϲ�ƥ��ģʽ���ļ�������ļ���֧�ֱ����Զ����
    
    Args:
        pattern: �ļ���ƥ��ģʽ
        output_file: ����ļ�·��
        input_dir: �����ļ�����Ŀ¼
    """
    try:
        files = sorted(input_dir.glob(pattern))
        if not files:
            logger.warning(f"δ�ҵ�ƥ�� {pattern} ���ļ�")
            return

        with open(output_file, 'w', encoding='utf-8') as out_f:
            for file in files:
                content = read_file_with_fallback(file)
                if content is not None:
                    out_f.write(content)
                    out_f.write('\n')  # ȷ���ļ����зָ�
            logger.info(f"�Ѻϲ� {len(files)} ���ļ��� {output_file}")
    except Exception as e:
        logger.error(f"�ϲ��ļ�ʧ��: {str(e)}", exc_info=True)
        raise

def read_file_with_fallback(file_path: Path) -> Optional[str]:
    """
    ��ȡ�ļ���֧�ֱ����Զ� fallback
    
    Args:
        file_path: �ļ�·��
        
    Returns:
        �ļ������ַ�����ʧ��ʱ���� None
    """
    encodings = ['utf-8', 'latin-1', 'gbk', 'gb2312']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.warning(f"��ȡ�ļ� {file_path} ʧ��: {str(e)}")
            return None
    logger.error(f"���б�����޷������ļ� {file_path}")
    return None

def clean_rules(input_file: Path, output_file: Path) -> None:
    """
    ��ϴ�����Ƴ�ע�ͺ���Ч��
    
    Args:
        input_file: �����ļ�·��
        output_file: ����ļ�·��
    """
    try:
        content = read_file_with_fallback(input_file)
        if content is None:
            logger.error(f"�޷���ȡ�����ļ� {input_file}")
            return

        # �Ƴ�ע���У�!��ͷ��#��ͷ�ķ�##�У�
        content = re.sub(r'^[!].*$\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^#(?!\s*#).*$\n?', '', content, flags=re.MULTILINE)
        
        # �Ƴ����кͶ���հ�
        content = re.sub(r'\n+', '\n', content).strip()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            f.write('\n')  # ȷ���ļ�ĩβ�л���
        logger.info(f"����ϴ���� {output_file}")
    except Exception as e:
        logger.error(f"��ϴ����ʧ��: {str(e)}", exc_info=True)
        raise

def extract_allow_lines(
    allow_file: Path,
    adblock_combined_file: Path,
    allow_output_file: Path
) -> None:
    """
    ��ȡ�������@��ͷ���У�������
    
    Args:
        allow_file: ��������ļ�
        adblock_combined_file: �ϲ��Ĺ������ļ�
        allow_output_file: �������������ļ�
    """
    try:
        # ��ȡ�������
        allow_lines = read_file_with_fallback(allow_file)
        if allow_lines is None:
            logger.error(f"�޷���ȡ��������ļ� {allow_file}")
            return
        allow_lines = allow_lines.splitlines()

        # ׷�ӵ��ϲ��Ĺ�����
        with open(adblock_combined_file, 'a', encoding='utf-8') as out_f:
            out_f.write('\n'.join(allow_lines))
            out_f.write('\n')

        # ��ȡ@��ͷ����
        combined_content = read_file_with_fallback(adblock_combined_file)
        if combined_content is None:
            logger.error(f"�޷���ȡ�ϲ��Ĺ����� {adblock_combined_file}")
            return
        
        # ȥ�ز�����
        allow_rules = sorted(
            {line.strip() for line in combined_content.splitlines() 
             if line.strip().startswith('@')}
        )

        # д����
        with open(allow_output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(allow_rules))
            f.write('\n')
        logger.info(f"����ȡ {len(allow_rules)} ��������� {allow_output_file}")
    except Exception as e:
        logger.error(f"��ȡ�������ʧ��: {str(e)}", exc_info=True)
        raise

def move_files_to_target(adblock_file: Path, allow_file: Path, target_dir: Path) -> None:
    """
    �ƶ��������ļ���Ŀ��Ŀ¼
    
    Args:
        adblock_file: �������ļ�
        allow_file: ��������ļ�
        target_dir: Ŀ��Ŀ¼
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        adblock_target = target_dir / 'adblock.txt'
        allow_target = target_dir / 'allow.txt'
        
        adblock_file.rename(adblock_target)
        allow_file.rename(allow_target)
        
        logger.info(f"���ƶ��ļ��� {target_dir}")
        logger.info(f"������: {adblock_target}")
        logger.info(f"�������: {allow_target}")
    except Exception as e:
        logger.error(f"�ƶ��ļ�ʧ��: {str(e)}", exc_info=True)
        raise

def deduplicate_txt_files(target_dir: Path) -> None:
    """
    �Ƴ�Ŀ��Ŀ¼������txt�ļ����ظ���
    
    Args:
        target_dir: Ŀ��Ŀ¼
    """
    try:
        for file in target_dir.glob('*.txt'):
            content = read_file_with_fallback(file)
            if content is None:
                continue
                
            # ȥ�ز�����˳��
            seen = set()
            unique_lines: List[str] = []
            for line in content.splitlines():
                stripped = line.strip()
                if stripped and stripped not in seen:
                    seen.add(stripped)
                    unique_lines.append(line)
            
            # д���ļ�
            with open(file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(unique_lines))
                f.write('\n')
            
            logger.info(f"��ȥ�� {file}��ԭ����: {len(content.splitlines())}, ������: {len(unique_lines)}")
    except Exception as e:
        logger.error(f"ȥ���ļ�ʧ��: {str(e)}", exc_info=True)
        raise

def main() -> None:
    """��������ִ�й���ϲ�����"""
    try:
        # ��ʼ��Ŀ¼
        tmp_dir = Path('tmp')
        rules_dir = Path('data/rules')
        tmp_dir.mkdir(parents=True, exist_ok=True)
        rules_dir.mkdir(parents=True, exist_ok=True)
        logger.info("��ʼ��Ŀ¼���")

        # �ϲ�������
        logger.info("��ʼ�ϲ�������...")
        merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
        clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')
        logger.info("������ϲ����")

        # �ϲ��������
        logger.info("��ʼ�ϲ��������...")
        merge_files('allow*.txt', tmp_dir / 'combined_allow.txt')
        clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt')
        logger.info("�������ϲ����")

        # ��ȡ�������
        logger.info("��ʼ��ȡ�������...")
        extract_allow_lines(
            tmp_dir / 'cleaned_allow.txt',
            tmp_dir / 'combined_adblock.txt',
            tmp_dir / 'allow.txt'
        )

        # �ƶ��ļ���Ŀ��Ŀ¼
        logger.info("��ʼ�ƶ��ļ���Ŀ��Ŀ¼...")
        move_files_to_target(
            tmp_dir / 'cleaned_adblock.txt',
            tmp_dir / 'allow.txt',
            rules_dir
        )

        # ȥ�ش���
        logger.info("��ʼȥ�ش���...")
        deduplicate_txt_files(rules_dir)
        
        logger.info("��������ִ�����")
    except Exception as e:
        logger.critical(f"ִ��ʧ��: {str(e)}", exc_info=True)
        raise SystemExit(1)

if __name__ == '__main__':
    main()