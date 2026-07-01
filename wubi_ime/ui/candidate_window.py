"""候选窗口 UI

使用 tkinter 实现五笔输入法的候选窗口。
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import List, Optional, Callable

class CandidateWindow:
    """候选窗口"""
    
    # 颜色配置
    CODE_COLOR = "#1976D2"  # 编码颜色 (蓝色)
    CANDIDATE_COLOR = "#333333"  # 候选字颜色
    INDEX_COLOR = "#1976D2"  # 序号颜色 (蓝色)
    FIRST_CANDIDATE_COLOR = "#D32F2F"  # 首选候选字颜色 (红色)
    PAGE_COLOR = "#757575"  # 页码颜色 (灰色)
    HIGHLIGHT_BG = "#E3F2FD"  # 高亮背景
    BG_COLOR = "#FFFFFF"  # 窗口背景色
    
    def __init__(self, on_select: Optional[Callable] = None):
        self._root: Optional[tk.Tk] = None
        self._window: Optional[tk.Toplevel] = None
        self._on_select = on_select
        self._candidates: List[str] = []
        self._code = ""
        self._page = 1
        self._total_pages = 1
        self._is_visible = False
        self._lock = threading.Lock()
        self._ui_thread: Optional[threading.Thread] = None
        self._after_ids: List[int] = []
    
    def show(self, x: int, y: int):
        """显示候选窗口在指定位置"""
        with self._lock:
            if self._window is None or not self._window.winfo_exists():
                self._create_window()
            
            if self._window:
                # 调整位置，确保窗口不超出屏幕
                screen_width = self._window.winfo_screenwidth()
                screen_height = self._window.winfo_screenheight()
                
                # 先更新窗口大小
                self._window.update_idletasks()
                width = self._window.winfo_width()
                height = self._window.winfo_height()
                
                # 如果超出右边界，显示在光标左侧
                if x + width > screen_width:
                    x = max(0, x - width - 10)
                
                # 如果超出下边界，显示在光标上方
                if y + height > screen_height:
                    y = max(0, y - height - 20)
                
                self._window.geometry(f"+{x}+{y}")
                self._window.deiconify()
                self._window.lift()
                self._window.attributes('-topmost', True)
                self._is_visible = True
    
    def hide(self):
        """隐藏候选窗口"""
        with self._lock:
            if self._window and self._window.winfo_exists():
                self._window.withdraw()
            self._is_visible = False
    
    def update_candidates(self, candidates: List[str], code: str, page: int = 1, total_pages: int = 1):
        """更新候选字列表和编码显示"""
        with self._lock:
            self._candidates = candidates[:9]  # 每行最多9个
            self._code = code
            self._page = page
            self._total_pages = max(1, total_pages)
            
            # 如果窗口不存在，先创建
            if self._window is None or not self._window.winfo_exists():
                self._create_window()
            
            if self._window and self._window.winfo_exists():
                self._window.after(0, self._update_ui)
    
    def is_visible(self) -> bool:
        return self._is_visible
    
    def _create_window(self):
        """创建 tkinter 窗口"""
        if self._root is None or not self._root.winfo_exists():
            self._root = tk.Tk()
            self._root.withdraw()  # 隐藏主窗口
        
        self._window = tk.Toplevel(self._root)
        self._window.overrideredirect(True)  # 无边框
        self._window.attributes('-topmost', True)  # 始终置顶
        self._window.configure(bg=self.BG_COLOR)
        self._window.withdraw()  # 初始隐藏
        
        # 创建主框架
        self._main_frame = tk.Frame(self._window, bg=self.BG_COLOR, padx=8, pady=6)
        self._main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 编码标签 (顶部)
        self._code_label = tk.Label(
            self._main_frame,
            text="",
            font=("Microsoft YaHei", 11, "bold"),
            fg=self.CODE_COLOR,
            bg=self.BG_COLOR,
            anchor=tk.W
        )
        self._code_label.pack(fill=tk.X, pady=(0, 4))
        
        # 分隔线
        self._separator = tk.Frame(self._main_frame, height=1, bg="#E0E0E0")
        self._separator.pack(fill=tk.X, pady=(0, 4))
        
        # 候选字容器
        self._candidates_frame = tk.Frame(self._main_frame, bg=self.BG_COLOR)
        self._candidates_frame.pack(fill=tk.X)
        
        # 候选字标签列表
        self._candidates_labels = []
        for i in range(9):
            frame = tk.Frame(self._candidates_frame, bg=self.BG_COLOR)
            frame.pack(side=tk.LEFT, padx=(0, 8))
            
            index_label = tk.Label(
                frame,
                text=f"{i+1}.",
                font=("Microsoft YaHei", 10),
                fg=self.INDEX_COLOR,
                bg=self.BG_COLOR
            )
            index_label.pack(side=tk.LEFT)
            
            char_label = tk.Label(
                frame,
                text="",
                font=("Microsoft YaHei", 14, "bold"),
                fg=self.CANDIDATE_COLOR,
                bg=self.BG_COLOR,
                cursor="hand2"
            )
            char_label.pack(side=tk.LEFT)
            
            # 绑定点击事件
            char_label.bind("<Button-1>", lambda e, idx=i: self._on_click(idx))
            index_label.bind("<Button-1>", lambda e, idx=i: self._on_click(idx))
            frame.bind("<Button-1>", lambda e, idx=i: self._on_click(idx))
            
            self._candidates_labels.append((frame, index_label, char_label))
        
        # 页码标签 (底部)
        self._page_label = tk.Label(
            self._main_frame,
            text="",
            font=("Microsoft YaHei", 9),
            fg=self.PAGE_COLOR,
            bg=self.BG_COLOR,
            anchor=tk.E
        )
        self._page_label.pack(fill=tk.X, pady=(4, 0))
        
        # 更新UI
        self._update_ui()
    
    def _on_click(self, index: int):
        """点击候选字回调"""
        if self._on_select and index < len(self._candidates):
            self._on_select(index)
    
    def _update_ui(self):
        """更新UI显示"""
        if self._window is None or not self._window.winfo_exists():
            return
        
        # 更新编码显示
        if self._code_label and self._code_label.winfo_exists():
            self._code_label.config(text=f"wubi: {self._code}")
        
        # 更新候选字显示
        for i, (frame, index_label, char_label) in enumerate(self._candidates_labels):
            if i < len(self._candidates):
                candidate = self._candidates[i]
                index_label.config(text=f"{i+1}.")
                # 第一个候选字用不同颜色高亮
                if i == 0:
                    char_label.config(text=candidate, fg=self.FIRST_CANDIDATE_COLOR)
                else:
                    char_label.config(text=candidate, fg=self.CANDIDATE_COLOR)
                frame.pack(side=tk.LEFT, padx=(0, 8))
            else:
                index_label.config(text="")
                char_label.config(text="")
                frame.pack_forget()
        
        # 更新页码显示
        if self._page_label and self._page_label.winfo_exists():
            self._page_label.config(text=f"[{self._page}/{self._total_pages}]")
        
        # 调整窗口大小
        self._window.update_idletasks()
        
        # 设置边框效果
        self._window.configure(
            highlightbackground="#BDBDBD",
            highlightthickness=1
        )
    
    def _run_in_ui_thread(self, func):
        """在 UI 线程中运行函数"""
        if self._window and self._window.winfo_exists():
            after_id = self._window.after(0, func)
            self._after_ids.append(after_id)
    
    def destroy(self):
        """销毁窗口"""
        with self._lock:
            # 取消所有待执行的 after 任务
            if self._window and self._window.winfo_exists():
                for after_id in self._after_ids:
                    try:
                        self._window.after_cancel(after_id)
                    except Exception:
                        pass
            self._after_ids.clear()
            
            if self._window and self._window.winfo_exists():
                self._window.destroy()
                self._window = None
            if self._root and self._root.winfo_exists():
                self._root.destroy()
                self._root = None
            self._is_visible = False
