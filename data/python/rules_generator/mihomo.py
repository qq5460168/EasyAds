import sys
import shutil
import tempfile
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

def process_adguard_rules(input_path, temp_path):
    """处理AdGuard规则（示例逻辑，根据实际需求调整）"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, \
             open(temp_path, 'w', encoding='utf-8') as f_out:
            # 保留注释和有效规则
            for line in f_in:
                line = line.strip()
                if line or line.startswith(('#', '!')):  # 保留空行、注释和规则
                    f_out.write(line + '\n')
        log(f"已处理AdGuard规则: {input_path} -> {temp_path}")
        return True
    except Exception as e:
        error(f"处理AdGuard规则失败: {str(e)}")
        return False

def download_mihomo_tool(tool_dir: Path):
    """下载mihomo转换工具（示例逻辑）"""
    tool_dir.mkdir(parents=True, exist_ok=True)
    tool_path = tool_dir / "mihomo-converter"
    try:
        # 实际场景中替换为真实下载逻辑（如curl/wget）
        tool_path.touch()  # 模拟创建工具文件
        tool_path.chmod(0o755)  # 赋予执行权限
        log(f"已下载工具至: {tool_path}")
        return tool_path
    except Exception as e:
        error(f"下载工具失败: {str(e)}")
        return None

def convert_to_mrs(temp_path: Path, output_path: Path, tool_path: Path):
    """转换为mrs格式（示例逻辑）"""
    try:
        # 实际场景中替换为真实转换命令
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 转换自 {temp_path}（{datetime.now().strftime('%Y-%m-%d')}）\n")
            with open(temp_path, 'r', encoding='utf-8') as f_temp:
                f.write(f_temp.read())
        log(f"已生成MRS文件: {output_path}")
        return True
    except Exception as e:
        error(f"转换格式失败: {str(e)}")
        return False

def main():
    try:
        # 关键修复：正确计算项目根目录
        # 脚本路径：data/python/rules_generator/mihomo.py
        script_dir = Path(__file__).resolve().parent  # data/python/rules_generator
        project_root = script_dir.parent.parent.parent  # 向上三级 -> 项目根目录（EasyAds/）
        
        # 配置路径（指向根目录下的文件）
        config = {
            "input": project_root / "adblock-filtered.txt",  # 前序脚本生成的文件（根目录）
            "temp": Path(tempfile.gettempdir()) / "mihomo_temp.txt",
            "output": project_root / "adb.mrs",  # 输出到根目录
            "tool_dir": Path(tempfile.gettempdir()) / "mihomo_tools"
        }

        # 路径验证日志（方便调试）
        log("="*50)
        log("路径验证信息：")
        log(f"脚本目录: {script_dir}")
        log(f"项目根目录: {project_root}")
        log(f"预期输入文件路径: {config['input']}")
        log(f"预期输出文件路径: {config['output']}")
        log("="*50)

        # 检查输入文件是否存在
        if not config["input"].exists():
            error(f"输入文件不存在: {config['input']}")
            error(f"请确认前序脚本 'filter-ad.py' 已在根目录生成该文件")
            sys.exit(1)

        # 处理规则
        if not process_adguard_rules(config["input"], config["temp"]):
            error("规则处理失败，终止流程")
            sys.exit(1)

        # 下载工具
        tool = download_mihomo_tool(config["tool_dir"])
        if not tool or not tool.exists():
            error("工具下载失败，终止流程")
            sys.exit(1)

        # 转换格式
        if not convert_to_mrs(config["temp"], config["output"], tool):
            error("格式转换失败，终止流程")
            sys.exit(1)

        # 清理临时文件
        try:
            if config["temp"].exists():
                config["temp"].unlink()
                log(f"已删除临时文件: {config['temp']}")
            if config["tool_dir"].exists():
                shutil.rmtree(config["tool_dir"], ignore_errors=True)
                log(f"已清理工具目录: {config['tool_dir']}")
        except Exception as e:
            error(f"清理临时文件时出错: {str(e)}")  # 非致命错误，仅警告

        log("="*50)
        log("Mihomo规则生成完成！")
        log(f"最终文件: {config['output']}")
        log("="*50)

    except Exception as e:
        error(f"主流程失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
