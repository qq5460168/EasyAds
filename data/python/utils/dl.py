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
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/black.txt",  #5460
    "https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt",  #大萌主
    "https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt",  #DD
    "https://raw.githubusercontent.com/Cats-Team/dns-filter/main/abp.txt",  #AdRules DNS Filter
    "https://raw.hellogithub.com/hosts",  #GitHub加速
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt",  #测试hosts
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",  #白名单
    "https://raw.githubusercontent.com/qq5460168/Who520/refs/heads/main/Other%20rules/Replenish.txt",  #补充
    "https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Blacklist.txt",  #mphin
    "https://gitee.com/zjqz/ad-guard-home-dns/raw/master/black-list",  #周木木
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/black.txt",  #liwenjie119
    "https://github.com/entr0pia/fcm-hosts/raw/fcm/fcm-hosts",  #FCM Hosts
    "https://raw.githubusercontent.com/790953214/qy-Ads-Rule/refs/heads/main/black.txt",  #晴雅
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",  #秋风规则
    "https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/refs/heads/master/SMAdHosts",  #下一个ID见
    "https://raw.githubusercontent.com/tongxin0520/AdFilterForAdGuard/refs/heads/main/KR_DNS_Filter.txt",  #tongxin0520
    "https://raw.githubusercontent.com/Zisbusy/AdGuardHome-Rules/refs/heads/main/Rules/blacklist.txt",  #Zisbusy
    "",  #
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingBlockList.txt",  #茯苓
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt",  #茯苓白名单
    ""  #
]

allow = [
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",
    "https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Allowlist.txt",
    "https://file-git.trli.club/file-hosts/allow/Domains",  # 冷漠
    "https://raw.githubusercontent.com/user001235/112/main/white.txt",  # 浅笑
    "https://raw.githubusercontent.com/jhsvip/ADRuls/main/white.txt",  # jhsvip
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",  # liwenjie119
    "https://raw.githubusercontent.com/miaoermua/AdguardFilter/main/whitelist.txt",  # 喵二白名单
    "https://raw.githubusercontent.com/Zisbusy/AdGuardHome-Rules/refs/heads/main/Rules/whitelist.txt",  # Zisbusy
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/refs/heads/main/FuLingRules/FuLingAllowList.txt",  # 茯苓
    "https://raw.githubusercontent.com/urkbio/adguardhomefilter/main/whitelist.txt",  # 酷安cocieto
    "",  #
    ""
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