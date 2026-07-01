"""状态窗口 UI

显示输入法状态（中文/英文、全角/半角等）。
"""

import tkinter as tk
import threading

class StatusWindow:
    """输入法状态窗口"""
    
    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._is_chinese = True
        self._is_fullwidth = False
        self._label: Optional[tk.Label] = None
    
    def show(self):
        """显示状态窗口"""
        pass
    
    def hide(self):
        """隐藏状态窗口"""
        pass
    
    def set_chinese_mode(self, is_chinese: bool):
        """设置中文/英文模式显示"""
        pass
    
    def set_fullwidth_mode(self, is_fullwidth: bool):
        """设置全角/半角模式显示"""
        pass
    
    def destroy(self):
        """销毁窗口"""
        pass
