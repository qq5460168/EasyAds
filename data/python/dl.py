import os
import subprocess
import time
import shutil
from pathlib import Path

def clean_directory(path: str):
    """清理目录（文件+文件夹）"""
    dir_path = Path(path)
    if dir_path.exists():
        # 先删除文件
        for item in dir_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f"清理失败: {item}, 错误: {e}")
        # 再删除目录本身
        try:
            shutil.rmtree(dir_path)
            print(f"成功清理目录: {dir_path}")
        except Exception as e:
            print(f"删除目录失败: {dir_path}, 错误: {e}")

def main():
    # 清理旧规则目录
    clean_directory("./data/rules/")
    
    # 创建临时目录（确保干净）
    tmp_dir = Path("./tmp/")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for item in tmp_dir.iterdir():  # 清空tmp目录
        try:
            if item.is_file():
                item.unlink()
        except Exception as e:
            print(f"清理tmp文件失败: {item}, 错误: {e}")

    # 复制补充规则（使用shutil更跨平台）
    try:
        shutil.copy("./data/mod/adblock.txt", tmp_dir / "adblock01.txt")
        shutil.copy("./data/mod/whitelist.txt", tmp_dir / "allow01.txt")
        print("补充规则复制完成")
    except Exception as e:
        print(f"复制补充规则失败: {e}")
        return

    # 规则源列表
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

    # 下载拦截规则（修复curl管道无效问题，编码处理移至merge阶段）
    for i, url in enumerate(adblock, start=2):
        filename = tmp_dir / f"adblock{i:02d}.txt"
        try:
            # 移除无效的iconv管道（-o已重定向输出，stdout不经过管道）
            subprocess.run(
                f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o {filename} --connect-timeout 60 -s '{url}'",
                shell=True,
                check=True,
                capture_output=True
            )
            time.sleep(1)
            print(f"下载成功: {url}")
        except subprocess.CalledProcessError as e:
            print(f"下载失败: {url}, 错误: {e.stderr.decode()}")

    # 下载白名单规则
    for j, url in enumerate(allow, start=2):
        filename = tmp_dir / f"allow{j:02d}.txt"
        try:
            subprocess.run(
                f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o {filename} --connect-timeout 60 -s '{url}'",
                shell=True,
                check=True,
                capture_output=True
            )
            time.sleep(1)
            print(f"下载成功: {url}")
        except subprocess.CalledProcessError as e:
            print(f"下载失败: {url}, 错误: {e.stderr.decode()}")

    print("所有规则下载完成")

if __name__ == "__main__":
    main()