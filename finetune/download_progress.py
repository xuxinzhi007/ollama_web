#!/usr/bin/env python3
"""
模型下载进度提示工具
"""

import time
import threading
from typing import Optional

class DownloadProgressIndicator:
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.start_time = 0

    def start(self, message: str = "⏳ 正在下载模型..."):
        """开始显示进度提示"""
        self.running = True
        self.start_time = time.time()

        def show_progress():
            dots = 0
            while self.running:
                elapsed = time.time() - self.start_time
                mins, secs = divmod(int(elapsed), 60)

                dots_str = "." * (dots % 4)
                spaces_str = " " * (3 - (dots % 4))

                print(f"\r{message}{dots_str}{spaces_str} ({mins:02d}:{secs:02d})", end="", flush=True)

                time.sleep(3)  # 每3秒更新一次，减少输出频率
                dots += 1

        self.thread = threading.Thread(target=show_progress, daemon=True)
        self.thread.start()

    def stop(self, success_message: str = "✅ 下载完成"):
        """停止显示进度"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        print(f"\r{success_message} ({mins:02d}:{secs:02d})          ")

# 全局进度指示器
progress_indicator = DownloadProgressIndicator()

def with_progress(func, message: str = "⏳ 正在处理..."):
    """装饰器：为函数添加进度提示"""
    def wrapper(*args, **kwargs):
        progress_indicator.start(message)
        try:
            result = func(*args, **kwargs)
            progress_indicator.stop("✅ 处理完成")
            return result
        except Exception as e:
            progress_indicator.stop(f"❌ 处理失败: {e}")
            raise
    return wrapper

if __name__ == "__main__":
    # 测试代码
    print("测试下载进度指示器...")
    progress_indicator.start("⏳ 模拟下载中")
    time.sleep(5)
    progress_indicator.stop("✅ 下载完成")