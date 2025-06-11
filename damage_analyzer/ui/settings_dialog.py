# settings_dialog.py - 设置对话框

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from typing import Dict, Callable, Optional
from .components.theme_selector import ThemeSelector
from .components.font_size_selector import FontSizeSelector

class SettingsDialog(ttk.Toplevel):
    """设置对话框"""
    
    def __init__(self, parent, config_manager, theme_manager, font_manager):
        """
        初始化设置对话框
        
        Args:
            parent: 父窗口
            config_manager: 配置管理器
            theme_manager: 主题管理器
            font_manager: 字体管理器
        """
        super().__init__(parent)
        
        self.parent_window = parent
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.font_manager = font_manager
        
        # 存储原始设置以便取消时恢复
        self.original_settings = self.config_manager.get_ui_settings()
        
        # 存储组件引用
        self.category_tree = None
        self.content_frame = None
        self.theme_selector = None
        self.font_selector = None
        self.current_panel = None
        
        # 设置对话框属性
        self.setup_dialog_properties()
        
        # 创建界面
        self.setup_ui()
        
        # 居中显示
        self.center_dialog()
    
    def setup_dialog_properties(self):
        """设置对话框属性"""
        self.title("设置 - 塔防游戏伤害分析器")
        self.geometry("600x500")
        self.resizable(True, True)
        self.minsize(500, 400)
        
        # 设置模态
        self.transient(self.parent_window)
        self.grab_set()
        
        # 设置关闭事件
        self.protocol("WM_DELETE_WINDOW", self.cancel_and_close)
    
    def setup_ui(self):
        """创建主界面"""
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # 使用 Notebook 替代 PanedWindow，避免布局问题
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 创建主题设置标签页
        self.create_theme_tab()
        
        # 创建字体设置标签页
        self.create_font_tab()
        
        # 底部按钮栏
        self.create_button_bar(main_frame)
    
    def create_theme_tab(self):
        """创建主题设置标签页"""
        theme_frame = ttk.Frame(self.notebook)
        self.notebook.add(theme_frame, text="🎨 主题")
        
        # 创建主题选择器
        self.theme_selector = ThemeSelector(
            theme_frame,
            self.theme_manager,
            self.config_manager,
            self.on_theme_change
        )
        self.theme_selector.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    def create_font_tab(self):
        """创建字体设置标签页"""
        font_frame = ttk.Frame(self.notebook)
        self.notebook.add(font_frame, text="🔤 字体")
        
        # 创建字体选择器
        self.font_selector = FontSizeSelector(
            font_frame,
            self.font_manager,
            self.config_manager,
            self.on_font_change
        )
        self.font_selector.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    def create_category_tree(self, parent):
        """创建分类树（已废弃，使用Notebook代替）"""
        pass
    
    def create_button_bar(self, parent):
        """创建底部按钮栏"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, pady=(10, 0))
        
        # 右侧按钮组
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=RIGHT)
        
        # 确定按钮
        ok_btn = ttk.Button(
            right_buttons,
            text="确定",
            bootstyle=SUCCESS,
            command=self.save_and_close,
            width=8
        )
        ok_btn.pack(side=RIGHT, padx=(5, 0))
        
        # 取消按钮
        cancel_btn = ttk.Button(
            right_buttons,
            text="取消",
            bootstyle=SECONDARY,
            command=self.cancel_and_close,
            width=8
        )
        cancel_btn.pack(side=RIGHT, padx=(5, 0))
        
        # 应用按钮
        apply_btn = ttk.Button(
            right_buttons,
            text="应用",
            bootstyle=PRIMARY,
            command=self.apply_settings,
            width=8
        )
        apply_btn.pack(side=RIGHT, padx=(5, 0))
        
        # 左侧按钮组
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=LEFT)
        
        # 重置按钮
        reset_btn = ttk.Button(
            left_buttons,
            text="🔄 重置",
            bootstyle=WARNING,
            command=self.reset_to_defaults,
            width=10
        )
        reset_btn.pack(side=LEFT)
    
    def on_category_select(self, event=None):
        """分类选择处理（已废弃，使用Notebook代替）"""
        pass
    
    def show_appearance_panel(self):
        """显示外观设置面板（已废弃，使用Notebook代替）"""
        pass
    
    def show_font_panel(self):
        """显示字体设置面板（已废弃，使用Notebook代替）"""
        pass
    
    def clear_content_frame(self):
        """清空内容区域（已废弃，使用Notebook代替）"""
        pass
    
    def on_theme_change(self, theme_name):
        """主题变更回调"""
        try:
            # 立即应用主题到当前对话框
            self.theme_manager.apply_theme_to_window(self, theme_name)
            print(f"设置对话框主题变更: {theme_name}")
        except Exception as e:
            print(f"主题变更回调失败: {e}")
    
    def on_font_change(self, font_settings):
        """字体变更回调"""
        try:
            # 可以在这里添加实时字体应用逻辑
            print(f"设置对话框字体变更: {font_settings}")
        except Exception as e:
            print(f"字体变更回调失败: {e}")
    
    def apply_settings(self):
        """应用设置"""
        try:
            current_settings = self.collect_all_settings()
            
            # 更新配置
            self.config_manager.update_ui_settings(current_settings)
            
            # 应用到主题管理器
            if 'theme' in current_settings:
                self.theme_manager.apply_theme(current_settings['theme'])
            
            # 使用安全的字体应用方法
            font_settings = {k: v for k, v in current_settings.items() 
                           if k in ['font_size_preset', 'custom_font_scale', 'font_family']}
            if font_settings:
                self.font_manager.apply_font_settings_safely(font_settings)
            
            print("设置应用成功")
            
        except Exception as e:
            print(f"应用设置失败: {e}")
            tk.messagebox.showerror("错误", f"应用设置失败: {str(e)}")
    
    def save_and_close(self):
        """保存并关闭"""
        try:
            self.apply_settings()
            self.destroy()
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def cancel_and_close(self):
        """取消并关闭"""
        try:
            # 恢复原始设置
            self.config_manager.update_ui_settings(self.original_settings)
            
            # 恢复主题和字体
            original_theme = self.original_settings.get('theme', 'cosmo')
            self.theme_manager.apply_theme(original_theme)
            
            # 使用安全的方法恢复字体设置
            original_font_settings = {
                'font_size_preset': self.original_settings.get('font_size_preset', 'medium'),
                'custom_font_scale': self.original_settings.get('custom_font_scale', 1.0),
                'font_family': self.original_settings.get('font_family', '微软雅黑')
            }
            self.font_manager.apply_font_settings_safely(original_font_settings)
            
            self.destroy()
            
        except Exception as e:
            print(f"取消设置失败: {e}")
            self.destroy()
    
    def reset_to_defaults(self):
        """重置为默认值"""
        try:
            # 确认对话框
            result = tk.messagebox.askyesno(
                "确认重置",
                "确定要重置所有设置为默认值吗？",
                parent=self
            )
            
            if result:
                # 重置配置
                default_ui_settings = {
                    'theme': 'cosmo',
                    'font_size_preset': 'medium',
                    'font_family': '微软雅黑',
                    'custom_font_scale': 1.0
                }
                
                self.config_manager.update_ui_settings(default_ui_settings)
                
                # 重置管理器
                self.theme_manager.apply_theme('cosmo')
                
                # 使用安全的方法重置字体
                default_font_settings = {
                    'font_size_preset': 'medium',
                    'custom_font_scale': 1.0,
                    'font_family': '微软雅黑'
                }
                self.font_manager.apply_font_settings_safely(default_font_settings)
                
                # 刷新当前面板
                if self.current_panel == 'appearance' and self.theme_selector:
                    self.theme_selector.load_current_theme()
                elif self.current_panel == 'font' and self.font_selector:
                    self.font_selector.load_current_settings()
                
                print("设置已重置为默认值")
                
        except Exception as e:
            print(f"重置设置失败: {e}")
    
    def collect_all_settings(self) -> Dict[str, any]:
        """收集所有设置"""
        settings = {}
        
        try:
            # 收集主题设置
            if self.theme_selector:
                selected_theme = self.theme_selector.get_selected_theme()
                if selected_theme:
                    settings['theme'] = selected_theme
            
            # 收集字体设置
            if self.font_selector:
                font_settings = self.font_selector.get_current_settings()
                settings.update(font_settings)
            
            return settings
            
        except Exception as e:
            print(f"收集设置失败: {e}")
            return {}
    
    def center_dialog(self):
        """居中显示对话框"""
        self.update_idletasks()
        
        # 获取对话框尺寸
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        # 获取父窗口位置和尺寸
        parent_x = self.parent_window.winfo_x()
        parent_y = self.parent_window.winfo_y()
        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}") 