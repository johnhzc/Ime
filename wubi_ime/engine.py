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
        pass
    
    def process_key(self, key: str) -> Tuple[Action, Optional[str]]:
        """处理按键输入
        
        Returns:
            (action, data): 动作类型和附加数据
        """
        pass
    
    def select_candidate(self, index: int) -> Optional[str]:
        """选择候选字，返回要输出的汉字"""
        pass
    
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
        pass
