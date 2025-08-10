def main():
    try:
        # 路径修改为根目录
        script_dir = Path(__file__).parent  # /data/python
        base_dir = script_dir.parent.parent  # 项目根目录
        
        config = {
            "input": base_dir / "adblock-filtered.txt",  # 根目录输入
            "temp": Path(tempfile.gettempdir()) / "mihomo.txt",
            "output": base_dir / "adb.mrs",  # 根目录输出
            "tool_dir": Path(tempfile.gettempdir()) / "mihomo_tools"
        }

        # 调试输出路径信息
        log("="*50)
        log("路径验证信息：")
        log(f"脚本目录: {script_dir}")
        log(f"基础目录: {base_dir}")
        log(f"输入文件: {config['input']}")
        log("="*50)

        if not config["input"].exists():
            error(f"输入文件不存在: {config['input']}")
            error(f"请确保前序脚本已生成: {config['input']}")
            sys.exit(1)

        if not process_adguard_rules(config["input"], config["temp"]):
            sys.exit(1)

        tool = download_mihomo_tool(config["tool_dir"])
        if not tool:
            sys.exit(1)

        if not convert_to_mrs(config["temp"], config["output"], tool):
            sys.exit(1)

        try:
            config["temp"].unlink(missing_ok=True)
            shutil.rmtree(config["tool_dir"], ignore_errors=True)
            log("已清理临时文件和目录")
        except Exception as e:
            error(f"清理临时文件时出错: {str(e)}")

        log("="*50)
        log("AdGuard Home 黑名单转换完成！")
        log(f"最终输出: {config['output']}")
        log("="*50)

    except Exception as e:
        error(f"主流程执行失败: {str(e)}")
        sys.exit(1)