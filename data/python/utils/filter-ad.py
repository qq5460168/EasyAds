# EasyAds/data/python/utils/filter-ad.py
import sys
from pathlib import Path
import common  # 导入通用工具

class AdGuardProcessor:
    """AdGuard规则处理器（假设已有实现）"""
    def process_blacklist(self, black_path, white_path, output_path):
        # 原有处理逻辑...
        pass
    
    def generate_report(self):
        return "处理完成报告"

def main():
    try:
        processor = AdGuardProcessor()
        
        # 更可靠的路径计算（基于当前脚本定位项目根目录）
        script_path = Path(__file__).resolve()
        # 脚本位于 data/python/utils/，根目录为上三级
        base_dir = script_path.parent.parent.parent  # EasyAds/
        
        # 验证路径存在
        black_path = base_dir / "dns.txt"
        white_path = base_dir / "allow.txt"
        output_path = base_dir / "adblock-filtered.txt"
        
        for path in [black_path, white_path]:
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
        
        # 调试日志
        common.logger.debug(f"基础目录: {base_dir}")
        common.logger.debug(f"黑名单路径: {black_path}")
        common.logger.debug(f"白名单路径: {white_path}")
        
        # 处理规则
        processor.process_blacklist(
            black_path=black_path,
            white_path=white_path,
            output_path=output_path
        )
        
        common.logger.info(processor.generate_report())
        sys.exit(0)
    except Exception as e:
        common.logger.error(f"处理失败: {str(e)}", exc_info=True)  # 输出堆栈信息
        sys.exit(1)

if __name__ == "__main__":
    main()