import re
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from pathlib import Path
from typing import Set, Tuple, List, Optional

# 配置日志（更详细的解析结果记录）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dns_filter.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 国内外DNS服务器（保持原配置，增加超时重试参数）
DNS_CONFIG = {
    "servers": {
        "domestic": [
            "223.5.5.5",    # 阿里云
            "119.29.29.29", # 腾讯云
            "114.114.114.114"  # 114DNS
        ],
        "foreign": [
            "8.8.8.8",      # Google
            "1.1.1.1",      # Cloudflare
            "208.67.222.222"  # OpenDNS
        ]
    },
    "timeout": 3,       # 单次解析超时（秒）
    "retry": 1          # 超时重试次数
}

# 支持的规则格式正则（扩展适配项目所有格式）
RULE_PATTERNS = [
    re.compile(r'^\|\|([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-.]+)\^?$'),  # dns.txt: ||domain.com^
    re.compile(r'^block\s+([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-.]+)$'),  # adclose.txt: block domain
    re.compile(r'^([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-.]+)\s+block$'),  # invizible.txt: domain block
    re.compile(r'^([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-.]+)$')            # domain_list.txt: 纯域名
]

# 解析结果缓存（避免重复解析）
dns_cache: dict[str, bool] = {}


def load_whitelist(whitelist_paths: List[Path]) -> Set[str]:
    """加载白名单域名（从多个白名单文件提取）"""
    whitelist = set()
    for path in whitelist_paths:
        if not path.exists():
            logger.warning(f"白名单文件不存在：{path}")
            continue
        with path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if not line or line.startswith(('#', '!')):
                    continue
                # 从白名单规则中提取域名（复用规则解析逻辑）
                domain = extract_domain(line)
                if domain:
                    whitelist.add(domain)
    logger.info(f"加载白名单完成，共 {len(whitelist)} 个域名")
    return whitelist


def extract_domain(rule_line: str) -> Optional[str]:
    """从规则行提取域名（适配所有支持的格式）"""
    line = rule_line.strip().lower()
    if not line or line.startswith(('#', '!')):
        return None
    for pattern in RULE_PATTERNS:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def check_dns_with_retry(domain: str, dns_server: str) -> bool:
    """带重试的DNS解析检查（处理临时网络错误）"""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [dns_server]
    resolver.timeout = DNS_CONFIG["timeout"]
    resolver.lifetime = DNS_CONFIG["timeout"]

    for _ in range(DNS_CONFIG["retry"] + 1):
        try:
            # 同时检查A和AAAA记录
            resolver.resolve(domain, 'A')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            try:
                resolver.resolve(domain, 'AAAA')
                return True
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return False
            except dns.resolver.Timeout:
                continue  # 超时重试
        except dns.resolver.Timeout:
            continue  # 超时重试
        except Exception as e:
            logger.warning(f"DNS {dns_server} 解析 {domain} 异常：{str(e)}")
            return False
    logger.warning(f"DNS {dns_server} 解析 {domain} 多次超时")
    return False


def is_domain_valid(domain: str, whitelist: Set[str]) -> bool:
    """检查域名有效性（白名单优先，再查DNS缓存，最后实时解析）"""
    # 白名单直接有效
    if domain in whitelist:
        return True
    # 缓存命中直接返回
    if domain in dns_cache:
        return dns_cache[domain]
    
    # 并行检查所有DNS服务器
    all_servers = DNS_CONFIG["servers"]["domestic"] + DNS_CONFIG["servers"]["foreign"]
    with ThreadPoolExecutor(max_workers=len(all_servers)) as executor:
        futures = [executor.submit(check_dns_with_retry, domain, server) for server in all_servers]
        results = [future.result() for future in as_completed(futures)]
    
    # 任一DNS解析成功则有效
    is_valid = any(results)
    dns_cache[domain] = is_valid  # 写入缓存
    return is_valid


def process_rules_file(input_path: Path, output_path: Path, whitelist: Set[str], max_workers: int = 100) -> None:
    """处理单个规则文件，过滤无效域名"""
    logger.info(f"开始处理规则文件：{input_path}")
    
    # 流式读取并分类行（避免大文件占用内存）
    comments: List[str] = []          # 注释/空行
    non_domain_lines: List[str] = []  # 非域名规则
    domain_tasks: List[Tuple[str, str]] = []  # (域名, 原始行)

    with input_path.open('r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(('#', '!')):
                comments.append(line)
                continue
            domain = extract_domain(stripped)
            if domain:
                domain_tasks.append((domain, line))
            else:
                non_domain_lines.append(line)  # 保留非域名规则（如元素隐藏规则）

    logger.info(f"文件 {input_path.name} 解析完成：{len(domain_tasks)} 个域名待验证")

    # 并发验证域名
    valid_lines = set()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(is_domain_valid, domain, whitelist): line 
                  for domain, line in domain_tasks}
        for future in as_completed(futures):
            line = futures[future]
            try:
                if future.result():
                    valid_lines.add(line)
                else:
                    domain = extract_domain(line.strip())
                    logger.debug(f"无效域名（所有DNS均无法解析）：{domain}")
            except Exception as e:
                logger.error(f"验证域名时异常：{str(e)}，保留原始行：{line.strip()}")
                valid_lines.add(line)

    # 按原始顺序合并结果（保持规则文件结构）
    final_lines = comments + non_domain_lines
    # 追加有效域名规则（保持原始顺序）
    for domain, line in domain_tasks:
        if line in valid_lines:
            final_lines.append(line)

    # 写入输出文件
    with output_path.open('w', encoding='utf-8') as f:
        f.writelines(final_lines)
    
    logger.info(f"文件 {output_path.name} 处理完成："
                f"原始域名规则 {len(domain_tasks)} 个，有效保留 {len(valid_lines)} 个")


def main():
    """主函数：整合项目流程，处理所有规则文件"""
    # 项目路径配置（适配现有项目结构）
    project_root = Path(__file__).parent.parent.parent  # 假设脚本位于 data/python/utils/
    tmp_dir = project_root / "tmp"  # 与merge_files.py一致的临时目录
    rule_files = [
        project_root / "adclose.txt",
        project_root / "dns.txt",
        project_root / "domain_list.txt",
        project_root / "invizible.txt",
        tmp_dir / "combined_adblock.txt",  # 合并后的广告规则
        tmp_dir / "combined_allow.txt"     # 合并后的允许规则
    ]
    whitelist_files = [
        project_root / "white.txt",
        tmp_dir / "cleaned_allow.txt"      # 清洗后的白名单
    ]

    # 确保目录存在
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 加载白名单
    whitelist = load_whitelist(whitelist_files)

    # 处理所有规则文件（输出到临时目录，供后续合并）
    for input_path in rule_files:
        if not input_path.exists():
            logger.warning(f"规则文件不存在，跳过：{input_path}")
            continue
        output_path = tmp_dir / f"filtered_{input_path.name}"
        process_rules_file(input_path, output_path, whitelist)

    logger.info("所有规则文件过滤完成")


if __name__ == "__main__":
    main()