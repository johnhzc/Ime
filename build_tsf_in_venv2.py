#!/usr/bin/env python3
"""Build TSF DLL inside the project virtual environment.

Always outputs to wubi_ime_tsf/build/bin/WubiIME_TSF.dll.
If the DLL is currently locked by the IME/TSF service, the script prints
cleanup instructions and exits instead of creating extra build directories.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TSF_DIR = os.path.join(ROOT, "wubi_ime_tsf")
BUILD_DIR = os.path.join(TSF_DIR, "build")
DLL_FILE = os.path.join(BUILD_DIR, "bin", "WubiIME_TSF.dll")
CMAKE_EXE = os.path.join(TSF_DIR, "cmake", "bin", "cmake.exe")
VCVARS = r"D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
UNREGISTER_BAT = os.path.join(TSF_DIR, "scripts", "unregister.bat")


def is_admin() -> bool:
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def is_dll_locked(path: str) -> bool:
    if not os.path.exists(path):
        return False
    try:
        with open(path, "ab"):
            pass
        return False
    except PermissionError:
        return True


def run_unregister() -> bool:
    if not os.path.exists(UNREGISTER_BAT):
        return False
    print("[INFO] Trying to unregister the old DLL automatically...")
    result = subprocess.run(
        f'"{UNREGISTER_BAT}"',
        shell=True,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


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

    if is_dll_locked(DLL_FILE):
        print(f"[WARN] DLL is locked: {DLL_FILE}")
        print("[WARN] The IME is probably still active in some process.")
        print()
        print("Cleanup steps (choose one):")
        print("  1. Run the unregister script as Administrator:")
        print(f"       {UNREGISTER_BAT}")
        print("     Then run this build script again.")
        print()
        print("  2. If unregister does not release the lock, sign out and")
        print("     sign back in (or restart), then run this build script again.")
        print()

        if is_admin():
            if run_unregister() and not is_dll_locked(DLL_FILE):
                print("[INFO] Unregister succeeded and DLL is now free.")
            else:
                print("[FAIL] Could not free the DLL. Please restart and retry.")
                sys.exit(1)
        else:
            print("[INFO] Re-run this script as Administrator to auto-unregister,")
            print("      or unregister manually and re-run.")
            sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)

    print("[INFO] Configuring CMake...")
    config_cmd = (
        f'"{CMAKE_EXE}" .. -G Ninja '
        f"-DCMAKE_BUILD_TYPE=Release "
        f"-DCMAKE_C_COMPILER=cl.exe "
        f"-DCMAKE_CXX_COMPILER=cl.exe"
    )
    result = run_in_vcvars(config_cmd, BUILD_DIR)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("[FAIL] CMake configuration failed")
        sys.exit(1)

    print("[INFO] Building...")
    build_cmd = f'"{CMAKE_EXE}" --build . --config Release'
    result = run_in_vcvars(build_cmd, BUILD_DIR)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("[FAIL] Build failed")
        sys.exit(1)

    if not os.path.exists(DLL_FILE):
        print(f"[FAIL] DLL missing after build: {DLL_FILE}")
        sys.exit(1)

    size = os.path.getsize(DLL_FILE)
    print(f"[PASS] DLL built: {DLL_FILE} ({size} bytes)")


if __name__ == "__main__":
    main()
