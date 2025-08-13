import os
import subprocess
import time
import shutil
from pathlib import Path  # 引入pathlib处理路径，更可靠

# 获取脚本所在目录的绝对路径，确保tmp目录位置固定
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent  # 项目根目录（EasyAds/）
TMP_DIR = ROOT_DIR / "tmp"  # 绝对路径的tmp目录

# 1. 清理根目录下的旧规则文件
def clean_old_rules():
    target_files = ['adblock.txt', 'allow.txt', 'dns.txt', 'qx.list', 'loon-rules.list', 'adb.mrs']
    for file_name in target_files:
        file_path = ROOT_DIR / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"已删除旧规则文件: {file_path}")
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")

# 2. 确保tmp目录存在（绝对路径）
def init_tmp_dir():
    try:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        print(f"临时目录已初始化（绝对路径）: {TMP_DIR}")
    except Exception as e:
        print(f"创建tmp目录失败: {e}")
        exit(1)

# 3. 复制补充规则到tmp目录
def copy_supplement_rules():
    try:
        # 源文件路径（基于项目根目录）
        adblock_src = ROOT_DIR / "data" / "mod" / "adblock.txt"
        whitelist_src = ROOT_DIR / "data" / "mod" / "whitelist.txt"
        
        # 目标路径
        adblock_dst = TMP_DIR / "adblock01.txt"
        whitelist_dst = TMP_DIR / "allow01.txt"
        
        # 复制文件（如果源文件存在）
        if adblock_src.exists():
            shutil.copy2(adblock_src, adblock_dst)
            print(f"已复制补充规则: {adblock_src} -> {adblock_dst}")
        else:
            print(f"警告: 补充规则 {adblock_src} 不存在，跳过复制")
        
        if whitelist_src.exists():
            shutil.copy2(whitelist_src, whitelist_dst)
            print(f"已复制白名单补充规则: {whitelist_src} -> {whitelist_dst}")
        else:
            print(f"警告: 白名单补充规则 {whitelist_src} 不存在，跳过复制")
    except Exception as e:
        print(f"复制补充规则失败: {e}")
        exit(1)

# 4. 下载规则（修正curl命令，增加校验）
def download_rules(url_list, prefix):
    success_count = 0
    for i, url in enumerate(url_list, start=2):  # 从2开始编号（1是本地补充规则）
        filename = TMP_DIR / f"{prefix}{i:02d}.txt"
        try:
            # 修正curl命令：移除多余的| iconv，增加-v输出调试信息，超时参数优化
            result = subprocess.run(
                f'curl -m 60 --retry-delay 2 --retry 3 -k -L -C - -o "{filename}" --connect-timeout 30 -s -w "%{http_code}" "{url}"',
                shell=True,
                capture_output=True,
                text=True
            )
            # 检查HTTP状态码（200/304为成功）
            if result.returncode == 0 and result.stdout.strip() in ["200", "304"]:
                if os.path.getsize(filename) > 0:  # 确保文件非空
                    success_count += 1
                    print(f"下载成功 [{i}/{len(url_list)}]: {url} -> {filename.name}")
                else:
                    os.remove(filename)
                    print(f"下载失败 [{i}/{len(url_list)}]: {url}（文件为空）")
            else:
                print(f"下载失败 [{i}/{len(url_list)}]: {url}（状态码: {result.stdout.strip()}，错误: {result.stderr}）")
            time.sleep(1)  # 避免请求过于频繁
        except Exception as e:
            print(f"下载异常 [{i}/{len(url_list)}]: {url}，错误: {e}")
    return success_count

# 规则源列表
adblock_urls = [
    "https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt",
    "https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt",
    "https://raw.hellogithub.com/hosts",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adblock.txt",
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt",
    "https://lingeringsound.github.io/10007_auto/adb.txt",
    "https://raw.githubusercontent.com/790953214/qy-Ads-Rule/main/black.txt",
    "https://raw.githubusercontent.com/2771936993/HG/main/hg1.txt",
    "https://github.com/entr0pia/fcm-hosts/raw/fcm/fcm-hosts",
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",
    "https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/master/SMAdHosts",
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/main/FuLingRules/FuLingBlockList.txt"
]

allow_urls = [
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",
    "https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Allowlist.txt",
    "https://file-git.trli.club/file-hosts/allow/Domains",
    "https://raw.githubusercontent.com/jhsvip/ADRuls/main/white.txt",
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",
    "https://raw.githubusercontent.com/miaoermua/AdguardFilter/main/whitelist.txt",
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/main/FuLingRules/FuLingAllowList.txt",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/script/allowlist.txt",
    "https://anti-ad.net/easylist.txt"
]

# 主流程
def main():
    print("===== 开始清理旧规则 =====")
    clean_old_rules()
    
    print("\n===== 初始化临时目录 =====")
    init_tmp_dir()
    
    print("\n===== 复制补充规则 =====")
    copy_supplement_rules()
    
    print("\n===== 下载拦截规则 =====")
    adblock_success = download_rules(adblock_urls, "adblock")
    print(f"拦截规则下载完成: {adblock_success}/{len(adblock_urls)} 成功")
    
    print("\n===== 下载白名单规则 =====")
    allow_success = download_rules(allow_urls, "allow")
    print(f"白名单规则下载完成: {allow_success}/{len(allow_urls)} 成功")
    
    # 检查tmp目录是否有文件（至少1个成功才算有效）
    total_files = len(list(TMP_DIR.glob("*.txt")))
    if total_files == 0:
        print("\nError: tmp目录中未找到任何下载的规则文件，流程终止")
        exit(1)
    else:
        print(f"\n规则下载完成，tmp目录共 {total_files} 个文件")

if __name__ == "__main__":
    main()
