import re
from pathlib import Path
from datetime import datetime
import sys  # 新增

def generate_hosts_rules():
    """生成Hosts规则（0.0.0.0 域名格式）"""
    # 定位项目根目录（基于脚本自身路径）
    script_path = Path(__file__).resolve()
    rules_gen_dir = script_path.parent  # data/python/rules_generator
    project_root = rules_gen_dir.parent.parent.parent  # 项目根目录（EasyAds/）
    
    input_path = project_root / "adblock.txt"
    output_path = project_root / "hosts.txt"
    
    if not input_path.exists():
        raise FileNotFoundError(f"源文件不存在: {input_path}")
    
    domain_pattern = re.compile(r'^\|\|([a-zA-Z0-9.-]+)\^.*$', re.MULTILINE)
    
    with input_path.open('r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    domains = set(domain_pattern.findall(content))
    total = len(domains)
    
    with output_path.open('w', encoding='utf-8') as f:
        f.write(f"# Hosts规则 - 自动生成\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 规则总数: {total}\n\n")
        for domain in sorted(domains):
            f.write(f"0.0.0.0 {domain}\n")
    
    # 新增：校验输出文件是否生成成功
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"生成失败，文件不存在或为空: {output_path}")
    
    print(f"Hosts规则生成完成，输出到 {output_path}，共 {total} 条")

if __name__ == "__main__":
    try:
        generate_hosts_rules()
        sys.exit(0)  # 显式返回成功退出码
    except Exception as e:
        print(f"::error::{str(e)}")
        sys.exit(1)  # 异常时返回错误退出码