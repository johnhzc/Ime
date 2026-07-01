"""配置管理模块

管理输入法的配置项，如热键、候选词数量、词库路径等。
"""

import json
import os
from typing import Dict, Any, Optional

# 默认配置
DEFAULT_CONFIG = {
    "activation_hotkey": "ctrl+shift+w",
    "candidates_per_page": 9,
    "wubi_table_path": None,  # 使用内置编码表
    "user_dict_path": "user_dict.json",
    "auto_commit_single": True,  # 单字是否自动提交
    "show_status_window": True,
    "theme": "default",
}


class Config:
    """配置管理类"""
    
    CONFIG_FILE = "wubi_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or self.CONFIG_FILE
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """从文件加载配置"""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._config = DEFAULT_CONFIG.copy()
                    self._config.update(loaded)
            except Exception:
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
    
    def save(self):
        """保存配置到文件"""
        try:
            dir_path = os.path.dirname(self._config_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self._config[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """支持 dict 风格的读取"""
        return self._config.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """支持 dict 风格的写入"""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return key in self._config
    
    @property
    def config_path(self) -> str:
        """获取配置文件路径"""
        return self._config_path
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置的副本"""
        return self._config.copy()
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = DEFAULT_CONFIG.copy()
