import sys
from pathlib import Path

class AdGuardProcessor:
    def __init__(self):
        # 初始化计数器用于生成报告
        self.total_black = 0
        self.total_white = 0
        self.filtered_count = 0

    def process_blacklist(self, black_path, white_path, output_path):
        """处理黑名单并应用白名单过滤"""
        # 读取白名单规则
        white_domains = self._load_white_domains(white_path)
        self.total_white = len(white_domains)
        
        # 处理黑名单并过滤
        with open(black_path, 'r', encoding='utf-8') as black_file, \
             open(output_path, 'w', encoding='utf-8') as out_file:
            
            for line in black_file:
                line = line.strip()
                if not line or line.startswith(('#', '!')):
                    continue  # 跳过注释和空行
                self.total_black += 1
                
                # 检查是否在白名单中
                if not self._is_whitelisted(line, white_domains):
                    out_file.write(line + '\n')
                    self.filtered_count += 1

    def _load_white_domains(self, white_path):
        """加载白名单域名"""
        domains = set()
        with open(white_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('@@||') and line.endswith('^'):
                    # 提取 @@||domain.com^ 中的 domain.com
                    domain = line[2:-1]
                    domains.add(domain)
        return domains

    def _is_whitelisted(self, line, white_domains):
        """检查规则是否命中白名单"""
        if line.startswith('||') and line.endswith('^'):
            domain = line[2:-1]
            return domain in white_domains
        return False

    def generate_report(self):
        """生成处理报告（新增此方法）"""
        return (
            f"处理完成：\n"
            f"- 原始黑名单规则数：{self.total_black}\n"
            f"- 白名单规则数：{self.total_white}\n"
            f"- 过滤后规则数：{self.filtered_count}"
        )

def main():
    try:
        processor = AdGuardProcessor()
        
        script_dir = Path(__file__).parent  # data/python/utils
        base_dir = script_dir.parent.parent.parent  # 项目根目录（EasyAds/）
        
        # 调试输出路径信息
        print(f"::debug::基础目录: {base_dir}")
        print(f"::debug::白名单路径: {base_dir / 'allow.txt'}")
        print(f"::debug::黑名单路径: {base_dir / 'dns.txt'}")
        
        processor.process_blacklist(
            black_path=base_dir / 'dns.txt',
            white_path=base_dir / 'allow.txt',
            output_path=base_dir / 'adblock-filtered.txt'
        )
        
        # 调用生成报告的方法
        print(processor.generate_report())
        sys.exit(0)
    except Exception as e:
        print(f"::error::🚨 处理失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()