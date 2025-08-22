import re
from pathlib import Path
import sys

def extract_domains(input_path: Path, output_path: Path) -> None:
    """从dns.txt提取域名并生成纯域名列表"""
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    
    # 提取域名的正则模式（适配AdBlock规则）
    pattern = re.compile(r'^(\|\||\|http(s)?:\/\/)([^*^|~#]+)')
    domains = set()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith(('!', '#', '@@')):
                continue
                
            match = pattern.match(line.split('$')[0])
            if match:
                domain = match.group(3).lower()
                # 移除可能的路径和参数
                if '/' in domain:
                    domain = domain.split('/')[0]
                # 移除端口号
                if ':' in domain:
                    domain = domain.split(':')[0]
                # 过滤无效域名
                if '.' in domain and not domain.startswith(('.', '*')):
                    domains.add(domain)
    
    # 排序并写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# EasyAds 纯域名列表\n")
        f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}（北京时间）\n")
        f.write(f"# 共 {len(domains)} 个域名\n\n")
        for domain in sorted(domains):
            f.write(f"{domain}\n")
    
    print(f"已提取 {len(domains)} 个域名到 {output_path}")

if __name__ == "__main__":
    try:
        import time
        
        # 修正路径计算：从rules_generator目录定位到项目根目录
        # 当前脚本路径: data/python/rules_generator/domain_list.py
        script_path = Path(__file__).resolve()  # 绝对路径
        rules_gen_dir = script_path.parent      # data/python/rules_generator
        python_dir = rules_gen_dir.parent       # data/python
        data_dir = python_dir.parent            # data
        root_dir = data_dir.parent              # 项目根目录 (EasyAds)
        
        # 定义输入输出路径（dns.txt在根目录，输出也到根目录）
        input_file = root_dir / "dns.txt"
        output_file = root_dir / "domain_list.txt"
        
        # 调试路径信息
        print(f"提取域名列表中...")
        print(f"寻找输入文件位置: {input_file}")
        print(f"绝对输入路径: {input_file.absolute()}")
        
        extract_domains(input_file, output_file)
        sys.exit(0)
    except Exception as e:
        print(f"::error::处理失败: {str(e)}")
        sys.exit(1)
