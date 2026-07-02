"""五笔输入法主程序（Win11 兼容版）

整合所有模块，提供输入法的主入口。
专门针对 Windows 11 的兼容性进行了优化：
- 使用 keyboard 库替代 pynput（更稳定的 Win32 钩子）
- 使用 pystray 系统托盘图标
- 正确的 Unicode SendInput 输出
- 管理员权限检测和提示
- 详细的错误日志
"""

import sys
import os
import time
import threading
import ctypes
import traceback
from typing import Optional, Tuple

from .engine import WubiEngine, Action
from .keyboard_handler import KeyboardHandler
from .ui.candidate_window import CandidateWindow, get_cursor_position
from .ui.tray_icon import get_tray_icon
from .config import Config


class WubiIME:
    """五笔输入法主类（Win11 兼容）"""
    
    def __init__(self):
        self.config = Config()
        self.engine = WubiEngine()
        self.keyboard = KeyboardHandler()
        self.candidate_window = CandidateWindow(on_select=self._on_candidate_select)
        self.tray_icon = get_tray_icon(
            on_toggle=self._on_toggle_mode,
            on_exit=self._on_exit
        )
        self._running = False
        self._lock = threading.Lock()
        
        # 日志
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志文件"""
        log_dir = os.path.join(os.path.expanduser("~"), ".wubi_ime")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "wubi_ime.log")
        
    def _log(self, msg: str):
        """写入日志"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
        except Exception:
            pass
    
    def _log_exception(self, e: Exception):
        """写入异常日志"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} ERROR: {e}\n")
                f.write(traceback.format_exc())
                f.write("\n")
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
        """键盘事件处理回调
        
        Returns:
            是否消耗此按键
        """
        try:
            with self._lock:
                # Check activation hotkey
                if key.lower() == 'hotkey':
                    self._on_activation_hotkey()
                    return True
                
                # If engine is not active, don't consume keys
                if not self.engine.is_active():
                    return False
                
                # Process key through engine
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
                    self.tray_icon.set_chinese_mode(self.engine.is_chinese_mode())
                
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
            self._log_exception(e)
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
                
                # 获取光标位置
                x, y = get_cursor_position()
                
                if not self.candidate_window.is_visible():
                    self.candidate_window.show(x, y)
                
                self.candidate_window.update_candidates(candidates, code, page, total_pages)
                
        except Exception as e:
            self._log_exception(e)
    
    def _send_output(self, text: str):
        """发送输出到当前应用程序（Win11 Unicode 兼容）"""
        if not text:
            return
        
        self._log(f"Sending output: {repr(text)}")
        
        try:
            # 使用 ctypes SendInput 发送 Unicode 字符
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # 定义 KEYBDINPUT 结构
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t),
                ]
            
            # 定义 INPUT 结构
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("ki", KEYBDINPUT),
                ]
            
            # 为每个 Unicode 字符发送按键事件
            inputs = []
            for ch in text:
                scan_code = ord(ch)
                
                # KEYDOWN (KEYEVENTF_UNICODE = 0x0004)
                ki = KEYBDINPUT(0, scan_code, 0x0004, 0, 0)
                inp = INPUT()
                inp.type = 1  # INPUT_KEYBOARD
                inp.ki = ki
                inputs.append(inp)
                
                # KEYUP (KEYEVENTF_UNICODE | KEYEVENTF_KEYUP = 0x0004 | 0x0002)
                ki = KEYBDINPUT(0, scan_code, 0x0004 | 0x0002, 0, 0)
                inp = INPUT()
                inp.type = 1
                inp.ki = ki
                inputs.append(inp)
            
            if inputs:
                n = len(inputs)
                arr = (INPUT * n)(*inputs)
                sent = user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
                if sent != n:
                    self._log(f"SendInput warning: sent {sent}/{n}")
                else:
                    self._log(f"SendInput success: {n} events")
                    
        except Exception as e:
            self._log(f"SendInput failed: {e}")
            # Fallback: 尝试写入剪贴板（不太理想但可用）
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                self._log("Fallback: text copied to clipboard")
            except Exception:
                pass
    
    def _on_activation_hotkey(self):
        """激活/关闭输入法"""
        with self._lock:
            if self.engine.is_active():
                self.engine.deactivate()
                self.candidate_window.hide()
                self.tray_icon.set_active(False)
                self._log("IME deactivated")
                print("\n[五笔输入法已关闭]")
            else:
                self.engine.activate()
                self.tray_icon.set_active(True)
                self._log("IME activated")
                print("\n[五笔输入法已激活] Ctrl+Shift+W 关闭, Shift 切换中英文")
    
    def _on_toggle_mode(self):
        """托盘图标切换回调"""
        self._on_activation_hotkey()
    
    def _on_exit(self):
        """托盘图标退出回调"""
        self._log("Exit requested from tray")
        self._running = False
    
    def _check_admin(self) -> bool:
        """检查是否以管理员权限运行"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def start(self):
        """启动输入法"""
        self._log("=" * 50)
        self._log("WubiIME starting...")
        self._log(f"Python: {sys.version}")
        self._log(f"Platform: {sys.platform}")
        
        # 检查管理员权限
        is_admin = self._check_admin()
        self._log(f"Admin privileges: {is_admin}")
        
        if not is_admin:
            print("⚠️ 警告：当前未以管理员权限运行")
            print("   在 Windows 11 中，全局键盘监听需要管理员权限")
            print("   建议：右键 WubiIME.exe → '以管理员身份运行'")
            print()
            self._log("WARNING: Running without admin privileges")
        
        print("五笔输入法启动中...")
        print("按 Ctrl+Shift+W 激活/关闭输入法")
        print("按 Shift 切换中英文模式")
        print(f"日志文件: {self.log_file}")
        
        try:
            # 设置键盘回调
            self.keyboard.set_callback(self._on_key)
            
            # 启动键盘监听
            self.keyboard.start()
            self._log("Keyboard listener started")
            
            # 启动系统托盘图标
            self.tray_icon.start()
            self._log("Tray icon started")
            
            # 激活输入法（默认开启）
            self.engine.activate()
            self.tray_icon.set_active(True)
            self.tray_icon.set_chinese_mode(self.engine.is_chinese_mode())
            self._log("IME activated by default")
            
            print("\n[五笔输入法已激活] 系统托盘图标已显示")
            print("按 Ctrl+Shift+W 关闭输入法")
            
            self._running = True
            
            # 主循环（保持程序运行）
            while self._running:
                time.sleep(0.1)
                
        except Exception as e:
            self._log_exception(e)
            print(f"\n❌ 启动失败: {e}")
            print(f"请查看日志: {self.log_file}")
            raise
    
    def stop(self):
        """停止输入法"""
        self._log("Stopping WubiIME...")
        self._running = False
        
        try:
            self.keyboard.stop()
            self._log("Keyboard listener stopped")
        except Exception as e:
            self._log(f"Error stopping keyboard: {e}")
        
        try:
            self.candidate_window.destroy()
            self._log("Candidate window destroyed")
        except Exception:
            pass
        
        try:
            self.tray_icon.stop()
            self._log("Tray icon stopped")
        except Exception:
            pass
        
        try:
            self.config.save()
            self._log("Config saved")
        except Exception:
            pass
        
        self._log("WubiIME stopped")
        print("\n五笔输入法已关闭")


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
    finally:
        ime.stop()


if __name__ == '__main__':
    main()
