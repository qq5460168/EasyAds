import os
from pathlib import Path

def replace_content_in_file(input_file: str, output_file: str) -> int:
    """Convert DNS rules to Quantumult X format"""
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    processed_count = 0
    
    try:
        with input_path.open('r', encoding='utf-8') as infile, \
             output_path.open('w', encoding='utf-8') as outfile:
            
            for line in infile:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if (':' not in line and '.js' not in line and '/' not in line and
                    line.startswith("||") and line.endswith("^")):
                    new_line = line.replace("||", "DOMAIN,").replace("^", ",reject")
                    outfile.write(new_line + '\n')
                    processed_count += 1
                    
        return processed_count
        
    except IOError as e:
        print(f"Error processing files: {e}")
        return 0

def remove_whitelist_domains(input_file: str, whitelist_file: str) -> int:
    """Remove whitelisted domains from the rules file"""
    input_path = Path(input_file)
    whitelist_path = Path(whitelist_file)
    
    if not input_path.exists() or not whitelist_path.exists():
        raise FileNotFoundError("Input or whitelist file not found")
    
    removed_count = 0
    
    try:
        with whitelist_path.open('r', encoding='utf-8') as wfile:
            whitelist = {entry.strip()[4:-1] 
                        for entry in wfile 
                        if entry.strip().startswith('@@||') 
                        and entry.strip().endswith('^')}
        
        with input_path.open('r', encoding='utf-8') as infile:
            lines = infile.readlines()
        
        with input_path.open('w', encoding='utf-8') as outfile:
            for line in lines:
                domain = line.split(',')[1] if line.startswith('DOMAIN,') else None
                if domain and domain in whitelist:
                    removed_count += 1
                else:
                    outfile.write(line)
                    
        return removed_count
        
    except IOError as e:
        print(f"Error processing files: {e}")
        return 0

if __name__ == "__main__":
    # 路径改为根目录
    input_file = Path("./dns.txt")               # 根目录的dns.txt
    output_file = Path("./qx.list")              # 输出到根目录
    whitelist_file = Path("./data/mod/whitelist.txt")  # 白名单路径不变
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    processed = replace_content_in_file(input_file, output_file)
    removed = remove_whitelist_domains(output_file, whitelist_file)
    
    print(f"Processed {processed} rules, removed {removed} whitelisted domains")