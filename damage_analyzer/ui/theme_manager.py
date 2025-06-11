# theme_manager.py - 简化的主题管理器

import ttkbootstrap as ttk
from typing import List, Dict, Callable, Optional

class ThemeManager:
    """简化的主题管理器"""
    
    def __init__(self):
        """初始化主题管理器"""
        # 支持的主题列表
        self.available_themes = [
            'cosmo', 'flatly', 'litera', 'minty', 'lux', 'sandstone', 'yeti', 
            'pulse', 'united', 'morph', 'journal', 'darkly', 'superhero', 
            'solar', 'cyborg', 'vapor'
        ]
        
        # 主题显示名称映射
        self.theme_display_names = {
            'cosmo': 'Cosmo (默认浅色)',
            'flatly': 'Flatly (扁平浅色)',
            'litera': 'Litera (文学风格)',
            'minty': 'Minty (薄荷绿)',
            'lux': 'Lux (豪华风格)',
            'sandstone': 'Sandstone (沙石风格)',
            'yeti': 'Yeti (雪白主题)',
            'pulse': 'Pulse (脉冲紫)',
            'united': 'United (联合橙)',
            'morph': 'Morph (变形风格)',
            'journal': 'Journal (期刊风格)',
            'darkly': 'Darkly (深色主题)',
            'superhero': 'Superhero (超级英雄)',
            'solar': 'Solar (太阳能黄)',
            'cyborg': 'Cyborg (机械风格)',
            'vapor': 'Vapor (蒸汽波)'
        }
        
        # 当前主题
        self.current_theme = 'cosmo'
        
        # 主题变更回调
        self.theme_change_callback: Optional[Callable] = None
    
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return self.available_themes
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme
    
    def get_theme_display_name(self, theme_name: str) -> str:
        """获取主题显示名称"""
        return self.theme_display_names.get(theme_name, theme_name.title())
    
    def set_theme_change_callback(self, callback_func: Callable):
        """设置主题变更回调函数"""
        self.theme_change_callback = callback_func
    
    def apply_theme(self, theme_name: str) -> bool:
        """应用主题"""
        if theme_name in self.available_themes:
            self.current_theme = theme_name
            # 触发回调
            if self.theme_change_callback:
                try:
                    self.theme_change_callback(theme_name)
                except Exception as e:
                    print(f"主题回调执行失败: {e}")
            return True
        return False
    
    def apply_theme_to_window(self, window, theme_name: str) -> bool:
        """应用主题到指定窗口"""
        if theme_name in self.available_themes:
            try:
                # 如果窗口有style属性，更新主题
                if hasattr(window, 'style'):
                    window.style.theme_use(theme_name)
                # 对于ttk.Window类型，直接设置主题
                elif hasattr(window, 'style') or isinstance(window, ttk.Window):
                    style = ttk.Style()
                    style.theme_use(theme_name)
                
                self.current_theme = theme_name
                return True
            except Exception as e:
                print(f"应用主题到窗口失败: {e}")
                return False
        return False 