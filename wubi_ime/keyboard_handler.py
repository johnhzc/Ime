"""全局键盘监听模块

使用 pynput 监听全局键盘事件，并将事件分发给输入法引擎。
"""

from pynput import keyboard
from typing import Callable, Optional
import threading

class KeyboardHandler:
    """全局键盘监听器"""
    
    # 激活/关闭快捷键
    ACTIVATION_HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('w')}
    
    def __init__(self):
        self._listener: Optional[keyboard.Listener] = None
        self._callback: Optional[Callable] = None
        self._pressed_keys: set = set()
        self._is_running = False
        self._lock = threading.Lock()
    
    def set_callback(self, callback: Callable):
        """设置按键处理回调函数
        
        callback(key: str) -> Tuple[bool, str]:
            返回 (是否消耗此按键, 要输出的字符)
        """
        self._callback = callback
    
    def start(self):
        """启动键盘监听"""
        pass
    
    def stop(self):
        """停止键盘监听"""
        pass
    
    def _on_press(self, key):
        """按键按下回调"""
        pass
    
    def _on_release(self, key):
        """按键释放回调"""
        pass
    
    def _is_hotkey_pressed(self) -> bool:
        """检查是否按下了激活快捷键"""
        pass
    
    def _is_shift_only(self) -> bool:
        """检查是否只按了 Shift 键"""
        pass
    
    def _key_to_char(self, key) -> Optional[str]:
        """将按键转换为字符"""
        pass
