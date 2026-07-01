"""五笔编码表模块

管理汉字到五笔编码的映射关系。
"""

import json
import os
from typing import Dict, List, Optional, Union

class WubiTable:
    """五笔编码表管理类"""
    
    # 一级简码表（25个高频字，对应 25 个键位）
    FIRST_LEVEL_CODES = {
        'g': '一', 'f': '地', 'd': '在', 's': '要', 'a': '工',
        'h': '上', 'j': '是', 'k': '中', 'l': '国', 'm': '同',
        't': '和', 'r': '的', 'e': '有', 'w': '人', 'q': '我',
        'y': '主', 'u': '产', 'i': '不', 'o': '为', 'p': '这',
        'n': '民', 'b': '了', 'v': '发', 'c': '以', 'x': '经'
    }
    
    def __init__(self, data_path: Optional[str] = None):
        self.char_to_code: Dict[str, Union[str, List[str]]] = {}
        self.code_to_chars: Dict[str, List[str]] = {}
        self._load(data_path)
    
    def _load(self, data_path: Optional[str] = None):
        """加载五笔编码表，兼容 PyInstaller 打包环境"""
        if data_path is None:
            # PyInstaller 打包环境：资源文件在 sys._MEIPASS 中
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
                # 尝试多个可能的路径
                candidates = [
                    os.path.join(base_dir, "wubi_ime", "data", "wubi_86.json"),
                    os.path.join(base_dir, "data", "wubi_86.json"),
                ]
                for c in candidates:
                    if os.path.exists(c):
                        data_path = c
                        break
            
            # 开发环境：从当前模块所在目录查找
            if data_path is None:
                module_dir = os.path.dirname(os.path.abspath(__file__))
                data_path = os.path.join(module_dir, "data", "wubi_86.json")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            self.char_to_code = json.load(f)
        
        # Build reverse mapping: code -> list of chars
        # Preserve order from JSON (which is weight-ordered from rime dict)
        for char, codes in self.char_to_code.items():
            if isinstance(codes, str):
                codes = [codes]
            for code in codes:
                if code not in self.code_to_chars:
                    self.code_to_chars[code] = []
                if char not in self.code_to_chars[code]:
                    self.code_to_chars[code].append(char)
    
    def get_char_code(self, char: str) -> Optional[str]:
        """获取汉字的五笔编码（返回主编码，即权重最高的）"""
        codes = self.char_to_code.get(char)
        if isinstance(codes, list):
            return codes[0] if codes else None
        return codes
    
    def get_char_codes(self, char: str) -> List[str]:
        """获取汉字的所有五笔编码"""
        codes = self.char_to_code.get(char)
        if codes is None:
            return []
        if isinstance(codes, str):
            return [codes]
        return codes
    
    def get_candidates(self, code: str) -> List[str]:
        """根据编码精确匹配获取候选字列表（按使用频率排序）"""
        return self.code_to_chars.get(code, [])
    
    def get_candidates_by_prefix(self, prefix: str) -> List[str]:
        """根据编码前缀获取候选字列表（用于编码过程中的实时匹配）"""
        if not prefix:
            return []
        
        result = []
        seen = set()
        # Iterate through all entries to preserve weight order
        for char, codes in self.char_to_code.items():
            if isinstance(codes, str):
                codes = [codes]
            for code in codes:
                if code.startswith(prefix):
                    if char not in seen:
                        result.append(char)
                        seen.add(char)
                    break  # Once matched for this char, move to next
        return result
    
    def get_first_level(self, code: str) -> Optional[str]:
        """查询一级简码"""
        return self.FIRST_LEVEL_CODES.get(code)
    
    def get_second_level(self, code: str) -> List[str]:
        """查询二级简码（编码长度为2）"""
        if len(code) != 2:
            return []
        return self.code_to_chars.get(code, [])
    
    def get_all_first_level(self) -> Dict[str, str]:
        """获取所有一级简码"""
        return self.FIRST_LEVEL_CODES.copy()

# 全局编码表实例
_default_table: Optional[WubiTable] = None

def get_wubi_table() -> WubiTable:
    """获取全局编码表实例"""
    global _default_table
    if _default_table is None:
        _default_table = WubiTable()
    return _default_table
