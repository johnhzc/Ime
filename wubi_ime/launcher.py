"""PyInstaller 打包入口脚本（Win11 简化版）

直接启动输入法，不强制要求管理员权限。
Windows 11 下 keyboard 库的 WH_KEYBOARD_LL 钩子不需要管理员权限。
"""

import sys
import os
import multiprocessing

# 确保项目根目录在 sys.path 中
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

def main():
    """主函数"""
    print("=" * 50)
    print("五笔输入法启动中...")
    print("=" * 50)
    print()
    
    try:
        # 导入主程序并运行
        from wubi_ime.main import WubiIME
        
        ime = WubiIME()
        ime.start()
        
    except ImportError as e:
        print(f"\n[FAIL] 导入失败: {e}")
        print("请确保已安装依赖: pip install -r requirements.txt")
        input("\n按 Enter 键退出...")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n[FAIL] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")
        sys.exit(1)

if __name__ == '__main__':
    # PyInstaller 多进程支持（Windows 必需）
    multiprocessing.freeze_support()
    main()
