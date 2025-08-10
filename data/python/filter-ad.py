"""GitHub Actions 专用环境优化"""
import os
import resource  # 补充缺失的导入

def setup_github_actions() -> None:
    """GitHub Actions 专用环境优化：限制内存使用、文件描述符和交换区"""
    try:
        # 计算总内存并限制为80%
        page_size = os.sysconf('SC_PAGE_SIZE')
        total_pages = os.sysconf('SC_PHYS_PAGES')
        mem_total = page_size * total_pages
        resource.setrlimit(resource.RLIMIT_AS, (int(mem_total * 0.8), mem_total))
        
        # 限制文件描述符数量
        resource.setrlimit(resource.RLIMIT_NOFILE, (8192, 8192))
        
        # 禁用交换区（如果系统支持）
        if hasattr(resource, 'RLIMIT_SWAP'):
            resource.setrlimit(resource.RLIMIT_SWAP, (0, 0))
            
    except Exception as e:
        print(f"环境优化警告: {str(e)}")  # 捕获异常避免执行中断