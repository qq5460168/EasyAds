import os
import subprocess
import time
import shutil

# 删除根目录下的规则文件（原data/rules调整为根目录）
directory = "./"  # 根目录

# 确保目录存在并遍历删除其中的规则文件
if os.path.exists(directory):
    for file_name in os.listdir(directory):
        # 只删除规则相关的txt文件
        if file_name.endswith(('.txt', '.list', '.mrs')) and file_name in ['adblock.txt', 'allow.txt', 'dns.txt', 'qx.list', 'loon-rules.list', 'adb.mrs']:
            file_path = os.path.join(directory, file_name)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"无法删除文件: {file_path}, 错误: {e}")
else:
    print(f"目录 {directory} 不存在")

# 保留临时文件夹（仍用于中间处理）
os.makedirs("./tmp/", exist_ok=True)

# 复制补充规则到tmp文件夹（路径不变）
subprocess.run("cp ./data/mod/adblock.txt ./tmp/adblock01.txt", shell=True)
subprocess.run("cp ./data/mod/whitelist.txt ./tmp/allow01.txt", shell=True)

# 规则源列表（不变）
adblock = [
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

allow = [
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

# 下载拦截规则（临时文件路径不变）
for i, url in enumerate(adblock, start=2):
    filename = f"tmp/adblock{i:02d}.txt"
    try:
        subprocess.run(
            f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o {filename} --connect-timeout 60 -s '{url}' | iconv -t utf-8",
            shell=True,
            check=True
        )
        time.sleep(1)
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {url}, 错误: {e}")

# 下载白名单规则（临时文件路径不变）
for j, url in enumerate(allow, start=2):
    filename = f"tmp/allow{j:02d}.txt"
    try:
        subprocess.run(
            f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o {filename} --connect-timeout 60 -s '{url}' | iconv -t utf-8",
            shell=True,
            check=True
        )
        time.sleep(1)
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {url}, 错误: {e}")

print('规则下载完成')