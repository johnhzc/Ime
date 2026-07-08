#!/usr/bin/env python3
"""Build TSF DLL inside the project virtual environment.

Outputs to wubi_ime_tsf/buildN/ so we do not overwrite a DLL that is
currently locked by the IME/TSF service. The script picks the first
buildN directory whose DLL is not locked.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TSF_DIR = os.path.join(ROOT, "wubi_ime_tsf")
CMAKE_EXE = os.path.join(TSF_DIR, "cmake", "bin", "cmake.exe")
VCVARS = r"D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"


def find_build_dir() -> str:
    """Find a build directory whose DLL is not locked."""
    for i in range(2, 10):
        build_dir = os.path.join(TSF_DIR, f"build{i}")
        dll_path = os.path.join(build_dir, "bin", "WubiIME_TSF.dll")
        if not os.path.exists(dll_path):
            return build_dir
        # Try to open the DLL exclusively to see if it is locked.
        try:
            with open(dll_path, "ab"):
                pass
            return build_dir
        except PermissionError:
            print(f"[INFO] {dll_path} is locked, trying next directory")
            continue
    print("[FAIL] Could not find an unlocked build directory")
    sys.exit(1)


def run_in_vcvars(command: str, cwd: str) -> subprocess.CompletedProcess:
    full_cmd = f'"{VCVARS}" && {command}'
    print(f">>> {full_cmd}")
    return subprocess.run(
        full_cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def main():
    if not os.path.exists(CMAKE_EXE):
        print(f"[FAIL] CMake not found: {CMAKE_EXE}")
        sys.exit(1)

    if not os.path.exists(VCVARS):
        print(f"[FAIL] VS environment script not found: {VCVARS}")
        sys.exit(1)

    build_dir = find_build_dir()
    os.makedirs(build_dir, exist_ok=True)
    print(f"[INFO] Using build directory: {build_dir}")

    print("[INFO] Configuring CMake...")
    config_cmd = (
        f'"{CMAKE_EXE}" .. -G Ninja '
        f"-DCMAKE_BUILD_TYPE=Release "
        f"-DCMAKE_C_COMPILER=cl.exe "
        f"-DCMAKE_CXX_COMPILER=cl.exe"
    )
    result = run_in_vcvars(config_cmd, build_dir)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("[FAIL] CMake configuration failed")
        sys.exit(1)

    print("[INFO] Building...")
    build_cmd = f'"{CMAKE_EXE}" --build . --config Release'
    result = run_in_vcvars(build_cmd, build_dir)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("[FAIL] Build failed")
        sys.exit(1)

    dll_path = os.path.join(build_dir, "bin", "WubiIME_TSF.dll")
    if not os.path.exists(dll_path):
        print(f"[FAIL] DLL missing after build: {dll_path}")
        sys.exit(1)

    size = os.path.getsize(dll_path)
    print(f"[PASS] DLL built: {dll_path} ({size} bytes)")

    # Remember the build directory for the register script.
    marker = os.path.join(TSF_DIR, "scripts", "latest_build_dir.txt")
    with open(marker, "w", encoding="utf-8") as f:
        f.write(build_dir)


if __name__ == "__main__":
    main()
