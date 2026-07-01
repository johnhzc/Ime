"""PyInstaller 打包脚本

一键将五笔输入法打包为 Windows 可执行文件。
"""
import os
import sys
import subprocess
import shutil


def build():
    """执行 PyInstaller 打包"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # 确保 PyInstaller 可用
    try:
        import PyInstaller
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 构建输出目录
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")
    
    # 清理旧构建
    for d in [dist_dir, build_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"已清理: {d}")
    
    # PyInstaller 参数
    # 注意：Windows 上 --add-data 使用分号分隔
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # 单文件模式
        "--name", "WubiIME",   # 输出文件名
        "--clean",             # 清理临时文件
        "--noconfirm",         # 不确认覆盖
        # 包含数据文件
        "--add-data", f"wubi_ime/data{os.pathsep}wubi_ime/data",
        # 隐藏导入（pynput 的 Windows 后端）
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        # 入口脚本
        "wubi_ime/launcher.py",
    ]
    
    print("=" * 60)
    print("开始打包五笔输入法...")
    print("=" * 60)
    print("命令:", " ".join(cmd))
    print()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("✅ 打包成功!")
        print("=" * 60)
        exe_path = os.path.join(dist_dir, "WubiIME.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"输出文件: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print(f"输出目录: {dist_dir}")
        print()
        print("使用说明:")
        print("  1. 直接运行 WubiIME.exe 即可启动输入法")
        print("  2. 按 Ctrl+Shift+W 激活/关闭输入法")
        print("  3. 按 Shift 切换中英文模式")
        print("  4. 按 Ctrl+C 或在任务栏右键退出")
    else:
        print()
        print("=" * 60)
        print("❌ 打包失败")
        print("=" * 60)
        print("错误码:", result.returncode)
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
        return result.returncode
    
    return 0


if __name__ == '__main__':
    sys.exit(build())
