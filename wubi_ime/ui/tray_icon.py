"""系统托盘图标模块

使用 pystray 在 Windows 11 系统托盘显示输入法图标，
提供右键菜单、状态切换、退出等功能。
"""

import threading
from typing import Optional, Callable
from PIL import Image, ImageDraw

try:
    import pystray
except ImportError:
    pystray = None


def create_icon_image(color: str = "#2196F3") -> Image.Image:
    """创建输入法图标（256x256 圆角正方形）"""
    width = 256
    height = 256
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆角矩形背景
    radius = 48
    draw.rounded_rectangle(
        [(0, 0), (width-1, height-1)],
        radius=radius,
        fill=color
    )
    
    # 绘制文字 "五"（白色）
    # 由于没有字体，绘制简单的 "五" 字形
    margin = 60
    cx, cy = width // 2, height // 2
    # 横线
    draw.rectangle([(margin, cy-20), (width-margin, cy+20)], fill="white")
    # 竖线
    draw.rectangle([(cx-20, margin), (cx+20, height-margin)], fill="white")
    # 底横
    draw.rectangle([(margin, height-margin-30), (width-margin, height-margin+10)], fill="white")
    
    return img


class TrayIcon:
    """系统托盘图标管理器"""
    
    def __init__(self, 
                 on_toggle: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None):
        self._icon = None
        self._on_toggle = on_toggle
        self._on_exit = on_exit
        self._is_active = False
        self._is_chinese = True
        self._lock = threading.Lock()
        
    def start(self):
        """启动系统托盘图标"""
        if pystray is None:
            print("警告: pystray 未安装，系统托盘图标不可用")
            print("请运行: pip install pystray pillow")
            return
            
        try:
            # 创建托盘图标
            icon_img = create_icon_image("#2196F3" if self._is_chinese else "#9E9E9E")
            
            self._icon = pystray.Icon(
                name="WubiIME",
                icon=icon_img,
                title="五笔输入法 (Ctrl+Shift+W)",
                menu=self._create_menu()
            )
            
            # 在后台线程运行托盘图标
            threading.Thread(target=self._icon.run, daemon=True).start()
            
        except Exception as e:
            print(f"系统托盘启动失败: {e}")
    
    def stop(self):
        """停止系统托盘图标"""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
    
    def set_active(self, active: bool):
        """设置输入法激活状态"""
        self._is_active = active
        self._update_title()
    
    def set_chinese_mode(self, is_chinese: bool):
        """设置中文/英文模式"""
        self._is_chinese = is_chinese
        self._update_icon()
        self._update_title()
    
    def _update_icon(self):
        """更新图标颜色"""
        if self._icon is None:
            return
        try:
            color = "#2196F3" if self._is_chinese else "#9E9E9E"
            self._icon.icon = create_icon_image(color)
        except Exception:
            pass
    
    def _update_title(self):
        """更新托盘提示文字"""
        if self._icon is None:
            return
        try:
            status = "已激活" if self._is_active else "已关闭"
            mode = "中文" if self._is_chinese else "英文"
            self._icon.title = f"五笔输入法 [{status}] {mode}模式 (Ctrl+Shift+W)"
        except Exception:
            pass
    
    def _create_menu(self):
        """创建右键菜单"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda text: f"{'✓ ' if self._is_active else ''}激活输入法",
                self._on_toggle_click
            ),
            pystray.MenuItem(
                lambda text: f"{'✓ ' if self._is_chinese else ''}中文模式",
                self._on_chinese_click
            ),
            pystray.MenuItem(
                lambda text: f"{'✓ ' if not self._is_chinese else ''}英文模式",
                self._on_english_click
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._on_exit_click)
        )
    
    def _on_toggle_click(self, icon, item):
        """切换激活状态"""
        if self._on_toggle:
            self._on_toggle()
    
    def _on_chinese_click(self, icon, item):
        """切换到中文模式"""
        if self._is_chinese:
            return
        if self._on_toggle:
            self._on_toggle()  # 通过切换实现
    
    def _on_english_click(self, icon, item):
        """切换到英文模式"""
        if not self._is_chinese:
            return
        if self._on_toggle:
            self._on_toggle()
    
    def _on_exit_click(self, icon, item):
        """退出程序"""
        if self._on_exit:
            self._on_exit()


class DummyTrayIcon:
    """当 pystray 不可用时使用的虚拟托盘图标"""
    
    def __init__(self, **kwargs):
        pass
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def set_active(self, active: bool):
        pass
    
    def set_chinese_mode(self, is_chinese: bool):
        pass


def get_tray_icon(**kwargs):
    """获取可用的托盘图标实现"""
    if pystray is not None:
        return TrayIcon(**kwargs)
    return DummyTrayIcon(**kwargs)
