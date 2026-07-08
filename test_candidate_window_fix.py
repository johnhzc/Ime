#!/usr/bin/env python3
"""候选框修复验证脚本（在虚拟环境中运行）。

验证目标：
1. candidate_window.cpp 已按诊断报告完成两处修改；
2. TSF DLL 构建成功；
3. DLL 导出符号完整。
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_FILE = os.path.join(ROOT, "wubi_ime_tsf", "src", "candidate_window.cpp")
DLL_FILE = os.path.join(ROOT, "wubi_ime_tsf", "build2", "bin", "WubiIME_TSF.dll")
if not os.path.exists(DLL_FILE):
    DLL_FILE = os.path.join(ROOT, "wubi_ime_tsf", "build", "bin", "WubiIME_TSF.dll")


def check_source_modifications() -> list:
    """检查源码修改点。"""
    issues = []
    with open(SRC_FILE, "r", encoding="utf-8") as f:
        source = f.read()

    if "GetDesktopWindow()" not in source:
        issues.append("未找到 GetDesktopWindow() 调用")
    else:
        print("[OK] 已定义候选窗 owner")

    if "PeekMessage" not in source or "PM_NOREMOVE" not in source:
        issues.append("未找到 PeekMessage + PM_NOREMOVE 消息队列初始化")
    else:
        print("[OK] 已添加 PeekMessage 消息队列初始化")

    # 检查 WM_NCCREATE 是否正确返回 TRUE
    nccreate_match = re.search(
        r"if\s*\(\s*msg\s*==\s*WM_NCCREATE\s*\)\s*\{([^}]+)\}",
        source,
        re.DOTALL,
    )
    if not nccreate_match:
        issues.append("未找到 WM_NCCREATE 处理逻辑")
    elif "return TRUE" not in nccreate_match.group(1):
        issues.append("WM_NCCREATE 处理分支未返回 TRUE")
    else:
        print("[OK] WM_NCCREATE 已正确返回 TRUE")

    # 确认 owner 定义
    create_block = re.search(
        r"HWND owner\s*=\s*([^;]+);.*?CreateWindowExW",
        source,
        re.DOTALL,
    )
    if create_block:
        owner_value = create_block.group(1).strip()
        print(f"[OK] owner 取值: {owner_value}")
    else:
        issues.append("无法定位 owner 定义")

    return issues


def check_dll_exists() -> list:
    """检查 DLL 构建产物。"""
    issues = []
    if not os.path.exists(DLL_FILE):
        issues.append(f"DLL 不存在: {DLL_FILE}")
    else:
        size = os.path.getsize(DLL_FILE)
        mtime = os.path.getmtime(DLL_FILE)
        src_mtime = os.path.getmtime(SRC_FILE)
        print(f"[OK] DLL 存在: {DLL_FILE} ({size} bytes)")
        if mtime < src_mtime:
            issues.append("DLL 修改时间早于源码，可能未重新构建")
        else:
            print("[OK] DLL 构建时间晚于源码修改时间")
    return issues


def check_dll_exports() -> list:
    """检查 DLL 导出符号。"""
    issues = []
    try:
        result = subprocess.run(
            ["dumpbin", "/exports", DLL_FILE],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[WARN] 未找到 dumpbin，跳过导出符号检查")
        return issues

    if result.returncode != 0:
        issues.append(f"dumpbin 执行失败: {result.stderr}")
        return issues

    exports = result.stdout
    required = ["DllGetClassObject", "DllCanUnloadNow", "DllRegisterServer", "DllUnregisterServer"]
    missing = [name for name in required if name not in exports]
    if missing:
        issues.append(f"DLL 缺少导出符号: {missing}")
    else:
        print(f"[OK] DLL 导出符号完整: {required}")
    return issues


def main():
    print("=" * 60)
    print("候选框修复验证")
    print("=" * 60)

    issues = []
    issues.extend(check_source_modifications())
    issues.extend(check_dll_exists())
    issues.extend(check_dll_exports())

    print("=" * 60)
    if issues:
        print("[FAIL] 验证失败:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("[PASS] 所有验证通过")
        print("=" * 60)
        print("说明：")
        print("  本脚本验证了源码修改点和构建产物。")
        print("  候选窗口的实际显示效果仍需在 Windows 中注册 DLL 后人工测试。")
        print("  注册命令（管理员权限）: wubi_ime_tsf\\scripts\\register.bat")
        sys.exit(0)


if __name__ == "__main__":
    main()
