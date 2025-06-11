# font_manager.py - 字体管理器

import tkinter as tk
import os
import sys
from typing import Dict, Tuple, Optional, Callable

class FontManager:
    """字体管理器，处理DPI检测和字体大小自动调整"""
    
    def __init__(self, root_widget: tk.Widget):
        self.root_widget = root_widget
        self.dpi_scale_factor = 1.0
        self.user_scale_factor = 1.0
        
        # 基础字体大小（优化后的合理默认值）
        self.base_font_sizes = {
            'default': 10,   # 从12降到10
            'title': 12,     # 从14降到12  
            'header': 11,    # 从13降到11
            'button': 9,     # 从11降到9
            'small': 8       # 从10降到8
        }
        
        # 预设字号选项
        self.font_size_presets = {
            'extra_small': {'scale': 0.8, 'name': '超小'},
            'small': {'scale': 0.9, 'name': '小'},
            'medium': {'scale': 1.0, 'name': '中等'},
            'large': {'scale': 1.1, 'name': '大'},
            'extra_large': {'scale': 1.2, 'name': '超大'}
        }
        
        self.current_preset = 'medium'
        
        # 字体变更回调
        self.font_change_callback: Optional[Callable] = None
        
        # 检测DPI（优化缩放逻辑）
        self.detect_dpi()
        
    def detect_dpi(self) -> float:
        """检测屏幕DPI并计算缩放因子（优化缩放逻辑）"""
        try:
            # 获取DPI信息
            dpi = self.root_widget.winfo_fpixels('1i')
            raw_scale_factor = dpi / 96.0  # 96是标准DPI
            
            # 优化：减少自动缩放的激进程度
            if raw_scale_factor <= 1.1:
                self.dpi_scale_factor = 1.0  # 接近标准DPI时不缩放
            elif raw_scale_factor <= 1.5:
                self.dpi_scale_factor = 1.1  # 轻微缩放
            elif raw_scale_factor <= 2.0:
                self.dpi_scale_factor = 1.2  # 中等缩放
            else:
                self.dpi_scale_factor = 1.3  # 高DPI时适度缩放
                
            # 限制缩放因子在合理范围内
            self.dpi_scale_factor = max(0.8, min(1.5, self.dpi_scale_factor))
                
            return self.dpi_scale_factor
            
        except Exception as e:
            print(f"DPI检测失败: {e}")
            self.dpi_scale_factor = 1.0
            return 1.0
    
    def get_font_size(self, font_type: str = 'default') -> int:
        """获取调整后的字体大小"""
        base_size = self.base_font_sizes.get(font_type, 10)
        
        # 应用预设缩放和DPI缩放
        preset_scale = self.font_size_presets[self.current_preset]['scale']
        adjusted_size = int(base_size * self.dpi_scale_factor * self.user_scale_factor * preset_scale)
        
        # 确保字体大小在合理范围内
        return max(6, min(24, adjusted_size))
    
    def get_font_config(self, font_type: str = 'default', family: str = '微软雅黑', weight: str = 'normal') -> Tuple[str, int, str]:
        """获取完整的字体配置"""
        size = self.get_font_size(font_type)
        return (family, size, weight)
    
    def set_user_scale_factor(self, factor: float):
        """设置用户自定义缩放因子"""
        if 0.5 <= factor <= 2.0:
            self.user_scale_factor = factor
            # 立即应用全局字体变更
            self.apply_global_font_change()
    
    def set_font_preset(self, preset_name: str):
        """设置字号预设"""
        if preset_name in self.font_size_presets:
            self.current_preset = preset_name
            # 立即应用全局字体变更
            self.apply_global_font_change()
            return True
        return False
    
    def set_user_scale_factor_silent(self, factor: float):
        """静默设置用户自定义缩放因子（仅更新内部状态，不触发全局更新）"""
        if 0.5 <= factor <= 2.0:
            self.user_scale_factor = factor
    
    def set_font_preset_silent(self, preset_name: str):
        """静默设置字号预设（仅更新内部状态，不触发全局更新）"""
        if preset_name in self.font_size_presets:
            self.current_preset = preset_name
            return True
        return False
    
    def apply_font_settings_safely(self, font_settings: Dict[str, any]):
        """安全地应用字体设置，避免覆盖按钮颜色"""
        try:
            # 先静默更新内部状态
            if 'font_size_preset' in font_settings:
                self.set_font_preset_silent(font_settings['font_size_preset'])
            
            if 'custom_font_scale' in font_settings:
                self.set_user_scale_factor_silent(font_settings['custom_font_scale'])
            
            # 然后安全地应用全局更新
            self.apply_global_font_change_safely()
            
        except Exception as e:
            print(f"安全应用字体设置失败: {e}")
    
    def apply_global_font_change_safely(self):
        """安全地应用全局字体变更，保护按钮颜色"""
        try:
            # 先更新TTK样式（这个会避免覆盖按钮颜色）
            self.update_global_ttk_styles()
            
            # 然后应用到传统tkinter组件
            if self.main_window:
                self.apply_font_to_all_widgets(self.main_window)
            
            # 调用字体变更回调
            if self.font_change_callback:
                try:
                    font_settings = {
                        'font_size_preset': self.current_preset,
                        'custom_font_scale': self.user_scale_factor
                    }
                    self.font_change_callback(font_settings)
                except Exception as callback_error:
                    print(f"字体变更回调失败: {callback_error}")
                    
        except Exception as e:
            print(f"安全字体变更失败: {e}")
    
    def get_available_presets(self) -> Dict[str, str]:
        """获取可用的字号预设"""
        return {key: value['name'] for key, value in self.font_size_presets.items()}
    
    def get_current_preset_name(self) -> str:
        """获取当前预设的显示名称"""
        return self.font_size_presets[self.current_preset]['name']
    
    def get_current_scale_info(self) -> Dict:
        """获取当前缩放信息"""
        preset_scale = self.font_size_presets[self.current_preset]['scale']
        return {
            'dpi_scale': self.dpi_scale_factor,
            'user_scale': self.user_scale_factor,
            'preset_scale': preset_scale,
            'total_scale': self.dpi_scale_factor * self.user_scale_factor * preset_scale,
            'current_preset': self.current_preset
        }
    
    def apply_font_to_widget(self, widget: tk.Widget, font_type: str = 'default', family: str = '微软雅黑', weight: str = 'normal'):
        """应用字体配置到指定控件"""
        try:
            font_config = self.get_font_config(font_type, family, weight)
            widget.configure(font=font_config)
        except Exception as e:
            print(f"应用字体失败: {e}")
    
    def set_font_change_callback(self, callback_func: Callable):
        """设置字体变更回调函数"""
        self.font_change_callback = callback_func
    
    def apply_font_to_all_widgets(self, root_widget: tk.Widget):
        """递归应用字体到所有子组件"""
        try:
            # 安全检查：确保root_widget不为None
            if root_widget is None:
                return
                
            # 定义需要应用字体的组件类型（包括tkinter和ttk组件）
            tkinter_widgets = (
                'Label', 'Button', 'Checkbutton', 'Radiobutton', 
                'Entry', 'Text', 'Listbox', 'Menubutton'
            )
            
            ttk_widgets = (
                'TLabel', 'TButton', 'TCheckbutton', 'TRadiobutton',
                'TEntry', 'TCombobox', 'TSpinbox', 'TLabelFrame',
                'TTreeview', 'TScale', 'TMenubutton', 'TNotebook'
            )
            
            # 检查当前控件是否需要应用字体
            try:
                widget_class = root_widget.winfo_class()
            except Exception:
                # 如果无法获取控件类型，跳过该控件
                return
            
            # 处理传统tkinter组件
            if widget_class in tkinter_widgets:
                try:
                    # 根据控件类型确定字体类型
                    if widget_class in ['Button', 'Menubutton']:
                        font_type = 'button'
                    elif widget_class in ['Label']:
                        font_type = 'default'
                    elif widget_class in ['Entry', 'Text', 'Listbox']:
                        font_type = 'default'
                    else:
                        font_type = 'default'
                    
                    # 应用字体配置
                    font_config = self.get_font_config(font_type)
                    root_widget.configure(font=font_config)
                    
                except Exception as widget_error:
                    # 某些控件可能不支持字体配置，跳过它们
                    pass
            
            # 处理TTK组件 - 使用ttk.Style
            elif widget_class in ttk_widgets:
                try:
                    import ttkbootstrap as ttk
                    style = ttk.Style()
                    
                    # 根据控件类型确定字体类型
                    if widget_class in ['TButton', 'TMenubutton']:
                        font_type = 'button'
                    elif widget_class in ['TLabel', 'TLabelFrame']:
                        font_type = 'default'
                    elif widget_class in ['TEntry', 'TCombobox', 'TSpinbox']:
                        font_type = 'default'
                    elif widget_class in ['TTreeview']:
                        font_type = 'small'
                    else:
                        font_type = 'default'
                    
                    # 获取字体配置
                    font_config = self.get_font_config(font_type)
                    
                    # 为不同的TTK组件设置字体样式
                    style_name = f"Custom.{widget_class}"
                    
                    # 配置样式
                    try:
                        style.configure(style_name, font=font_config)
                        
                        # 尝试应用样式到控件
                        if hasattr(root_widget, 'configure'):
                            root_widget.configure(style=style_name)
                        
                    except Exception as style_error:
                        # 如果样式设置失败，尝试直接设置字体（某些组件支持）
                        try:
                            root_widget.configure(font=font_config)
                        except:
                            pass
                    
                except Exception as ttk_error:
                    # TTK组件处理失败，跳过
                    pass
            
            # 递归应用到子控件
            try:
                children = root_widget.winfo_children()
                if children:  # 确保children不为None
                    for child in children:
                        if child is not None:  # 确保child不为None
                            self.apply_font_to_all_widgets(child)
            except Exception as child_error:
                # 不输出过多的错误信息，静默跳过
                pass
                
        except Exception as e:
            # 只在调试时输出错误信息
            pass
    
    def update_global_ttk_styles(self):
        """更新全局TTK样式字体"""
        try:
            import ttkbootstrap as ttk
            style = ttk.Style()
            
            # 定义TTK组件的样式映射
            ttk_style_mappings = {
                'TLabel': 'default',
                'TEntry': 'default',
                'TCombobox': 'default',
                'TSpinbox': 'default',
                'TLabelFrame': 'default',
                'TCheckbutton': 'default',
                'TRadiobutton': 'default',
                'TTreeview': 'small',
                'TScale': 'small',
                'TNotebook': 'default',
                'TNotebook.Tab': 'small'
            }
            
            # 只为非按钮组件配置字体（避免覆盖按钮颜色）
            for style_name, font_type in ttk_style_mappings.items():
                try:
                    font_config = self.get_font_config(font_type)
                    
                    # 获取当前样式配置
                    current_config = style.configure(style_name)
                    if current_config is None:
                        current_config = {}
                    
                    # 只更新字体属性，保留其他属性
                    updated_config = dict(current_config)
                    updated_config['font'] = font_config
                    
                    # 应用更新后的配置
                    style.configure(style_name, **updated_config)
                    
                except Exception as e:
                    # 某些样式可能不支持字体配置，跳过
                    continue
            
            # 特殊处理：按钮样式 - 更保守的方法
            try:
                # 只更新基础TButton，不触碰带颜色的按钮样式
                button_font = self.get_font_config('button')
                
                # 获取当前TButton样式
                current_button_config = style.configure('TButton') or {}
                
                # 检查是否存在font配置，如果没有就添加，如果有就更新
                if 'font' not in current_button_config or not current_button_config.get('font'):
                    # 只在没有字体配置时才设置
                    updated_button_config = dict(current_button_config)
                    updated_button_config['font'] = button_font
                    style.configure('TButton', **updated_button_config)
                else:
                    # 如果已经有字体配置，只更新字体大小
                    current_font = current_button_config.get('font')
                    if isinstance(current_font, tuple) and len(current_font) >= 2:
                        # 保持原字体家族和样式，只更新大小
                        new_font = (current_font[0], self.get_font_size('button'))
                        if len(current_font) > 2:
                            new_font = new_font + current_font[2:]
                        updated_button_config = dict(current_button_config)
                        updated_button_config['font'] = new_font
                        style.configure('TButton', **updated_button_config)
                    else:
                        # 如果字体格式不标准，使用我们的默认字体
                        updated_button_config = dict(current_button_config)
                        updated_button_config['font'] = button_font
                        style.configure('TButton', **updated_button_config)
                        
            except Exception as e:
                print(f"更新TButton样式失败: {e}")
            
            # 特殊处理：Treeview的heading和cell（也只更新字体）
            try:
                heading_font = self.get_font_config('small')
                current_heading = style.configure('Treeview.Heading') or {}
                updated_heading = dict(current_heading)
                updated_heading['font'] = heading_font
                style.configure('Treeview.Heading', **updated_heading)
                
                cell_font = self.get_font_config('small')
                current_cell = style.configure('Treeview') or {}
                updated_cell = dict(current_cell)
                updated_cell['font'] = cell_font
                style.configure('Treeview', **updated_cell)
            except Exception:
                pass
            
            # 不再尝试更新彩色按钮样式，让ttkbootstrap自己管理
            # 这可以避免覆盖SUCCESS、PRIMARY、WARNING等按钮的颜色
                
        except ImportError:
            # 如果没有ttkbootstrap，跳过
            pass
        except Exception as e:
            print(f"更新TTK样式失败: {e}")
    
    def apply_global_font_change(self):
        """应用全局字体变更（用于设置变更时调用）"""
        try:
            # 首先更新全局TTK样式
            self.update_global_ttk_styles()
            
            # 然后递归应用到所有控件
            if hasattr(self, 'main_window_ref') and self.main_window_ref:
                self.apply_font_to_all_widgets(self.main_window_ref)
            else:
                # 否则应用到根控件
                self.apply_font_to_all_widgets(self.root_widget)
                
            # 触发回调通知其他组件
            if self.font_change_callback:
                try:
                    self.font_change_callback(self.current_preset)
                except Exception as e:
                    print(f"字体回调执行失败: {e}")
                    
        except Exception as e:
            print(f"全局字体应用失败: {e}")
    
    def set_main_window_reference(self, main_window):
        """设置主窗口引用以便全局字体应用"""
        self.main_window_ref = main_window
    
    def get_preview_font_config(self, preset_name: str) -> Tuple[str, int, str]:
        """获取预览字体配置"""
        if preset_name in self.font_size_presets:
            # 临时计算预览字体大小
            base_size = self.base_font_sizes.get('default', 10)
            preset_scale = self.font_size_presets[preset_name]['scale']
            preview_size = int(base_size * self.dpi_scale_factor * self.user_scale_factor * preset_scale)
            preview_size = max(6, min(24, preview_size))
            return ('微软雅黑', preview_size, 'normal')
        return self.get_font_config()
    
    def reset_to_default(self):
        """重置为默认字体设置"""
        self.current_preset = 'medium'
        self.user_scale_factor = 1.0
        # 触发回调
        if self.font_change_callback:
            try:
                self.font_change_callback(self.current_preset)
            except Exception as e:
                print(f"重置字体回调执行失败: {e}") 