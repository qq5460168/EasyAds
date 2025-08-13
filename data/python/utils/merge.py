import re
import os
from pathlib import Path
from datetime import datetime

# 保持原有路径逻辑：在tmp目录内操作，目标目录为../data/rules/
TMP_DIR = Path("tmp")
TARGET_DIR = Path("../data/rules/")

# 规则匹配模式（沿用参考代码的核心正则）
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
    """清理规则内容，保留匹配模式的有效规则（移除注释和无效行）"""
    # 移除注释行（!或#开头）
    content = re.sub(r'^[!#].*$\n?', '', content, flags=re.MULTILINE)
    # 过滤出符合模式的有效规则
    valid_lines = [
        line for line in content.splitlines()
        if line.strip() and pattern.search(line.strip())
    ]
    return '\n'.join(valid_lines)

def extract_allow_rules_from_block(content: str) -> str:
    """从黑名单内容中提取白名单规则（@@开头的例外规则）"""
    allow_lines = [
        line.strip() for line in content.splitlines()
        if line.strip().startswith('@@') and ALLOW_PATTERN.search(line.strip())
    ]
    return '\n'.join(allow_lines)

def deduplicate_file(filepath: Path):
    """去重文件内容（保留顺序，不区分大小写）"""
    if not filepath.exists():
        log(f"去重失败：文件不存在 {filepath}")
        return
    
    with open(filepath, 'r+', encoding='utf-8') as f:
        seen = set()
        unique_lines = []
        for line in f:
            # 忽略空行
            if not line.strip():
                continue
            # 大小写不敏感去重
            lower_line = line.lower()
            if lower_line not in seen:
                seen.add(lower_line)
                unique_lines.append(line)
        # 写入去重后内容
        f.seek(0)
        f.writelines(unique_lines)
        f.truncate()
    log(f"已去重：{filepath}（保留 {len(unique_lines)} 条规则）")

def main():
    try:
        # 确保目录存在
        TMP_DIR.mkdir(exist_ok=True)
        TARGET_DIR.mkdir(exist_ok=True)
        log(f"工作目录：{os.getcwd()}/tmp")
        log(f"目标目录：{TARGET_DIR.resolve()}")

        # 1. 合并所有adblock规则文件
        adblock_files = list(TMP_DIR.glob("adblock*.txt"))
        if not adblock_files:
            log("警告：未找到adblock*.txt文件，跳过黑名单合并")
            return
        
        log(f"合并 {len(adblock_files)} 个黑名单文件...")
        combined_adblock_path = TMP_DIR / "combined_adblock.txt"
        with open(combined_adblock_path, 'w', encoding='utf-8', errors='ignore') as out_f:
            for file in adblock_files:
                with open(file, 'r', encoding='utf-8', errors='ignore') as in_f:
                    out_f.write(in_f.read() + '\n')
                log(f"已合并：{file.name}")

        # 2. 处理黑名单：清理规则 + 提取白名单规则
        log("处理黑名单规则...")
        with open(combined_adblock_path, 'r', encoding='utf-8', errors='ignore') as f:
            block_content = f.read()
        
        # 提取黑名单中的白名单规则
        extracted_allow = extract_allow_rules_from_block(block_content)
        log(f"从黑名单中提取 {len(extracted_allow.splitlines())} 条白名单规则")
        
        # 清理黑名单规则
        cleaned_block = clean_rules(block_content, BLOCK_PATTERN)
        cleaned_block_path = TMP_DIR / "cleaned_adblock.txt"
        with open(cleaned_block_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_block)
        log(f"清理后黑名单规则：{len(cleaned_block.splitlines())} 条")

        # 3. 合并所有白名单规则文件
        allow_files = list(TMP_DIR.glob("allow*.txt"))
        if not allow_files:
            log("警告：未找到allow*.txt文件，仅使用从黑名单提取的白名单规则")
            combined_allow_content = extracted_allow
        else:
            log(f"合并 {len(allow_files)} 个白名单文件...")
            combined_allow_path = TMP_DIR / "combined_allow.txt"
            with open(combined_allow_path, 'w', encoding='utf-8', errors='ignore') as out_f:
                for file in allow_files:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as in_f:
                        out_f.write(in_f.read() + '\n')
                    log(f"已合并：{file.name}")
            # 读取合并后的白名单内容
            with open(combined_allow_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_allow_content = f.read() + '\n' + extracted_allow  # 合并提取的规则

        # 4. 清理白名单规则
        log("处理白名单规则...")
        cleaned_allow = clean_rules(combined_allow_content, ALLOW_PATTERN)
        cleaned_allow_path = TMP_DIR / "cleaned_allow.txt"
        with open(cleaned_allow_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_allow)
        log(f"清理后白名单规则：{len(cleaned_allow.splitlines())} 条")

        # 5. 生成最终规则（黑名单 + 白名单）
        log("生成最终规则文件...")
        with open(cleaned_block_path, 'a', encoding='utf-8') as f:
            f.write('\n' + cleaned_allow)  # 追加白名单到黑名单

        # 6. 生成独立白名单文件
        allow_final_path = TMP_DIR / "allow.txt"
        with open(allow_final_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_allow)

        # 7. 移动文件到目标目录
        log("移动文件到目标目录...")
        adblock_target = TARGET_DIR / "adblock.txt"
        allow_target = TARGET_DIR / "allow.txt"
        
        # 覆盖目标文件（若存在）
        if cleaned_block_path.exists():
            cleaned_block_path.rename(adblock_target)
        if allow_final_path.exists():
            allow_final_path.rename(allow_target)

        # 8. 去重处理
        log("开始去重...")
        deduplicate_file(adblock_target)
        deduplicate_file(allow_target)

        log("所有规则处理完成！")

    except Exception as e:
        log(f"处理失败：{str(e)}")
        raise  # 抛出异常便于调试

if __name__ == "__main__":
    main()
