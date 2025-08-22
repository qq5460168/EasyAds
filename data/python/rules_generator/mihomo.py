import sys
import shutil
import tempfile
import subprocess
import urllib.request
import gzip
from pathlib import Path
from datetime import datetime
import pytz

# 日志函数（带北京时间）
def log(msg: str):
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{beijing_time}] INFO: {msg}")

def error(msg: str):
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{beijing_time}] ERROR: {msg}", file=sys.stderr)

def process_adguard_rules(input_path: Path, temp_path: Path) -> bool:
    """处理AdGuard规则，转换为mihomo兼容格式"""
    try:
        processed_lines = 0
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(temp_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith(('#', '!')):
                    continue
                
                # 转换规则格式（适配mihomo要求）
                if line.startswith("||") and line.endswith("^"):
                    f_out.write(f"+.{line[2:-1]}\n")  # 移除首尾标记并添加前缀
                    processed_lines += 1
                elif line.startswith("0.0.0.0 "):
                    f_out.write(f"+.{line[8:]}\n")   # 转换hosts格式
                    processed_lines += 1
                elif line.startswith("||"):
                    f_out.write(f"+.{line[2:]}\n")   # 处理域名规则
                    processed_lines += 1
                elif line.startswith("."):
                    f_out.write(f"+{line}\n")        # 保留子域名标记
                    processed_lines += 1
                else:
                    f_out.write(f"+.{line}\n")       # 通用规则处理

        log(f"已处理 {processed_lines} 条规则: {input_path.name} -> {temp_path.name}")
        return True
    except Exception as e:
        error(f"处理AdGuard规则失败: {str(e)}")
        return False

def download_mihomo_tool(tool_dir: Path) -> Path:
    """下载并解压最新版mihomo转换工具"""
    try:
        tool_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取最新版本号
        version_url = "https://github.com/MetaCubeX/mihomo/releases/latest/download/version.txt"
        version_file = tool_dir / "version.txt"
        log(f"获取mihomo最新版本: {version_url}")
        urllib.request.urlretrieve(version_url, version_file)
        
        with open(version_file, 'r') as f:
            version = f.read().strip()
        
        # 构建下载链接
        tool_name = f"mihomo-linux-amd64-{version}"
        tool_url = f"https://github.com/MetaCubeX/mihomo/releases/latest/download/{tool_name}.gz"
        tool_gz_path = tool_dir / f"{tool_name}.gz"
        
        # 下载并解压
        log(f"下载mihomo工具 v{version}: {tool_url}")
        urllib.request.urlretrieve(tool_url, tool_gz_path)
        
        tool_path = tool_dir / tool_name
        with gzip.open(tool_gz_path, 'rb') as f_in:
            with open(tool_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 设置执行权限并清理临时文件
        tool_path.chmod(0o755)
        version_file.unlink(missing_ok=True)
        tool_gz_path.unlink(missing_ok=True)
        
        log(f"mihomo工具已准备就绪: {tool_path.name}")
        return tool_path
    except Exception as e:
        error(f"下载mihomo工具失败: {str(e)}")
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
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        # 验证输出文件
        if output_path.exists() and output_path.stat().st_size > 0:
            log(f"MRS转换成功，文件大小: {output_path.stat().st_size} bytes")
            return True
        else:
            error("转换后文件为空或不存在")
            return False
            
    except subprocess.CalledProcessError as e:
        error(f"转换命令执行失败: {e.stderr}")
        return False
    except Exception as e:
        error(f"MRS转换失败: {str(e)}")
        return False

def main():
    try:
        # 路径计算（保持原规则路径不变）
        script_dir = Path(__file__).resolve().parent  # data/python/rules_generator
        project_root = script_dir.parent.parent.parent  # 项目根目录（EasyAds/）
        
        # 配置路径（严格保持原规则路径）
        config = {
            "input": project_root / "adblock-filtered.txt",  # 输入文件路径（根目录）
            "temp": Path(tempfile.gettempdir()) / "mihomo_temp.txt",  # 临时文件
            "output": project_root / "adb.mrs",  # 输出文件路径（根目录）
            "tool_dir": Path(tempfile.gettempdir()) / "mihomo_tools"  # 工具目录
        }

        # 路径验证日志
        log("="*50)
        log("路径配置信息:")
        log(f"脚本目录: {script_dir}")
        log(f"项目根目录: {project_root}")
        log(f"输入文件: {config['input']}")
        log(f"输出文件: {config['output']}")
        log("="*50)

        # 检查输入文件
        if not config["input"].exists():
            error(f"关键错误：输入文件不存在 - {config['input']}")
            error("请确保前置脚本已成功生成adblock-filtered.txt")
            sys.exit(1)

        # 处理规则
        if not process_adguard_rules(config["input"], config["temp"]):
            error("规则预处理失败，终止流程")
            sys.exit(1)

        # 下载工具
        tool_path = download_mihomo_tool(config["tool_dir"])
        if not tool_path or not tool_path.exists():
            error("工具准备失败，终止流程")
            sys.exit(1)

        # 转换格式
        if not convert_to_mrs(config["temp"], config["output"], tool_path):
            error("MRS格式转换失败，终止流程")
            sys.exit(1)

        # 清理临时文件
        try:
            if config["temp"].exists():
                config["temp"].unlink()
                log(f"已清理临时文件: {config['temp']}")
            if config["tool_dir"].exists():
                shutil.rmtree(config["tool_dir"], ignore_errors=True)
                log(f"已清理工具目录: {config['tool_dir']}")
        except Exception as e:
            error(f"临时文件清理警告: {str(e)}")  # 非致命错误

        log("="*50)
        log("Mihomo规则生成流程完成！")
        log(f"最终输出文件: {config['output']}")
        log("="*50)

    except Exception as e:
        error(f"主流程执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
