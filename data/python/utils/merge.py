import re
import shutil
from pathlib import Path
from datetime import datetime

# 配置常量（统一路径管理）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # 项目根目录
TMP_DIR = PROJECT_ROOT / "tmp"  # 临时文件目录
WHITELIST_OUTPUT = PROJECT_ROOT / "allow.txt"  # 根目录白名单文件
ADBLOCK_OUTPUT = PROJECT_ROOT / "adblock.txt"  # 根目录广告规则文件

def log(message: str):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [MERGE] {message}")

def error(message: str):
    """错误日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [MERGE ERROR] {message}", file=sys.stderr)

def merge_files(pattern: str, output_path: Path) -> bool:
    """合并匹配模式的文件到指定路径，返回是否成功"""
    # 查找所有匹配的文件（基于临时目录）
    files = sorted(TMP_DIR.glob(pattern))
    if not files:
        log(f"未找到匹配 {pattern} 的文件，返回空内容")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("")  # 生成空文件避免后续步骤报错
        return True

    # 合并文件内容
    try:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            for file in files:
                # 尝试多种编码读取，兼容不同格式文件
                for:
                    try:
                        with open(file, 'r', encoding=encoding) as in_f:
                            content = in_f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    log(f"跳过无法解析的文件 {file}")
                    continue
                # 移除连续空行，保留单空行分隔
                content = re.sub(r'\n{3,}', '\n\n', content.strip()) + '\n'
                out_f.write(f"# 合并自 {file.name}\n")
                out_f.write(content)
        log(f"成功合并 {len(files)} 个文件到 {output_path}")
        return True
    except Exception as e:
        error(f"合并文件失败: {str(e)}")
        return False

def clean_rules(input_path: Path, output_path: Path) -> bool:
    """清洗规则文件，保留有效规则，返回是否成功"""
    if not input_path.exists():
        error(f"清洗失败：输入文件不存在 {input_path}")
        return False

    # 读取文件内容
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception as e:
        error(f"读取文件失败 {input_path}: {str(e)}")
        return False

    # 清洗逻辑：保留有效规则和必要注释
    lines = []
    for line in content.splitlines():
        line_strip = line.strip()
        # 保留白名单规则（@@开头）、广告规则（||/*/^等）、元素隐藏规则（##开头）
        if line_strip.startswith(('@@', '||', '|http', '|https', '/', '^', '##')):
            lines.append(line_strip)
        # 保留关键注释（含"白名单"、"规则说明"等关键词）
        elif line_strip.startswith(('!', '#')) and any(keyword in line_strip for keyword in ['白名单', '规则', '说明', '允许']):
            lines.append(line_strip)

    # 去重并写入清洗后文件
    try:
        unique_lines = list(dict.fromkeys(lines))  # 保留顺序去重
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_lines) + '\n')
        log(f"规则清洗完成，保留 {len(unique_lines)} 条有效规则 -> {output_path}")
        return True
    except Exception as e:
        error(f"写入清洗文件失败 {output_path}: {str(e)}")
        return False

def extract_whitelist(cleaned_allow: Path, cleaned_adblock: Path, output_allow: Path) -> bool:
    """从清洗后的文件中提取白名单规则，确保生成独立白名单文件"""
    # 读取清洗后的白名单规则
    if not cleaned_allow.exists():
        error(f"提取白名单失败：源文件不存在 {cleaned_allow}")
        return False

    try:
        with open(cleaned_allow, 'r', encoding='utf-8') as f:
            allow_lines = [line.strip() for line in f if line.strip().startswith('@@')]
    except Exception as e:
        error(f"读取白名单源文件失败: {str(e)}")
        return False

    # 合并广告规则中的白名单（如果有）
    if cleaned_adblock.exists():
        with open(cleaned_adblock, 'r', encoding='utf-8') as f:
            adblock_lines = [line.strip() for line in f if line.strip().startswith('@@')]
        allow_lines.extend(adblock_lines)

    # 去重并写入根目录白名单文件
    try:
        unique_allow = list(dict.fromkeys(allow_lines))  # 保留顺序去重
        with open(output_allow, 'w', encoding='utf-8') as f:
            f.write("# 自动生成的白名单规则\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 规则数量: {len(unique_allow)}\n")
            f.write('\n'.join(unique_allow) + '\n')
        log(f"白名单提取完成，共 {len(unique_allow)} 条规则 -> {output_allow}")
        return True
    except Exception as e:
        error(f"写入白名单文件失败 {output_allow}: {str(e)}")
        return False

def main():
    # 确保临时目录存在
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    log(f"开始规则合并流程，项目根目录: {PROJECT_ROOT}")

    # 1. 合并广告规则（tmp/adblock*.txt）
    merged_adblock = TMP_DIR / "combined_adblock.txt"
    if not merge_files("adblock*.txt", merged_adblock):
        error("广告规则合并失败，终止流程")
        return

    # 2. 清洗广告规则
    cleaned_adblock = TMP_DIR / "cleaned_adblock.txt"
    if not clean_rules(merged_adblock, cleaned_adblock):
        error("广告规则清洗失败，终止流程")
        return

    # 3. 合并白名单规则（tmp/allow*.txt）
    merged_allow = TMP_DIR / "combined_allow.txt"
    if not merge_files("allow*.txt", merged_allow):
        log("白名单合并文件为空，使用空规则继续")

    # 4. 清洗白名单规则
    cleaned_allow = TMP_DIR / "cleaned_allow.txt"
    if not clean_rules(merged_allow, cleaned_allow):
        error("白名单规则清洗失败，终止流程")
        return

    # 5. 提取白名单并生成根目录allow.txt（核心修复步骤）
    if not extract_whitelist(cleaned_allow, cleaned_adblock, WHITELIST_OUTPUT):
        error("白名单生成失败，终止流程")
        return

    # 6. 移动清洗后的广告规则到根目录
    try:
        shutil.move(cleaned_adblock, ADBLOCK_OUTPUT)
        log(f"广告规则已移动到根目录 -> {ADBLOCK_OUTPUT}")
    except Exception as e:
        error(f"移动广告规则失败: {str(e)}")
        return

    # 7. 最终校验：确认根目录文件存在
    if not WHITELIST_OUTPUT.exists():
        error("致命错误：根目录未生成allow.txt")
        return
    if not ADBLOCK_OUTPUT.exists():
        error("致命错误：根目录未生成adblock.txt")
        return

    log("所有规则处理完成，根目录文件验证通过")
    log(f"白名单路径: {WHITELIST_OUTPUT}")
    log(f"广告规则路径: {ADBLOCK_OUTPUT}")

if __name__ == '__main__':
    import sys  # 确保sys模块可用
    main()
