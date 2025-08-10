import os
import shutil
import time
from pathlib import Path
import requests  # 更跨平台的HTTP客户端

# 常量定义
RULES_DIR = Path("./data/rules/")
TMP_DIR = Path("./tmp/")
REQUEST_TIMEOUT = 60  # 超时时间（秒）
RETRY_MAX = 5  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔（秒）

def clean_rules_dir() -> None:
    """清理规则目录"""
    if RULES_DIR.exists():
        try:
            shutil.rmtree(RULES_DIR)
            print(f"已删除目录: {RULES_DIR}")
        except Exception as e:
            print(f"删除目录失败 {RULES_DIR}: {e}")

def download_file(url: str, save_path: Path) -> bool:
    """下载文件（带重试和超时）"""
    for retry in range(RETRY_MAX):
        try:
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                stream=True,
                verify=False  # 对应原curl的-k参数
            )
            response.raise_for_status()  # 触发HTTP错误
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"下载成功: {url}")
            return True
        except Exception as e:
            print(f"下载失败（重试 {retry+1}/{RETRY_MAX}）{url}: {e}")
            time.sleep(RETRY_DELAY)
    return False

def main() -> None:
    # 清理并重建目录
    clean_rules_dir()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 复制补充规则
    try:
        shutil.copy("./data/mod/adblock.txt", TMP_DIR / "adblock01.txt")
        shutil.copy("./data/mod/whitelist.txt", TMP_DIR / "allow01.txt")
        print("已复制补充规则到临时目录")
    except Exception as e:
        print(f"复制补充规则失败: {e}")
        return
    
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
    
    # 下载拦截规则
    for i, url in enumerate(adblock_urls, start=2):
        save_path = TMP_DIR / f"adblock{i:02d}.txt"
        if not download_file(url, save_path):
            print(f"放弃下载: {url}")
    
    # 下载白名单规则
    for j, url in enumerate(allow_urls, start=2):
        save_path = TMP_DIR / f"allow{j:02d}.txt"
        if not download_file(url, save_path):
            print(f"放弃下载: {url}")
    
    print("规则下载完成")

if __name__ == "__main__":
    main()