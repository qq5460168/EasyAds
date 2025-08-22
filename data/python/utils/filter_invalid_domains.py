import re
import logging
from pathlib import Path
from typing import Set, List
import sys
import dns.resolver
from datetime import datetime
import pytz

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class InvalidDomainFilter:
    """过滤无效域名的工具类"""
    
    # 有效域名的正则模式
    VALID_DOMAIN_PATTERN = re.compile(
        r'^(?=.{1,253}$)'  # 总长度限制
        r'([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'  # 子域名部分
        r'[a-zA-Z]{2,}$'   # 顶级域名（至少2个字母）
    )
    
    # 需要排除的特殊域名模式
    EXCLUDED_PATTERNS = [
        re.compile(r'^localhost$'),
        re.compile(r'^local$'),
        re.compile(r'^loopback$'),
        re.compile(r'^ip6-localhost$'),
        re.compile(r'^::1$'),
        re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'),  # IP地址
        re.compile(r'^[0-9a-fA-F:]+$')  # IPv6地址
    ]

    def __init__(self):
        self.valid_domains: Set[str] = set()
        self.invalid_domains: Set[str] = set()
        self.skipped_domains: Set[str] = set()

    def is_domain_format_valid(self, domain: str) -> bool:
        """检查域名格式是否有效"""
        # 排除特殊模式
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern.match(domain):
                self.skipped_domains.add(domain)
                return False
                
        # 检查基本格式
        return bool(self.VALID_DOMAIN_PATTERN.match(domain))

    def is_domain_resolvable(self, domain: str, timeout: int = 5) -> bool:
        """检查域名是否可解析（尝试A记录或AAAA记录）"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = timeout
            resolver.lifetime = timeout
            
            # 尝试解析A记录
            resolver.query(domain, 'A')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            try:
                # 尝试解析AAAA记录
                resolver.query(domain, 'AAAA')
                return True
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return False
        except Exception as e:
            logger.debug(f"解析域名 {domain} 时出错: {str(e)}")
            return False

    def filter_domains(self, domains: List[str], check_resolvability: bool = True) -> None:
        """过滤域名列表，区分有效和无效域名"""
        logger.info(f"开始过滤域名，共 {len(domains)} 个待检查域名")
        
        for domain in domains:
            domain = domain.strip().lower()
            if not domain:
                continue
                
            # 先检查格式有效性
            if not self.is_domain_format_valid(domain):
                self.invalid_domains.add(domain)
                continue
                
            # 检查解析能力（可选）
            if check_resolvability and not self.is_domain_resolvable(domain):
                self.invalid_domains.add(domain)
                continue
                
            # 所有检查通过
            self.valid_domains.add(domain)
        
        logger.info(f"域名过滤完成 - 有效: {len(self.valid_domains)}, 无效: {len(self.invalid_domains)}, 跳过: {len(self.skipped_domains)}")

    def process_file(self, input_path: Path, output_path: Path, check_resolvability: bool = True) -> None:
        """处理单个文件，过滤无效域名"""
        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
        # 读取域名
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            domains = [line.strip() for line in f if line.strip() and not line.strip().startswith(('#', '!'))]
        
        # 过滤域名
        self.filter_domains(domains, check_resolvability)
        
        # 写入结果
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入头部信息
            beijing_tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            f.write(f"# 过滤后的域名列表\n")
            f.write(f"# 生成时间: {current_time}（北京时间）\n")
            f.write(f"# 原始域名数: {len(domains)}, 有效域名数: {len(self.valid_domains)}\n")
            f.write(f"# 过滤无效域名数: {len(self.invalid_domains)}, 跳过特殊域名数: {len(self.skipped_domains)}\n\n")
            
            # 写入有效域名（排序后）
            for domain in sorted(self.valid_domains):
                f.write(f"{domain}\n")
        
        logger.info(f"已将过滤结果写入 {output_path}")

def main():
    try:
        # 确定路径（从脚本位置定位到项目结构）
        script_path = Path(__file__).resolve()
        utils_dir = script_path.parent  # data/python/utils
        python_dir = utils_dir.parent   # data/python
        data_dir = python_dir.parent    # data
        root_dir = data_dir.parent      # 项目根目录
        tmp_dir = root_dir / "tmp"      # tmp目录
        
        # 确保tmp目录存在
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义输入输出文件（根据实际流程调整需要过滤的文件）
        input_files = {
            root_dir / "adblock.txt": tmp_dir / "filtered_adblock.txt",
            root_dir / "dns.txt": tmp_dir / "filtered_dns.txt",
            root_dir / "domain_list.txt": tmp_dir / "filtered_domain_list.txt"
        }
        
        # 处理每个文件
        for input_file, output_file in input_files.items():
            logger.info(f"开始处理文件: {input_file}")
            filter = InvalidDomainFilter()
            # 对于大型列表可以关闭解析检查以提高速度
            check_resolvability = not (input_file.name == "domain_list.txt" and input_file.stat().st_size > 1024 * 1024)
            filter.process_file(input_file, output_file, check_resolvability)
        
        logger.info("所有文件过滤完成")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"过滤域名失败: {str(e)}", exc_info=True)
        print(f"::error::过滤无效域名失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()