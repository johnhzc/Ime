"""Win11 诊断脚本 - 测试键盘监听和输出是否正常工作

直接运行此脚本来诊断问题：
python test_wubi_simple.py
"""

import sys
import time
import threading
import ctypes

# Test 1: 检查 keyboard 库是否可用
print("=" * 50)
print("诊断测试 1/4: 检查 keyboard 库")
print("=" * 50)

try:
    import keyboard
    print("[OK] keyboard 库已安装")
except ImportError:
    print("[FAIL] keyboard 库未安装")
    print("   请运行: pip install keyboard")
    sys.exit(1)

# Test 2: 验证 SendInput INPUT 结构体定义
print("\n" + "=" * 50)
print("诊断测试 2/4: 验证 SendInput INPUT 结构体")
print("=" * 50)

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", ctypes.c_byte * 28),
        ("ki", KEYBDINPUT),
        ("hi", ctypes.c_byte * 8),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]

sizeof_input = ctypes.sizeof(INPUT)
print(f"  sizeof(INPUT) = {sizeof_input} bytes")
if sizeof_input == 40:
    print("[OK] INPUT 结构体大小正确（40 bytes）")
else:
    print(f"[FAIL] INPUT 结构体大小错误，应为 40 bytes，实际 {sizeof_input} bytes")
    print("   这将导致 SendInput 静默失败，无法输出文字")

# Test 3: 测试键盘钩子（不 suppress）
print("\n" + "=" * 50)
print("诊断测试 3/4: 测试键盘钩子（不拦截）")
print("=" * 50)
print("请在 5 秒内按几次 'w' 键...")

events = []

def test_hook(event):
    if event.event_type == 'down' and event.name and event.name.lower() == 'w':
        events.append('w')
        print(f"  检测到 'w' 按下 (#{len(events)})")
    return True

hook_id = keyboard.hook(test_hook, suppress=False)
time.sleep(5)
keyboard.unhook(hook_id)

print(f"\n共检测到 {len(events)} 次 'w' 按下")
if events:
    print("[OK] 键盘钩子正常工作（不拦截模式）")
else:
    print("[WARN] 未检测到按键，可能需要管理员权限")

# Test 4: 测试 SendInput Unicode 输出
print("\n" + "=" * 50)
print("诊断测试 4/4: 测试 SendInput Unicode 输出（关键测试）")
print("=" * 50)
print("请打开记事本，把光标放在里面...")
print("3 秒后将使用 SendInput 发送 '人' 字")
for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

# 构造并发送 Unicode 输入
ki_down = KEYBDINPUT(0, 0x4EBA, 0x0004, 0, 0)
inp_down = INPUT(1, _INPUT_UNION(ki=ki_down))
ki_up = KEYBDINPUT(0, 0x4EBA, 0x0004 | 0x0002, 0, 0)
inp_up = INPUT(1, _INPUT_UNION(ki=ki_up))

arr = (INPUT * 2)(inp_down, inp_up)
user32 = ctypes.windll.user32
ret = user32.SendInput(2, ctypes.byref(arr), ctypes.sizeof(INPUT))
print(f"\nSendInput 返回: {ret} (应等于 2)")
if ret == 2:
    print("[OK] SendInput Unicode 输出调用成功")
else:
    error_code = ctypes.get_last_error()
    print(f"[FAIL] SendInput 失败，错误码: {error_code}")
    print("   请检查 INPUT 结构体定义或管理员权限")

print("\n" + "=" * 50)
print("诊断完成")
print("=" * 50)
print("\n说明：")
print("- 若测试 2 失败，说明 ctypes 结构体定义有误，SendInput 会静默失败。")
print("- 若测试 3 失败，说明 keyboard 钩子未生效，可能需要以管理员身份运行。")
print("- 若测试 4 失败，说明 SendInput 无法向目标窗口注入 Unicode 输入。")
