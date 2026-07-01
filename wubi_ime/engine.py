"""五笔编码引擎

处理五笔编码的输入、匹配、候选词排序等逻辑。
"""

from enum import Enum, auto
from typing import List, Optional, Tuple
from .wubi_table import get_wubi_table, WubiTable

class Action(Enum):
    """按键动作枚举"""
    ADD_KEY = auto()         # 添加编码字符
    SELECT_CANDIDATE = auto() # 选择候选字
    DELETE = auto()           # 删除编码
    CANCEL = auto()           # 取消输入
    SUBMIT = auto()           # 提交当前输入
    SWITCH_MODE = auto()      # 切换中英文模式
    PAGE_UP = auto()          # 上翻页
    PAGE_DOWN = auto()        # 下翻页
    IGNORE = auto()           # 忽略此按键

class WubiEngine:
    """五笔编码引擎"""
    
    # 一级简码表（25个高频字，对应 25 个键位）
    FIRST_LEVEL_CODES = {
        'g': '一', 'f': '地', 'd': '在', 's': '要', 'a': '工',
        'h': '上', 'j': '是', 'k': '中', 'l': '国', 'm': '同',
        't': '和', 'r': '的', 'e': '有', 'w': '人', 'q': '我',
        'y': '主', 'u': '产', 'i': '不', 'o': '为', 'p': '这',
        'n': '民', 'b': '了', 'v': '发', 'c': '以', 'x': '经'
    }
    
    CANDIDATES_PER_PAGE = 9
    
    def __init__(self, table: Optional[WubiTable] = None):
        self.table = table or get_wubi_table()
        self._code = ""
        self._candidates: List[str] = []
        self._page = 0
        self._is_active = True
        self._is_chinese_mode = True
    
    @property
    def current_code(self) -> str:
        return self._code
    
    @property
    def current_candidates(self) -> List[str]:
        return self._get_page_candidates()
    
    def _get_page_candidates(self) -> List[str]:
        """获取当前页的候选字"""
        if not self._candidates:
            return []
        start = self._page * self.CANDIDATES_PER_PAGE
        end = start + self.CANDIDATES_PER_PAGE
        return self._candidates[start:end]
    
    def _update_candidates(self):
        """更新候选字列表"""
        if not self._code:
            self._candidates = []
        else:
            # Exact matches first
            exact = self.table.get_candidates(self._code)
            # Prefix matches
            prefix = self.table.get_candidates_by_prefix(self._code)
            
            # Combine: exact matches first (deduplicated), then prefix matches
            seen = set()
            self._candidates = []
            for c in exact:
                if c not in seen:
                    self._candidates.append(c)
                    seen.add(c)
            for c in prefix:
                if c not in seen:
                    self._candidates.append(c)
                    seen.add(c)
        self._page = 0
    
    def process_key(self, key: str) -> Tuple[Action, Optional[str]]:
        """处理按键输入
        
        Args:
            key: 按键字符，特殊键使用名称如 "space", "backspace", "esc", "pageup", "pagedown", "shift"
            
        Returns:
            (action, data): 动作类型和附加数据
        """
        if not self._is_active:
            return (Action.IGNORE, None)
        
        if not self._is_chinese_mode:
            return (Action.IGNORE, None)
        
        # Normalize key
        if len(key) == 1 and key.isalpha():
            key = key.lower()
        
        # Handle encoding letters (a-z)
        if len(key) == 1 and key.isalpha() and 'a' <= key <= 'z':
            # All a-z keys are buffered as encoding input
            # First-level short codes (e.g. 'w' -> '人') appear as the first candidate
            self._code += key
            self._update_candidates()
            
            # Auto-commit when full code (4 chars) has unique exact match
            if len(self._code) == 4:
                exact = self.table.get_candidates(self._code)
                if len(exact) == 1:
                    candidate = exact[0]
                    self.clear()
                    return (Action.SUBMIT, candidate)
            
            return (Action.ADD_KEY, None)
        
        # Handle digit keys (1-9)
        if len(key) == 1 and key.isdigit():
            idx = int(key) - 1
            page_candidates = self._get_page_candidates()
            if 0 <= idx < len(page_candidates):
                return (Action.SELECT_CANDIDATE, str(idx))
            return (Action.IGNORE, None)
        
        # Space: submit first candidate or current code
        if key == " " or key == "space":
            page_candidates = self._get_page_candidates()
            if page_candidates:
                self.clear()
                return (Action.SUBMIT, page_candidates[0])
            elif self._code:
                self.clear()
                return (Action.SUBMIT, self._code)
            else:
                return (Action.SUBMIT, " ")
        
        # Enter: submit first candidate or current code
        if key == "\r" or key == "\n" or key == "return":
            page_candidates = self._get_page_candidates()
            if page_candidates:
                self.clear()
                return (Action.SUBMIT, page_candidates[0])
            elif self._code:
                self.clear()
                return (Action.SUBMIT, self._code)
            return (Action.IGNORE, None)
        
        # Backspace: delete last code char
        if key == "\b" or key == "backspace":
            if self._code:
                self._code = self._code[:-1]
                self._update_candidates()
                return (Action.DELETE, None)
            return (Action.IGNORE, None)
        
        # Esc: cancel input
        if key == "\x1b" or key == "esc":
            self.clear()
            return (Action.CANCEL, None)
        
        # PageUp / +: previous page
        if key == "pageup" or key == "+":
            if self._page > 0:
                self._page -= 1
            return (Action.PAGE_UP, None)
        
        # PageDown / -: next page
        if key == "pagedown" or key == "-":
            total_pages = self.get_page_info()[1]
            if self._page < total_pages - 1:
                self._page += 1
            return (Action.PAGE_DOWN, None)
        
        # Shift (alone): switch mode
        if key == "shift":
            return (Action.SWITCH_MODE, None)
        
        return (Action.IGNORE, None)
    
    def select_candidate(self, index: int) -> Optional[str]:
        """选择候选字，返回要输出的汉字"""
        page_candidates = self._get_page_candidates()
        if 0 <= index < len(page_candidates):
            candidate = page_candidates[index]
            self.clear()
            return candidate
        return None
    
    def clear(self):
        """清空当前编码"""
        self._code = ""
        self._candidates = []
        self._page = 0
    
    def toggle_mode(self):
        """切换中英文模式"""
        self._is_chinese_mode = not self._is_chinese_mode
    
    def is_active(self) -> bool:
        return self._is_active
    
    def activate(self):
        self._is_active = True
    
    def deactivate(self):
        self._is_active = False
        self.clear()
    
    def is_chinese_mode(self) -> bool:
        return self._is_chinese_mode
    
    def get_page_info(self) -> Tuple[int, int]:
        """返回当前页码和总页数"""
        if not self._candidates:
            return (0, 0)
        total_pages = (len(self._candidates) + self.CANDIDATES_PER_PAGE - 1) // self.CANDIDATES_PER_PAGE
        return (self._page, total_pages)
