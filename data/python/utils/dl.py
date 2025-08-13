import os
import subprocess
import time
import shutil
from pathlib import Path

def main():
    # 根目录路径（使用pathlib处理）
    root_dir = Path("./")
    
    # 1. 删除根目录下的旧规则文件
    target_files = {'adblock.txt', 'allow.txt', 'dns.txt', 'qx.list', 'loon-rules.list', 'adb.mrs'}
    for file in root_dir.iterdir():
        if file.suffix in ('.txt', '.list', '.mrs') and file.name in target_files:
            try:
                if file.is_file():
                    file.unlink()  # 删除文件
                    print(f"已删除旧规则文件: {file}")
            except Exception as e:
                print(f"删除文件失败 {file}: {e}")

    # 2. 确保临时目录存在
    tmp_dir = root_dir / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    print(f"临时目录准备完成: {tmp_dir}")

    # 3. 复制补充规则到临时目录（跨平台方式）
    补充规则源 = [
        (root_dir / "data/mod/adblock.txt", tmp_dir / "adblock01.txt"),
        (root_dir / "data/mod/whitelist.txt", tmp_dir / "allow01.txt")
    ]
    for src, dst in 补充规则源:
        try:
            if src.exists():
                shutil.copy(src, dst)  # 替代cp命令，跨平台兼容
                print(f"已复制补充规则: {src} -> {dst}")
            else:
                print(f"警告: 补充规则源文件不存在 {src}")
        except Exception as e:
            print(f"复制规则失败 {src} -> {dst}: {e}")
            # 核心补充规则缺失应终止流程
            if "adblock01.txt" in str(dst):
                print("核心补充规则缺失，终止执行")
                return

    # 4. 规则源列表（保留所有备注信息，仅过滤空URL）
    adblock_urls = [
        ("https://raw.githubusercontent.com/qq5460168/dangchu/main/black.txt", "5460"),  #5460
        ("https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt", "大萌主"),  #大萌主
        ("https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt", "DD"),  #DD
        ("https://raw.githubusercontent.com/Cats-Team/dns-filter/main/abp.txt", "AdRules DNS Filter"),  #AdRules DNS Filter
        ("https://raw.hellogithub.com/hosts", "GitHub加速"),  #GitHub加速
        ("https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt", "测试hosts"),  #测试hosts
        ("https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt", "白名单"),  #白名单
        ("https://raw.githubusercontent.com/qq5460168/Who520/refs/heads/main/Other%20rules/Replenish.txt", "补充"),  #补充
        ("https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Blacklist.txt", "mphin"),  #mphin
        ("https://gitee.com/zjqz/ad-guard-home-dns/raw/master/black-list", "周木木"),  #周木木
        ("https://raw.githubusercontent.com/liwenjie119/adg-rules/master/black.txt", "liwenjie119"),  #liwenjie119
        ("https://github.com/entr0pia/fcm-hosts/raw/fcm/fcm-hosts", "FCM Hosts"),  #FCM Hosts
        ("https://raw.githubusercontent.com/790953214/qy-Ads-Rule/refs/heads/main/black.txt", "晴雅"),  #晴雅
        ("https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt", "秋风规则"),  #秋风规则
        ("https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/refs/heads/master/SMAdHosts", "下一个ID见"),  #下一个ID见
        ("https://raw.githubusercontent.com/tongxin0520/AdFilterForAdGuard/refs/heads/main/KR_DNS_Filter.txt", "tongxin0520"),  #tongxin0520
        ("https://raw.githubusercontent.com/Zisbusy/AdGuardHome-Rules/refs/heads/main/Rules/blacklist.txt", "Zisbusy"),  #Zisbusy
        ("https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingBlockList.txt", "茯苓"),  #茯苓
        ("https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt", "茯苓白名单"),  #茯苓白名单
    ]

    allow_urls = [
        ("https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt", "5460白名单"),
        ("https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Allowlist.txt", "mphin白名单"),
        ("https://file-git.trli.club/file-hosts/allow/Domains", "冷漠白名单"),  # 冷漠
        ("https://raw.githubusercontent.com/user001235/112/main/white.txt", "浅笑白名单"),  # 浅笑
        ("https://raw.githubusercontent.com/jhsvip/ADRuls/main/white.txt", "jhsvip白名单"),  # jhsvip
        ("https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt", "liwenjie119白名单"),  # liwenjie119
        ("https://raw.githubusercontent.com/miaoermua/AdguardFilter/main/whitelist.txt", "喵二白名单"),  # 喵二白名单
        ("https://raw.githubusercontent.com/Zisbusy/AdGuardHome-Rules/refs/heads/main/Rules/whitelist.txt", "Zisbusy白名单"),  # Zisbusy
        ("https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt", "茯苓白名单"),  # 茯苓
        ("https://raw.githubusercontent.com/urkbio/adguardhomefilter/main/whitelist.txt", "酷安cocieto白名单"),  # 酷安cocieto
    ]

    # 5. 下载拦截规则（保留备注信息并优化curl调用）
    print("\n开始下载拦截规则...")
    for i, (url, comment) in enumerate(adblock_urls, start=2):  # 从2开始，与原逻辑一致
        filename = tmp_dir / f"adblock{i:02d}.txt"
        try:
            # 使用列表传递参数，移除shell=True提高安全性
            result = subprocess.run(
                [
                    "curl", "-m", "60", "--retry-delay", "2", "--retry", "5",
                    "-k", "-L", "-C", "-", "-o", str(filename),
                    "--connect-timeout", "60", "-s", url
                ],
                check=True,
                capture_output=True,
                text=True
            )
            # 检查文件是否有效（非空）
            if filename.exists() and filename.stat().st_size > 0:
                print(f"下载成功 [{i}] {comment}: {url} -> {filename.name}")
            else:
                print(f"警告: 下载文件为空 [{i}] {comment}: {url}")
            time.sleep(1)
        except subprocess.CalledProcessError as e:
            print(f"下载失败 [{i}] {comment}: {url}，错误: {e.stderr}")
        except Exception as e:
            print(f"未知错误 [{i}] {comment}: {url}，错误: {e}")

    # 6. 下载白名单规则（同样保留备注信息）
    print("\n开始下载白名单规则...")
    for j, (url, comment) in enumerate(allow_urls, start=2):
        filename = tmp_dir / f"allow{j:02d}.txt"
        try:
            result = subprocess.run(
                [
                    "curl", "-m", "60", "--retry-delay", "2", "--retry", "5",
                    "-k", "-L", "-C", "-", "-o", str(filename),
                    "--connect-timeout", "60", "-s", url
                ],
                check=True,
                capture_output=True,
                text=True
            )
            if filename.exists() and filename.stat().st_size > 0:
                print(f"下载成功 [{j}] {comment}: {url} -> {filename.name}")
            else:
                print(f"警告: 下载文件为空 [{j}] {comment}: {url}")
            time.sleep(1)
        except subprocess.CalledProcessError as e:
            print(f"下载失败 [{j}] {comment}: {url}，错误: {e.stderr}")
        except Exception as e:
            print(f"未知错误 [{j}] {comment}: {url}，错误: {e}")

    print("\n规则下载流程完成")

if __name__ == "__main__":
    main()
