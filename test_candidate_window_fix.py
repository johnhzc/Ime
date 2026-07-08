#!/usr/bin/env python3
"""Verify the candidate-window fix inside the project virtual environment.

Checks:
1. Source changes in candidate_window.cpp are present.
2. TSF DLL was rebuilt after the source change.
3. Required DLL export symbols exist (if dumpbin is available).
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_FILE = os.path.join(ROOT, "wubi_ime_tsf", "src", "candidate_window.cpp")

LATEST_BUILD_MARKER = os.path.join(ROOT, "wubi_ime_tsf", "scripts", "latest_build_dir.txt")
DLL_FILE = ""
if os.path.exists(LATEST_BUILD_MARKER):
    with open(LATEST_BUILD_MARKER, "r", encoding="utf-8") as f:
        build_dir = f.read().strip()
    DLL_FILE = os.path.join(build_dir, "bin", "WubiIME_TSF.dll")
if not DLL_FILE or not os.path.exists(DLL_FILE):
    for build_name in ("build3", "build2", "build"):
        candidate = os.path.join(ROOT, "wubi_ime_tsf", build_name, "bin", "WubiIME_TSF.dll")
        if os.path.exists(candidate):
            DLL_FILE = candidate
            break


def check_source_modifications() -> list:
    issues = []
    with open(SRC_FILE, "r", encoding="utf-8") as f:
        source = f.read()

    if "PeekMessage" not in source or "PM_NOREMOVE" not in source:
        issues.append("Missing PeekMessage + PM_NOREMOVE")
    else:
        print("[OK] PeekMessage + PM_NOREMOVE found")

    nccreate_match = re.search(
        r"if\s*\(\s*msg\s*==\s*WM_NCCREATE\s*\)\s*\{([^}]+)\}",
        source,
        re.DOTALL,
    )
    if not nccreate_match:
        issues.append("Missing WM_NCCREATE handler")
    elif "return TRUE" not in nccreate_match.group(1):
        issues.append("WM_NCCREATE handler does not return TRUE")
    else:
        print("[OK] WM_NCCREATE returns TRUE")

    create_block = re.search(
        r"HWND owner\s*=\s*([^;]+);.*?CreateWindowExW",
        source,
        re.DOTALL,
    )
    if create_block:
        owner_value = create_block.group(1).strip()
        print(f"[OK] owner value: {owner_value}")
    else:
        issues.append("Cannot locate owner definition")

    return issues


def check_dll_exists() -> list:
    issues = []
    if not os.path.exists(DLL_FILE):
        issues.append(f"DLL not found: {DLL_FILE}")
    else:
        size = os.path.getsize(DLL_FILE)
        mtime = os.path.getmtime(DLL_FILE)
        src_mtime = os.path.getmtime(SRC_FILE)
        print(f"[OK] DLL found: {DLL_FILE} ({size} bytes)")
        if mtime < src_mtime:
            issues.append("DLL is older than source; rebuild needed")
        else:
            print("[OK] DLL is newer than source")
    return issues


def check_dll_exports() -> list:
    issues = []
    try:
        result = subprocess.run(
            ["dumpbin", "/exports", DLL_FILE],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[WARN] dumpbin not found, skipping export check")
        return issues

    if result.returncode != 0:
        issues.append(f"dumpbin failed: {result.stderr}")
        return issues

    exports = result.stdout
    required = ["DllGetClassObject", "DllCanUnloadNow", "DllRegisterServer", "DllUnregisterServer"]
    missing = [name for name in required if name not in exports]
    if missing:
        issues.append(f"DLL missing exports: {missing}")
    else:
        print(f"[OK] DLL exports complete: {required}")
    return issues


def main():
    print("=" * 60)
    print("Candidate Window Fix Verification")
    print("=" * 60)

    issues = []
    issues.extend(check_source_modifications())
    issues.extend(check_dll_exists())
    issues.extend(check_dll_exports())

    print("=" * 60)
    if issues:
        print("[FAIL] Verification failed:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("[PASS] All checks passed")
        print("=" * 60)
        print("Note:")
        print("  This script verifies source changes and build artifacts.")
        print("  Actual candidate window display must be tested in Windows")
        print("  after registering the DLL with administrator privileges.")
        print("  Register script: wubi_ime_tsf\\scripts\\register_latest.bat")
        sys.exit(0)


if __name__ == "__main__":
    main()
