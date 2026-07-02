"""全局键盘监听模块（Win11 防冲突版）

核心策略：
- 只在输入法激活时拦截编码键（a-z）
- 发送输出前暂停钩子，发送后恢复（避免递归死循环）
- 系统输入法切换键（Ctrl+Shift, Win+Space）始终不拦截
- 所有其他键正常传递
"""

import threading
from typing import Callable, Optional, Set

try:
    import keyboard as _keyboard
except ImportError:
    _keyboard = None


class KeyboardHandler:
    """全局键盘监听器（Win11 防冲突）"""
    
    # 需要拦截的编码键（小写）
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
        self._hook_id = None
        self._paused = False  # 发送输出时暂停钩子
        
    def set_callback(self, callback: Callable[[str], bool]):
        """设置按键处理回调"""
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
    
    def pause(self):
        """暂停监听（发送输出时调用，防止递归）"""
        self._paused = True
    
    def resume(self):
        """恢复监听"""
        self._paused = False
    
    def _on_key_event(self, event):
        """处理键盘事件
        
        返回 True 表示按键继续传播（不拦截）
        返回 False 表示按键被拦截（不传播）
        """
        # 暂停期间（发送输出时）不处理任何事件
        if self._paused:
            return True
        
        if not self._callback or not self._is_running:
            return True
        
        # 只处理按键按下事件
        if event.event_type != 'down':
            return True
        
        key_name = event.name
        if key_name is None:
            return True
        
        key_lower = key_name.lower()
        
        try:
            # ===== 1. 系统输入法切换快捷键：绝不拦截 =====
            # Ctrl+Shift 是系统输入法切换
            if _keyboard.is_pressed('ctrl') and _keyboard.is_pressed('shift'):
                return True
            # Win+Space 是 Win11 输入法切换
            if _keyboard.is_pressed('win') and key_lower == 'space':
                return True
            # Alt+Shift 也是系统输入法切换
            if _keyboard.is_pressed('alt') and _keyboard.is_pressed('shift'):
                return True
            
            # ===== 2. Ctrl+Shift+W 热键：检测并拦截 =====
            if self._is_hotkey_pressed(key_lower):
                consumed = self._callback('hotkey')
                return not consumed  # consumed=True -> 不传播
            
            # ===== 3. 单独 Shift 键：切换中英文 =====
            if key_lower == 'shift':
                # 只处理单独的 Shift（不和其他修饰键组合）
                if not _keyboard.is_pressed('ctrl') and not _keyboard.is_pressed('alt') and not _keyboard.is_pressed('win'):
                    consumed = self._callback('shift')
                    return not consumed
                return True
            
            # ===== 4. 忽略所有修饰键组合 =====
            if _keyboard.is_pressed('ctrl') or _keyboard.is_pressed('alt') or _keyboard.is_pressed('win'):
                return True
            
            # ===== 5. 编码键或控制键：交给回调 =====
            mapped_key = self.KEY_MAP.get(key_lower, key_lower)
            if mapped_key in self.ENCODING_KEYS or mapped_key in self.KEY_MAP.values():
                consumed = self._callback(mapped_key)
                return not consumed  # 不传播（被拦截）或传播（未拦截）
            
            # ===== 6. 其他键：正常传播 =====
            return True
            
        except Exception as e:
            print(f"键盘事件处理错误: {e}")
            return True
    
    def _is_hotkey_pressed(self, key_lower: str) -> bool:
        """检查是否按下了 Ctrl+Shift+W"""
        try:
            return (_keyboard.is_pressed('ctrl') and 
                    _keyboard.is_pressed('shift') and 
                    key_lower == 'w')
        except Exception:
            return False
    
    def is_running(self) -> bool:
        return self._is_running
