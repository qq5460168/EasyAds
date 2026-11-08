import os
import sys
import shutil
import tempfile
import subprocess
import urllib.request
import gzip
import time
from pathlib import Path
from datetime import datetime
import pytz

# 固定版本，避免每次依赖 GitHub "latest" 命名；可用环境变量覆盖
DEFAULT_MIHOMO_VERSION = "v1.19.33"
DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_TIMEOUT = 180
MIN_TOOL_SIZE = 5 * 1024 * 1024  # 小于 5MB 视为下载不完整
# 可选镜像前缀（例：https://ghproxy.net/），留空则只走 GitHub 官方地址
MIRROR_PREFIX = os.environ.get("MIHOMO_MIRROR", "").strip()


def log(msg: str):
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{beijing_time}] INFO: {msg}", flush=True)


def error(msg: str):
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{beijing_time}] ERROR: {msg}", file=sys.stderr, flush=True)


def process_adguard_rules(input_path: Path, temp_path: Path) -> bool:
    """处理AdGuard规则，转换为mihomo兼容格式"""
    try:
        processed_lines = 0
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(temp_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                line = line.strip()
                if not line or line.startswith(('#', '!')):
                    continue

                if line.startswith("||") and line.endswith("^"):
                    f_out.write(f"+.{line[2:-1]}\n")
                    processed_lines += 1
                elif line.startswith("0.0.0.0 "):
                    f_out.write(f"+.{line[8:]}\n")
                    processed_lines += 1
                elif line.startswith("||"):
                    f_out.write(f"+.{line[2:]}\n")
                    processed_lines += 1
                elif line.startswith("."):
                    f_out.write(f"+{line}\n")
                    processed_lines += 1
                else:
                    f_out.write(f"+.{line}\n")
                    processed_lines += 1

        log(f"已处理 {processed_lines} 条规则: {input_path.name} -> {temp_path.name}")
        return True
    except Exception as e:
        error(f"处理AdGuard规则失败: {str(e)}")
        return False


def download_with_retry(url: str, dest: Path, label: str) -> bool:
    """带重试的下载，失败自动退避；成功后校验文件非空"""
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            target_url = f"{MIRROR_PREFIX}{url}" if MIRROR_PREFIX and attempt == DOWNLOAD_ATTEMPTS else url
            log(f"[{label}] 下载中（第 {attempt}/{DOWNLOAD_ATTEMPTS} 次）: {target_url}")
            req = urllib.request.Request(target_url, headers={'User-Agent': 'EasyAds-Rules-Bot'})
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp, open(dest, 'wb') as f_out:
                shutil.copyfileobj(resp, f_out)
            if dest.exists() and dest.stat().st_size > 0:
                log(f"[{label}] 下载成功，大小 {dest.stat().st_size} bytes")
                return True
            error(f"[{label}] 下载内容为空")
        except Exception as e:
            error(f"[{label}] 第 {attempt} 次下载失败: {str(e)}")
        if attempt < DOWNLOAD_ATTEMPTS:
            backoff = 2 ** attempt
            log(f"[{label}] {backoff} 秒后重试")
            time.sleep(backoff)
    return False


def resolve_version(cache_dir: Path) -> str:
    """确定要使用的 mihomo 版本；latest 时读取官方 version.txt（带重试）"""
    env_version = os.environ.get('MIHOMO_VERSION', '').strip()
    if env_version and env_version.lower() != 'latest':
        log(f"使用配置的 mihomo 版本: {env_version}")
        return env_version

    if env_version.lower() == 'latest' or not env_version:
        if env_version.lower() == 'latest':
            version_url = "https://github.com/MetaCubeX/mihomo/releases/latest/download/version.txt"
            version_file = cache_dir / "version.txt"
            if not download_with_retry(version_url, version_file, "version.txt"):
                return DEFAULT_MIHOMO_VERSION
            try:
                content = version_file.read_text(encoding='utf-8', errors='ignore').strip()
                if content.startswith('v') and len(content) > 1:
                    log(f"解析到最新版本: {content}")
                    return content
                error(f"version.txt 内容异常: {content!r}，回退固定版本")
            except Exception as e:
                error(f"读取 version.txt 失败: {str(e)}，回退固定版本")
            finally:
                version_file.unlink(missing_ok=True)
            return DEFAULT_MIHOMO_VERSION

    return DEFAULT_MIHOMO_VERSION


def prepare_mihomo_tool(cache_dir: Path, version: str) -> Path:
    """优先复用缓存中的二进制，缺失或损坏才下载"""
    tool_name = f"mihomo-linux-amd64-{version}"
    tool_path = cache_dir / tool_name
    cache_dir.mkdir(parents=True, exist_ok=True)

    if tool_path.exists() and tool_path.stat().st_size >= MIN_TOOL_SIZE:
        try:
            probe = subprocess.run([str(tool_path), "-v"], capture_output=True, text=True, timeout=15)
            if probe.returncode == 0:
                log(f"命中缓存，跳过下载: {tool_name}")
                tool_path.chmod(0o755)
                return tool_path
            error(f"缓存二进制不可执行（exit={probe.returncode}），重新下载")
        except Exception as e:
            error(f"缓存二进制不可用: {str(e)}，重新下载")
        tool_path.unlink(missing_ok=True)

    tool_url = f"https://github.com/MetaCubeX/mihomo/releases/latest/download/{tool_name}.gz"
    gz_path = cache_dir / f"{tool_name}.gz"

    if not download_with_retry(tool_url, gz_path, tool_name):
        error("mihomo 二进制下载失败，已重试 %d 次" % DOWNLOAD_ATTEMPTS)
        return None

    try:
        with gzip.open(gz_path, 'rb') as f_in, open(tool_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        tool_path.chmod(0o755)
        gz_path.unlink(missing_ok=True)
        if tool_path.stat().st_size < MIN_TOOL_SIZE:
            error(f"解压后文件过小: {tool_path.stat().st_size} bytes")
            return None
        log(f"mihomo 工具已准备就绪: {tool_name}")
        return tool_path
    except Exception as e:
        error(f"解压 mihomo 失败: {str(e)}")
        return None


def convert_to_mrs(temp_path: Path, output_path: Path, tool_path: Path) -> bool:
    """使用mihomo工具将文本规则转换为MRS格式"""
    try:
        cmd = [
            str(tool_path),
            "convert-ruleset",
            "domain",
            "text",
            str(temp_path),
            str(output_path)
        ]

        log(f"开始转换为MRS格式: {output_path.name}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)

        if output_path.exists() and output_path.stat().st_size > 0:
            log(f"MRS转换成功，文件大小: {output_path.stat().st_size} bytes")
            return True

        error("转换后文件为空或不存在")
        return False

    except subprocess.CalledProcessError as e:
        error(f"转换命令执行失败: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        error("转换命令超时（600s）")
        return False
    except Exception as e:
        error(f"MRS转换失败: {str(e)}")
        return False


def main():
    try:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent.parent

        config = {
            "input": project_root / "adblock-filtered.txt",
            "temp": Path(tempfile.gettempdir()) / "mihomo_temp.txt",
            "output": project_root / "adb.mrs",
            "cache_dir": Path(os.environ.get('MIHOMO_CACHE_DIR', str(Path.home() / ".cache" / "mihomo")),
        }

        log("=" * 50)
        log("路径配置信息:")
        log(f"脚本目录: {script_dir}")
        log(f"项目根目录: {project_root}")
        log(f"输入文件: {config['input']}")
        log(f"输出文件: {config['output']}")
        log(f"缓存目录: {config['cache_dir']}")
        log("=" * 50)

        if not config["input"].exists():
            error(f"关键错误：输入文件不存在 - {config['input']}")
            error("请确保前置脚本已成功生成 adblock-filtered.txt")
            sys.exit(1)

        if not process_adguard_rules(config["input"], config["temp"]):
            error("规则预处理失败，终止流程")
            sys.exit(1)

        version = resolve_version(config["cache_dir"])
        tool_path = prepare_mihomo_tool(config["cache_dir"], version)
        if not tool_path or not tool_path.exists():
            error("工具准备失败，终止流程")
            sys.exit(1)

        if not convert_to_mrs(config["temp"], config["output"], tool_path):
            error("MRS格式转换失败，终止流程")
            sys.exit(1)

        try:
            if config["temp"].exists():
                config["temp"].unlink()
                log(f"已清理临时文件: {config['temp']}")
        except Exception as e:
            error(f"临时文件清理警告: {str(e)}")

        log("=" * 50)
        log("Mihomo规则生成流程完成！")
        log(f"最终输出文件: {config['output']}")
        log("=" * 50)

    except Exception as e:
        error(f"主流程执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
