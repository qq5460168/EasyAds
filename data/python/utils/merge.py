import re
import shutil
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录计算（确保路径绝对化）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # 从当前脚本向上三级
TMP_DIR = PROJECT_ROOT / "tmp"  # 临时文件目录
WHITELIST_OUTPUT = PROJECT_ROOT / "allow.txt"  # 根目录白名单
ADBLOCK_OUTPUT = PROJECT_ROOT / "adblock.txt"  # 根目录广告规则

def log(message: str):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [MERGE] {message}")

def error(message: str):
    """错误日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [MERGE ERROR] {message}", file=sys.stderr)

def merge_files(pattern: str, output_path: Path) -> bool:
    """合并匹配模式的文件，修复语法错误并优化编码处理"""
    TMP_DIR.mkdir(parents=True, exist_ok=True)  # 确保临时目录存在
    files = sorted(TMP_DIR.glob(pattern))  # 查找匹配文件

    if not files:
        log(f"未找到匹配 {pattern} 的文件，生成空文件")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("")
        return True

    try:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            for file in files:
                content = ""
                # 修复语法错误：正确的编码迭代循环（原错误为for:）
                for encoding in ['utf-8', 'latin-1', 'gbk']:  # 这里修复了for循环的语法
                    try:
                        with open(file, 'r', encoding=encoding) as in_f:
                            content = in_f.read()
                        break  # 编码正确则退出循环
                    except UnicodeDecodeError:
                        continue  # 尝试下一种编码
                else:
                    log(f"警告：无法解析文件 {file}，跳过")
                    continue

                # 清理内容并写入
                content = re.sub(r'\n{3,}', '\n\n', content.strip()) + '\n'
                out_f.write(f"# 合并自 {file.name}\n")
                out_f.write(content)
        log(f"成功合并 {len(files)} 个文件到 {output_path}")
        return True
    except Exception as e:
        error(f"合并文件失败: {str(e)}")
        return False

def clean_rules(input_path: Path, output_path: Path) -> bool:
    """清洗规则文件，保留有效规则"""
    if not input_path.exists():
        error(f"清洗失败：输入文件不存在 {input_path}")
        return False

    try:
        # 读取文件内容（兼容多种编码）
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception as e:
        error(f"读取文件失败 {input_path}: {str(e)}")
        return False

    # 提取有效规则
    valid_lines = []
    for line in content.splitlines():
        line_strip = line.strip()
        # 保留白名单（@@）、广告规则（||/*/^）、元素隐藏（##）及关键注释
        if (line_strip.startswith(('@@', '||', '|http', '|https', '/', '^', '##')) or
            (line_strip.startswith(('!', '#')) and 
             any(k in line_strip for k in ['白名单', '规则', '说明']))):
            valid_lines.append(line_strip)

    # 去重并写入
    unique_lines = list(dict.fromkeys(valid_lines))  # 保留顺序去重
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unique_lines) + '\n')
    log(f"清洗完成，保留 {len(unique_lines)} 条规则 -> {output_path}")
    return True

def extract_whitelist(cleaned_allow: Path, cleaned_adblock: Path) -> bool:
    """提取白名单规则并写入根目录allow.txt"""
    # 读取清洗后的白名单
    allow_lines = []
    if cleaned_allow.exists():
        with open(cleaned_allow, 'r', encoding='utf-8') as f:
            allow_lines = [line.strip() for line in f if line.strip().startswith('@@')]

    # 从广告规则中补充白名单（如果有）
    if cleaned_adblock.exists():
        with open(cleaned_adblock, 'r', encoding='utf-8') as f:
            adblock_allow = [line.strip() for line in f if line.strip().startswith('@@')]
            allow_lines.extend(adblock_allow)

    # 去重并写入根目录
    unique_allow = list(dict.fromkeys(allow_lines))
    with open(WHITELIST_OUTPUT, 'w', encoding='utf-8') as f:
        f.write("# 自动生成的白名单规则\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write('\n'.join(unique_allow) + '\n')
    log(f"白名单生成完成，共 {len(unique_allow)} 条规则 -> {WHITELIST_OUTPUT}")
    return True

def main():
    log(f"开始规则合并流程，根目录: {PROJECT_ROOT}")

    # 1. 合并广告规则
    merged_adblock = TMP_DIR / "combined_adblock.txt"
    if not merge_files("adblock*.txt", merged_adblock):
        error("广告规则合并失败，终止流程")
        sys.exit(1)

    # 2. 清洗广告规则
    cleaned_adblock = TMP_DIR / "cleaned_adblock.txt"
    if not clean_rules(merged_adblock, cleaned_adblock):
        error("广告规则清洗失败，终止流程")
        sys.exit(1)

    # 3. 合并白名单规则
    merged_allow = TMP_DIR / "combined_allow.txt"
    if not merge_files("allow*.txt", merged_allow):
        error("白名单合并失败，终止流程")
        sys.exit(1)

    # 4. 清洗白名单规则
    cleaned_allow = TMP_DIR / "cleaned_allow.txt"
    if not clean_rules(merged_allow, cleaned_allow):
        error("白名单清洗失败，终止流程")
        sys.exit(1)

    # 5. 提取并生成根目录白名单
    if not extract_whitelist(cleaned_allow, cleaned_adblock):
        error("白名单生成失败，终止流程")
        sys.exit(1)

    # 6. 移动广告规则到根目录
    try:
        shutil.move(cleaned_adblock, ADBLOCK_OUTPUT)
        log(f"广告规则已移动到根目录 -> {ADBLOCK_OUTPUT}")
    except Exception as e:
        error(f"移动广告规则失败: {str(e)}")
        sys.exit(1)

    # 7. 最终校验
    if not WHITELIST_OUTPUT.exists() or not ADBLOCK_OUTPUT.exists():
        error("根目录未生成allow.txt或adblock.txt")
        sys.exit(1)

    log("所有规则处理完成，文件验证通过")

if __name__ == '__main__':
    main()
