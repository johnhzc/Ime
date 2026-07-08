#!/usr/bin/env python3
"""在虚拟环境中调用 Visual Studio 环境构建 TSF DLL（输出到 build2 避免占用）。"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TSF_DIR = os.path.join(ROOT, "wubi_ime_tsf")
BUILD_DIR = os.path.join(TSF_DIR, "build2")
CMAKE_EXE = os.path.join(TSF_DIR, "cmake", "bin", "cmake.exe")
VCVARS = r"D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"


def run_in_vcvars(command: str) -> subprocess.CompletedProcess:
    full_cmd = f'"{VCVARS}" && {command}'
    print(f">>> {full_cmd}")
    return subprocess.run(
        full_cmd,
        shell=True,
        cwd=BUILD_DIR,
        capture_output=True,
        text=True,
    )


def main():
    if not os.path.exists(CMAKE_EXE):
        print(f"[FAIL] 找不到 CMake: {CMAKE_EXE}")
        sys.exit(1)

    if not os.path.exists(VCVARS):
        print(f"[FAIL] 找不到 VS 环境脚本: {VCVARS}")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)

    print("[INFO] 配置 CMake...")
    config_cmd = (
        f'"{CMAKE_EXE}" .. -G Ninja '
        f"-DCMAKE_BUILD_TYPE=Release "
        f"-DCMAKE_C_COMPILER=cl.exe "
        f"-DCMAKE_CXX_COMPILER=cl.exe"
    )
    result = run_in_vcvars(config_cmd)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("[FAIL] CMake 配置失败")
        sys.exit(1)

    print("[INFO] 构建...")
    build_cmd = f'"{CMAKE_EXE}" --build . --config Release'
    result = run_in_vcvars(build_cmd)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("[FAIL] 构建失败")
        sys.exit(1)

    dll_path = os.path.join(BUILD_DIR, "bin", "WubiIME_TSF.dll")
    if not os.path.exists(dll_path):
        print(f"[FAIL] 构建成功但 DLL 不存在: {dll_path}")
        sys.exit(1)

    size = os.path.getsize(dll_path)
    print(f"[PASS] DLL 构建成功: {dll_path} ({size} bytes)")


if __name__ == "__main__":
    main()
