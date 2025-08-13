import sys
from pathlib import Path

class AdGuardProcessor:
    """AdGuard规则处理器（假设已有实现，此处补充核心逻辑）"""
    def process_blacklist(self, black_path, white_path, output_path):
        # 读取黑名单和白名单
        with open(black_path, 'r', encoding='utf-8') as f:
            black_rules = set(f.read().splitlines())
        
        with open(white_path, 'r', encoding='utf-8') as f:
            white_rules = set(f.read().splitlines())
        
        # 过滤：黑名单排除白名单规则
        filtered = [rule for rule in black_rules if rule not in white_rules]
        
        # 写入输出
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(filtered)))
    
    def generate_report(self):
        return "规则过滤完成"

def main():
    try:
        processor = AdGuardProcessor()
        
        # 计算路径（严格校验层级）
        script_dir = Path(__file__).resolve().parent  # data/python/utils
        base_dir = script_dir.parent.parent.parent  # 项目根目录
        
        # 校验文件是否存在
        black_path = base_dir / 'dns.txt'
        white_path = base_dir / 'allow.txt'
        output_path = base_dir / 'adblock-filtered.txt'
        
        if not black_path.exists():
            raise FileNotFoundError(f"黑名单文件不存在: {black_path}")
        if not white_path.exists():
            raise FileNotFoundError(f"白名单文件不存在: {white_path}")
        
        # 调试路径
        print(f"::debug::根目录: {base_dir}")
        print(f"::debug::黑名单: {black_path}")
        print(f"::debug::白名单: {white_path}")
        print(f"::debug::输出文件: {output_path}")
        
        # 处理规则
        processor.process_blacklist(black_path, white_path, output_path)
        
        # 校验输出
        if not output_path.exists():
            raise RuntimeError("过滤后文件生成失败")
        
        print(processor.generate_report())
        sys.exit(0)
    except Exception as e:
        print(f"::error::处理失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()