# -*- coding: utf-8 -*-
"""转换规则为Loon格式"""
import re
from pathlib import Path
import datetime
import pytz

def get_beijing_time() -> str:
    """获取当前北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

def extract_to_loon_rules(input_file: str, output_file: str):
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    try:
        ip_rules, domain_rules, suffix_rules, keyword_rules = [], [], [], []
        ip_pattern = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?$')
        
        # 尝试多种编码读取
        lines = []
        for encoding in ['utf-8', 'gbk', 'latin-1']:
            try:
                with input_path.open('r', encoding=encoding, errors='ignore') as infile:
                    lines = infile.readlines()
                break
            except UnicodeDecodeError:
                continue

        for line in lines:
            line = line.strip()
            if not line or line.startswith(('!', '#')):
                continue
            
            # 处理域名后缀规则（||xxx^）
            if line.startswith("||") and line.endswith("^"):
                rule = line[2:-1]
                if ip_pattern.match(rule.split('/')[0]):
                    ip_rules.append(f"IP-CIDR,{rule},REJECT,no-resolve")
                else:
                    suffix_rules.append(f"DOMAIN-SUFFIX,{rule},REJECT")
            
            # 处理完整域名规则（|http(s)://xxx^）
            elif line.startswith(("|http://", "|https://")):
                domain = line.split('://')[1].split('^')[0].split('/')[0]
                if domain:
                    domain_rules.append(f"DOMAIN,{domain},REJECT")
            
            # 处理关键词规则（含*）
            elif '*' in line:
                keyword = re.sub(r'[\^*|]', '', line.replace('||', ''))  # 清理特殊字符
                if keyword:
                    keyword_rules.append(f"DOMAIN-KEYWORD,{keyword},REJECT")

        # 去重并保持顺序
        def deduplicate(lst):
            seen = set()
            return [x for x in lst if not (x in seen or seen.add(x))]
        
        ip_rules = deduplicate(ip_rules)
        domain_rules = deduplicate(domain_rules)
        suffix_rules = deduplicate(suffix_rules)
        keyword_rules = deduplicate(keyword_rules)

        # 统计数量
        total_count = len(ip_rules) + len(domain_rules) + len(suffix_rules) + len(keyword_rules)

        # 写入输出文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as outfile:
            outfile.write("# Loon规则由EasyAds生成\n")
            outfile.write(f"# 更新时间(北京时间): {get_beijing_time()}\n")
            outfile.write(f"# 规则统计: 总计{total_count}条 (IP:{len(ip_rules)} DOMAIN:{len(domain_rules)} "
                         f"SUFFIX:{len(suffix_rules)} KEYWORD:{len(keyword_rules)})\n\n")
            
            if ip_rules:
                outfile.write("# IP规则\n" + "\n".join(ip_rules) + "\n\n")
            if domain_rules:
                outfile.write("# 域名规则\n" + "\n".join(domain_rules) + "\n\n")
            if suffix_rules:
                outfile.write("# 域名后缀\n" + "\n".join(suffix_rules) + "\n\n")
            if keyword_rules:
                outfile.write("# 关键词规则\n" + "\n".join(keyword_rules))

        print(f"Loon规则生成成功! 总数: {total_count}")

    except Exception as e:
        print(f"处理失败: {e}")
        raise

if __name__ == "__main__":
    # 示例调用（实际路径根据工作流配置）
    extract_to_loon_rules("./data/rules/adblock.txt", "./data/rules/loon.txt")