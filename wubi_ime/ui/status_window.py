"""状态窗口 UI

显示输入法状态（中文/英文、全角/半角等）。
"""

import tkinter as tk
import threading
from typing import Optional, Callable


class StatusWindow:
    """输入法状态窗口"""

    # 颜色配置
    CHINESE_BG = "#4CAF50"  # 中文模式背景 (绿色)
    ENGLISH_BG = "#9E9E9E"  # 英文模式背景 (灰色)
    FULLWIDTH_BG = "#FF9800"  # 全角背景 (橙色)
    TEXT_COLOR = "#FFFFFF"  # 文字颜色 (白色)
    BG_COLOR = "#F5F5F5"  # 窗口背景

    def __init__(self, master=None, on_click: Optional[Callable] = None):
        self._root = master  # 共享的根窗口
        self._window: Optional[tk.Toplevel] = None
        self._is_chinese = True
        self._is_fullwidth = False
        self._label: Optional[tk.Label] = None
        self._on_click = on_click
        self._lock = threading.Lock()
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

    def show(self):
        """显示状态窗口"""
        with self._lock:
            if self._window is None or not self._window.winfo_exists():
                self._create_window()

            if self._window:
                self._window.deiconify()
                self._window.lift()
                self._window.attributes('-topmost', True)

    def hide(self):
        """隐藏状态窗口"""
        with self._lock:
            if self._window and self._window.winfo_exists():
                self._window.withdraw()

    def set_chinese_mode(self, is_chinese: bool):
        """设置中文/英文模式显示"""
        with self._lock:
            self._is_chinese = is_chinese
            if self._label and self._label.winfo_exists():
                self._update_display()

    def set_fullwidth_mode(self, is_fullwidth: bool):
        """设置全角/半角模式显示"""
        with self._lock:
            self._is_fullwidth = is_fullwidth
            if self._label and self._label.winfo_exists():
                self._update_display()

    def _create_window(self):
        """创建状态窗口"""
        if self._root is None or not self._root.winfo_exists():
            self._root = tk.Tk()
            self._root.withdraw()

        self._window = tk.Toplevel(self._root)
        self._window.overrideredirect(True)  # 无边框
        self._window.attributes('-topmost', True)  # 始终置顶
        self._window.configure(bg=self.BG_COLOR)

        # 设置窗口大小
        width = 80
        height = 30

        # 计算屏幕右下角位置
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()
        x = screen_width - width - 20
        y = screen_height - height - 60

        self._window.geometry(f"{width}x{height}+{x}+{y}")

        # 创建主框架
        main_frame = tk.Frame(self._window, bg=self.BG_COLOR, padx=1, pady=1)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 状态标签
        self._label = tk.Label(
            main_frame,
            text="中",
            font=("Microsoft YaHei", 12, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.CHINESE_BG,
            width=4,
            height=1,
            cursor="hand2"
        )
        self._label.pack(fill=tk.BOTH, expand=True)

        # 绑定点击事件
        self._label.bind("<Button-1>", self._on_mouse_click)
        self._label.bind("<B1-Motion>", self._on_mouse_drag)
        self._label.bind("<ButtonRelease-1>", self._on_mouse_release)
        self._window.bind("<Button-1>", self._on_mouse_click)
        self._window.bind("<B1-Motion>", self._on_mouse_drag)
        self._window.bind("<ButtonRelease-1>", self._on_mouse_release)

    def _update_display(self):
        """更新显示内容"""
        if self._label is None or not self._label.winfo_exists():
            return

        if self._is_chinese:
            if self._is_fullwidth:
                text = "全"
                bg = self.FULLWIDTH_BG
            else:
                text = "中"
                bg = self.CHINESE_BG
        else:
            if self._is_fullwidth:
                text = "全"
                bg = self.FULLWIDTH_BG
            else:
                text = "英"
                bg = self.ENGLISH_BG

        self._label.config(text=text, bg=bg)

    def _on_mouse_click(self, event):
        """鼠标点击处理"""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._is_dragging = False

    def _on_mouse_drag(self, event):
        """鼠标拖动处理"""
        self._is_dragging = True
        if self._window and self._window.winfo_exists():
            x = self._window.winfo_x() + event.x - self._drag_start_x
            y = self._window.winfo_y() + event.y - self._drag_start_y
            self._window.geometry(f"+{x}+{y}")

    def _on_mouse_release(self, event):
        """鼠标释放处理"""
        if not self._is_dragging:
            # 如果不是拖动，则认为是点击
            if self._on_click:
                self._on_click()
            else:
                # 默认切换中英文模式
                self._is_chinese = not self._is_chinese
                self._update_display()
        self._is_dragging = False

    def destroy(self):
        """销毁窗口"""
        with self._lock:
            if self._window and self._window.winfo_exists():
                self._window.destroy()
                self._window = None
            # 共享根窗口由主程序统一销毁，这里不销毁
