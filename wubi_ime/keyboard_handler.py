"""全局键盘监听模块（keyboard 库，unhook/rehook 防递归）

使用 keyboard 库的 suppress=True 拦截编码键，
发送输出前通过 unhook 取消钩子，发送后重新注册，
彻底避免 SendInput 触发递归死循环。

同时兼容系统输入法切换：
- Ctrl+Shift、Win+Space、Alt+Shift 等系统输入法热键不拦截
- 确保用户可以在系统输入法之间正常切换
"""

import threading
import time
from typing import Callable, Optional

try:
    import keyboard as _keyboard
except ImportError:
    _keyboard = None

class KeyboardHandler:
    """全局键盘监听器（unhook/rehook 防递归版）"""
    
    ENCODING_KEYS = set('abcdefghijklmnopqrstuvwxyz')
    DIGIT_KEYS = set('123456789')
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
        self._hook_id = None
        
    def set_callback(self, callback: Callable[[str], bool]):
        self._callback = callback
    
    def start(self):
        """启动键盘监听"""
        if self._is_running:
            return
        if _keyboard is None:
            raise ImportError("keyboard 库未安装。请运行: pip install keyboard")
        
        with self._lock:
            self._hook_id = _keyboard.hook(self._on_key_event, suppress=True)
            self._is_running = True
    
    def stop(self):
        """停止键盘监听"""
        with self._lock:
            if self._hook_id is not None:
                try:
                    _keyboard.unhook(self._hook_id)
                except Exception:
                    pass
                self._hook_id = None
            self._is_running = False
    
    def unhook(self):
        """临时取消键盘钩子（发送输出前调用）"""
        with self._lock:
            if self._hook_id is not None:
                try:
                    _keyboard.unhook(self._hook_id)
                except Exception:
                    pass
                self._hook_id = None
            # 短暂等待，确保 C 层钩子已解除
            time.sleep(0.005)
    
    def rehook(self):
        """重新注册键盘钩子（发送输出后调用）"""
        with self._lock:
            if self._hook_id is None and self._is_running:
                self._hook_id = _keyboard.hook(self._on_key_event, suppress=True)
    
    def _on_key_event(self, event):
        """处理键盘事件"""
        if not self._callback or not self._is_running:
            return True
        
        if event.event_type != 'down':
            return True
        
        key_name = event.name
        if key_name is None:
            return True
        
        key_lower = key_name.lower()
        
        try:
            # 1. 系统输入法切换快捷键：绝不拦截
            if _keyboard.is_pressed('ctrl') and _keyboard.is_pressed('shift'):
                return True
            if _keyboard.is_pressed('win') and key_lower == 'space':
                return True
            if _keyboard.is_pressed('alt') and _keyboard.is_pressed('shift'):
                return True
            
            # 2. Ctrl+Shift+W 热键
            if self._is_hotkey_pressed(key_lower):
                consumed = self._callback('hotkey')
                return not consumed
            
            # 3. 单独 Shift
            if key_lower == 'shift':
                if not _keyboard.is_pressed('ctrl') and not _keyboard.is_pressed('alt') and not _keyboard.is_pressed('win'):
                    consumed = self._callback('shift')
                    return not consumed
                return True
            
            # 4. 忽略修饰键组合
            if _keyboard.is_pressed('ctrl') or _keyboard.is_pressed('alt') or _keyboard.is_pressed('win'):
                return True
            
            # 5. 编码键或控制键
            mapped_key = self.KEY_MAP.get(key_lower, key_lower)
            if mapped_key in self.ENCODING_KEYS or mapped_key in self.DIGIT_KEYS or mapped_key in self.KEY_MAP.values():
                consumed = self._callback(mapped_key)
                return not consumed
            
            return True
            
        except Exception as e:
            print(f"键盘事件处理错误: {e}")
            return True
    
    def _is_hotkey_pressed(self, key_lower: str) -> bool:
        try:
            return (_keyboard.is_pressed('ctrl') and 
                    _keyboard.is_pressed('shift') and 
                    key_lower == 'w')
        except Exception:
            return False
    
    def is_running(self) -> bool:
        return self._is_running
