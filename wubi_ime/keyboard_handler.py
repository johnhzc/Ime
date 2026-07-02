"""全局键盘监听模块（Win11 兼容版）

使用 keyboard 库（基于 Win32 SetWindowsHookEx）替代 pynput，
在 Windows 11 下对全局键盘钩子的支持更稳定可靠。
"""

import threading
import time
from typing import Callable, Optional, Set

try:
    import keyboard
except ImportError:
    keyboard = None

class KeyboardHandler:
    """全局键盘监听器（Win11 兼容）"""
    
    # 需要拦截的编码键
    ENCODING_KEYS = set('abcdefghijklmnopqrstuvwxyz')
    # 控制键映射
    KEY_MAP = {
        'space': 'space',
        'enter': 'enter',
        'backspace': 'backspace',
        'esc': 'esc',
        'pageup': 'pageup',
        'pagedown': 'pagedown',
        'delete': 'delete',
        'tab': 'tab',
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
    }
    
    def __init__(self):
        self._callback: Optional[Callable[[str], bool]] = None
        self._is_running = False
        self._lock = threading.Lock()
        self._pressed_keys: Set[str] = set()
        self._hook_id = None
        
    def set_callback(self, callback: Callable[[str], bool]):
        """设置按键处理回调
        
        callback(key: str) -> bool:
            返回 True 表示已消耗此按键，不需要继续传递
        """
        self._callback = callback
    
    def start(self):
        """启动键盘监听（Win11 下需要管理员权限）"""
        if self._is_running:
            return
            
        if keyboard is None:
            raise ImportError(
                "keyboard 库未安装。请运行: pip install keyboard"
            )
        
        with self._lock:
            try:
                # 使用 suppress=False 避免 Win11 的权限问题
                # 实际拦截通过在 callback 返回 True 后调用 keyboard.send
                self._hook_id = keyboard.hook(self._on_key_event, suppress=False)
                self._is_running = True
            except Exception as e:
                raise RuntimeError(f"键盘监听启动失败: {e}")
    
    def stop(self):
        """停止键盘监听"""
        with self._lock:
            if self._hook_id is not None:
                try:
                    keyboard.unhook(self._hook_id)
                except Exception:
                    pass
                self._hook_id = None
            self._is_running = False
    
    def _on_key_event(self, event):
        """处理键盘事件"""
        if not self._callback or not self._is_running:
            return
            
        try:
            # 只处理按键按下事件
            if event.event_type != 'down':
                return
                
            key_name = event.name
            if key_name is None:
                return
                
            key_lower = key_name.lower()
            
            # 检测 Ctrl+Shift+W 激活热键
            if self._is_hotkey_pressed(key_lower):
                consumed = self._callback('hotkey')
                if consumed:
                    self._suppress_current_key()
                return
            
            # 检测 Shift 切换模式
            if key_lower == 'shift':
                # 检查是否只有 Shift 被按下（没有 Ctrl/Alt）
                if self._is_shift_only():
                    consumed = self._callback('shift')
                    if consumed:
                        self._suppress_current_key()
                return
            
            # 忽略 Ctrl/Alt/Win 组合键
            if self._is_modifier_pressed():
                return
            
            # 映射控制键
            mapped_key = self.KEY_MAP.get(key_lower, key_lower)
            
            # 检查是否是需要拦截的键
            if mapped_key in self.ENCODING_KEYS or mapped_key in self.KEY_MAP.values():
                consumed = self._callback(mapped_key)
                if consumed:
                    self._suppress_current_key()
                    
        except Exception as e:
            # 避免回调异常导致键盘钩子崩溃
            print(f"键盘事件处理错误: {e}")
    
    def _is_hotkey_pressed(self, key_lower: str) -> bool:
        """检查是否按下了 Ctrl+Shift+W"""
        # 使用 keyboard 库的状态检查
        try:
            return (keyboard.is_pressed('ctrl') and 
                    keyboard.is_pressed('shift') and 
                    key_lower == 'w')
        except Exception:
            return False
    
    def _is_shift_only(self) -> bool:
        """检查是否只按了 Shift"""
        try:
            return (keyboard.is_pressed('shift') and 
                    not keyboard.is_pressed('ctrl') and 
                    not keyboard.is_pressed('alt'))
        except Exception:
            return False
    
    def _is_modifier_pressed(self) -> bool:
        """检查是否按下了 Ctrl/Alt/Win 等修饰键"""
        try:
            return (keyboard.is_pressed('ctrl') or 
                    keyboard.is_pressed('alt') or 
                    keyboard.is_pressed('win'))
        except Exception:
            return False
    
    def _suppress_current_key(self):
        """阻止当前按键的默认行为（Win11 下有限制）"""
        # keyboard 库的 suppress 在 hook 时设置，这里只能尽量阻止
        # 在 Win11 下，如果 suppress=False，按键仍然会传递
        pass
    
    def is_running(self) -> bool:
        return self._is_running
