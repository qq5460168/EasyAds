import os
import re
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

# 配置常量（优化：增加最小文件大小校验阈值）
MAX_WORKERS = 5  # 并发下载数量
TIMEOUT = 60      # 超时时间(秒)
RETRY = 5         # 重试次数
RETRY_DELAY = 2   # 重试间隔(秒)
ENCODING = "utf-8"  # 目标编码
MIN_FILE_SIZE = 1024  # 最小文件大小(字节)，过滤空文件或无效响应

# 路径计算（基于脚本绝对路径，优化：使用更清晰的路径层级）
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[3]  # 项目根目录（更健壮的层级计算）
TMP_DIR = ROOT_DIR / "tmp"                  # 临时目录
ADBLOCK_SUPPLEMENT = ROOT_DIR / "data/mod/adblock.txt"  # 补充规则
WHITELIST_SUPPLEMENT = ROOT_DIR / "data/mod/whitelist.txt"  # 补充白名单

# 日志函数（优化：增加日志级别和详细信息）
def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [DL] [{level}] {msg}")

def error(msg: str):
    log(msg, "ERROR")

def debug(msg: str):
    log(msg, "DEBUG")

# 1. 初始化环境（优化：增加权限检查和清理容错）
def init_env():
    try:
        # 清理临时目录（优化：增加错误捕获，避免目录被占用导致失败）
        if TMP_DIR.exists():
            try:
                shutil.rmtree(TMP_DIR, ignore_errors=True)
                log(f"已清理旧临时目录: {TMP_DIR}")
            except Exception as e:
                error(f"清理临时目录失败，将继续创建新目录: {str(e)}")
        
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        log(f"初始化临时目录成功: {TMP_DIR}")

        # 清理根目录旧规则（优化：仅删除存在的文件）
        for file in ["adblock.txt", "allow.txt", "rules.txt"]:
            file_path = ROOT_DIR / file
            if file_path.exists():
                try:
                    file_path.unlink()
                    log(f"清理旧规则文件: {file}")
                except Exception as e:
                    error(f"清理旧规则文件 {file} 失败: {str(e)}")

        # 复制补充规则（优化：增加文件大小检查）
        for src, dst_name, desc in [
            (ADBLOCK_SUPPLEMENT, "rules01.txt", "补充拦截规则"),
            (WHITELIST_SUPPLEMENT, "allow01.txt", "补充白名单规则")
        ]:
            if src.exists():
                if src.stat().st_size < MIN_FILE_SIZE:
                    log(f"警告: {desc} 文件过小（{src.stat().st_size}字节），可能无效")
                try:
                    shutil.copy2(src, TMP_DIR / dst_name)
                    log(f"复制{desc}成功: {dst_name}")
                except Exception as e:
                    error(f"复制{desc}失败: {str(e)}")
            else:
                log(f"警告: {desc}不存在 {src}")
    except Exception as e:
        error(f"环境初始化失败: {str(e)}")
        raise  # 初始化失败终止流程

# 2. 下载函数（优化：增强容错和校验）
def download_url(url: str, save_path: Path) -> Tuple[bool, str]:
    """
    下载单个URL并转码
    返回：(是否成功, 错误信息/成功信息)
    """
    try:
        if not url.strip():
            return False, "空URL跳过"

        # 构造curl命令（优化：增加进度抑制和错误输出捕获）
        cmd = [
            "curl",
            "-m", str(TIMEOUT),
            "--retry", str(RETRY),
            "--retry-delay", str(RETRY_DELAY),
            "-k", "-L", "-C", "-",  # 忽略证书、跟随重定向、断点续传
            "--connect-timeout", str(TIMEOUT),
            "-s", "-S",  # 静默模式但保留错误输出
            url,
            "-o", str(save_path)  # 直接输出到文件，减少内存占用
        ]

        # 执行命令（优化：直接输出到文件，避免内存缓冲大文件）
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        # 检查返回码和文件大小
        if result.returncode != 0:
            err_msg = f"curl失败（返回码: {result.returncode}），错误: {result.stderr.strip()}"
            return False, err_msg

        # 检查文件是否有效
        if not save_path.exists() or save_path.stat().st_size < MIN_FILE_SIZE:
            err_msg = f"文件无效（大小: {save_path.stat().st_size if save_path.exists() else 0}字节）"
            if save_path.exists():
                save_path.unlink()  # 删除无效文件
            return False, err_msg

        # 转码处理（优化：先检查文件编码，减少解码尝试）
        with open(save_path, "rb") as f:
            raw_content = f.read()

        for encoding in ["utf-8", "latin-1", "gbk", "utf-16"]:
            try:
                content = raw_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            save_path.unlink()
            return False, "所有编码尝试均失败"

        # 统一换行符并写入（优化：去除多余空行）
        with open(save_path, "w", encoding=ENCODING) as f:
            cleaned = re.sub(r'\n+', '\n', content.strip()) + '\n'
            f.write(cleaned)

        return True, f"大小: {save_path.stat().st_size}字节"

    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        return False, f"异常: {str(e)}"

# 3. 并发下载规则（优化：增加统计和结果汇总）
def download_rules(concurrent: int = MAX_WORKERS):
    # 规则URL列表（保持原数据，优化：提取为常量便于维护）
    RULES_URLS = [
        "https://raw.githubusercontent.com/qq5460168/dangchu/main/black.txt", #5460
        "https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt", #大萌主
        "https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt",  #DD
        "https://raw.githubusercontent.com/Cats-Team/dns-filter/main/abp.txt", #AdRules DNS Filter
        "https://raw.hellogithub.com/hosts", #GitHub加速
        "https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt", #测试hosts
        "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt", #白名单
        "https://raw.githubusercontent.com/qq5460168/Who520/refs/heads/main/Other%20rules/Replenish.txt",#补充
        "https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Blacklist.txt", #mphin
        "https://gitee.com/zjqz/ad-guard-home-dns/raw/master/black-list", #周木木
        "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/black.txt", #liwenjie119
        "https://github.com/entr0pia/fcm-hosts/raw/fcm/fcm-hosts", #FCM Hosts
        "https://raw.githubusercontent.com/790953214/qy-Ads-Rule/refs/heads/main/black.txt", #晴雅
        "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt", #秋风规则
        "https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/refs/heads/master/SMAdHosts", #下一个ID见
        "https://raw.githubusercontent.com/tongxin0520/AdFilterForAdGuard/refs/heads/main/KR_DNS_Filter.txt", #tongxin0520
        "https://raw.githubusercontent.com/Zisbusy/AdGuardHome-Rules/refs/heads/main/Rules/blacklist.txt", #Zisbusy
        "", # 空行（跳过下载）
        "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingBlockList.txt", #茯苓
        "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt", #茯苓白名单
        "", # 空行（跳过下载）
    ]

    ALLOW_URLS = [
        "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",
        "https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Allowlist.txt",
        "https://file-git.trli.club/file-hosts/allow/Domains", #冷漠
        "https://raw.githubusercontent.com/user001235/112/main/white.txt", #浅笑
        "https://raw.githubusercontent.com/jhsvip/ADRuls/main/white.txt", #jhsvip
        "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt", #liwenjie119
        "https://raw.githubusercontent.com/miaoermua/AdguardFilter/main/whitelist.txt", #喵二白名单
        "https://raw.githubusercontent.com/Zisbusy/AdGuardHome-Rules/refs/heads/main/Rules/whitelist.txt", #Zisbusy
        "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt", #茯苓
        "https://raw.githubusercontent.com/urkbio/adguardhomefilter/main/whitelist.txt", #酷安cocieto
        "",# 空行（跳过下载）
        "" # 空行（跳过下载）
    ]

    # 下载函数（复用逻辑）
    def download_batch(urls: List[str], prefix: str, start_idx: int) -> Tuple[int, int]:
        success = 0
        fail = 0
        log(f"\n开始下载{prefix}规则（共{len([u for u in urls if u.strip()])}个有效URL）...")
        
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = []
            for i, url in enumerate(urls, start=start_idx):
                if not url.strip():
                    continue
                save_path = TMP_DIR / f"{prefix}{i:02d}.txt"
                futures.append((executor.submit(download_url, url, save_path), url, save_path.name))
            
            for future, url, fname in as_completed(futures):
                try:
                    ok, msg = future.result()
                    if ok:
                        success += 1
                        debug(f"下载成功 {fname} -> {msg}")
                    else:
                        fail += 1
                        error(f"下载失败 {url.split('/')[-1]}: {msg}")
                except Exception as e:
                    fail += 1
                    error(f"任务异常 {url}: {str(e)}")
        
        log(f"{prefix}规则下载完成：成功{success}个，失败{fail}个")
        return success, fail

    # 执行下载
    rule_success, rule_fail = download_batch(RULES_URLS, "rules", 2)
    allow_success, allow_fail = download_batch(ALLOW_URLS, "allow", 2)

    # 检查是否有有效文件
    if (rule_success + allow_success) == 0:
        error("所有规则下载失败，可能导致后续处理出错")

# 4. 规则预处理（优化：提升正则效率和去重逻辑）
def process_rules():
    log("\n开始预处理规则...")

    # 预编译正则（优化：减少重复编译开销）
    IP_FILTER_PATTERN = re.compile(r"^[0-9f\.:]+\s+(ip6\-|localhost|local|loopback)$")
    LOCAL_DOMAIN_PATTERN = re.compile(r"local.*\.local.*$")
    ALLOW_RULE_PATTERN = re.compile(r"^@@\|\|.*\^(\$important)?$")

    # 合并所有规则文件（优化：按类型分类读取）
    all_rules = []
    for file in TMP_DIR.glob("*.txt"):
        try:
            with open(file, "r", encoding=ENCODING, errors="ignore") as f:
                # 按行读取并过滤空行（优化：减少内存占用）
                lines = [line.strip() for line in f if line.strip()]
                all_rules.extend(lines)
                debug(f"读取文件 {file.name}，有效行: {len(lines)}")
        except Exception as e:
            error(f"读取文件失败 {file}: {str(e)}")

    # 过滤与转换（优化：使用列表推导式提升效率）
    filtered = []
    seen = set()  # 用于去重
    for line in all_rules:
        # 过滤注释行和空行（已在读取时处理空行，这里再保险）
        if not line or line.startswith(("#", "!", "[")):
            continue
        # 过滤无效IP规则
        if IP_FILTER_PATTERN.match(line) or LOCAL_DOMAIN_PATTERN.match(line):
            continue
        # 转换IP格式并去重
        line = line.replace("127.0.0.1", "0.0.0.0").replace("::", "0.0.0.0")
        if "0.0.0.0" in line and ".0.0.0.0 " not in line and line not in seen:
            seen.add(line)
            filtered.append(line)

    # 生成基础规则（优化：保持顺序的去重）
    base_hosts = TMP_DIR / "base-src-hosts.txt"
    with open(base_hosts, "w", encoding=ENCODING) as f:
        f.write("\n".join(filtered) + "\n")
    log(f"生成基础规则 {base_hosts.name}（{len(filtered)} 条，去重后）")

    # 提取AdGuard规则（优化：去重逻辑）
    adblock_seen = set()
    adblock_rules = []
    for line in all_rules:
        line_strip = line.strip()
        if line_strip and not line_strip.startswith(("#", "!", "[")) and line_strip not in adblock_seen:
            adblock_seen.add(line_strip)
            adblock_rules.append(line_strip)
    
    tmp_rules = TMP_DIR / "tmp-rules.txt"
    with open(tmp_rules, "w", encoding=ENCODING) as f:
        f.write("\n".join(adblock_rules) + "\n")
    log(f"生成拦截规则 {tmp_rules.name}（{len(adblock_rules)} 条，去重后）")

    # 提取白名单规则（优化：使用预编译正则）
    allow_rules = []
    allow_seen = set()
    for line in all_rules:
        line_strip = line.strip()
        if ALLOW_RULE_PATTERN.match(line_strip) and line_strip not in allow_seen:
            allow_seen.add(line_strip)
            allow_rules.append(line_strip)
    
    allow_output = TMP_DIR / "tmp-allow.txt"
    with open(allow_output, "w", encoding=ENCODING) as f:
        f.write("\n".join(allow_rules) + "\n")
    log(f"生成白名单规则 {allow_output.name}（{len(allow_rules)} 条，去重后）")

# 主函数（优化：增加流程控制和异常处理）
def main():
    try:
        log("===== 开始规则下载与处理流程 =====")
        init_env()
        download_rules()
        process_rules()
        log("===== 流程完成 =====")
    except Exception as e:
        error(f"主流程失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()