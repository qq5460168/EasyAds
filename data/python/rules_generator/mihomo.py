import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import pytz  # 需确保依赖已安装

# 新增：统一日志函数（与其他脚本风格一致）
def log(msg: str):
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{beijing_time}] INFO: {msg}")

def error(msg: str):
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{beijing_time}] ERROR: {msg}", file=sys.stderr)

def process_adguard_rules(input_path, temp_path):
    """处理AdGuard规则（示例实现，需根据实际逻辑补充）"""
    try:
        # 示例：简单复制文件（替换为真实处理逻辑）
        shutil.copy2(input_path, temp_path)
        log(f"已处理AdGuard规则: {input_path} -> {temp_path}")
        return True
    except Exception as e:
        error(f"处理AdGuard规则失败: {str(e)}")
        return False

def download_mihomo_tool(tool_dir: Path):
    """下载mihomo工具（示例实现）"""
    tool_dir.mkdir(parents=True, exist_ok=True)
    tool_path = tool_dir / "mihomo-converter"  # 假设工具文件名
    try:
        # 示例：创建空文件模拟下载（替换为真实下载逻辑）
        tool_path.touch()
        tool_path.chmod(0o755)  # 赋予执行权限
        log(f"已下载mihomo工具至: {tool_path}")
        return tool_path
    except Exception as e:
        error(f"下载mihomo工具失败: {str(e)}")
        return None

def convert_to_mrs(temp_path: Path, output_path: Path, tool_path: Path):
    """转换为mrs格式（示例实现）"""
    try:
        # 示例：模拟转换过程（替换为真实命令调用）
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 转换自 {temp_path}\n")
        log(f"已转换为MRS格式: {output_path}")
        return True
    except Exception as e:
        error(f"转换为MRS格式失败: {str(e)}")
        return False

def main():
    try:
        # 路径计算（与其他脚本保持一致）
        script_dir = Path(__file__).parent  # /data/python/rules_generator
        base_dir = script_dir.parent.parent  # 项目根目录（EasyAds/）
        
        config = {
            "input": base_dir / "adblock-filtered.txt",
            "temp": Path(tempfile.gettempdir()) / "mihomo.txt",
            "output": base_dir / "adb.mrs",
            "tool_dir": Path(tempfile.gettempdir()) / "mihomo_tools"
        }

        # 路径验证日志
        log("="*50)
        log("路径验证信息：")
        log(f"脚本目录: {script_dir.resolve()}")
        log(f"基础目录: {base_dir.resolve()}")
        log(f"输入文件: {config['input'].resolve()}")
        log("="*50)

        # 检查输入文件存在性
        if not config["input"].exists():
            error(f"输入文件不存在: {config['input']}")
            error(f"请确保前置脚本 'filter-ad.py' 已成功生成该文件")
            sys.exit(1)

        # 处理规则
        if not process_adguard_rules(config["input"], config["temp"]):
            error("AdGuard规则处理失败，终止流程")
            sys.exit(1)

        # 下载工具
        tool = download_mihomo_tool(config["tool_dir"])
        if not tool or not tool.exists():
            error("mihomo工具获取失败，终止流程")
            sys.exit(1)

        # 转换格式
        if not convert_to_mrs(config["temp"], config["output"], tool):
            error("MRS格式转换失败，终止流程")
            sys.exit(1)

        # 清理临时文件（增强版）
        try:
            if config["temp"].exists():
                config["temp"].unlink()
                log(f"已删除临时文件: {config['temp']}")
            if config["tool_dir"].exists():
                shutil.rmtree(config["tool_dir"], onexc=lambda func, path, exc: error(f"删除 {path} 失败: {exc}"))
                log(f"已删除工具目录: {config['tool_dir']}")
        except Exception as e:
            error(f"清理临时文件时出错: {str(e)}")
            # 不终止流程，仅警告

        # 最终日志
        log("="*50)
        log("AdGuard Home 黑名单转换完成！")
        log(f"最终输出文件: {config['output'].resolve()}")
        log(f"文件大小: {config['output'].stat().st_size / 1024:.2f} KB")  # 新增文件大小信息
        log("="*50)

    except Exception as e:
        error(f"主流程执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
