"""PyInstaller 打包入口脚本（Win11 优化版）

此文件作为 PyInstaller 的打包入口，处理 sys.path 后调用 main.py 的逻辑。
包含管理员权限检测和自动提权功能。
"""

import sys
import os
import multiprocessing
import ctypes
import traceback

# 检查是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# 请求管理员权限
def run_as_admin():
    """以管理员权限重新运行自身"""
    if is_admin():
        return True
    
    try:
        # 使用 ShellExecuteW 以管理员权限启动
        ctypes.windll.shell32.ShellExecuteW(
            None,  # hwnd
            "runas",  # lpOperation
            sys.executable,  # lpFile
            " ".join(sys.argv),  # lpParameters
            None,  # lpDirectory
            1  # nShowCmd (SW_SHOWNORMAL)
        )
        return False
    except Exception as e:
        print(f"无法请求管理员权限: {e}")
        return True  # 继续运行，让用户自行处理

# Setup error logging to file
log_dir = os.path.join(os.path.expanduser("~"), ".wubi_ime")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "wubi_ime.log")

def log(msg):
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{msg}\n")
    except Exception:
        pass

def log_exception(e):
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"ERROR: {e}\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception:
        pass

# 确保项目根目录在 sys.path 中
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

def main():
    log(f"{'='*50}")
    log(f"WubiIME Launcher starting...")
    log(f"Python: {sys.version}")
    log(f"Base dir: {base_dir}")
    log(f"sys.path: {sys.path[:3]}")
    
    # 检查管理员权限
    if not is_admin():
        log("WARNING: Not running as admin, attempting elevation...")
        print("五笔输入法需要管理员权限才能在 Windows 11 下正常工作。")
        print("正在请求管理员权限...")
        
        if not run_as_admin():
            log("Elevation requested, exiting current process")
            print("已请求管理员权限，请在新窗口中确认。")
            print("如果未看到 UAC 提示，请手动右键以管理员身份运行。")
            input("\n按 Enter 键退出...")
            sys.exit(0)
    else:
        log("Running with admin privileges")
        print("✅ 已以管理员权限运行")
    
    try:
        # 导入主程序并运行
        from wubi_ime.main import WubiIME
        
        log("WubiIME imported successfully")
        
        print("\n五笔输入法启动中...")
        print("按 Ctrl+Shift+W 激活/关闭输入法")
        print("按 Shift 切换中英文模式")
        print(f"日志文件: {log_file}")
        print("")
        
        ime = WubiIME()
        log("WubiIME instance created")
        
        try:
            ime.start()
            log("WubiIME started")
        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在关闭...")
            log("KeyboardInterrupt received")
        finally:
            ime.stop()
            log("WubiIME stopped")
            
    except Exception as e:
        log_exception(e)
        print(f"\n❌ 启动失败: {e}")
        print(f"详细日志: {log_file}")
        print("\n常见问题：")
        print("  1. 杀毒软件拦截了键盘监听功能")
        print("  2. 缺少必要的依赖库（keyboard、pystray）")
        print("  3. Windows 安全策略阻止了全局键盘钩子")
        input("\n按 Enter 键退出...")
        raise

if __name__ == '__main__':
    # PyInstaller 多进程支持（Windows 必需）
    multiprocessing.freeze_support()
    main()
