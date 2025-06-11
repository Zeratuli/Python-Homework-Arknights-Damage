# font_size_selector.py - 字号选择组件

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from typing import Dict, Callable, Optional

class FontSizeSelector(ttk.Frame):
    """字号选择组件"""
    
    def __init__(self, parent, font_manager, config_manager, on_change_callback=None):
        """
        初始化字号选择器
        
        Args:
            parent: 父容器
            font_manager: 字体管理器
            config_manager: 配置管理器
            on_change_callback: 字体变更回调函数
        """
        super().__init__(parent)
        
        self.font_manager = font_manager
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        
        # 存储组件引用
        self.preset_combobox = None
        self.scale_var = None
        self.scale_widget = None
        self.preview_label = None
        self.info_label = None
        
        # 设置UI
        self.setup_ui()
        
        # 加载当前设置
        self.load_current_settings()
    
    def setup_ui(self):
        """创建界面"""
        # 主标题
        title_label = ttk.Label(self, text="字号设置", font=('微软雅黑', 12, 'bold'))
        title_label.pack(anchor=W, pady=(0, 10))
        
        # 预设字号选择区域
        preset_frame = ttk.LabelFrame(self, text="预设字号", padding=10)
        preset_frame.pack(fill=X, pady=(0, 10))
        
        # 预设字号标签
        ttk.Label(preset_frame, text="字号预设:").pack(anchor=W, pady=(0, 5))
        
        # 预设字号下拉框
        presets = self.font_manager.get_available_presets()
        preset_names = list(presets.values())
        
        self.preset_combobox = ttk.Combobox(
            preset_frame,
            values=preset_names,
            state='readonly',
            width=20
        )
        self.preset_combobox.pack(fill=X, pady=(0, 10))
        self.preset_combobox.bind('<<ComboboxSelected>>', self.on_preset_change)
        
        # 自定义缩放区域
        scale_frame = ttk.LabelFrame(self, text="自定义缩放", padding=10)
        scale_frame.pack(fill=X, pady=(0, 10))
        
        # 缩放说明
        ttk.Label(
            scale_frame, 
            text="自定义缩放 (0.5x - 2.0x):",
            font=('微软雅黑', 9)
        ).pack(anchor=W, pady=(0, 5))
        
        # 缩放滑块
        self.scale_var = tk.DoubleVar(value=1.0)
        self.scale_widget = ttk.Scale(
            scale_frame,
            from_=0.5,
            to=2.0,
            variable=self.scale_var,
            orient=HORIZONTAL,
            length=300,
            command=self.on_scale_change
        )
        self.scale_widget.pack(fill=X, pady=(0, 5))
        
        # 缩放值显示
        self.info_label = ttk.Label(
            scale_frame,
            text="当前缩放: 1.0x",
            font=('微软雅黑', 9),
            bootstyle=INFO
        )
        self.info_label.pack(anchor=W, pady=(0, 10))
        
        # 预览区域
        preview_frame = ttk.LabelFrame(self, text="预览效果", padding=15)
        preview_frame.pack(fill=X, pady=(0, 10))
        
        # 预览文本
        self.preview_label = ttk.Label(
            preview_frame,
            text="这是字体预览文本 - Font Preview Text",
            font=('微软雅黑', 10),
            bootstyle=PRIMARY,
            anchor=CENTER
        )
        self.preview_label.pack(fill=X, pady=10)
        
        # 按钮区域
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=X, pady=(0, 5))
        
        # 重置按钮
        reset_btn = ttk.Button(
            button_frame,
            text="🔄 重置",
            bootstyle=SECONDARY,
            command=self.reset_to_default
        )
        reset_btn.pack(side=LEFT, padx=(0, 5))
        
        # 应用按钮
        apply_btn = ttk.Button(
            button_frame,
            text="✅ 应用",
            bootstyle=SUCCESS,
            command=self.apply_current_settings
        )
        apply_btn.pack(side=LEFT)
    
    def load_current_settings(self):
        """加载当前设置"""
        try:
            # 从配置获取当前设置
            ui_settings = self.config_manager.get_ui_settings()
            current_preset = ui_settings.get('font_size_preset', 'medium')
            current_scale = ui_settings.get('custom_font_scale', 1.0)
            
            # 更新字体管理器
            self.font_manager.current_preset = current_preset
            self.font_manager.user_scale_factor = current_scale
            
            # 更新预设下拉框
            presets = self.font_manager.get_available_presets()
            preset_keys = list(presets.keys())
            if current_preset in preset_keys:
                index = preset_keys.index(current_preset)
                self.preset_combobox.current(index)
            
            # 更新缩放滑块
            self.scale_var.set(current_scale)
            
            # 更新预览
            self.update_preview()
            
        except Exception as e:
            print(f"加载字体设置失败: {e}")
    
    def on_preset_change(self, event=None):
        """预设变更处理"""
        selected_index = self.preset_combobox.current()
        if selected_index >= 0:
            presets = self.font_manager.get_available_presets()
            preset_keys = list(presets.keys())
            selected_preset = preset_keys[selected_index]
            
            # 只更新字体管理器的内部状态，不立即应用全局变更
            self.font_manager.current_preset = selected_preset
            
            # 更新预览
            self.update_preview()
    
    def on_scale_change(self, value=None):
        """缩放变更处理"""
        scale_value = self.scale_var.get()
        
        # 只更新字体管理器的内部状态，不立即应用全局变更
        self.font_manager.user_scale_factor = scale_value
        
        # 更新信息标签
        self.info_label.configure(text=f"当前缩放: {scale_value:.1f}x")
        
        # 更新预览
        self.update_preview()
    
    def update_preview(self):
        """更新预览文本"""
        try:
            # 获取当前字体配置
            font_config = self.font_manager.get_font_config('default', '微软雅黑', 'normal')
            
            # 应用到预览标签
            self.preview_label.configure(font=font_config)
            
            # 更新预览文本显示当前设置
            preset_name = self.font_manager.get_current_preset_name()
            scale_info = self.font_manager.get_current_scale_info()
            
            preview_text = f"字体预览 - {preset_name} ({font_config[1]}pt)"
            self.preview_label.configure(text=preview_text)
            
        except Exception as e:
            print(f"更新预览失败: {e}")
    
    def reset_to_default(self):
        """重置为默认设置"""
        try:
            # 重置字体管理器
            self.font_manager.reset_to_default()
            
            # 重置UI控件
            presets = self.font_manager.get_available_presets()
            preset_keys = list(presets.keys())
            medium_index = preset_keys.index('medium') if 'medium' in preset_keys else 0
            self.preset_combobox.current(medium_index)
            
            # 重置缩放滑块
            self.scale_var.set(1.0)
            
            # 更新预览
            self.update_preview()
            
            print("字体设置已重置为默认值")
            
        except Exception as e:
            print(f"重置字体设置失败: {e}")
    
    def apply_current_settings(self):
        """应用当前设置"""
        try:
            current_settings = self.get_current_settings()
            
            # 保存到配置
            self.config_manager.update_ui_settings(current_settings)
            
            # 使用安全的字体应用方法
            self.font_manager.apply_font_settings_safely(current_settings)
            
            # 触发外部回调
            if self.on_change_callback:
                self.on_change_callback(current_settings)
            
            # 更新信息显示
            self.info_label.configure(
                text=f"已应用缩放: {current_settings['custom_font_scale']:.1f}x",
                bootstyle=SUCCESS
            )
            
            print("字体设置应用成功")
            
        except Exception as e:
            print(f"应用字体设置失败: {e}")
    
    def get_current_settings(self) -> Dict[str, any]:
        """获取当前设置"""
        presets = self.font_manager.get_available_presets()
        preset_keys = list(presets.keys())
        
        selected_index = self.preset_combobox.current()
        current_preset = preset_keys[selected_index] if selected_index >= 0 else 'medium'
        
        return {
            'font_size_preset': current_preset,
            'custom_font_scale': self.scale_var.get(),
            'font_family': '微软雅黑'
        } 