"""PyInstaller 打包入口脚本

此文件作为 PyInstaller 的打包入口，处理 sys.path 后调用 main.py 的逻辑。
"""

import sys
import os
import multiprocessing

# Ensure the project root is in sys.path
if hasattr(sys, '_MEIPASS'):
    # PyInstaller 打包环境
    base_dir = sys._MEIPASS
else:
    # 开发环境：获取当前文件所在目录的父目录
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# 导入主程序并运行
from wubi_ime.main import WubiIME

def main():
    """主函数"""
    print("五笔输入法启动中...")
    print("按 Ctrl+Shift+W 激活/关闭输入法")
    print("按 Shift 切换中英文模式")
    print("按 Ctrl+C 或关闭窗口退出输入法")
    
    ime = WubiIME()
    try:
        ime.start()
        import time
        while ime._running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n输入法关闭中...")
    finally:
        ime.stop()

if __name__ == '__main__':
    # PyInstaller 多进程支持（Windows 必需）
    multiprocessing.freeze_support()
    main()
