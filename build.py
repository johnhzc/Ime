"""PyInstaller 打包脚本（Win11 简化版）"""
import os
import sys
import subprocess
import shutil


def build():
    """执行 PyInstaller 打包"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # 构建输出目录
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")
    
    # 清理旧构建
    for d in [dist_dir, build_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"已清理: {d}")
    
    # PyInstaller 参数（Windows 使用分号分隔）
    sep = os.pathsep
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "WubiIME",
        "--clean",
        "--noconfirm",
        # 包含数据文件
        "--add-data", f"wubi_ime{sep}wubi_ime",
        # 隐藏导入
        "--hidden-import", "keyboard",
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
        print("[OK] 打包成功!")
        print("=" * 60)
        exe_path = os.path.join(dist_dir, "WubiIME.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"输出文件: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print(f"输出目录: {dist_dir}")
    else:
        print()
        print("=" * 60)
        print("[FAIL] 打包失败")
        print("=" * 60)
        print("错误码:", result.returncode)
        return result.returncode
    
    return 0


if __name__ == '__main__':
    sys.exit(build())
