import dns.resolver
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def is_valid_domain(domain: str) -> bool:
    """验证域名是否有效（通过DNS解析）"""
    if not domain or len(domain) > 255:
        return False
    # 简单格式校验
    if not all(c in "abcdefghijklmnopqrstuvwxyz0123456789-." for c in domain.lower()):
        return False
    # DNS解析校验
    try:
        # 尝试解析A记录或AAAA记录
        dns.resolver.resolve(domain, 'A')
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
        try:
            dns.resolver.resolve(domain, 'AAAA')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
            return False
    except Exception as e:
        logger.warning(f"验证域名 {domain} 时出错: {str(e)}")
        return False

def filter_invalid_domains(input_path: Path, output_path: Path) -> None:
    """过滤无效域名并保存结果"""
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}")
        return
    
    valid_domains = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            domain = line.strip()
            if domain and is_valid_domain(domain):
                valid_domains.append(domain)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(valid_domains) + '\n')
    logger.info(f"过滤完成: 保留 {len(valid_domains)} 个有效域名，输出至 {output_path}")

def main():
    # 路径配置（与项目其他脚本保持一致）
    tmp_dir = Path('tmp')
    filter_invalid_domains(
        input_path=tmp_dir / "cleaned_adblock.txt",
        output_path=tmp_dir / "filtered_adblock.txt"
    )
    filter_invalid_domains(
        input_path=tmp_dir / "dns.txt",
        output_path=tmp_dir / "filtered_dns.txt"
    )

if __name__ == "__main__":
    main()