import os
from pathlib import Path
import datetime

def filter_adblock_rules(input_path, output_path):
    """Filter AdBlock rules and write DNS rules format"""
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        with input_path.open('r', encoding='utf-8') as infile, \
             output_path.open('w', encoding='utf-8') as outfile:
            
            # Write header
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
    # 输入输出路径改为根目录
    input_file = Path("./adblock.txt")  # 根目录的adblock.txt
    output_file = Path("./dns.txt")     # 输出到根目录
    
    # 确保输出目录存在（根目录已存在）
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    filter_adblock_rules(input_file, output_file)