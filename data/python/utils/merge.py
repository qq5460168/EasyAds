import re
from pathlib import Path
import shutil

def merge_files(pattern, output_file):
    """合并匹配模式的文件，支持编码容错"""
    files = sorted(Path('tmp').glob(pattern))
    if not files:
        print(f"警告: 未找到匹配 {pattern} 的文件")
        return False
        
    with open(output_file, 'w', encoding='utf-8') as out:
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file, 'r', encoding='latin-1') as f:
                    content = f.read()
            # 合并时移除空行，减少后续处理压力
            content = re.sub(r'\n+', '\n', content).strip() + '\n'
            out.write(content)
    return True

def clean_rules(input_file, output_file):
    """增强规则清洗：保留有效AdBlock规则，过滤无效格式"""
    if not Path(input_file).exists():
        print(f"错误: 清洗失败，文件不存在 {input_file}")
        return False

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # 移除注释行（!或#开头，允许行首空格）
    content = re.sub(r'^\s*[!#].*$\n?', '', content, flags=re.MULTILINE)
    # 移除纯空行
    content = re.sub(r'\n+', '\n', content).strip()
    
    # 保留有效AdBlock规则格式（基础过滤）
    valid_lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # 白名单规则（@@开头）
        if line.startswith('@@'):
            valid_lines.append(line)
        # 黑名单规则（支持||域名、|URL、通配符等格式）
        elif line.startswith(('||', '|http://', '|https://', '/', '^')) or '*' in line:
            valid_lines.append(line)
        # 元素隐藏规则（##开头）
        elif line.startswith('##'):
            valid_lines.append(line)
    
    # 写入清洗后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(valid_lines))
    return True

def extract_allow_lines(allow_file, adblock_combined_file, allow_output_file):
    """提取并合并白名单规则，避免重复"""
    if not Path(allow_file).exists():
        print(f"警告: 白名单源文件不存在 {allow_file}")
        return False

    # 读取白名单规则
    try:
        with open(allow_file, 'r', encoding='utf-8') as f:
            allow_lines = [line.strip() for line in f if line.strip().startswith('@@')]
    except UnicodeDecodeError:
        with open(allow_file, 'r', encoding='latin-1') as f:
            allow_lines = [line.strip() for line in f if line.strip().startswith('@@')]
    
    # 合并到主规则并去重
    combined_lines = set(allow_lines)
    if Path(adblock_combined_file).exists():
        with open(adblock_combined_file, 'r', encoding='utf-8') as f:
            combined_lines.update([line.strip() for line in f if line.strip()])
    
    # 写入合并后的主规则
    with open(adblock_combined_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(combined_lines)))
    
    # 单独提取白名单（去重排序）
    with open(allow_output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(set(allow_lines))))
    return True

def move_files_to_target(adblock_file, allow_file, target_dir):
    """移动文件到目标目录，确保目录存在"""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    adblock_target = target_dir / 'adblock.txt'
    allow_target = target_dir / 'allow.txt'
    
    # 仅在源文件存在时移动
    if Path(adblock_file).exists():
        shutil.move(adblock_file, adblock_target)
    if Path(allow_file).exists():
        shutil.move(allow_file, allow_target)
    return True

def deduplicate_txt_files(target_dir):
    """严格去重：保留首次出现的规则，维持顺序"""
    target_dir = Path(target_dir)
    for file in target_dir.glob('*.txt'):
        if not file.exists():
            continue
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError:
            with open(file, 'r', encoding='latin-1') as f:
                lines = [line.strip() for line in f if line.strip()]
        
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        # 写入去重后的内容
        with open(file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_lines) + '\n')
    return True

def main():
    tmp_dir = Path('tmp')
    rules_dir = Path('./')  # 根目录
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 1. 合并并清洗广告规则
    print("合并广告规则...")
    if not merge_files('adblock*.txt', tmp_dir / 'combined_adblock.txt'):
        print("错误: 广告规则合并失败")
        return
    
    print("清洗广告规则...")
    if not clean_rules(tmp_dir / 'combined_adblock.txt', tmp_dir / 'cleaned_adblock.txt'):
        print("错误: 广告规则清洗失败")
        return

    # 2. 合并并清洗白名单规则（仅处理data/rules/allow.txt，避免根目录重复）
    print("合并白名单规则...")
    if not merge_files('data/rules/allow.txt', tmp_dir / 'combined_allow.txt'):  # 明确源路径
        print("警告: 未找到白名单文件，使用空规则")
        with open(tmp_dir / 'combined_allow.txt', 'w') as f:
            f.write('')
    
    print("清洗白名单规则...")
    if not clean_rules(tmp_dir / 'combined_allow.txt', tmp_dir / 'cleaned_allow.txt'):
        print("错误: 白名单规则清洗失败")
        return

    # 3. 提取白名单并合并
    print("提取白名单规则...")
    if not extract_allow_lines(
        tmp_dir / 'cleaned_allow.txt',
        tmp_dir / 'cleaned_adblock.txt',
        tmp_dir / 'allow.txt'
    ):
        print("错误: 白名单提取失败")
        return

    # 4. 移动到根目录并去重
    print("移动文件到目标目录...")
    if not move_files_to_target(
        tmp_dir / 'cleaned_adblock.txt',
        tmp_dir / 'allow.txt',
        rules_dir
    ):
        print("错误: 文件移动失败")
        return

    print("去重处理...")
    if not deduplicate_txt_files(rules_dir):
        print("错误: 去重失败")
        return

    print("所有规则处理完成")

if __name__ == '__main__':
    main()