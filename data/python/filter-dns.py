import os
from pathlib import Path
import datetime

def filter_adblock_rules(input_path, output_path):
    """
    Filter AdBlock rules and write DNS rules format.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        # 增加详细路径信息用于调试
        raise FileNotFoundError(
            f"Input file not found: {input_path}\n"
            f"Absolute path: {input_path.absolute()}"
        )
    
    try:
        with input_path.open('r', encoding='utf-8') as infile, \
             output_path.open('w', encoding='utf-8') as outfile:
            
            # 写入文件头
            outfile.write(f"# DNS rules extracted from {input_path.name}\n")
            outfile.write(f"# Generated on {datetime.datetime.now()}\n\n")
            
            count = 0
            for line in infile:
                line = line.strip()
                if line.startswith("||") and line.endswith("^"):
                    outfile.write(line + '\n')
                    count += 1
            
            print(f"Processed {count} DNS rules")
            
    except IOError as e:
        print(f"Error processing files: {e}")

if __name__ == "__main__":
    # 修正路径计算：确保正确获取规则目录
    script_dir = Path(__file__).resolve().parent  # 获取当前脚本所在目录（绝对路径）
    rules_dir = script_dir.parent / "rules"       # 规则目录：data/python/../rules → data/rules
    
    # 明确输入输出文件路径
    input_file = rules_dir / "adblock.txt"
    output_file = rules_dir / "dns.txt"
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 调试：打印实际路径（可在修复后删除）
    print(f"Script directory: {script_dir}")
    print(f"Rules directory: {rules_dir}")
    print(f"Input file path: {input_file}")
    
    filter_adblock_rules(input_file, output_file)
