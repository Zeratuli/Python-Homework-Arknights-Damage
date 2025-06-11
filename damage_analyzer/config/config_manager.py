# config_manager.py - 极简的配置管理器

import json
import os
from typing import Any, Dict
from pathlib import Path

class ConfigManager:
    """极简的配置管理器"""
    
    def __init__(self):
        # 设置配置文件路径
        config_dir = os.path.dirname(__file__)
        self.config_file = os.path.join(config_dir, 'app_config.json')
        
        # 默认配置
        self.default_config = {
            'app_name': '塔防游戏伤害分析器',
            'version': '2.0.0',
            'theme': 'litera',
            'window_size': [1200, 800],
            'default_enemy_def': 300,
            'default_enemy_mdef': 30,
            'ui_settings': {
                'theme': 'cosmo',
                'font_size_preset': 'medium',
                'font_family': '微软雅黑',
                'custom_font_scale': 1.0
            }
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 使用默认值填充缺失项
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
        except Exception:
            pass
        
        return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """获取UI设置"""
        return self.config.get('ui_settings', self.default_config['ui_settings']).copy()
    
    def update_ui_settings(self, settings_dict: Dict[str, Any]):
        """批量更新UI设置"""
        if 'ui_settings' not in self.config:
            self.config['ui_settings'] = self.default_config['ui_settings'].copy()
        
        self.config['ui_settings'].update(settings_dict)
        self.save_config()
    
    def get_available_themes(self) -> list:
        """获取可用主题列表"""
        return ['cosmo', 'flatly', 'litera', 'minty', 'lux', 'sandstone', 'yeti', 
                'pulse', 'united', 'morph', 'journal', 'darkly', 'superhero', 
                'solar', 'cyborg', 'vapor']
    
    def get_available_font_presets(self) -> Dict[str, str]:
        """获取可用字号预设"""
        return {
            'extra_small': '超小',
            'small': '小',
            'medium': '中等',
            'large': '大',
            'extra_large': '超大'
        }

# 全局配置管理器实例
config_manager = ConfigManager()