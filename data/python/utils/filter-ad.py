# 在 filter-ad.py 的 main 函数中，修正路径：
def main():
    try:
        processor = AdGuardProcessor()
        
        # 原路径错误：script_dir 是 data/python，rules_dir 应为项目根目录
        script_dir = Path(__file__).parent  # data/python/utils
        base_dir = script_dir.parent.parent.parent  # 项目根目录（EasyAds/）
        
        # 调试输出路径信息
        print(f"::debug::基础目录: {base_dir}")
        print(f"::debug::白名单路径: {base_dir / 'allow.txt'}")
        print(f"::debug::黑名单路径: {base_dir / 'dns.txt'}")  # 匹配 filter-dns.py 的输出路径
        
        processor.process_blacklist(
            black_path=base_dir / 'dns.txt',  # 修正为根目录的 dns.txt
            white_path=base_dir / 'allow.txt',  # 修正为根目录的 allow.txt
            output_path=base_dir / 'adblock-filtered.txt'
        )
        
        print(processor.generate_report())
        sys.exit(0)
    except Exception as e:
        print(f"::error::🚨 处理失败: {str(e)}")
        sys.exit(1)
