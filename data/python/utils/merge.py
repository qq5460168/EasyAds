import re
import os
from pathlib import Path
from datetime import datetime

# 基于脚本绝对路径计算目录（核心修复）
SCRIPT_DIR = Path(__file__).resolve().parent  # 脚本所在目录：data/python/utils
# 目标目录：data/rules（基于脚本目录向上两级找到data，再进入rules）
TARGET_DIR = SCRIPT_DIR.parent.parent / "rules"  # 等价于 data/rules
TMP_DIR = SCRIPT_DIR.parent.parent.parent / "tmp"  # 临时目录：项目根目录/tmp

# 规则匹配模式（保持不变）
ALLOW_PATTERN = re.compile(
    r'^@@\|\|[\w.-]+\^?(\$~?[\w,=-]+)?|'  # 域名白名单规则
    r'^@@##.+|'                           # 元素隐藏白名单
    r'^@@/[^/]+/|'                        # 正则白名单
    r'^@@\d+\.\d+\.\d+\.\d+'              # IP白名单
)

BLOCK_PATTERN = re.compile(
    r'^\|\|[\w.-]+\^(\$~?[\w,=-]+)?|'     # 域名拦截规则
    r'^/[\w/-]+/|'                        # 正则拦截规则
    r'^##.+|'                             # 元素隐藏规则
    r'^\d+\.\d+\.\d+\.\d+\s+[\w.-]+'      # Hosts格式规则
)

def log(message: str):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [PROCESS] {message}")

def clean_rules(content: str, pattern: re.Pattern) -> str:
    """清理规则内容，保留有效规则"""
    content = re.sub(r'^[!#].*$\n?', '', content, flags=re.MULTILINE)  # 移除注释
    valid_lines = [
        line for line in content.splitlines()
        if line.strip() and pattern.search(line.strip())
    ]
    return '\n'.join(valid_lines)

def extract_allow_rules_from_block(content: str) -> str:
    """从黑名单中提取白名单规则"""
    allow_lines = [
        line.strip() for line in content.splitlines()
        if line.strip().startswith('@@') and ALLOW_PATTERN.search(line.strip())
    ]
    return '\n'.join(allow_lines)

def deduplicate_file(filepath: Path):
    """去重文件内容（保留顺序，忽略大小写）"""
    if not filepath.exists():
        log(f"去重失败：文件不存在 {filepath}")
        return
    
    with open(filepath, 'r+', encoding='utf-8') as f:
        seen = set()
        unique_lines = []
        for line in f:
            if not line.strip():
                continue
            lower_line = line.lower()
            if lower_line not in seen:
                seen.add(lower_line)
                unique_lines.append(line)
        f.seek(0)
        f.writelines(unique_lines)
        f.truncate()
    log(f"已去重：{filepath}（{len(unique_lines)} 条规则）")

def main():
    try:
        # 打印路径调试信息（关键）
        log(f"脚本目录：{SCRIPT_DIR}")
        log(f"目标目录：{TARGET_DIR}")
        log(f"临时目录：{TMP_DIR}")

        # 确保目录存在（修复：添加parents=True创建父目录）
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        TARGET_DIR.mkdir(parents=True, exist_ok=True)  # 这里修复父目录不存在的问题

        # 1. 合并adblock规则
        adblock_files = list(TMP_DIR.glob("adblock*.txt"))
        if not adblock_files:
            log("错误：未找到adblock*.txt文件，终止流程")
            return
        
        log(f"合并 {len(adblock_files)} 个黑名单文件...")
        combined_adblock = TMP_DIR / "combined_adblock.txt"
        with open(combined_adblock, 'w', encoding='utf-8', errors='ignore') as out_f:
            for file in adblock_files:
                with open(file, 'r', encoding='utf-8', errors='ignore') as in_f:
                    out_f.write(in_f.read() + '\n')

        # 2. 处理黑名单
        with open(combined_adblock, 'r', encoding='utf-8', errors='ignore') as f:
            block_content = f.read()
        extracted_allow = extract_allow_rules_from_block(block_content)
        cleaned_block = clean_rules(block_content, BLOCK_PATTERN)
        
        cleaned_block_path = TMP_DIR / "cleaned_adblock.txt"
        with open(cleaned_block_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_block)
        log(f"清理后黑名单：{len(cleaned_block.splitlines())} 条规则")

        # 3. 合并白名单规则
        allow_files = list(TMP_DIR.glob("allow*.txt"))
        combined_allow_content = extracted_allow  # 先加入从黑名单提取的规则
        if allow_files:
            log(f"合并 {len(allow_files)} 个白名单文件...")
            combined_allow = TMP_DIR / "combined_allow.txt"
            with open(combined_allow, 'w', encoding='utf-8', errors='ignore') as out_f:
                for file in allow_files:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as in_f:
                        out_f.write(in_f.read() + '\n')
            with open(combined_allow, 'r', encoding='utf-8', errors='ignore') as f:
                combined_allow_content += '\n' + f.read()

        # 4. 清理白名单
        cleaned_allow = clean_rules(combined_allow_content, ALLOW_PATTERN)
        cleaned_allow_path = TMP_DIR / "cleaned_allow.txt"
        with open(cleaned_allow_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_allow)
        log(f"清理后白名单：{len(cleaned_allow.splitlines())} 条规则")

        # 5. 生成最终文件
        with open(cleaned_block_path, 'a', encoding='utf-8') as f:
            f.write('\n' + cleaned_allow)  # 黑名单追加白名单

        allow_final_path = TMP_DIR / "allow.txt"
        with open(allow_final_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_allow)

        # 6. 移动到目标目录（data/rules）
        adblock_target = TARGET_DIR / "adblock.txt"
        allow_target = TARGET_DIR / "allow.txt"
        cleaned_block_path.rename(adblock_target)
        allow_final_path.rename(allow_target)
        log(f"文件已移动到：{TARGET_DIR}")

        # 7. 去重
        deduplicate_file(adblock_target)
        deduplicate_file(allow_target)

        # 8. 复制到根目录（满足验证步骤需求）
        root_dir = SCRIPT_DIR.parent.parent.parent  # 项目根目录
        shutil.copy2(adblock_target, root_dir / "adblock.txt")
        shutil.copy2(allow_target, root_dir / "allow.txt")
        log(f"已复制到根目录：{root_dir}")

        log("所有处理完成！")

    except Exception as e:
        log(f"处理失败：{str(e)}")
        raise

if __name__ == "__main__":
    import shutil  # 确保shutil可用
    main()
