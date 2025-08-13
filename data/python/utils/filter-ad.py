def main():
    try:
        processor = AdGuardProcessor()
        
        # 修正路径计算，确保指向项目根目录
        script_dir = Path(__file__).parent  # data/python/utils
        base_dir = script_dir.parent.parent.parent  # 项目根目录（EasyAds/）
        
        # 调试输出路径信息（确认路径正确性）
        print(f"::debug::基础目录: {base_dir}")
        print(f"::debug::白名单路径: {base_dir / 'allow.txt'}")
        print(f"::debug::黑名单路径: {base_dir / 'dns.txt'}")  # 关键修正：根目录的dns.txt
        
        processor.process_blacklist(
            black_path=base_dir / 'dns.txt',  # 修正为根目录的dns.txt
            white_path=base_dir / 'allow.txt',  # 根目录的allow.txt
            output_path=base_dir / 'adblock-filtered.txt'
        )
        
        print(processor.generate_report())
        sys.exit(0)
    except Exception as e:
        print(f"::error::🚨 处理失败: {str(e)}")
        sys.exit(1)
