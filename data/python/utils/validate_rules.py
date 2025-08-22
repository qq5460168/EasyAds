import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime
import pytz

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class RuleValidator:
    """规则验证器，用于检查各类规则文件的格式有效性"""
    
    # 各类规则的验证模式
    RULE_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
        # 键: 文件名模式, 值: (规则名称, 验证正则)
        "adblock.txt": [
            ("标准广告拦截规则", r'^\|\|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\^$'),
            ("例外规则", r'^@@\|\|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\^$'),
            ("注释行", r'^!.*$'),
            ("标题行", r'^\[Adblock Plus.*\]$')
        ],
        "allow.txt": [
            ("允许规则", r'^@.*$'),
            ("注释行", r'^!.*$')
        ],
        "dns.txt": [
            ("DNS拦截规则", r'^\|\|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\^$'),
            ("注释行", r'^#.*$')
        ],
        "clash.txt": [
            ("Clash域名后缀规则", r'^DOMAIN-SUFFIX,([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}),REJECT$'),
            ("注释行", r'^#.*$')
        ],
        "shadowrocket.txt": [
            ("Shadowrocket域名规则", r'^DOMAIN-SUFFIX,([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}),REJECT$'),
            ("注释行", r'^#.*$')
        ],
        "singbox.txt": [
            ("Singbox域名规则", r'^domain: ([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}), policy: reject$'),
            ("注释行", r'^#.*$')
        ],
        "hosts.txt": [
            ("Hosts规则", r'^0\.0\.0\.0 ([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'),
            ("注释行", r'^#.*$')
        ],
        "loon-rules.list": [
            ("Loon IP规则", r'^IP-CIDR,([0-9.]+/[0-9]+),REJECT,no-resolve$'),
            ("Loon域名规则", r'^DOMAIN,([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}),REJECT$'),
            ("Loon域名后缀规则", r'^DOMAIN-SUFFIX,([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}),REJECT$'),
            ("Loon关键词规则", r'^DOMAIN-KEYWORD,([a-zA-Z0-9.-]+),REJECT$'),
            ("注释行", r'^#.*$')
        ],
        "qx.list": [
            ("Quantumult X规则", r'^DOMAIN,([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}),reject$'),
            ("注释行", r'^#.*$')
        ],
        "invizible.txt": [
            ("Invizible规则", r'^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}) block$'),
            ("注释行", r'^#.*$')
        ],
        "adclose.txt": [
            ("Adclose规则", r'^block ([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'),
            ("注释行", r'^#.*$')
        ]
    }

    def __init__(self, root_dir: Path = Path(".")):
        """
        初始化规则验证器
        
        :param root_dir: 规则文件所在的根目录
        """
        self.root_dir = root_dir
        self.results: Dict[str, Dict] = {}  # 存储验证结果

    def get_beijing_time(self) -> str:
        """获取当前北京时间"""
        tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    def _get_patterns_for_file(self, filename: str) -> List[Tuple[str, str]]:
        """根据文件名获取对应的验证模式"""
        for pattern, patterns in self.RULE_PATTERNS.items():
            if filename == pattern:
                return patterns
        return []

    def validate_file(self, filename: str) -> Dict:
        """
        验证单个规则文件
        
        :param filename: 文件名
        :return: 验证结果字典
        """
        file_path = self.root_dir / filename
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return {"valid": False, "error": "文件不存在", "counts": {}}

        patterns = self._get_patterns_for_file(filename)
        if not patterns:
            logger.warning(f"没有找到 {filename} 的验证规则")
            return {"valid": False, "error": "无验证规则", "counts": {}}

        # 初始化统计数据
        counts = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "duplicates": 0,
            "rule_types": {name: 0 for name, _ in patterns}
        }
        invalid_lines: List[Tuple[int, str]] = []
        seen_lines: Set[str] = set()
        duplicate_lines: Set[str] = set()

        try:
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # 跳过空行
                        continue
                        
                    counts["total"] += 1
                    is_valid = False
                    
                    # 检查是否为重复行
                    if line in seen_lines:
                        duplicate_lines.add(line)
                        counts["duplicates"] += 1
                    else:
                        seen_lines.add(line)
                    
                    # 验证规则类型
                    for name, pattern in patterns:
                        if re.match(pattern, line):
                            counts["valid"] += 1
                            counts["rule_types"][name] += 1
                            is_valid = True
                            break
                    
                    if not is_valid:
                        counts["invalid"] += 1
                        invalid_lines.append((line_num, line))
                        if len(invalid_lines) <= 10:  # 只记录前10条无效行
                            logger.debug(f"无效行 {filename}:{line_num} - {line}")

            # 生成验证结果
            result = {
                "valid": counts["invalid"] == 0,
                "file": str(file_path),
                "timestamp": self.get_beijing_time(),
                "counts": counts,
                "top_invalid": invalid_lines[:10],  # 只保留前10条无效行
                "duplicate_examples": list(duplicate_lines)[:5]  # 只保留前5条重复行示例
            }
            
            self.results[filename] = result
            self._log_validation_result(filename, counts, len(invalid_lines))
            return result
            
        except Exception as e:
            error_msg = f"验证文件时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"valid": False, "error": error_msg, "counts": {}}

    def _log_validation_result(self, filename: str, counts: Dict, invalid_count: int) -> None:
        """记录验证结果日志"""
        if counts["invalid"] == 0 and counts["duplicates"] == 0:
            logger.info(
                f"✅ {filename} 验证通过 - "
                f"总规则: {counts['total']}, "
                f"有效规则: {counts['valid']}"
            )
        else:
            logger.warning(
                f"❌ {filename} 验证不通过 - "
                f"总规则: {counts['total']}, "
                f"有效规则: {counts['valid']}, "
                f"无效规则: {counts['invalid']}, "
                f"重复规则: {counts['duplicates']}"
            )

    def validate_all_files(self) -> Dict[str, Dict]:
        """验证所有支持的规则文件"""
        logger.info("开始批量验证所有规则文件...")
        for filename in self.RULE_PATTERNS.keys():
            self.validate_file(filename)
        
        # 生成汇总报告
        summary = {
            "total_files": len(self.RULE_PATTERNS),
            "valid_files": sum(1 for res in self.results.values() if res.get("valid", False)),
            "invalid_files": sum(1 for res in self.results.values() if not res.get("valid", False)),
            "total_rules": sum(res["counts"].get("total", 0) for res in self.results.values() if "counts" in res),
            "total_invalid": sum(res["counts"].get("invalid", 0) for res in self.results.values() if "counts" in res),
            "total_duplicates": sum(res["counts"].get("duplicates", 0) for res in self.results.values() if "counts" in res),
            "timestamp": self.get_beijing_time()
        }
        
        logger.info("\n" + "="*50)
        logger.info(f"规则验证汇总报告 ({summary['timestamp']})")
        logger.info("="*50)
        logger.info(f"验证文件总数: {summary['total_files']}")
        logger.info(f"完全有效文件: {summary['valid_files']}")
        logger.info(f"存在问题文件: {summary['invalid_files']}")
        logger.info(f"总规则数量: {summary['total_rules']}")
        logger.info(f"无效规则数量: {summary['total_invalid']}")
        logger.info(f"重复规则数量: {summary['total_duplicates']}")
        logger.info("="*50 + "\n")
        
        self.results["summary"] = summary
        return self.results

    def export_report(self, output_file: Optional[Path] = None) -> None:
        """
        导出验证报告到文件
        
        :param output_file: 输出文件路径，默认为当前目录的rule_validation_report.txt
        """
        if not output_file:
            output_file = self.root_dir / "rule_validation_report.txt"
        
        try:
            with output_file.open('w', encoding='utf-8') as f:
                f.write(f"# 规则验证报告\n")
                f.write(f"# 生成时间: {self.get_beijing_time()} (北京时间)\n")
                f.write(f"# 总览: 验证文件 {self.results['summary']['total_files']} 个, "
                       f"有效 {self.results['summary']['valid_files']} 个, "
                       f"无效 {self.results['summary']['invalid_files']} 个\n")
                f.write(f"# 规则总量: {self.results['summary']['total_rules']} 条, "
                       f"无效 {self.results['summary']['total_invalid']} 条, "
                       f"重复 {self.results['summary']['total_duplicates']} 条\n\n")
                
                for filename, result in self.results.items():
                    if filename == "summary":
                        continue
                    
                    f.write(f"## {filename}\n")
                    if "error" in result:
                        f.write(f"- 错误: {result['error']}\n\n")
                        continue
                    
                    counts = result["counts"]
                    f.write(f"- 总规则: {counts['total']} 条\n")
                    f.write(f"- 有效规则: {counts['valid']} 条\n")
                    f.write(f"- 无效规则: {counts['invalid']} 条\n")
                    f.write(f"- 重复规则: {counts['duplicates']} 条\n")
                    
                    f.write("- 规则类型分布:\n")
                    for name, count in counts["rule_types"].items():
                        if count > 0:
                            f.write(f"  - {name}: {count} 条\n")
                    
                    if result["top_invalid"]:
                        f.write("- 无效行示例:\n")
                        for line_num, line in result["top_invalid"][:5]:
                            f.write(f"  - 行 {line_num}: {line}\n")
                    
                    if result["duplicate_examples"]:
                        f.write("- 重复行示例:\n")
                        for line in result["duplicate_examples"][:5]:
                            f.write(f"  - {line}\n")
                    
                    f.write("\n")
            
            logger.info(f"验证报告已导出至: {output_file}")
        
        except Exception as e:
            logger.error(f"导出报告失败: {str(e)}", exc_info=True)

def main():
    """主函数：执行规则验证流程"""
    try:
        # 确定根目录（与其他脚本保持一致）
        script_dir = Path(__file__).parent
        root_dir = script_dir.parent.parent.parent  # 项目根目录
        
        logger.info(f"开始规则验证，根目录: {root_dir.resolve()}")
        
        validator = RuleValidator(root_dir=root_dir)
        validator.validate_all_files()
        validator.export_report()
        
        # 检查是否有严重问题
        summary = validator.results.get("summary", {})
        if summary.get("total_invalid", 0) > 100 or summary.get("invalid_files", 0) > 5:
            logger.error("发现大量无效规则或问题文件，可能需要紧急处理")
            exit(1)
        
        logger.info("规则验证流程完成")
        
    except Exception as e:
        logger.critical(f"规则验证执行失败: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()