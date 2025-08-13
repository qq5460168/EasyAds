import re
from pathlib import Path

# 保持原有函数逻辑不变，增强main函数的验证
def main():
    tmp_dir = Path('tmp')
    rules_dir = Path('./')  # 根目录
    tmp_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)

    print("Merging adblock rules...")
    merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt')
    clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt')
    if not (tmp_dir / 'cleaned_adblock.txt').exists():
        print("::error::合并adblock规则失败，未生成cleaned_adblock.txt")
        sys.exit(1)

    print("Merging allow rules...")
    merge_files('allow*.txt', tmp_dir / 'combined_allow.txt')
    clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt')
    if not (tmp_dir / 'cleaned_allow.txt').exists():
        print("::error::合并allow规则失败，未生成cleaned_allow.txt")
        sys.exit(1)

    print("Extracting allow rules...")
    extract_allow_lines(
        tmp_dir / 'cleaned_allow.txt',
        tmp_dir / 'combined_adblock.txt',
        tmp_dir / 'allow.txt'
    )

    print("Moving files to target directory...")
    move_files_to_target(
        tmp_dir / 'cleaned_adblock.txt',
        tmp_dir / 'allow.txt',
        rules_dir
    )

    print("Deduplicating files...")
    deduplicate_txt_files(rules_dir)
    # 最终验证
    if not (rules_dir / 'adblock.txt').exists() or not (rules_dir / 'allow.txt').exists():
        print("::error::合并流程未生成最终的adblock.txt或allow.txt")
        sys.exit(1)
    print("Process completed successfully")

if __name__ == '__main__':
    import sys  # 确保导入sys
    main()