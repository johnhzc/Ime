"""候选窗口 UI（Win11 风格）

使用 tkinter 实现无边框、置顶、圆角的候选窗口，
适配 Windows 11 的 DPI 缩放和 UI 风格。
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
from typing import List, Optional, Callable, Tuple


class CandidateWindow:
    """候选窗口（Win11 风格）"""
    
    # Win11 风格配色
    BG_COLOR = "#F3F3F3"
    CODE_BG_COLOR = "#E8E8E8"
    CODE_FG_COLOR = "#0078D4"
    CANDIDATE_FG_COLOR = "#1F1F1F"
    INDEX_FG_COLOR = "#0078D4"
    PAGE_FG_COLOR = "#666666"
    HIGHLIGHT_BG = "#E1F5FE"
    BORDER_COLOR = "#D1D1D1"
    
    def __init__(self, on_select: Optional[Callable[[int], None]] = None):
        self._root: Optional[tk.Tk] = None
        self._on_select = on_select
        self._candidates: List[str] = []
        self._code_text = ""
        self._page = 1
        self._total_pages = 1
        self._is_visible = False
        self._lock = threading.Lock()
        self._docked = False  # 是否停靠在光标位置
        
    def show(self, x: int, y: int):
        """显示候选窗口在指定位置"""
        with self._lock:
            if self._root is None or not self._root.winfo_exists():
                self._create_window()
            
            if self._root is None:
                return
                
            # 确保窗口在屏幕范围内
            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            
            # 估算窗口大小
            win_w = 400
            win_h = 120
            
            # 调整位置避免超出屏幕
            if x + win_w > screen_w:
                x = screen_w - win_w - 10
            if y + win_h > screen_h:
                y = y - win_h - 20  # 显示在光标上方
            if y < 0:
                y = 10
            
            self._root.geometry(f"+{x}+{y}")
            self._root.deiconify()
            self._root.lift()
            self._root.attributes('-topmost', True)
            self._is_visible = True
    
    def hide(self):
        """隐藏候选窗口"""
        with self._lock:
            if self._root and self._root.winfo_exists():
                self._root.withdraw()
            self._is_visible = False
    
    def update_candidates(self, candidates: List[str], code: str, page: int = 1, total_pages: int = 1):
        """更新候选字列表和编码显示"""
        with self._lock:
            self._candidates = candidates
            self._code_text = code
            self._page = page
            self._total_pages = total_pages
            
            if self._root is None or not self._root.winfo_exists():
                return
            
            # 更新编码标签
            if hasattr(self, '_code_label') and self._code_label:
                self._code_label.config(text=code if code else " ")
            
            # 更新候选字标签
            if hasattr(self, '_candidates_frame') and self._candidates_frame:
                self._update_candidates_display()
            
            # 更新页码标签
            if hasattr(self, '_page_label') and self._page_label:
                self._page_label.config(text=f"[{page}/{total_pages}]")
    
    def is_visible(self) -> bool:
        return self._is_visible
    
    def _create_window(self):
        """创建 tkinter 窗口（Win11 风格）"""
        self._root = tk.Tk()
        self._root.overrideredirect(True)  # 无边框
        self._root.attributes('-topmost', True)  # 置顶
        self._root.configure(bg=self.BORDER_COLOR)
        
        # 主内容框（内边距模拟边框）
        self._main_frame = tk.Frame(self._root, bg=self.BG_COLOR, padx=1, pady=1)
        self._main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 编码显示区
        self._code_frame = tk.Frame(self._main_frame, bg=self.CODE_BG_COLOR, padx=8, pady=4)
        self._code_frame.pack(fill=tk.X, padx=4, pady=(4, 0))
        
        self._code_label = tk.Label(
            self._code_frame,
            text=" ",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.CODE_BG_COLOR,
            fg=self.CODE_FG_COLOR
        )
        self._code_label.pack(anchor=tk.W)
        
        # 候选字区域
        self._candidates_frame = tk.Frame(self._main_frame, bg=self.BG_COLOR, padx=8, pady=6)
        self._candidates_frame.pack(fill=tk.X, padx=4, pady=(0, 2))
        
        # 页码区域
        self._page_frame = tk.Frame(self._main_frame, bg=self.BG_COLOR, padx=8, pady=(0, 4))
        self._page_frame.pack(fill=tk.X, padx=4)
        
        self._page_label = tk.Label(
            self._page_frame,
            text="[1/1]",
            font=("Microsoft YaHei UI", 9),
            bg=self.BG_COLOR,
            fg=self.PAGE_FG_COLOR
        )
        self._page_label.pack(anchor=tk.E)
        
        # 初始隐藏
        self._root.withdraw()
    
    def _update_candidates_display(self):
        """更新候选字显示"""
        # 清除旧的候选字标签
        for widget in self._candidates_frame.winfo_children():
            widget.destroy()
        
        if not self._candidates:
            tk.Label(
                self._candidates_frame,
                text="无候选字",
                font=("Microsoft YaHei UI", 11),
                bg=self.BG_COLOR,
                fg="#999999"
            ).pack(anchor=tk.W)
            return
        
        # 创建候选字标签（横向排列）
        for i, candidate in enumerate(self._candidates[:9]):
            idx = i + 1
            
            # 每个候选字用一个小框架
            cand_frame = tk.Frame(self._candidates_frame, bg=self.BG_COLOR)
            cand_frame.pack(side=tk.LEFT, padx=(0, 12))
            
            # 序号标签
            idx_label = tk.Label(
                cand_frame,
                text=f"{idx}.",
                font=("Microsoft YaHei UI", 9),
                bg=self.BG_COLOR,
                fg=self.INDEX_FG_COLOR
            )
            idx_label.pack(side=tk.LEFT)
            
            # 候选字标签
            char_label = tk.Label(
                cand_frame,
                text=candidate,
                font=("Microsoft YaHei UI", 16, "bold"),
                bg=self.BG_COLOR,
                fg=self.CANDIDATE_FG_COLOR,
                cursor="hand2"
            )
            char_label.pack(side=tk.LEFT)
            
            # 点击事件
            char_label.bind("<Button-1>", lambda e, idx=i: self._on_click_candidate(idx))
            idx_label.bind("<Button-1>", lambda e, idx=i: self._on_click_candidate(idx))
    
    def _on_click_candidate(self, index: int):
        """点击候选字回调"""
        if self._on_select:
            self._on_select(index)
    
    def destroy(self):
        """销毁窗口"""
        with self._lock:
            if self._root and self._root.winfo_exists():
                self._root.destroy()
            self._root = None
            self._is_visible = False
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前窗口位置"""
        if self._root and self._root.winfo_exists():
            return self._root.winfo_x(), self._root.winfo_y()
        return 0, 0


def get_cursor_position() -> Tuple[int, int]:
    """获取当前光标位置（Win32 API）"""
    try:
        import ctypes
        # 使用 GetGUIThreadInfo 获取当前输入焦点窗口的插入符号位置
        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("flags", ctypes.c_uint),
                ("hwndActive", ctypes.c_void_p),
                ("hwndFocus", ctypes.c_void_p),
                ("hwndCapture", ctypes.c_void_p),
                ("hwndMenuOwner", ctypes.c_void_p),
                ("hwndMoveSize", ctypes.c_void_p),
                ("hwndCaret", ctypes.c_void_p),
                ("rcCaret", ctypes.c_int * 4),
                ("dwInsertionPoint", ctypes.c_uint),
            ]
        
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        
        if ctypes.windll.user32.GetGUIThreadInfo(0, ctypes.byref(gui_info)):
            # rcCaret 包含插入符的矩形坐标 (left, top, right, bottom)
            x = gui_info.rcCaret[0]
            y = gui_info.rcCaret[3] + 2  # 显示在光标下方
            return x, y
    except Exception:
        pass
    
    # Fallback: 使用 GetCursorPos
    try:
        pt = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y + 20
    except Exception:
        pass
    
    return 100, 100
