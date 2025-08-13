import re
import shutil
import sys
from pathlib import Path
from datetime import datetime

# 关键修复：正确计算项目根目录（向上四级）
# 脚本路径：data/python/utils/merge.py → 向上四级为项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # 修正为四级
TMP_DIR = PROJECT_ROOT / "tmp"  # 项目根目录下的tmp（如：/EasyAds/tmp）
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
    """合并tmp目录下的匹配文件（确保路径正确）"""
    TMP_DIR.mkdir(parents=True, exist_ok=True)  # 确保根目录下的tmp存在
    files = sorted(TMP_DIR.glob(pattern))  # 查找根目录tmp下的文件

    if not files:
        error(f"未找到匹配 {pattern} 的文件（路径：{TMP_DIR}）")
        return False  # 找不到文件时返回失败，避免生成空文件

    try:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            for file in files:
                content = ""
                # 尝试多种编码读取
                for encoding in ['utf-8', 'latin-1', 'gbk']:
                    try:
                        with open(file, 'r', encoding=encoding) as in_f:
                            content = in_f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    log(f"跳过无法解析的文件：{file}")
                    continue

                content = re.sub(r'\n{3,}', '\n\n', content.strip()) + '\n'
                out_f.write(f"# 合并自 {file.name}\n")
                out_f.write(content)
        log(f"合并完成：{len(files)} 个文件 → {output_path}")
        return True
    except Exception as e:
        error(f"合并失败：{str(e)}")
        return False

def clean_rules(input_path: Path, output_path: Path) -> bool:
    """清洗规则并保留有效内容"""
    if not input_path.exists():
        error(f"清洗失败：输入文件不存在 {input_path}")
        return False

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception as e:
        error(f"读取文件失败：{str(e)}")
        return False

    valid_lines = []
    for line in content.splitlines():
        line_strip = line.strip()
        # 保留有效规则和关键注释
        if (line_strip.startswith(('@@', '||', '|http', '|https', '/', '^', '##')) or
            (line_strip.startswith(('!', '#')) and 
             any(k in line_strip for k in ['白名单', '规则', '说明']))):
            valid_lines.append(line_strip)

    if not valid_lines:
        error(f"清洗后无有效规则：{input_path}")
        return False

    unique_lines = list(dict.fromkeys(valid_lines))  # 去重并保留顺序
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unique_lines) + '\n')
    log(f"清洗完成：{len(unique_lines)} 条规则 → {output_path}")
    return True

def extract_whitelist(cleaned_allow: Path, cleaned_adblock: Path) -> bool:
    """提取白名单并写入根目录allow.txt"""
    allow_lines = []
    # 从白名单文件提取
    if cleaned_allow.exists():
        with open(cleaned_allow, 'r', encoding='utf-8') as f:
            allow_lines = [line.strip() for line in f if line.strip().startswith('@@')]

    # 从广告规则中补充白名单
    if cleaned_adblock.exists():
        with open(cleaned_adblock, 'r', encoding='utf-8') as f:
            adblock_allow = [line.strip() for line in f if line.strip().startswith('@@')]
            allow_lines.extend(adblock_allow)

    if not allow_lines:
        error("未提取到任何白名单规则")
        return False

    unique_allow = list(dict.fromkeys(allow_lines))
    with open(WHITELIST_OUTPUT, 'w', encoding='utf-8') as f:
        f.write("# 自动生成的白名单规则\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write('\n'.join(unique_allow) + '\n')
    log(f"白名单生成：{len(unique_allow)} 条规则 → {WHITELIST_OUTPUT}")
    return True

def main():
    log(f"开始合并流程，项目根目录：{PROJECT_ROOT}")
    log(f"tmp目录：{TMP_DIR}")
    log(f"白名单输出路径：{WHITELIST_OUTPUT}")
    log(f"广告规则输出路径：{ADBLOCK_OUTPUT}")

    # 1. 合并广告规则（根目录tmp下的adblock*.txt）
    merged_adblock = TMP_DIR / "combined_adblock.txt"
    if not merge_files("adblock*.txt", merged_adblock):
        error("广告规则合并失败，终止流程")
        sys.exit(1)

    # 2. 清洗广告规则
    cleaned_adblock = TMP_DIR / "cleaned_adblock.txt"
    if not clean_rules(merged_adblock, cleaned_adblock):
        error("广告规则清洗失败，终止流程")
        sys.exit(1)

    # 3. 合并白名单规则（根目录tmp下的allow*.txt）
    merged_allow = TMP_DIR / "combined_allow.txt"
    if not merge_files("allow*.txt", merged_allow):
        error("白名单合并失败，终止流程")
        sys.exit(1)

    # 4. 清洗白名单规则
    cleaned_allow = TMP_DIR / "cleaned_allow.txt"
    if not clean_rules(merged_allow, cleaned_allow):
        error("白名单清洗失败，终止流程")
        sys.exit(1)

    # 5. 提取白名单到根目录
    if not extract_whitelist(cleaned_allow, cleaned_adblock):
        error("白名单生成失败，终止流程")
        sys.exit(1)

    # 6. 移动广告规则到根目录
    try:
        shutil.move(cleaned_adblock, ADBLOCK_OUTPUT)
        log(f"广告规则已移动到根目录 → {ADBLOCK_OUTPUT}")
    except Exception as e:
        error(f"移动广告规则失败：{str(e)}")
        sys.exit(1)

    # 7. 最终验证（确保文件在根目录）
    if not WHITELIST_OUTPUT.exists():
        error(f"根目录未找到白名单：{WHITELIST_OUTPUT}")
        sys.exit(1)
    if not ADBLOCK_OUTPUT.exists():
        error(f"根目录未找到广告规则：{ADBLOCK_OUTPUT}")
        sys.exit(1)

    log("所有流程完成，文件验证通过")

if __name__ == '__main__':
    main()
