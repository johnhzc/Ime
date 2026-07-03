"""全局键盘监听模块（keyboard 库，Win11 优化版）

使用 keyboard 库的 WH_KEYBOARD_LL 钩子，但把按键处理移到主线程：
1. 钩子回调只快速判断是否需要拦截，并将事件加入线程安全队列；
2. 主线程从队列取出事件，调用引擎处理、更新 UI、发送输出；
3. 避免在钩子回调里执行 SendInput、更新 tkinter 等耗时操作，防止 Windows
   因低级键盘钩子超时而自动卸载钩子。

同时兼容系统输入法切换：
- Ctrl+Shift、Win+Space、Alt+Shift 等系统输入法热键不拦截
"""

import threading
import time
from typing import Optional
from queue import Queue, Empty

try:
    import keyboard as _keyboard
except ImportError:
    _keyboard = None


class KeyboardHandler:
    """全局键盘监听器（Win11 优化版）"""

    ENCODING_KEYS = set('abcdefghijklmnopqrstuvwxyz')
    DIGIT_KEYS = set('123456789')
    PAGE_KEYS = {'+', '-'}
    CONTROL_KEYS = {
        'space', 'enter', 'backspace', 'esc', 'pageup', 'pagedown',
        'delete', 'tab', 'up', 'down', 'left', 'right'
    }

    def __init__(self,
                 engine=None,
                 lock: Optional[threading.Lock] = None,
                 activation_hotkey: str = "ctrl+alt+w"):
        self._engine = engine
        self._engine_lock = lock
        self._activation_hotkey = activation_hotkey
        self._hotkey_modifiers: set = set()
        self._hotkey_key: str = ""
        self._parse_activation_hotkey()
        self._is_running = False
        self._internal_lock = threading.Lock()
        self._hook_id = None
        self._key_queue: Queue = Queue()

    def get_key_event(self, block: bool = False, timeout: Optional[float] = None):
        """从队列取出一个按键事件（供主线程调用）

        Args:
            block: 是否阻塞等待
            timeout: 阻塞等待超时时间（秒）

        Returns:
            按键名称字符串；无事件时返回 None
        """
        try:
            return self._key_queue.get(block=block, timeout=timeout)
        except Empty:
            return None

    def start(self):
        """启动键盘监听"""
        if self._is_running:
            return
        if _keyboard is None:
            raise ImportError("keyboard 库未安装。请运行: pip install keyboard")

        with self._internal_lock:
            self._hook_id = _keyboard.hook(self._on_key_event, suppress=True)
            self._is_running = True

    def stop(self):
        """停止键盘监听"""
        with self._internal_lock:
            if self._hook_id is not None:
                try:
                    _keyboard.unhook(self._hook_id)
                except Exception:
                    pass
                self._hook_id = None
            self._is_running = False

    def unhook(self):
        """临时取消键盘钩子（发送输出前调用）"""
        with self._internal_lock:
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
        with self._internal_lock:
            if self._hook_id is None and self._is_running:
                self._hook_id = _keyboard.hook(self._on_key_event, suppress=True)

    def _enqueue(self, key: str):
        """将按键事件加入队列"""
        self._key_queue.put(key)

    def _on_key_event(self, event):
        """处理键盘事件（钩子回调，必须快速返回）"""
        if not self._is_running:
            return True

        if event.event_type != 'down':
            return True

        key_name = event.name
        if key_name is None:
            return True

        key_lower = key_name.lower()

        try:
            # 1. 激活热键：优先检测，避免被系统热键兼容逻辑放行
            if self._is_hotkey_pressed(key_lower):
                self._enqueue('hotkey')
                return False

            # 2. 系统输入法切换快捷键：绝不拦截
            if _keyboard.is_pressed('ctrl') and _keyboard.is_pressed('shift'):
                return True
            if _keyboard.is_pressed('win') and key_lower == 'space':
                return True
            if _keyboard.is_pressed('alt') and _keyboard.is_pressed('shift'):
                return True

            # 3. 单独 Shift
            if key_lower == 'shift':
                if self._should_suppress_shift():
                    self._enqueue('shift')
                    return False
                return True

            # 4. 忽略带修饰键的组合（Ctrl/Alt/Win）
            if _keyboard.is_pressed('ctrl') or _keyboard.is_pressed('alt') or _keyboard.is_pressed('win'):
                return True

            # 5. 编码键 a-z：中文模式下拦截
            if key_lower in self.ENCODING_KEYS:
                if self._should_suppress_encoding():
                    self._enqueue(key_lower)
                    return False
                return True

            # 6. 控制键、翻页键、数字键：仅在 IME 有输入时拦截
            if (key_lower in self.CONTROL_KEYS or
                key_lower in self.DIGIT_KEYS or
                key_lower in self.PAGE_KEYS):
                if self._should_suppress_control():
                    self._enqueue(key_lower)
                    return False
                return True

            return True

        except Exception as e:
            print(f"键盘事件处理错误: {e}")
            return True

    def _parse_activation_hotkey(self):
        """解析激活热键字符串，例如 'ctrl+alt+w' -> {'ctrl', 'alt'}, 'w'"""
        parts = [p.strip().lower() for p in self._activation_hotkey.split('+')]
        if parts:
            self._hotkey_key = parts[-1]
            self._hotkey_modifiers = set(parts[:-1])
        else:
            self._hotkey_key = ""
            self._hotkey_modifiers = set()

    def _is_hotkey_pressed(self, key_lower: str) -> bool:
        """检测激活热键是否被按下（要求修饰键完全匹配）"""
        try:
            if key_lower != self._hotkey_key:
                return False
            pressed_mods = set()
            for mod in ('ctrl', 'alt', 'shift', 'win'):
                if _keyboard.is_pressed(mod):
                    pressed_mods.add(mod)
            return pressed_mods == self._hotkey_modifiers
        except Exception:
            return False

    def _read_engine_state(self):
        """读取引擎状态（非阻塞加锁），返回 (is_active, is_chinese, has_input)

        使用非阻塞方式获取锁，避免主线程在 SendInput 期间持有锁时，
        钩子回调线程等待锁造成死锁。若无法立即获取锁，保守返回 False，
        即放行当前按键。
        """
        if self._engine is None or self._engine_lock is None:
            return False, False, False
        acquired = self._engine_lock.acquire(blocking=False)
        if not acquired:
            # 主线程可能正在处理前一个按键或发送输出，保守放行
            return False, False, False
        try:
            is_active = self._engine.is_active()
            is_chinese = self._engine.is_chinese_mode()
            has_input = bool(self._engine.current_code or self._engine.current_candidates)
            return is_active, is_chinese, has_input
        finally:
            self._engine_lock.release()

    def _should_suppress_encoding(self) -> bool:
        is_active, is_chinese, _ = self._read_engine_state()
        return is_active and is_chinese

    def _should_suppress_shift(self) -> bool:
        is_active, _, _ = self._read_engine_state()
        return is_active

    def _should_suppress_control(self) -> bool:
        is_active, is_chinese, has_input = self._read_engine_state()
        return is_active and is_chinese and has_input

    def is_running(self) -> bool:
        return self._is_running
