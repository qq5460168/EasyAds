import os
import subprocess
import time
import shutil

# 删除目录下所有的文件
directory = "./data/rules/"

# 确保目录存在并遍历删除其中的文件
if os.path.exists(directory):
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"无法删除文件: {file_path}, 错误: {e}")
else:
    print(f"目录 {directory} 不存在")

# 删除目录本身
try:
    shutil.rmtree(directory)
    print(f"成功删除目录 {directory} 及其中的所有文件")
except Exception as e:
    print(f"无法删除目录 {directory}, 错误: {e}")

# 创建临时文件夹
os.makedirs("./tmp/", exist_ok=True)

# 复制补充规则到tmp文件夹
subprocess.run("cp ./data/mod/adblock.txt ./tmp/adblock01.txt", shell=True)
subprocess.run("cp ./data/mod/whitelist.txt ./tmp/allow01.txt", shell=True)

# ============== 规则源列表 (带详细注释) ==============
adblock = [
    # 大萌主-接口广告规则
    "https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt",

    # DD-AD去广告规则
    "https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt",

    # GitHub加速hosts (HelloGitHub提供)
    "https://raw.hellogithub.com/hosts",

    # Anti-AD通用规则
    #"https://anti-ad.net/easylist.txt",

    # Cats-Team广告规则
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adblock.txt",

    # 挡广告hosts规则
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt",

    # 10007自动规则
    "https://lingeringsound.github.io/10007_auto/adb.txt",

    # 晴雅去广告规则
    "https://raw.githubusercontent.com/790953214/qy-Ads-Rule/main/black.txt",

    # 海哥广告规则
    "https://raw.githubusercontent.com/2771936993/HG/main/hg1.txt",

    # FCM hosts规则
    "https://github.com/entr0pia/fcm-hosts/raw/fcm/fcm-hosts",

    # 秋风广告规则
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",

    # SMAdHosts规则
    "https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/master/SMAdHosts",

    # 茯苓拦截规则
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/main/FuLingRules/FuLingBlockList.txt"
]

allow = [
    # 挡广告白名单
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",

    # AdGuardHome通用白名单
    "https://raw.githubusercontent.com/mphin/AdGuardHomeRules/main/Allowlist.txt",

    # 冷漠域名白名单
    "https://file-git.trli.club/file-hosts/allow/Domains",

    # jhsvip白名单
    "https://raw.githubusercontent.com/jhsvip/ADRuls/main/white.txt",

    # liwenjie119白名单
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",

    # 喵二白名单
    "https://raw.githubusercontent.com/miaoermua/AdguardFilter/main/whitelist.txt",

    # 茯苓白名单
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/main/FuLingRules/FuLingAllowList.txt",

    # Cats-Team白名单
    "https://raw.githubusercontent.com/Cats-Team/AdRules/script/allowlist.txt",

    # Anti-AD白名单
    "https://anti-ad.net/easylist.txt"
]

# 下载拦截规则
for i, url in enumerate(adblock, start=2):  # 从2开始编号以避免覆盖之前的文件
    filename = f"tmp/adblock{i:02d}.txt"
    try:
        subprocess.run(
            f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o {filename} --connect-timeout 60 -s '{url}' | iconv -t utf-8",
            shell=True,
            check=True
        )
        time.sleep(1)  # 避免请求过于频繁
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {url}, 错误: {e}")

# 下载白名单规则
for j, url in enumerate(allow, start=2):  # 从2开始编号以避免覆盖之前的文件
    filename = f"tmp/allow{j:02d}.txt"
    try:
        subprocess.run(
            f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o {filename} --connect-timeout 60 -s '{url}' | iconv -t utf-8",
            shell=True,
            check=True
        )
        time.sleep(1)  # 避免请求过于频繁
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {url}, 错误: {e}")

print('规则下载完成')