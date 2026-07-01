"""候选窗口 UI

使用 tkinter 实现五笔输入法的候选窗口。
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import List, Optional, Callable

class CandidateWindow:
    """候选窗口"""
    
    def __init__(self, on_select: Optional[Callable] = None):
        self._root: Optional[tk.Tk] = None
        self._on_select = on_select
        self._candidates: List[str] = []
        self._code_label: Optional[tk.Label] = None
        self._candidates_labels: List[tk.Label] = []
        self._is_visible = False
        self._lock = threading.Lock()
    
    def show(self, x: int, y: int):
        """显示候选窗口在指定位置"""
        pass
    
    def hide(self):
        """隐藏候选窗口"""
        pass
    
    def update_candidates(self, candidates: List[str], code: str, page: int = 1, total_pages: int = 1):
        """更新候选字列表和编码显示"""
        pass
    
    def is_visible(self) -> bool:
        return self._is_visible
    
    def _create_window(self):
        """创建 tkinter 窗口"""
        pass
    
    def _on_click(self, index: int):
        """点击候选字回调"""
        pass
    
    def _run_in_ui_thread(self, func):
        """在 UI 线程中运行函数"""
        pass
    
    def destroy(self):
        """销毁窗口"""
        pass
