# data/python/rules_generator/mihomo.py
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess
import datetime

# 日志函数
def log(msg: str):
    print(f"[{datetime.datetime.now()}] INFO: {msg}")

def error(msg: str):
    print(f"[{datetime.datetime.now()}] ERROR: {msg}", file=sys.stderr)

def process_adguard_rules(input_path: Path, temp_path: Path) -> bool:
    """处理AdGuard规则为Mihomo兼容格式"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单过滤注释和空行
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith(('!', '#'))]
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        log(f"已处理AdGuard规则，生成临时文件: {temp_path}")
        return True
    except Exception as e:
        error(f"规则处理失败: {str(e)}")
        return False

def download_mihomo_tool(tool_dir: Path) -> Path:
    """下载Mihomo转换工具（示例实现，需根据实际工具调整）"""
    tool_dir.mkdir(parents=True, exist_ok=True)
    tool_path = tool_dir / "mihomo-converter"
    
    # 这里仅为示例，实际应替换为真实的工具下载逻辑
    try:
        with open(tool_path, 'w') as f:
            f.write("#!/bin/sh\ncat $1 > $2")  # 模拟转换工具
        tool_path.chmod(0o755)
        log(f"工具已准备: {tool_path}")
        return tool_path
    except Exception as e:
        error(f"工具下载失败: {str(e)}")
        return None

def convert_to_mrs(input_path: Path, output_path: Path, tool_path: Path) -> bool:
    """使用工具转换为MRS格式"""
    try:
        # 修复输出文件名为 Mihomo.yaml（与工作流矩阵匹配）
        result = subprocess.run(
            [str(tool_path), str(input_path), str(output_path)],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            error(f"转换命令失败: {result.stderr}")
            return False
            
        log(f"已转换为MRS格式: {output_path}")
        return True
    except Exception as e:
        error(f"格式转换失败: {str(e)}")
        return False

def main():
    try:
        # 路径计算
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent.parent
        
        # 配置路径（修复输出文件名为 Mihomo.yaml）
        config = {
            "input": project_root / "adblock-filtered.txt",
            "temp": Path(tempfile.gettempdir()) / "mihomo_temp.txt",
            "output": project_root / "Mihomo.yaml",  # 修复输出文件名
            "tool_dir": Path(tempfile.gettempdir()) / "mihomo_tools"
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
            error(f"临时文件清理警告: {str(e)}")

        log("="*50)
        log("Mihomo规则生成流程完成！")
        log(f"最终输出文件: {config['output']}")
        log("="*50)

    except Exception as e:
        error(f"主流程执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()