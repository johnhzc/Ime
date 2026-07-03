"""五笔输入法主程序（Win11 优化版）

主线程负责：
1. 从 KeyboardHandler 的队列中取出按键事件；
2. 调用引擎处理；
3. 更新候选/状态窗口；
4. 调用 SendInput 输出文本。

键盘钩子回调只做最小判断和入队，避免在钩子线程中执行耗时操作。
"""

import sys
import os
import time
import threading
import traceback
import ctypes
from typing import Optional

import tkinter as tk
from tkinter import messagebox

from .engine import WubiEngine, Action
from .keyboard_handler import KeyboardHandler
from .ui.candidate_window import CandidateWindow, get_cursor_position
from .ui.status_window import StatusWindow
from .config import Config


class WubiIME:
    """五笔输入法主类（Win11 优化版）"""

    def __init__(self):
        self.config = Config()
        self.engine = WubiEngine()
        self._lock = threading.Lock()
        self._activation_hotkey = self.config.get("activation_hotkey", "ctrl+alt+w")
        self._previous_hkl: Optional[int] = None  # 激活前保存的系统键盘布局
        self.keyboard = KeyboardHandler(
            engine=self.engine,
            lock=self._lock,
            activation_hotkey=self._activation_hotkey
        )
        self._root: Optional[tk.Tk] = None
        self.candidate_window: Optional[CandidateWindow] = None
        self.status_window: Optional[StatusWindow] = None
        self._running = False

    def _set_dpi_awareness(self):
        """设置 Win11 DPI 感知，避免 UI 模糊"""
        try:
            # 2 = Per-monitor DPI aware (V2)，Win10 1607+/Win11 支持
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # 旧版 Windows 回退
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _on_candidate_select(self, index: int):
        """候选字选择回调"""
        with self._lock:
            candidate = self.engine.select_candidate(index)
            if candidate:
                self._send_output(candidate)
            self.engine.clear()
            self._update_ui()

    def _on_key(self, key: str) -> bool:
        """键盘事件处理回调（在主线程中调用）

        Returns:
            True: 已消耗此按键，不需要继续传播
        """
        try:
            with self._lock:
                # 检测激活热键
                if key.lower() == 'hotkey':
                    self._on_activation_hotkey()
                    return True

                # 如果输入法未激活，不消耗按键
                if not self.engine.is_active():
                    return False

                # 处理按键
                result = self.engine.process_key(key)
                if result is None:
                    return False
                elif isinstance(result, tuple):
                    action, data = result
                else:
                    action = result
                    data = None

                consumed = False

                if action == Action.ADD_KEY:
                    consumed = True
                    self._update_ui()

                elif action == Action.SELECT_CANDIDATE:
                    consumed = True
                    candidate = None
                    if data is not None:
                        try:
                            candidate = self.engine.select_candidate(int(data))
                        except (ValueError, TypeError):
                            candidate = data
                    if candidate:
                        self._send_output(candidate)
                    self.engine.clear()
                    self._update_ui()

                elif action == Action.DELETE:
                    consumed = True
                    self._update_ui()

                elif action == Action.CANCEL:
                    consumed = True
                    self.engine.clear()
                    self.candidate_window.hide()

                elif action == Action.SUBMIT:
                    consumed = True
                    if data:
                        self._send_output(data)
                    else:
                        candidates = self.engine.current_candidates or []
                        if candidates:
                            self._send_output(candidates[0])
                        else:
                            code = self.engine.current_code
                            if code:
                                self._send_output(code)
                    self.engine.clear()
                    self._update_ui()

                elif action == Action.SWITCH_MODE:
                    consumed = True
                    self.engine.toggle_mode()
                    self.status_window.set_chinese_mode(self.engine.is_chinese_mode())

                elif action == Action.PAGE_UP:
                    consumed = True
                    self._update_ui()

                elif action == Action.PAGE_DOWN:
                    consumed = True
                    self._update_ui()

                elif action == Action.IGNORE:
                    consumed = False

                return consumed

        except Exception as e:
            print(f"键盘事件处理错误: {e}")
            return False

    def _update_ui(self):
        """更新候选窗口显示"""
        try:
            with self._lock:
                code = self.engine.current_code
                candidates = self.engine.current_candidates or []

                if not candidates and not code:
                    self.candidate_window.hide()
                    return

                page_info = self.engine.get_page_info()
                if page_info and isinstance(page_info, tuple) and len(page_info) >= 2:
                    page, total_pages = page_info[0] + 1, page_info[1]
                else:
                    page, total_pages = 1, 1

                x, y = get_cursor_position()

                if not self.candidate_window.is_visible():
                    self.candidate_window.show(x, y)

                self.candidate_window.update_candidates(candidates, code, page, total_pages)

        except Exception as e:
            print(f"UI 更新错误: {e}")

    def _send_output(self, text: str):
        """发送输出到当前应用程序

        关键：发送前先取消键盘钩子，防止 SendInput 触发的按键事件重新进入队列。
        """
        if not text:
            return

        # 1. 取消键盘钩子（防止 SendInput 触发的按键事件重新进入处理逻辑）
        self.keyboard.unhook()

        try:
            # 2. 使用 SendInput 发送 Unicode 文本
            user32 = ctypes.windll.user32

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", ctypes.wintypes.WORD),
                    ("wScan", ctypes.wintypes.WORD),
                    ("dwFlags", ctypes.wintypes.DWORD),
                    ("time", ctypes.wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t),
                ]

            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", ctypes.wintypes.DWORD),
                    ("ki", KEYBDINPUT),
                ]

            inputs = []
            for ch in text:
                scan_code = ord(ch)

                # KEYDOWN (KEYEVENTF_UNICODE = 0x0004)
                ki = KEYBDINPUT(0, scan_code, 0x0004, 0, 0)
                inp = INPUT()
                inp.type = 1
                inp.ki = ki
                inputs.append(inp)

                # KEYUP (KEYEVENTF_UNICODE | KEYEVENTF_KEYUP = 0x0006)
                ki = KEYBDINPUT(0, scan_code, 0x0004 | 0x0002, 0, 0)
                inp = INPUT()
                inp.type = 1
                inp.ki = ki
                inputs.append(inp)

            if inputs:
                n = len(inputs)
                arr = (INPUT * n)(*inputs)
                user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))

        except Exception as e:
            print(f"发送输出失败: {e}")
        finally:
            # 3. 重新注册键盘钩子
            self.keyboard.rehook()

    def _get_foreground_hkl(self) -> Optional[int]:
        """获取当前前台窗口的键盘布局（HKL）"""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None
            tid = user32.GetWindowThreadProcessId(hwnd, None)
            return user32.GetKeyboardLayout(tid)
        except Exception as e:
            print(f"获取键盘布局失败: {e}")
            return None

    def _set_foreground_hkl(self, hkl: int):
        """为当前前台窗口设置键盘布局"""
        try:
            user32 = ctypes.windll.user32
            user32.ActivateKeyboardLayout(hkl, 0)
        except Exception as e:
            print(f"恢复键盘布局失败: {e}")

    def _switch_to_english_layout(self):
        """切换到英文（美国）键盘布局，避免 TSF 输入法抢占按键"""
        try:
            user32 = ctypes.windll.user32
            # 0x04090409 是英语（美国）键盘布局的 HKL
            user32.ActivateKeyboardLayout(0x04090409, 0)
        except Exception as e:
            print(f"切换到英文布局失败: {e}")

    def _on_activation_hotkey(self):
        """激活/关闭输入法

        激活时临时切换到英文键盘布局，避免百度、微信等 TSF 输入法
        抢占按键；关闭时恢复之前的布局。
        """
        with self._lock:
            if self.engine.is_active():
                # 恢复之前的系统键盘布局
                if self._previous_hkl is not None:
                    self._set_foreground_hkl(self._previous_hkl)
                    self._previous_hkl = None
                self.engine.deactivate()
                self.candidate_window.hide()
                self.status_window.hide()
                print("\n[五笔输入法已关闭]")
            else:
                # 保存当前布局并切换到英文，确保全局钩子能拦截按键
                self._previous_hkl = self._get_foreground_hkl()
                self._switch_to_english_layout()
                self.engine.activate()
                self.status_window.show()
                self.status_window.set_chinese_mode(self.engine.is_chinese_mode())
                print("\n[五笔输入法已激活]")

    def _on_status_click(self):
        """状态窗口点击回调"""
        self._on_activation_hotkey()

    def _show_startup_dialog(self):
        """显示启动确认对话框

        对话框显示期间临时取消键盘钩子，避免用户按键在队列中堆积。
        """
        if self._root is None or not self._root.winfo_exists():
            return

        hotkey_display = self._activation_hotkey.replace('+', '+').upper()
        message = (
            "五笔输入法已启动！\n\n"
            f"状态窗口显示在屏幕右下角。\n"
            f"按 {hotkey_display} 切换输入法状态。\n"
            "按 Shift 切换中英文。\n\n"
            "提示：Windows 11 下建议以管理员权限运行，\n"
            "否则可能无法在某些程序中输入。\n\n"
            "系统输入法切换（Ctrl+Shift, Win+Space）已兼容。"
        )

        # 对话框弹出期间暂停钩子，避免按键堆积
        self.keyboard.unhook()
        try:
            self._root.attributes('-topmost', True)
            messagebox.showinfo("五笔输入法", message, parent=self._root)
        except Exception as e:
            print(f"启动对话框显示失败: {e}")
        finally:
            self.keyboard.rehook()

    def start(self):
        """启动输入法"""
        print("=" * 50)
        print("五笔输入法启动中...")
        print("=" * 50)
        print()
        hotkey_display = self._activation_hotkey.replace('+', '+').upper()
        print("使用说明：")
        print(f"  按 {hotkey_display} 激活/关闭输入法")
        print("  按 Shift 切换中英文模式")
        print("  系统输入法切换（Ctrl+Shift, Win+Space）已兼容")
        print()

        try:
            # 设置 DPI 感知（必须在创建窗口前）
            self._set_dpi_awareness()

            # 创建共享的 tkinter 根窗口
            self._root = tk.Tk()
            self._root.withdraw()
            self._root.attributes('-topmost', True)

            # 创建 UI（共享同一个根窗口）
            self.candidate_window = CandidateWindow(
                master=self._root,
                on_select=self._on_candidate_select
            )
            self.status_window = StatusWindow(
                master=self._root,
                on_click=self._on_status_click
            )

            # 启动键盘监听
            self.keyboard.start()
            print("[OK] 键盘监听已启动")

            # 显示状态窗口
            self.status_window.show()
            self.status_window.set_chinese_mode(self.engine.is_chinese_mode())
            print("[OK] 状态窗口已显示（右下角）")

            # 默认激活输入法
            self.engine.activate()
            print("[OK] 输入法已激活")

            # 显示启动确认对话框
            self._show_startup_dialog()

            self._running = True
            print("\n输入法正在运行，按 Ctrl+C 退出...")

            # 主循环：处理按键事件和 tkinter 事件
            while self._running:
                # 处理所有已排队的按键事件
                while True:
                    key = self.keyboard.get_key_event(block=False)
                    if key is None:
                        break
                    self._on_key(key)

                # 刷新 tkinter UI（处理窗口消息）
                try:
                    self._root.update()
                except tk.TclError:
                    break

                time.sleep(0.005)

        except Exception as e:
            print(f"\n[FAIL] 启动失败: {e}")
            traceback.print_exc()
            raise

    def stop(self):
        """停止输入法"""
        print("\n正在关闭输入法...")
        self._running = False

        try:
            self.keyboard.stop()
        except Exception as e:
            print(f"停止键盘监听出错: {e}")

        try:
            if self.candidate_window:
                self.candidate_window.destroy()
        except Exception:
            pass

        try:
            if self.status_window:
                self.status_window.destroy()
        except Exception:
            pass

        try:
            if self._root and self._root.winfo_exists():
                self._root.destroy()
        except Exception:
            pass

        try:
            self.config.save()
        except Exception:
            pass

        print("输入法已关闭")


def main():
    """主函数"""
    ime = WubiIME()
    try:
        ime.start()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在关闭...")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        traceback.print_exc()
        input("\n按 Enter 键退出...")
    finally:
        ime.stop()


if __name__ == '__main__':
    main()
