"""全局键盘监听模块

使用 pynput 监听全局键盘事件，并将事件分发给输入法引擎。
"""

from pynput import keyboard
from typing import Callable, Optional, Tuple
import threading
import time

class KeyboardHandler:
    """全局键盘监听器"""
    
    # 激活/关闭快捷键组合
    ACTIVATION_HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('w')}
    
    def __init__(self):
        self._listener: Optional[keyboard.Listener] = None
        self._callback: Optional[Callable[[str], Tuple[bool, Optional[str]]]] = None
        self._pressed_keys: set = set()
        self._is_running = False
        self._lock = threading.Lock()
        self._controller = keyboard.Controller()
        # 跟踪需要 pass-through 的按键（释放时需要重新发送）
        self._keys_to_pass_through: set = set()
        # Shift 状态跟踪（用于单独 Shift 检测）
        self._shift_state = {'pressed': False, 'used_with_other': False}
    
    def set_callback(self, callback: Callable[[str], Tuple[bool, Optional[str]]]):
        """设置按键处理回调函数
        
        callback(key: str) -> Tuple[bool, Optional[str]]:
            返回 (是否消耗此按键, 要输出的字符)
        """
        self._callback = callback
    
    def start(self):
        """启动键盘监听"""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=True  # 使用 pynput 的 suppress 机制
            )
            self._listener.start()
    
    def stop(self):
        """停止键盘监听"""
        with self._lock:
            self._is_running = False
            if self._listener:
                self._listener.stop()
                self._listener = None
    
    def _on_press(self, key, injected=False):
        """按键按下回调
        
        Args:
            key: 按下的键
            injected: 是否为模拟（注入）的按键事件
        """
        if not self._is_running:
            return
        
        # 忽略注入的按键事件，避免无限递归
        if injected:
            return
        
        # 记录按下的键
        self._pressed_keys.add(key)
        
        # 检测激活快捷键 Ctrl+Shift+W
        if self._is_hotkey_pressed():
            if self._callback:
                self._callback('hotkey')
            # 激活快捷键始终被消耗，不重新发送
            return
        
        # 跟踪 Shift 状态
        if self._is_shift_key(key):
            self._shift_state['pressed'] = True
            self._shift_state['used_with_other'] = False
        elif self._shift_state['pressed']:
            self._shift_state['used_with_other'] = True
        
        # 转换按键为可处理的字符串
        key_str = self._key_to_char(key)
        if key_str is None:
            # 未知按键，直接 pass-through
            self._keys_to_pass_through.add(key)
            self._controller.press(key)
            return
        
        # 调用回调处理按键
        if self._callback:
            consumed, output = self._callback(key_str)
            if not consumed:
                # 未消耗，重新发送给系统
                self._keys_to_pass_through.add(key)
                self._controller.press(key)
            # 若消耗，则不重新发送，按键保持被 suppress
        else:
            # 没有回调时，所有按键 pass-through
            self._keys_to_pass_through.add(key)
            self._controller.press(key)
    
    def _on_release(self, key, injected=False):
        """按键释放回调
        
        Args:
            key: 释放的键
            injected: 是否为模拟（注入）的按键事件
        """
        if not self._is_running:
            return
        
        # 忽略注入的按键事件
        if injected:
            return
        
        self._pressed_keys.discard(key)
        
        # 检测单独 Shift 释放（切换中英文）
        if self._is_shift_key(key) and self._shift_state['pressed'] and not self._shift_state['used_with_other']:
            self._shift_state['pressed'] = False
            if self._callback:
                consumed, output = self._callback('shift')
                if not consumed:
                    # 重新发送 Shift 的 press + release（因为 press 已被 suppress）
                    self._controller.press(key)
                    self._controller.release(key)
            return
        
        if self._is_shift_key(key):
            self._shift_state['pressed'] = False
        
        # 对 pass-through 的按键，释放时重新发送
        if key in self._keys_to_pass_through:
            self._keys_to_pass_through.discard(key)
            self._controller.release(key)
    
    def _is_hotkey_pressed(self) -> bool:
        """检查是否按下了激活快捷键"""
        has_ctrl = any(
            k in self._pressed_keys for k in 
            [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]
        )
        has_shift = any(
            k in self._pressed_keys for k in
            [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]
        )
        has_w = any(
            k in self._pressed_keys for k in
            [keyboard.KeyCode.from_char('w'), keyboard.KeyCode.from_char('W')]
        )
        return has_ctrl and has_shift and has_w
    
    def _is_shift_key(self, key) -> bool:
        """检查是否是 Shift 键"""
        return key in {
            keyboard.Key.shift,
            keyboard.Key.shift_l,
            keyboard.Key.shift_r
        }
    
    def _is_shift_only(self) -> bool:
        """检查是否只按了 Shift 键"""
        if not self._pressed_keys:
            return False
        
        shift_keys = {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}
        non_shift_pressed = self._pressed_keys - shift_keys
        
        # 如果有非 Shift 键被按下，返回 False
        if non_shift_pressed:
            return False
        
        # 至少有一个 Shift 键被按下
        return bool(self._pressed_keys & shift_keys)
    
    def _key_to_char(self, key) -> Optional[str]:
        """将按键转换为可处理的字符串
        
        支持的按键:
        - 字母键: 转换为小写字符
        - 数字键: 转换为数字字符
        - 空格、回车、Backspace、Esc、PageUp、PageDown、Tab 等控制键
        
        Returns:
            按键对应的字符串，或 None 表示不处理该按键
        """
        # 字母键和数字键
        if hasattr(key, 'char') and key.char is not None:
            if key.char.isalpha():
                return key.char.lower()
            elif key.char.isdigit():
                return key.char
            return None
        
        # 特殊按键
        if key == keyboard.Key.space:
            return 'space'
        elif key == keyboard.Key.enter:
            return 'enter'
        elif key == keyboard.Key.backspace:
            return 'backspace'
        elif key == keyboard.Key.esc:
            return 'esc'
        elif key == keyboard.Key.page_up:
            return 'page_up'
        elif key == keyboard.Key.page_down:
            return 'page_down'
        elif key == keyboard.Key.tab:
            return 'tab'
        elif key == keyboard.Key.delete:
            return 'delete'
        elif key == keyboard.Key.home:
            return 'home'
        elif key == keyboard.Key.end:
            return 'end'
        elif key == keyboard.Key.left:
            return 'left'
        elif key == keyboard.Key.right:
            return 'right'
        elif key == keyboard.Key.up:
            return 'up'
        elif key == keyboard.Key.down:
            return 'down'
        
        return None
    
    def is_running(self) -> bool:
        """检查监听器是否正在运行"""
        return self._is_running
