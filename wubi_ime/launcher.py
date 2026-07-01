"""PyInstaller 打包入口脚本

此文件作为 PyInstaller 的打包入口，处理 sys.path 后调用 main.py 的逻辑。
"""

import sys
import os
import multiprocessing
import traceback

# Setup error logging to file (helpful when running without console)
log_dir = os.path.join(os.path.expanduser("~"), ".wubi_ime")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "wubi_ime.log")

def log(msg):
    """Write message to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{msg}\n")

def log_exception(e):
    """Write exception to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"ERROR: {e}\n")
        f.write(traceback.format_exc())
        f.write("\n")

# Ensure the project root is in sys.path
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

def main():
    """主函数"""
    log(f"{'='*40}")
    log(f"WubiIME starting...")
    log(f"Python: {sys.version}")
    log(f"Base dir: {base_dir}")
    log(f"sys.path: {sys.path[:3]}")
    
    try:
        # 导入主程序并运行
        from wubi_ime.main import WubiIME
        
        log("WubiIME imported successfully")
        
        print("五笔输入法启动中...")
        print("按 Ctrl+Shift+W 激活/关闭输入法")
        print("按 Shift 切换中英文模式")
        print("按 Ctrl+C 或关闭窗口退出输入法")
        print(f"日志文件: {log_file}")
        
        ime = WubiIME()
        log("WubiIME instance created")
        
        try:
            ime.start()
            log("WubiIME started")
            import time
            while ime._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n输入法关闭中...")
            log("KeyboardInterrupt received")
        finally:
            ime.stop()
            log("WubiIME stopped")
            
    except Exception as e:
        log_exception(e)
        print(f"\n启动失败: {e}")
        print(f"详细日志: {log_file}")
        print("\n常见原因：")
        print("  1. 需要以管理员权限运行（右键 → 以管理员身份运行）")
        print("  2. 杀毒软件拦截了键盘监听功能")
        print("  3. 缺少必要的运行时依赖")
        input("\n按 Enter 键退出...")
        raise

if __name__ == '__main__':
    # PyInstaller 多进程支持（Windows 必需）
    multiprocessing.freeze_support()
    main()
