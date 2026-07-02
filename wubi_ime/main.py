"""五笔输入法主程序（keyboard 库，unhook/rehook 防递归版）

使用 keyboard 库的 suppress=True 拦截编码键，
发送输出前通过 unhook 取消钩子，发送后重新注册，
彻底避免 SendInput 触发递归死循环。
"""

import sys
import os
import time
import threading
import traceback
from typing import Optional

import tkinter as tk
from tkinter import messagebox

from .engine import WubiEngine, Action
from .keyboard_handler import KeyboardHandler
from .ui.candidate_window import CandidateWindow, get_cursor_position
from .ui.status_window import StatusWindow
from .config import Config


class WubiIME:
    """五笔输入法主类（unhook/rehook 防递归版）"""
    
    def __init__(self):
        self.config = Config()
        self.engine = WubiEngine()
        self.keyboard = KeyboardHandler()
        self.candidate_window = CandidateWindow(on_select=self._on_candidate_select)
        self.status_window = StatusWindow(on_click=self._on_status_click)
        self._running = False
        self._lock = threading.Lock()
        
    def _on_candidate_select(self, index: int):
        """候选字选择回调"""
        with self._lock:
            candidate = self.engine.select_candidate(index)
            if candidate:
                self._send_output(candidate)
            self.engine.clear()
            self._update_ui()
    
    def _on_key(self, key: str) -> bool:
        """键盘事件处理回调
        
        Returns:
            True: 已消耗此按键，不需要继续传播
        """
        try:
            with self._lock:
                # 检测热键 Ctrl+Shift+W
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
        
        关键：发送前先取消键盘钩子，防止 SendInput 触发递归死循环。
        """
        if not text:
            return
        
        # 1. 取消键盘钩子（防止 SendInput 触发的按键事件重新进入钩子）
        self.keyboard.unhook()
        
        try:
            # 2. 使用 SendInput 发送 Unicode 文本
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t),
                ]
            
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
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
    
    def _on_activation_hotkey(self):
        """激活/关闭输入法"""
        with self._lock:
            if self.engine.is_active():
                self.engine.deactivate()
                self.candidate_window.hide()
                self.status_window.hide()
                print("\n[五笔输入法已关闭]")
            else:
                self.engine.activate()
                self.status_window.show()
                self.status_window.set_chinese_mode(self.engine.is_chinese_mode())
                print("\n[五笔输入法已激活]")
    
    def _on_status_click(self):
        """状态窗口点击回调"""
        self._on_activation_hotkey()
    
    def _show_startup_dialog(self):
        """显示启动确认对话框"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        message = (
            "五笔输入法已启动！\n\n"
            "状态窗口显示在屏幕右下角。\n"
            "按 Ctrl+Shift+W 切换输入法状态。\n"
            "按 Shift 切换中英文。\n\n"
            "提示：Windows 11 下建议以管理员权限运行，\n"
            "否则可能无法在某些程序中输入。\n\n"
            "系统输入法切换（Ctrl+Shift, Win+Space）已兼容。"
        )
        
        messagebox.showinfo("五笔输入法", message)
        root.destroy()
    
    def start(self):
        """启动输入法"""
        print("=" * 50)
        print("五笔输入法启动中...")
        print("=" * 50)
        print()
        print("使用说明：")
        print("  按 Ctrl+Shift+W 激活/关闭输入法")
        print("  按 Shift 切换中英文模式")
        print("  系统输入法切换（Ctrl+Shift, Win+Space）已兼容")
        print()
        
        try:
            # 设置键盘回调
            self.keyboard.set_callback(self._on_key)
            
            # 启动键盘监听
            self.keyboard.start()
            print("✅ 键盘监听已启动")
            
            # 显示状态窗口
            self.status_window.show()
            self.status_window.set_chinese_mode(self.engine.is_chinese_mode())
            print("✅ 状态窗口已显示（右下角）")
            
            # 默认激活输入法
            self.engine.activate()
            print("✅ 输入法已激活")
            
            # 显示启动确认对话框
            self._show_startup_dialog()
            
            self._running = True
            print("\n输入法正在运行，按 Ctrl+C 退出...")
            
            # 主循环
            while self._running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"\n❌ 启动失败: {e}")
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
            self.candidate_window.destroy()
        except Exception:
            pass
        
        try:
            self.status_window.destroy()
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
