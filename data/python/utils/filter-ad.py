import sys
from pathlib import Path

class AdGuardProcessor:
    # 保持原有处理逻辑不变...
    def process_blacklist(self, black_path, white_path, output_path):
        if not black_path.exists():
            raise FileNotFoundError(f"黑名单文件不存在: {black_path}")
        if not white_path.exists():
            raise FileNotFoundError(f"白名单文件不存在: {white_path}")
        # 处理逻辑...

def main():
    try:
        processor = AdGuardProcessor()
        
        script_dir = Path(__file__).parent  # data/python/utils
        base_dir = script_dir.parent.parent.parent  # 项目根目录
        
        # 强制验证路径存在性
        dns_path = base_dir / 'dns.txt'
        allow_path = base_dir / 'allow.txt'
        output_path = base_dir / 'adblock-filtered.txt'
        
        if not dns_path.exists():
            print(f"::error::依赖文件缺失: {dns_path}，请检查DNS规则生成步骤")
            sys.exit(1)
        if not allow_path.exists():
            print(f"::error::依赖文件缺失: {allow_path}，请检查合并步骤")
            sys.exit(1)
        
        processor.process_blacklist(
            black_path=dns_path,
            white_path=allow_path,
            output_path=output_path
        )
        
        print(processor.generate_report())
        sys.exit(0)
    except Exception as e:
        print(f"::error::处理失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()