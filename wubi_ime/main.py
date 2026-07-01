"""五笔输入法主程序

整合所有模块，提供输入法的主入口。
"""

import sys
import os
import time
import threading
from typing import Optional, Tuple

# Support running as script: set __package__ before imports
if __name__ == '__main__' and __package__ is None:
    __package__ = 'wubi_ime'
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)

try:
    from .engine import WubiEngine, Action
    from .keyboard_handler import KeyboardHandler
    from .ui.candidate_window import CandidateWindow
    from .ui.status_window import StatusWindow
    from .config import Config
except ImportError:
    # Fallback: add paths and import via package
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _parent_dir = os.path.dirname(_current_dir)
    if _parent_dir not in sys.path:
        sys.path.insert(0, _parent_dir)
    if _current_dir not in sys.path:
        sys.path.insert(0, _current_dir)
    
    from wubi_ime.engine import WubiEngine, Action
    from wubi_ime.keyboard_handler import KeyboardHandler
    from wubi_ime.ui.candidate_window import CandidateWindow
    from wubi_ime.ui.status_window import StatusWindow
    from wubi_ime.config import Config


class WubiIME:
    """五笔输入法主类"""
    
    def __init__(self):
        self.config = Config()
        self.engine = WubiEngine()
        self.keyboard = KeyboardHandler()
        self.candidate_window = CandidateWindow(on_select=self._on_candidate_select)
        self.status_window = StatusWindow()
        self._running = False
        self._is_fullwidth = False
    
    def _on_candidate_select(self, index: int):
        """候选字选择回调"""
        candidate = self.engine.select_candidate(index)
        if candidate:
            self._send_output(candidate)
            self.engine.clear()
            self._update_ui()
    
    def _on_key(self, key: str) -> Tuple[bool, Optional[str]]:
        """键盘事件处理回调
        
        Args:
            key: 按键字符串
            
        Returns:
            (是否消耗按键, 要输出的字符)
        """
        # Check activation hotkey (keyboard_handler sends 'hotkey' when detected)
        if key.lower() == 'hotkey':
            self._on_activation_hotkey()
            return True, None
        
        # If engine is not active, don't consume keys
        if not self.engine.is_active():
            return False, None
        
        # Process key through engine
        result = self.engine.process_key(key)
        
        # Handle different return types gracefully
        if result is None:
            action = Action.IGNORE
            data = None
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
            # Engine may have already cleared and provided the candidate in data
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
        
        return consumed, None
    
    def _update_ui(self):
        """更新候选窗口显示"""
        code = self.engine.current_code or ""
        candidates = self.engine.current_candidates or []
        page_info = self.engine.get_page_info()
        
        if page_info and isinstance(page_info, tuple) and len(page_info) >= 2:
            page, total_pages = page_info[0] + 1, page_info[1]
        else:
            page, total_pages = 1, 1
        
        if code or candidates:
            # Try to get cursor position using pywin32
            x, y = 200, 200
            try:
                import win32gui
                pt = win32gui.GetCaretPos()
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    x, y = win32gui.ClientToScreen(hwnd, (pt[0], pt[1]))
                else:
                    x, y = pt[0], pt[1]
            except Exception:
                pass
            
            self.candidate_window.show(x, y)
            self.candidate_window.update_candidates(candidates, code, page, total_pages)
        else:
            self.candidate_window.hide()
    
    def _send_output(self, text: str):
        """发送输出到当前应用程序
        
        使用 pynput Controller 或 ctypes SendInput 发送 Unicode 文本。
        """
        if not text:
            return
        
        # 使用 pynput Controller 发送文本（最可靠的方式）
        try:
            from pynput.keyboard import Controller
            controller = Controller()
            controller.type(text)
            return
        except Exception:
            pass
        
        # Fallback: ctypes SendInput 发送 Unicode
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            
            # Define KEYBDINPUT structure
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", wintypes.ULONG_PTR),
                ]
            
            # Define INPUT structure with KEYBDINPUT directly
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("ki", KEYBDINPUT),
                ]
            
            # Send each character as Unicode
            inputs = []
            for ch in text:
                # KEYDOWN
                ki = KEYBDINPUT(0, ord(ch), 0x0004, 0, 0)
                inp = INPUT()
                inp.type = 1  # INPUT_KEYBOARD
                inp.ki = ki
                inputs.append(inp)
                
                # KEYUP
                ki = KEYBDINPUT(0, ord(ch), 0x0004 | 0x0002, 0, 0)
                inp = INPUT()
                inp.type = 1
                inp.ki = ki
                inputs.append(inp)
            
            n = len(inputs)
            arr = (INPUT * n)(*inputs)
            user32.SendInput(n, arr, ctypes.sizeof(INPUT))
            
        except Exception as e:
            print(f"发送输出失败: {e}")
    
    def _on_activation_hotkey(self):
        """激活/关闭输入法快捷键回调"""
        if self.engine.is_active():
            self.engine.deactivate()
            self.candidate_window.hide()
            self.status_window.hide()
            print("输入法已关闭")
        else:
            self.engine.activate()
            if self.config.get("show_status_window", True):
                self.status_window.show()
                self.status_window.set_chinese_mode(self.engine.is_chinese_mode())
            print("输入法已激活")
    
    def start(self):
        """启动输入法
        
        设置键盘回调、启动键盘监听、显示状态窗口、进入主循环。
        """
        self._running = True
        self.keyboard.set_callback(self._on_key)
        self.keyboard.start()
        
        if self.config.get("show_status_window", True):
            self.status_window.show()
            self.status_window.set_chinese_mode(self.engine.is_chinese_mode())
        
        print("五笔输入法已启动")
        print(f"按 {self.config.get('activation_hotkey', 'ctrl+shift+w')} 激活/关闭输入法")
        print("按 Shift 切换中英文模式")
        
        # Main loop
        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
    
    def stop(self):
        """停止输入法
        
        停止键盘监听、隐藏所有窗口、保存配置。
        """
        self._running = False
        self.keyboard.stop()
        self.candidate_window.hide()
        self.status_window.hide()
        try:
            self.candidate_window.destroy()
        except Exception:
            pass
        try:
            self.status_window.destroy()
        except Exception:
            pass
        self.config.save()
        print("五笔输入法已停止")


def main():
    """主函数"""
    print("=" * 40)
    print("五笔输入法 (Wubi IME)")
    print("=" * 40)
    print("快捷键:")
    print("  Ctrl+Shift+W - 激活/关闭输入法")
    print("  Shift - 切换中英文模式")
    print("=" * 40)
    
    ime = WubiIME()
    try:
        ime.start()
    except KeyboardInterrupt:
        print("\n收到退出信号...")
    finally:
        ime.stop()
        print("输入法已退出")


if __name__ == '__main__':
    main()
