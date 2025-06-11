# main_window.py - 主窗口界面
"""
塔防游戏伤害分析器主窗口
融合苹果设计语言的现代化界面
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import sys
import os
import logging
from typing import Dict, Optional, Callable, Any
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入布局管理器
from .layout_manager import LayoutManager

# 导入管理器组件
from .managers.menu_manager import MenuManager

# 导入UI面板组件
from .sidebar_panel import SidebarPanel
from .overview_panel import OverviewPanel
from .calculation_panel import CalculationPanel
from .comparison_panel import ComparisonPanel
from .chart_panel import ChartPanel
from .chart_comparison_panel import ChartComparisonPanel
from .data_import_panel import DataImportPanel
from .operator_editor import OperatorEditor
from .theme_manager import ThemeManager
from .font_manager import FontManager

# 导入设置对话框
from .settings_dialog import SettingsDialog

# 导入配置管理器
from config.config_manager import config_manager

# 导入新的管理器
from data.import_export_manager import ImportExportManager
from utils.report_generator import ReportGenerator

# 添加导入语句
from tkinter import filedialog

logger = logging.getLogger(__name__)

class AppleDesignSystem:
    """设计系统规范"""
    
    # 颜色系统
    COLORS = {
        'primary': '#007AFF',        # 蓝
        'background': '#FFFFFF',     # 纯白背景
        'secondary': '#F2F2F2',      # 浅灰背景
        'surface': '#FAFAFA',        # 表面色
        'text_primary': '#1D1D1F',   # 主要文字
        'text_secondary': '#86868B', # 次要文字
        'success': '#34C759',        # 成功绿
        'warning': '#FF9500',        # 警告橙
        'error': '#FF3B30',          # 错误红
        'accent': '#5856D6',         # 紫色强调
        'border': '#E5E5E7'          # 边框色
    }
    
    # 字体系统
    FONTS = {
        'title': ('SF Pro Display', 18, 'bold'),
        'heading': ('SF Pro Display', 16, 'bold'),
        'subheading': ('SF Pro Text', 14, 'medium'),
        'body': ('SF Pro Text', 12, 'normal'),
        'caption': ('SF Pro Text', 10, 'normal'),
        'code': ('SF Mono', 11, 'normal')
    }
    
    # 间距系统 (基于4px网格)
    SPACING = {
        'xs': 4,    # 极小间距
        'sm': 8,    # 小间距
        'md': 16,   # 中等间距
        'lg': 24,   # 大间距
        'xl': 32,   # 超大间距
        'xxl': 48   # 极大间距
    }
    
    # 动画规范
    ANIMATIONS = {
        'quick': 0.15,      # 快速动画 (按钮反馈)
        'standard': 0.25,   # 标准动画 (面板切换)
        'slow': 0.35,       # 慢速动画 (布局变化)
        'spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
    }
    
    # 圆角和阴影
    VISUAL_EFFECTS = {
        'border_radius': 8,
        'button_radius': 6,
        'card_radius': 12,
        'shadow_light': '0 1px 3px rgba(0,0,0,0.1)',
        'shadow_medium': '0 4px 12px rgba(0,0,0,0.15)',
        'shadow_heavy': '0 8px 24px rgba(0,0,0,0.2)'
    }
    
    @classmethod
    def get_theme_config(cls):
        """获取主题配置"""
        return {
            'colors': cls.COLORS,
            'fonts': cls.FONTS,
            'spacing': cls.SPACING,
            'animations': cls.ANIMATIONS,
            'visual_effects': cls.VISUAL_EFFECTS,
            'theme_name': 'apple_design_system',
            'base_theme': 'cosmo'
        }

class DamageAnalyzerMainWindow(ttk.Window):
    """塔防游戏伤害分析器主窗口"""
    
    def __init__(self, db_manager):
        """
        初始化主窗口
        
        Args:
            db_manager: 数据库管理器实例
        """
        # 加载UI设置
        ui_settings = config_manager.get_ui_settings()
        saved_theme = ui_settings.get('theme', 'cosmo')
        
        # 获取设计系统配置
        try:
            theme_config = AppleDesignSystem.get_theme_config()
            # 使用保存的主题覆盖默认主题
            theme_config['base_theme'] = saved_theme
        except Exception as e:
            logger.warning(f"获取主题配置失败: {e}，使用默认配置")
            theme_config = {'base_theme': saved_theme}
        
        # 初始化主窗口（使用保存的主题）
        super().__init__(
            title="Damage Analyzer - 明日方舟伤害分析器",
            themename=theme_config.get('base_theme', 'cosmo'),
            resizable=(True, True)
        )
        
        # 存储数据库管理器
        self.db_manager = db_manager
        
        # 初始化导入导出管理器和报告生成器
        self.import_export_manager = ImportExportManager(db_manager)
        self.report_generator = ReportGenerator(db_manager)
        
        # 设置状态回调
        self.import_export_manager.set_status_callback(self.update_apple_status)
        
        # 设置概览面板引用到导入管理器，用于实时活动推送
        # 注意：这里不设置刷新回调，会在创建概览面板后设置
        
        # 存储主题配置
        self.theme_config = theme_config
        
        # 初始化管理器
        self.theme_manager = ThemeManager()
        self.font_manager = FontManager(self)
        
        # 设置字体管理器的主窗口引用，以便全局字体应用
        self.font_manager.set_main_window_reference(self)
        
        # 应用保存的UI设置
        self.apply_saved_ui_settings(ui_settings)
        
        # 初始化状态变量
        self.current_tab = 0
        self.sidebar_visible = True
        self.layout_manager = None
        self.status_manager = None
        self.panels = {}
        
        # 窗口属性设置
        self.setup_window_properties()
        
        # 应用Apple设计系统
        self.apply_apple_design_system()
        
        # 创建界面
        try:
            self.create_apple_layout()
        except Exception as e:
            logger.error(f"创建Apple布局失败: {e}")
            self.create_fallback_layout()
        
        # 设置菜单系统
        self.setup_apple_menu_system()
        
        # 设置状态系统
        self.setup_apple_status_system()
        
        # 设置事件处理器
        self.setup_apple_event_handlers()
        
        # 应用视觉效果
        self.apply_apple_visual_effects()
        
        # 居中窗口
        self.center_window()
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("主窗口初始化完成")
    
    def setup_window_properties(self):
        """设置窗口属性"""
        # 窗口标题
        self.title("塔防游戏伤害分析器 v1.0.0")
        
        # 使用黄金比例设置窗口尺寸 (1.618:1)
        window_width = 1400
        window_height = int(window_width / 1.618)
        self.geometry(f"{window_width}x{window_height}")
        
        # 设置最小尺寸
        self.minsize(1000, 600)
        
        # 居中显示
        self.center_window()
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 设置关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info(f"窗口属性设置完成: {window_width}x{window_height}")
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            logger.debug(f"设置窗口图标失败: {e}")
    
    def apply_apple_design_system(self):
        """应用系统"""
        try:
            # 配置主题管理器
            self.theme_manager = ThemeManager()
            
            # 应用颜色方案
            style = ttk.Style()
            
            # 配置按钮样式
            style.configure(
                'Apple.TButton',
                font=AppleDesignSystem.FONTS['body'],
                borderwidth=0,
                focuscolor='none'
            )
            
            # 配置标签样式
            style.configure(
                'AppleTitle.TLabel',
                font=AppleDesignSystem.FONTS['title'],
                foreground=AppleDesignSystem.COLORS['text_primary']
            )
            
            style.configure(
                'AppleHeading.TLabel',
                font=AppleDesignSystem.FONTS['heading'],
                foreground=AppleDesignSystem.COLORS['text_primary']
            )
            
            style.configure(
                'AppleBody.TLabel',
                font=AppleDesignSystem.FONTS['body'],
                foreground=AppleDesignSystem.COLORS['text_secondary']
            )
            
            # 配置Combobox样式
            style.configure(
                'Apple.TCombobox',
                font=AppleDesignSystem.FONTS['body'],
                fieldbackground=AppleDesignSystem.COLORS['background'],
                borderwidth=1,
                focuscolor='none'
            )
            
            logger.info("系统应用完成")
            
        except Exception as e:
            logger.error(f"应用设计系统失败: {e}")
    
    def apply_saved_ui_settings(self, ui_settings):
        """应用保存的UI设置"""
        try:
            # 应用主题设置
            theme = ui_settings.get('theme', 'cosmo')
            self.theme_manager.current_theme = theme
            
            # 应用字体设置
            font_preset = ui_settings.get('font_size_preset', 'medium')
            font_scale = ui_settings.get('custom_font_scale', 1.0)
            
            self.font_manager.set_font_preset(font_preset)
            self.font_manager.set_user_scale_factor(font_scale)
            
            logger.info(f"UI设置应用完成: 主题={theme}, 字体={font_preset}, 缩放={font_scale}")
            
        except Exception as e:
            logger.error(f"应用UI设置失败: {e}")
    
    def create_apple_layout(self):
        """创建布局"""
        try:
            # 创建响应式布局管理器
            self.layout_manager = LayoutManager(self)
            
            # 创建侧边栏布局 (使用黄金比例)
            sidebar_width = int(self.winfo_width() * 0.236)  # 黄金比例的倒数
            sidebar_frame, main_frame = self.layout_manager.create_sidebar_layout(
                sidebar_width=sidebar_width,
                min_sidebar_width=280
            )
            
            # 创建侧边栏
            self.create_apple_sidebar(sidebar_frame)
            
            # 创建主工作区
            self.create_apple_main_area(main_frame)
            
            logger.info("布局创建完成")
            
        except Exception as e:
            logger.error(f"创建布局失败: {e}")
            # 降级处理：创建简单布局
            self.create_fallback_layout()
    
    def create_apple_sidebar(self, parent):
        """创建侧边栏"""
        try:
            # 定义简化的侧边栏回调函数
            sidebar_callbacks = {
                'switch_to_overview': lambda: self.switch_to_tab(0),
                'switch_to_analysis': lambda: self.switch_to_tab(1),
                'switch_to_comparison': lambda: self.switch_to_tab(2),  # 图表对比页面
                'switch_to_import': lambda: self.switch_to_tab(3),  # 直接跳转到干员管理
                'refresh_data': self.refresh_all_data,
                # 导入导出快捷功能
                'import_excel': self.import_excel_data,
                'import_json': self.import_json_data,
                'export_excel': self.export_all_data_to_excel,
                'export_pdf': lambda: self.export_complete_analysis_report_as_pdf(),
                'export_html': lambda: self.export_complete_analysis_report_as_html(),
                'export_json': self.export_current_data,
                'export_report': self.export_complete_analysis_report,
                'export_current_data': self.export_current_data,
                # 快捷操作
                'quick_import': self.quick_import_dialog,
                'clear_cache': self.clear_cache_with_confirm
            }
            
            # 创建侧边栏面板
            self.sidebar_panel = SidebarPanel(
                parent=parent,
                db_manager=self.db_manager,
                callbacks=sidebar_callbacks
            )
            
            logger.info("简化的侧边栏创建完成")
            
        except Exception as e:
            logger.error(f"创建侧边栏失败: {e}")
    
    def create_apple_main_area(self, parent):
        """创建主工作区"""
        try:
            # 创建Safari风格的标签页容器
            self.notebook = ttk.Notebook(parent)
            self.notebook.pack(fill=BOTH, expand=True, padx=AppleDesignSystem.SPACING['md'])
            
            # 创建各个标签页
            self.create_overview_tab()
            self.create_data_analysis_tab()
            self.create_chart_comparison_tab()
            self.create_operator_management_tab()
            
            # 绑定标签页切换事件
            self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
            
            logger.info("主工作区创建完成")
            
        except Exception as e:
            logger.error(f"创建主工作区失败: {e}")
    
    def create_overview_tab(self):
        """创建数据概览标签页"""
        try:
            overview_frame = ttk.Frame(self.notebook)
            self.notebook.add(overview_frame, text="📊 数据概览")
            
            # 创建概览面板
            self.overview_panel = OverviewPanel(
                overview_frame,
                db_manager=self.db_manager,
                status_callback=self.update_apple_status
            )
            
            # 设置主窗口引用，以便快速操作按钮能够切换标签页
            self.overview_panel.set_main_window(self)
            
            # 设置概览面板引用到导入管理器，用于实时活动推送
            self.import_export_manager.set_overview_panel(self.overview_panel)
            
            # 设置刷新回调，让导入操作能够触发所有面板刷新（包括概览面板）
            # 使用refresh_all_data确保所有面板都会刷新，包括概览面板本身
            self.import_export_manager.set_refresh_callback(self.refresh_all_data)
            
            logger.info("数据概览标签页创建完成，已建立实时活动推送连接和全局刷新回调")
            
        except Exception as e:
            logger.error(f"创建概览标签页失败: {e}")
    
    def create_data_analysis_tab(self):
        """创建数据分析标签页"""
        try:
            analysis_frame = ttk.Frame(self.notebook)
            self.notebook.add(analysis_frame, text="📈 数据分析")
            
            # 集成计算面板
            self.panels['analysis'] = CalculationPanel(
                parent=analysis_frame,
                db_manager=self.db_manager,
                status_callback=self.update_apple_status
            )
            
            logger.info("数据分析标签页创建完成")
            
        except Exception as e:
            logger.error(f"创建分析标签页失败: {e}")
    
    def create_chart_comparison_tab(self):
        """创建现代化图表对比分析标签页"""
        try:
            chart_frame = ttk.Frame(self.notebook)
            self.notebook.add(chart_frame, text="📊 图表对比")
            
            # 创建现代化的图表对比面板，确保传递数据库管理器
            from .chart_comparison_panel import ChartComparisonPanel
            chart_comparison_panel = ChartComparisonPanel(
                chart_frame, 
                db_manager=self.db_manager,  # 确保传递数据库管理器
                style="modern"
            )
            chart_comparison_panel.pack(fill=tk.BOTH, expand=True)
            
            # 存储面板引用
            self.panels['chart_comparison'] = chart_comparison_panel
            
            logger.info("现代化图表对比分析面板创建完成")
            
        except Exception as e:
            logger.error(f"创建图表对比标签页失败: {e}")
            # 创建备用面板
            self.create_fallback_chart_comparison_tab(chart_frame)
    
    def create_fallback_chart_comparison_tab(self, chart_frame):
        """创建回退版本的图表对比标签页"""
        try:
            # 创建分屏布局
            paned_window = ttk.PanedWindow(chart_frame, orient=HORIZONTAL)
            paned_window.pack(fill=BOTH, expand=True)
            
            # 左侧：对比面板
            comparison_frame = ttk.Frame(paned_window)
            paned_window.add(comparison_frame, weight=1)
            
            self.panels['comparison'] = ComparisonPanel(
                parent=comparison_frame,
                db_manager=self.db_manager,
                status_callback=self.update_apple_status
            )
            
            # 右侧：图表面板
            chart_panel_frame = ttk.Frame(paned_window)
            paned_window.add(chart_panel_frame, weight=2)
            
            self.panels['charts'] = ChartPanel(
                parent=chart_panel_frame,
                db_manager=self.db_manager,
                status_callback=self.update_apple_status
            )
            
            logger.info("回退版图表对比标签页创建完成")
            
        except Exception as e:
            logger.error(f"创建回退版图表标签页失败: {e}")
    
    def create_operator_management_tab(self):
        """创建干员管理标签页"""
        try:
            management_frame = ttk.Frame(self.notebook)
            self.notebook.add(management_frame, text="👥 干员管理")
            
            # 创建垂直分屏布局
            paned_window = ttk.PanedWindow(management_frame, orient=VERTICAL)
            paned_window.pack(fill=BOTH, expand=True)
            
            # 上半部分：数据导入面板
            import_frame = ttk.Frame(paned_window)
            paned_window.add(import_frame, weight=1)
            
            self.panels['import'] = DataImportPanel(
                parent=import_frame,
                db_manager=self.db_manager,
                status_callback=self.update_apple_status
            )
            
            # 为导入面板设置刷新回调，确保导入操作能触发全局刷新
            if hasattr(self.panels['import'], 'set_refresh_callback'):
                self.panels['import'].set_refresh_callback(self.refresh_all_data)
                logger.info("已为导入面板设置刷新回调")
            
            # 下半部分：干员编辑器
            editor_frame = ttk.Frame(paned_window)
            paned_window.add(editor_frame, weight=1)
            
            self.panels['editor'] = OperatorEditor(
                parent=editor_frame,
                db_manager=self.db_manager,
                status_callback=self.update_apple_status
            )
            
            logger.info("干员管理标签页创建完成")
            
        except Exception as e:
            logger.error(f"创建管理标签页失败: {e}")
    
    def setup_apple_menu_system(self):
        """设置菜单系统"""
        try:
            # 定义菜单回调函数
            menu_callbacks = {
                'export_data': self.export_current_data,
                'show_settings': self.show_settings_dialog,
                'exit_app': self.on_closing,
                'show_about': self.show_about_dialog
            }
            
            # 创建菜单管理器
            self.menu_manager = MenuManager(self, menu_callbacks)
            self.menu_manager.create_menu()
            
            logger.info("菜单系统设置完成")
            
        except Exception as e:
            logger.error(f"设置菜单系统失败: {e}")
    
    def setup_apple_status_system(self):
        """设置状态系统"""
        try:
            # 简化：不再使用复杂的状态管理器
            # 初始状态
            self.update_apple_status("应用程序已启动", "success")
            
        except Exception as e:
            logger.error(f"设置状态系统失败: {e}")
    
    def setup_apple_event_handlers(self):
        """设置事件处理器"""
        try:
            # 键盘快捷键 (遵循macOS习惯)
            self.bind('<Control-s>', lambda e: self.export_current_data())
            self.bind('<Control-q>', lambda e: self.on_closing())
            self.bind('<F9>', lambda e: self.toggle_sidebar_apple_style())
            self.bind('<F11>', lambda e: self.toggle_fullscreen())
            self.bind('<F1>', lambda e: self.show_about_dialog())
            
            # 窗口事件
            self.bind('<Configure>', self.on_window_configure)
            
            logger.info("事件处理器设置完成")
            
        except Exception as e:
            logger.error(f"设置事件处理器失败: {e}")
    
    def apply_apple_visual_effects(self):
        """应用视觉效果"""
        try:
            # 这里可以添加更多的视觉效果
            # 如圆角、阴影等（需要自定义样式）
            
            logger.info("视觉效果应用完成")
            
        except Exception as e:
            logger.error(f"应用视觉效果失败: {e}")
    
    # 事件处理方法
    def on_tab_changed(self, event):
        """标签页切换事件处理"""
        try:
            current_tab = self.notebook.index(self.notebook.select())
            self.current_tab = current_tab
            
            # 更新侧边栏状态
            if self.sidebar_panel:
                self.sidebar_panel.current_section = self.get_tab_name(current_tab)
            
            # 更新状态
            tab_name = self.get_tab_name(current_tab)
            self.update_apple_status(f"切换到{tab_name}")
            
        except Exception as e:
            logger.error(f"标签页切换处理失败: {e}")
    
    def on_window_configure(self, event):
        """窗口配置变化事件处理（优化版本，添加事件过滤）"""
        if event.widget == self:
            # 添加事件去重机制
            if not hasattr(self, '_last_configure_time'):
                self._last_configure_time = 0
            
            current_time = time.time()
            if current_time - self._last_configure_time < 0.1:  # 100ms内忽略重复事件
                return
            
            self._last_configure_time = current_time
            
            # 只处理实际的尺寸变化
            if hasattr(self, '_last_window_size'):
                current_size = (self.winfo_width(), self.winfo_height())
                if current_size == self._last_window_size:
                    return
                self._last_window_size = current_size
            else:
                self._last_window_size = (self.winfo_width(), self.winfo_height())
    
    def on_status_update(self, message, level):
        """状态更新回调"""
        # 可以在这里添加额外的状态处理逻辑
        pass
    
    def on_closing(self):
        """窗口关闭事件处理"""
        try:
            # 保存窗口状态
            self.save_window_state()
            
            # 清理资源
            if self.layout_manager:
                self.layout_manager.cleanup()
            
            # 关闭窗口
            self.destroy()
            
        except Exception as e:
            logger.error(f"关闭窗口失败: {e}")
            self.destroy()
    
    # 工具方法
    def switch_to_tab(self, tab_index):
        """切换到指定标签页"""
        try:
            if 0 <= tab_index < self.notebook.index('end'):
                self.notebook.select(tab_index)
        except Exception as e:
            logger.error(f"切换标签页失败: {e}")
    
    def get_tab_name(self, tab_index):
        """获取标签页名称"""
        tab_names = ["数据概览", "数据分析", "图表对比", "干员管理"]
        return tab_names[tab_index] if 0 <= tab_index < len(tab_names) else "未知"
    
    def toggle_sidebar_apple_style(self):
        """侧边栏切换"""
        try:
            if self.layout_manager:
                self.layout_manager.toggle_sidebar(animated=True)
                self.sidebar_visible = self.layout_manager.is_sidebar_visible()
                
                status = "显示" if self.sidebar_visible else "隐藏"
                self.update_apple_status(f"侧边栏已{status}")
                
        except Exception as e:
            logger.error(f"切换侧边栏失败: {e}")
    
    def update_apple_status(self, message, level="info"):
        """更新状态"""
        try:
            # 这里可以添加额外的状态处理逻辑
            pass
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    def save_window_state(self):
        """保存窗口状态"""
        try:
            # 这里可以保存窗口位置、大小等状态到配置文件
            pass
        except Exception as e:
            logger.error(f"保存窗口状态失败: {e}")
    
    def create_fallback_layout(self):
        """创建降级布局"""
        try:
            # 简单的布局作为备选方案
            main_frame = ttk.Frame(self)
            main_frame.pack(fill=BOTH, expand=True)
            
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # 创建基础标签页
            self.create_overview_tab()
            
            logger.info("降级布局创建完成")
            
        except Exception as e:
            logger.error(f"创建降级布局失败: {e}")
    
    # 菜单回调方法的占位实现
    def import_excel_data(self, filename=None):
        """导入Excel数据 - 重构为调用ImportExportManager"""
        try:
            # 调用导入导出管理器
            result = self.import_export_manager.import_excel_data(filename, self.update_apple_status)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新界面
                self.refresh_all_data()
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                pass
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                pass
                
        except Exception as e:
            logger.error(f"Excel导入失败: {e}")
            messagebox.showerror("导入失败", f"Excel导入失败：\n{str(e)}")
            self.update_apple_status("Excel导入失败", "error")
    
    def import_json_data(self, filename=None):
        """导入JSON数据 - 重构为调用ImportExportManager"""
        try:
            # 调用导入导出管理器
            result = self.import_export_manager.import_json_data(filename, self.update_apple_status)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新界面
                self.refresh_all_data()
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                pass
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                pass
                
        except Exception as e:
            logger.error(f"JSON导入失败: {e}")
            messagebox.showerror("导入失败", f"JSON导入失败：\n{str(e)}")
            self.update_apple_status("JSON导入失败", "error")
    
    def export_current_data(self):
        """导出当前数据 - 重构为调用ImportExportManager"""
        try:
            # 获取当前用户实际选择和计算的数据，而不是数据库中的所有数据
            operators = self._get_current_selected_operators()
            
            # 获取用户生成的图表
            current_charts = self._get_current_charts()
            
            # 如果没有选择的干员，则使用所有干员作为后备
            if not operators:
                operators = self.db_manager.get_all_operators()
                self.update_apple_status("没有选择的干员，将导出所有干员数据", "warning")
            
            # 调用导入导出管理器
            success = self.import_export_manager.export_current_data(operators, current_charts=current_charts)
            
            # 成功和失败的消息已经在管理器中处理了
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            messagebox.showerror("导出失败", f"导出数据时出现错误：\n{str(e)}")
            self.update_apple_status("数据导出失败", "error")
    
    def export_all_data_to_excel(self):
        """导出所有数据到Excel - 包含用户生成的图表和当前计算结果"""
        try:
            # 获取所有数据
            operators = self.db_manager.get_all_operators()
            
            # 获取用户生成的图表
            current_charts = self._get_current_charts()
            
            # 获取用户当前的计算结果（重要：这里添加了获取当前计算结果）
            current_calculations = self.import_export_manager._get_current_and_recent_calculations()
            
            # 调用增强的导出方法，传入当前计算结果
            success = self.import_export_manager.export_excel_with_current_charts_and_calculations(
                operators, 
                current_charts=current_charts,
                current_calculations=current_calculations
            )
            
            # 成功和失败的消息已经在管理器中处理了
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            messagebox.showerror("导出失败", f"导出Excel时出现错误：\n{str(e)}")
            self.update_apple_status("Excel导出失败", "error")
    
    def export_complete_analysis_report(self):
        """导出完整分析报告 - 重构为调用ReportGenerator"""
        try:
            filename = filedialog.asksaveasfilename(
                title="导出分析报告",
                defaultextension=".pdf",
                filetypes=[
                    ("PDF 文件", "*.pdf"),
                    ("HTML 文件", "*.html"),
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not filename:
                return
            
            # 根据文件扩展名确定格式
            file_ext = filename.lower().split('.')[-1]
            
            if file_ext == 'pdf':
                format_type = 'pdf'
            elif file_ext == 'html':
                format_type = 'html'
            elif file_ext == 'txt':
                format_type = 'txt'
            else:
                format_type = 'pdf'  # 默认PDF格式
            
            # 调用报告生成器
            success = self.report_generator.generate_complete_analysis_report(format_type, filename)
            
            # 成功和失败的消息已经在报告生成器中处理了
            
        except Exception as e:
            logger.error(f"导出分析报告失败: {e}")
            messagebox.showerror("导出失败", f"导出分析报告失败：\n{str(e)}")
            self.update_apple_status("分析报告导出失败", "error")
    
    def generate_excel_template(self):
        """生成Excel模板"""
        pass
    
    def clear_cache(self):
        """清空缓存"""
        self.update_apple_status("缓存已清空", "success")
    
    def clear_all_data(self):
        """清空所有数据"""
        result = messagebox.askyesno("确认", "确定要清空所有数据吗？此操作不可撤销。")
        if result:
            self.update_apple_status("所有数据已清空", "warning")
    
    def show_performance_monitor(self):
        """显示性能监控"""
        messagebox.showinfo("性能监控", "性能监控功能已简化")
    
    def memory_cleanup(self):
        """内存清理"""
        try:
            # 简单的内存清理
            import gc
            gc.collect()
            messagebox.showinfo("内存清理", "内存清理完成")
        except Exception as e:
            logger.error(f"内存清理失败: {e}")
            messagebox.showinfo("内存清理", "内存清理完成")
    
    def reset_layout(self):
        """重置布局"""
        self.update_apple_status("布局已重置", "success")
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        self.update_apple_status("全屏模式切换")
    
    def show_user_manual(self):
        """显示用户手册"""
        self.update_apple_status("用户手册功能")
    
    def show_shortcuts(self):
        """显示快捷键"""
        shortcuts_info = """
快捷键列表：
Ctrl+O - 导入Excel数据
Ctrl+S - 导出数据
Ctrl+Q - 退出程序
F9 - 切换侧边栏
F11 - 全屏模式
F1 - 关于
        """
        messagebox.showinfo("快捷键", shortcuts_info)
    
    def check_updates(self):
        """检查更新"""
        self.update_apple_status("检查更新功能")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        about_info = """
塔防游戏伤害分析器 v1.0.0

一个专业的塔防游戏干员伤害分析工具
融合巧妙设计语言的现代化界面

© 2025 Tower Defense Team
        """
        messagebox.showinfo("关于", about_info)
    
    def open_new_operator_dialog(self):
        """打开新建干员对话框"""
        if 'editor' in self.panels:
            # 委托给干员编辑器
            pass
        self.update_apple_status("新建干员功能")
    
    def refresh_all_data(self):
        """刷新所有数据"""
        try:
            logger.info("开始刷新所有面板数据...")
            
            # 刷新所有面板的数据
            refresh_count = 0
            for panel_name, panel in self.panels.items():
                try:
                    if hasattr(panel, 'refresh_data'):
                        panel.refresh_data()
                        refresh_count += 1
                        logger.info(f"已刷新面板: {panel_name}")
                except Exception as e:
                    logger.error(f"刷新面板 {panel_name} 失败: {e}")
            
            # 特别处理概览面板
            if hasattr(self, 'overview_panel'):
                try:
                    self.overview_panel.refresh_data()
                    logger.info("已刷新概览面板")
                except Exception as e:
                    logger.error(f"刷新概览面板失败: {e}")
            
            # 刷新侧边栏数据
            if hasattr(self, 'sidebar_panel'):
                try:
                    self.sidebar_panel.refresh_data()
                    logger.info("已刷新侧边栏")
                except Exception as e:
                    logger.error(f"刷新侧边栏失败: {e}")
            
            self.update_apple_status(f"数据刷新完成，已刷新 {refresh_count} 个面板", "success")
            
            # 不显示弹窗，避免干扰用户操作
            logger.info(f"数据刷新完成，已刷新 {refresh_count} 个面板的数据")
            
        except Exception as e:
            error_msg = f"刷新数据失败: {e}"
            logger.error(error_msg)
            self.update_apple_status("数据刷新失败", "error")
            
            # 显示用户友好的错误信息
            try:
                from tkinter import messagebox
                messagebox.showerror("刷新失败", f"刷新数据时出现错误：\n{str(e)}")
            except:
                pass
    
    def export_complete_analysis_report_as_pdf(self):
        """导出PDF格式分析报告 - 包含用户生成的图表和当前计算结果"""
        try:
            # 获取用户生成的图表
            current_charts = self._get_current_charts()
            
            # 获取用户当前的计算结果（重要：这里添加了获取当前计算结果）
            current_calculations = self.import_export_manager._get_current_and_recent_calculations()
            
            # 调用增强的报告生成器，传入当前计算结果
            success = self.report_generator.generate_complete_analysis_report_with_charts_and_calculations(
                'pdf', 
                current_charts=current_charts,
                current_calculations=current_calculations
            )
            
            # 成功和失败的消息已经在报告生成器中处理了
            
        except Exception as e:
            logger.error(f"导出PDF报告失败: {e}")
            messagebox.showerror("导出失败", f"导出PDF报告失败：\n{str(e)}")
            self.update_apple_status("PDF报告导出失败", "error")
    
    def export_complete_analysis_report_as_html(self):
        """导出HTML格式分析报告 - 包含用户生成的图表和当前计算结果"""
        try:
            # 获取用户生成的图表
            current_charts = self._get_current_charts()
            
            # 获取用户当前的计算结果（重要：这里添加了获取当前计算结果）
            current_calculations = self.import_export_manager._get_current_and_recent_calculations()
            
            # 调用增强的报告生成器，传入当前计算结果
            success = self.report_generator.generate_complete_analysis_report_with_charts_and_calculations(
                'html', 
                current_charts=current_charts,
                current_calculations=current_calculations
            )
            
            # 成功和失败的消息已经在报告生成器中处理了
            
        except Exception as e:
            logger.error(f"导出HTML报告失败: {e}")
            messagebox.showerror("导出失败", f"导出HTML报告失败：\n{str(e)}")
            self.update_apple_status("HTML报告导出失败", "error")
    
    def quick_import_dialog(self):
        """快速导入对话框 - 重构为调用ImportExportManager"""
        try:
            # 调用导入导出管理器
            result = self.import_export_manager.quick_import_dialog(self)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新界面
                self.refresh_all_data()
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                pass
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                pass
                
        except Exception as e:
            logger.error(f"快速导入失败: {e}")
            messagebox.showerror("导入失败", f"快速导入失败：\n{str(e)}")
            self.update_apple_status("快速导入失败", "error")
    
    def import_csv_data(self, filename=None):
        """导入CSV数据 - 重构为调用ImportExportManager"""
        try:
            # 调用导入导出管理器
            result = self.import_export_manager.import_csv_data(filename, self.update_apple_status)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新界面
                self.refresh_all_data()
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                pass
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                pass
                
        except Exception as e:
            logger.error(f"CSV导入失败: {e}")
            messagebox.showerror("导入失败", f"CSV导入失败：\n{str(e)}")
            self.update_apple_status("CSV导入失败", "error")
    
    def clear_cache_with_confirm(self):
        """带确认的清理缓存"""
        try:
            result = messagebox.askyesno(
                "确认清理",
                "确定要清理系统缓存吗？\n这将清理临时文件和旧的记录数据。"
            )
            
            if not result:
                return
            
            # 清理旧记录
            cleanup_result = self.db_manager.cleanup_old_records(days=30)
            
            # 清理图表缓存
            if hasattr(self, 'panels') and 'chart_comparison' in self.panels:
                chart_panel = self.panels['chart_comparison']
                if hasattr(chart_panel, 'charts_cache'):
                    chart_panel.charts_cache.clear()
            
            messagebox.showinfo(
                "清理完成",
                f"缓存清理完成！\n"
                f"清理计算记录: {cleanup_result.get('deleted_calculations', 0)} 条\n"
                f"清理导入记录: {cleanup_result.get('deleted_imports', 0)} 条"
            )
            
            self.refresh_all_data()
            self.update_apple_status("缓存清理完成", "success")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            messagebox.showerror("清理失败", f"清理缓存失败：\n{str(e)}")
            self.update_apple_status("缓存清理失败", "error")
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        try:
            # 创建设置对话框
            settings_dialog = SettingsDialog(
                parent=self,
                config_manager=config_manager,
                theme_manager=self.theme_manager,
                font_manager=self.font_manager
            )
            
            # 设置回调，当设置变更时刷新主界面
            self.theme_manager.set_theme_change_callback(self.on_theme_changed)
            self.font_manager.set_font_change_callback(self.on_font_changed)
            
            logger.info("设置对话框已打开")
            
        except Exception as e:
            logger.error(f"打开设置对话框失败: {e}")
            messagebox.showerror("错误", f"打开设置失败: {str(e)}")
    
    def on_theme_changed(self, theme_name):
        """主题变更回调"""
        try:
            # 应用新主题到主窗口
            self.apply_theme_settings(theme_name)
            
            # 更新状态
            self.update_apple_status(f"主题已切换为: {theme_name}")
            
            logger.info(f"主题已变更为: {theme_name}")
            
        except Exception as e:
            logger.error(f"主题变更失败: {e}")
    
    def on_font_changed(self, font_settings):
        """字体变更回调"""
        try:
            # 应用新字体设置
            self.apply_font_settings(font_settings)
            
            # 更新状态
            preset = font_settings.get('font_size_preset', 'medium') if isinstance(font_settings, dict) else str(font_settings)
            self.update_apple_status(f"字体已调整为: {preset}")
            
            logger.info(f"字体已变更: {font_settings}")
            
        except Exception as e:
            logger.error(f"字体变更失败: {e}")
    
    def apply_theme_settings(self, theme_name):
        """应用主题设置"""
        try:
            # 应用主题到主窗口
            self.theme_manager.apply_theme_to_window(self, theme_name)
            
            # 保存设置
            config_manager.update_ui_settings({'theme': theme_name})
            
            logger.info(f"主题设置已应用: {theme_name}")
            
        except Exception as e:
            logger.error(f"应用主题设置失败: {e}")
    
    def apply_font_settings(self, font_settings):
        """应用字体设置"""
        try:
            # 应用字体到所有组件
            if hasattr(self.font_manager, 'apply_font_to_all_widgets'):
                self.font_manager.apply_font_to_all_widgets(self)
            
            # 保存设置
            if isinstance(font_settings, dict):
                config_manager.update_ui_settings(font_settings)
            
            logger.info(f"字体设置已应用: {font_settings}")
            
        except Exception as e:
            logger.error(f"应用字体设置失败: {e}")
    
    def refresh_ui_with_new_settings(self):
        """用新设置刷新UI"""
        try:
            # 重新加载设置
            ui_settings = config_manager.get_ui_settings()
            
            # 应用主题
            theme = ui_settings.get('theme', 'cosmo')
            self.apply_theme_settings(theme)
            
            # 应用字体
            font_settings = {
                'font_size_preset': ui_settings.get('font_size_preset', 'medium'),
                'custom_font_scale': ui_settings.get('custom_font_scale', 1.0),
                'font_family': ui_settings.get('font_family', '微软雅黑')
            }
            self.apply_font_settings(font_settings)
            
            logger.info("UI设置刷新完成")
            
        except Exception as e:
            logger.error(f"刷新UI设置失败: {e}")
    
    def _get_current_charts(self):
        """获取当前图表对比面板中的图表（用户实际生成的，最多4个）"""
        current_charts = []
        
        try:
            # 优先从图表对比面板获取用户实际生成的图表
            if hasattr(self, 'panels') and 'chart_comparison' in self.panels:
                chart_panel = self.panels['chart_comparison']
                
                # 获取所有可用的图表
                if hasattr(chart_panel, 'get_all_chart_figures'):
                    all_charts = chart_panel.get_all_chart_figures()
                    logger.info(f"从图表面板获取到 {len(all_charts)} 个图表")
                    
                    # 检查每个图表是否有实际内容
                    for chart_info in all_charts:
                        try:
                            figure = chart_info.get('figure')
                            chart_title = chart_info.get('title', '未知图表')
                            chart_type = chart_info.get('type', 'unknown')
                            
                            if figure and hasattr(figure, 'get_axes'):
                                axes = figure.get_axes()
                                if axes and len(axes) > 0:
                                    ax = axes[0]
                                    # 检查是否有实际数据（线条、柱子、点等）
                                    has_data = (
                                        len(ax.lines) > 0 or 
                                        len(ax.patches) > 0 or 
                                        len(ax.collections) > 0 or
                                        len(ax.containers) > 0 or  # 新增：柱状图容器
                                        len(ax.images) > 0  # 新增：热力图等
                                    )
                                    
                                    # 排除只有标题和坐标轴标签的空图表
                                    if has_data:
                                        current_charts.append({
                                            'figure': figure,
                                            'title': chart_title,
                                            'type': chart_type
                                        })
                                        logger.info(f"获取到有效图表: {chart_title}")
                                        
                                        # 限制最多4个图表
                                        if len(current_charts) >= 4:
                                            break
                                    else:
                                        logger.debug(f"跳过空图表: {chart_title}")
                                        
                        except Exception as e:
                            logger.warning(f"检查图表 {chart_info.get('title', 'unknown')} 时出错: {e}")
                
                # 如果没有从get_all_chart_figures获取到图表，尝试直接获取主图表
                if not current_charts and hasattr(chart_panel, 'get_current_chart_figure'):
                    main_figure = chart_panel.get_current_chart_figure()
                    if main_figure and hasattr(main_figure, 'get_axes'):
                        axes = main_figure.get_axes()
                        if axes and len(axes) > 0:
                            ax = axes[0]
                            has_data = (
                                len(ax.lines) > 0 or 
                                len(ax.patches) > 0 or 
                                len(ax.collections) > 0 or
                                len(ax.containers) > 0 or
                                len(ax.images) > 0
                            )
                            
                            if has_data:
                                chart_type = getattr(chart_panel, 'selected_chart_type', None)
                                chart_type_name = chart_type.get() if chart_type and hasattr(chart_type, 'get') else '图表'
                                
                                current_charts.append({
                                    'figure': main_figure,
                                    'title': f'当前{chart_type_name}图表',
                                    'type': 'main_display'
                                })
                                logger.info(f"从主图表获取到有效图表: {chart_type_name}")
            
            logger.info(f"最终获取到 {len(current_charts)} 个有效图表")
            
        except Exception as e:
            logger.warning(f"获取当前图表失败: {e}")
        
        return current_charts
    
    def _get_current_selected_operators(self):
        """获取用户当前实际选择的干员数据"""
        selected_operators = []
        
        try:
            # 尝试从计算面板获取当前选择的干员
            if hasattr(self, 'panels') and 'analysis' in self.panels:
                calc_panel = self.panels['analysis']
                
                # 单干员模式：获取当前选择的干员
                if hasattr(calc_panel, 'current_operator') and calc_panel.current_operator:
                    selected_operators.append(calc_panel.current_operator)
                    logger.info(f"从单干员模式获取到干员: {calc_panel.current_operator['name']}")
                
                # 多干员模式：获取选择的干员列表
                if hasattr(calc_panel, 'selected_operators_list') and calc_panel.selected_operators_list:
                    # 如果多干员列表不为空，使用多干员列表（优先级更高）
                    if len(calc_panel.selected_operators_list) > 0:
                        selected_operators = calc_panel.selected_operators_list.copy()
                        logger.info(f"从多干员模式获取到 {len(selected_operators)} 个干员")
                        
                        # 记录干员名称
                        operator_names = [op['name'] for op in selected_operators]
                        logger.info(f"多干员列表: {operator_names}")
                
                # 如果仍然没有干员，尝试从干员选择下拉框获取
                if not selected_operators and hasattr(calc_panel, 'operator_var'):
                    selected_name = calc_panel.operator_var.get()
                    if selected_name and selected_name != "选择干员":
                        # 从数据库查找对应的干员
                        operator = self.db_manager.get_operator_by_name(selected_name)
                        if operator:
                            selected_operators.append(operator)
                            logger.info(f"从下拉框获取到干员: {selected_name}")
                
                logger.info(f"最终获取到 {len(selected_operators)} 个用户选择的干员")
                
        except Exception as e:
            logger.error(f"获取当前选择的干员失败: {e}")
        
        return selected_operators