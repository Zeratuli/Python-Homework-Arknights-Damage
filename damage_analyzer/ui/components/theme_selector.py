# theme_selector.py - 主题选择组件

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from typing import Dict, Callable, Optional

class ThemeSelector(ttk.Frame):
    """主题选择组件"""
    
    def __init__(self, parent, theme_manager, config_manager, on_change_callback=None):
        """
        初始化主题选择器
        
        Args:
            parent: 父容器
            theme_manager: 主题管理器
            config_manager: 配置管理器  
            on_change_callback: 主题变更回调函数
        """
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        
        # 存储组件引用
        self.theme_combobox = None
        self.preview_label = None
        
        # 设置UI
        self.setup_ui()
        
        # 加载当前主题
        self.load_current_theme()
    
    def setup_ui(self):
        """创建界面"""
        # 主标题
        title_label = ttk.Label(self, text="主题选择", font=('微软雅黑', 12, 'bold'))
        title_label.pack(anchor=W, pady=(0, 10))
        
        # 主题预览区域
        preview_frame = ttk.LabelFrame(self, text="主题预览", padding=10)
        preview_frame.pack(fill=X, pady=(0, 10))
        
        # 当前主题显示
        self.preview_label = ttk.Label(
            preview_frame, 
            text="当前主题: Cosmo (默认浅色)",
            font=('微软雅黑', 10),
            bootstyle=INFO
        )
        self.preview_label.pack(anchor=W)
        
        # 主题选择区域
        selection_frame = ttk.LabelFrame(self, text="选择主题", padding=10)
        selection_frame.pack(fill=X, pady=(0, 10))
        
        # 主题选择标签
        ttk.Label(selection_frame, text="主题:").pack(anchor=W, pady=(0, 5))
        
        # 主题下拉框
        themes = self.theme_manager.get_available_themes()
        theme_names = [self.theme_manager.get_theme_display_name(theme) for theme in themes]
        
        self.theme_combobox = ttk.Combobox(
            selection_frame,
            values=theme_names,
            state='readonly',
            width=30
        )
        self.theme_combobox.pack(fill=X, pady=(0, 10))
        self.theme_combobox.bind('<<ComboboxSelected>>', self.on_theme_change)
        
        # 按钮区域
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill=X)
        
        # 预览按钮
        preview_btn = ttk.Button(
            button_frame,
            text="🔍 预览",
            bootstyle=INFO,
            command=self.preview_theme
        )
        preview_btn.pack(side=LEFT, padx=(0, 5))
        
        # 应用按钮
        apply_btn = ttk.Button(
            button_frame,
            text="✅ 应用",
            bootstyle=SUCCESS,
            command=self.apply_selected_theme
        )
        apply_btn.pack(side=LEFT)
    
    def load_current_theme(self):
        """加载当前主题"""
        try:
            # 从配置获取当前主题
            ui_settings = self.config_manager.get_ui_settings()
            current_theme = ui_settings.get('theme', 'cosmo')
            
            # 更新主题管理器
            self.theme_manager.current_theme = current_theme
            
            # 在下拉框中选择对应项
            themes = self.theme_manager.get_available_themes()
            if current_theme in themes:
                index = themes.index(current_theme)
                theme_names = [self.theme_manager.get_theme_display_name(theme) for theme in themes]
                self.theme_combobox.current(index)
                
                # 更新预览标签
                display_name = self.theme_manager.get_theme_display_name(current_theme)
                self.preview_label.configure(text=f"当前主题: {display_name}")
        
        except Exception as e:
            print(f"加载主题失败: {e}")
    
    def on_theme_change(self, event=None):
        """主题变更处理"""
        selected_index = self.theme_combobox.current()
        if selected_index >= 0:
            themes = self.theme_manager.get_available_themes()
            selected_theme = themes[selected_index]
            
            # 更新预览标签
            display_name = self.theme_manager.get_theme_display_name(selected_theme)
            self.preview_label.configure(
                text=f"预览主题: {display_name}",
                bootstyle=WARNING
            )
    
    def preview_theme(self):
        """预览主题效果"""
        selected_theme = self.get_selected_theme()
        if selected_theme:
            try:
                # 临时应用主题进行预览
                display_name = self.theme_manager.get_theme_display_name(selected_theme)
                self.preview_label.configure(
                    text=f"正在预览: {display_name}",
                    bootstyle=INFO
                )
                
                # 这里可以添加更多预览效果
                print(f"预览主题: {selected_theme}")
                
            except Exception as e:
                print(f"预览主题失败: {e}")
    
    def apply_selected_theme(self):
        """应用选中的主题"""
        selected_theme = self.get_selected_theme()
        if selected_theme:
            try:
                # 应用主题
                self.theme_manager.apply_theme(selected_theme)
                
                # 保存到配置
                self.config_manager.update_ui_settings({'theme': selected_theme})
                
                # 更新预览标签
                display_name = self.theme_manager.get_theme_display_name(selected_theme)
                self.preview_label.configure(
                    text=f"当前主题: {display_name}",
                    bootstyle=SUCCESS
                )
                
                # 触发外部回调
                if self.on_change_callback:
                    self.on_change_callback(selected_theme)
                
                print(f"应用主题成功: {selected_theme}")
                
            except Exception as e:
                print(f"应用主题失败: {e}")
    
    def get_selected_theme(self) -> Optional[str]:
        """获取选中主题"""
        selected_index = self.theme_combobox.current()
        if selected_index >= 0:
            themes = self.theme_manager.get_available_themes()
            return themes[selected_index]
        return None 