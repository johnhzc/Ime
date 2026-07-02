"""Win11 诊断脚本 - 测试键盘监听和输出是否正常工作

直接运行此脚本来诊断问题：
python test_wubi_simple.py
"""

import sys
import time
import threading

# Test 1: 检查 keyboard 库是否可用
print("=" * 50)
print("诊断测试 1/3: 检查 keyboard 库")
print("=" * 50)

try:
    import keyboard
    print("✅ keyboard 库已安装")
except ImportError:
    print("❌ keyboard 库未安装")
    print("   请运行: pip install keyboard")
    sys.exit(1)

# Test 2: 测试键盘钩子（不 suppress）
print("\n" + "=" * 50)
print("诊断测试 2/3: 测试键盘钩子（不拦截）")
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
    print("✅ 键盘钩子正常工作（不拦截模式）")
else:
    print("⚠️ 未检测到按键，可能需要管理员权限")

# Test 3: 测试键盘钩子（拦截 + 输出）
print("\n" + "=" * 50)
print("诊断测试 3/3: 测试键盘拦截 + 输出（关键测试）")
print("=" * 50)
print("请打开记事本，把光标放在里面，然后按 'w' 键...")
print("预期：'w' 不出现，而是出现 '人'")
print("如果死机或输出错误，说明有兼容性问题")
print("测试将在 5 秒后自动结束...")

count = [0]

def intercept_hook(event):
    if event.event_type != 'down':
        return True
    if event.name and event.name.lower() == 'w':
        count[0] += 1
        print(f"  拦截 'w' (#{count[0]}), 发送 '人'")
        
        # 关键：尝试发送中文
        try:
            keyboard.send('backspace')  # 删除已输入的 w
            time.sleep(0.05)
            keyboard.write('人')          # 发送中文
        except Exception as e:
            print(f"  发送失败: {e}")
        
        return False  # 拦截原按键
    return True

hook_id2 = keyboard.hook(intercept_hook, suppress=True)

# 5秒后自动停止
time.sleep(5)
keyboard.unhook(hook_id2)

print(f"\n共拦截 {count[0]} 次 'w' 并发送 '人'")
if count[0] > 0:
    print("✅ 键盘拦截 + 输出功能正常")
    print("\n如果以上都正常，但五笔输入法仍有问题，")
    print("问题可能出在复杂的状态管理上。")
else:
    print("⚠️ 没有拦截到任何按键，Windows 11 可能限制了这个功能")
    print("   请尝试：右键运行 Python 脚本 -> 以管理员身份运行")

print("\n" + "=" * 50)
print("诊断完成")
print("=" * 50)
