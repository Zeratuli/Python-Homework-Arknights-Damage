# -*- coding: utf-8 -*-
"""
图表面板 - 负责图表的显示、交互和管理
"""

import logging
import sys
import time
from tkinter import ttk, messagebox, filedialog
from tkinter import *
from typing import Dict, Any, List, Optional, Callable, Tuple
import threading
import json
import os
from datetime import datetime

# matplotlib相关导入
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as patches

# 导入核心模块
from core.damage_calculator import DamageCalculator
from data.database_manager import DatabaseManager
from visualization.chart_factory import ChartFactory
from utils.event_manager import get_event_manager
from config.config_manager import config_manager
from visualization.enhanced_chart_factory import EnhancedChartFactory
from .components.chart_type_selector import ChartTypeSelector
from .components.chart_preview import ChartPreview
from .components.data_table import DataTable

logger = logging.getLogger(__name__)

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# 添加项目根目录到Python路径（如果还没有添加）
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加备用路径
backup_paths = [
    current_dir,
    os.path.join(current_dir, '..'),
    os.path.join(project_root, 'damage_analyzer'),
]

for path in backup_paths:
    abs_path = os.path.abspath(path)
    if abs_path not in sys.path:
        sys.path.append(abs_path)

try:
    from visualization.chart_factory import ChartFactory
    from core.damage_calculator import DamageCalculator
    # 导入事件管理器
    from utils.event_manager import get_event_manager
    
except ImportError as e:
    logger.error(f"导入错误: {e}")
    # 提供fallback
    ChartFactory = None
    DamageCalculator = None
    get_event_manager = None

class ChartPanel(ttk.Frame):
    """图表面板类 - 管理图表的显示和交互"""
    
    def __init__(self, parent, db_manager: DatabaseManager, **kwargs):
        """
        初始化图表面板
        
        Args:
            parent: 父窗口组件
            db_manager: 数据库管理器
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        
        # 存储核心组件
        self.db_manager = db_manager
        self.chart_factory = EnhancedChartFactory(parent)
        self.damage_calculator = DamageCalculator()
        self.event_manager = get_event_manager()
        
        # 状态变量
        self.current_chart = None
        self.current_figure = None
        self.chart_canvas = None
        self.chart_toolbar = None
        self.charts_cache = {}
        
        # 初始化界面变量
        self.enemy_def_var = tk.DoubleVar(value=300)
        self.enemy_mdef_var = tk.DoubleVar(value=30)
        self.duration_var = tk.DoubleVar(value=60)
        self.display_mode_var = tk.StringVar(value="embedded")
        
        # 创建界面
        self.create_ui()
        
        logger.info("图表面板初始化完成")
    
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右分栏
        paned_window = ttk.PanedWindow(main_frame, orient=HORIZONTAL)
        paned_window.pack(fill=BOTH, expand=True)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(paned_window, text="图表控制", padding=10)
        paned_window.add(control_frame, weight=1)
        
        # 右侧图表显示区
        chart_frame = ttk.LabelFrame(paned_window, text="图表显示", padding=10)
        paned_window.add(chart_frame, weight=3)
        
        self.setup_control_panel(control_frame)
        self.setup_chart_display(chart_frame)
    
    def setup_control_panel(self, parent):
        """设置控制面板"""
        
        # 创建可滚动的主容器
        main_canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 打包滚动组件
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 优化的鼠标滚轮事件绑定（防止重复绑定）
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 只在主画布上绑定一次，避免递归绑定污染
        if not hasattr(main_canvas, '_mousewheel_bound'):
            main_canvas.bind("<MouseWheel>", _on_mousewheel)
            main_canvas._mousewheel_bound = True
        
        # 在可滚动框架中创建内容
        
        # 干员选择区域（可折叠）
        operator_frame = ttk.LabelFrame(scrollable_frame, text="干员选择", padding=8)
        operator_frame.pack(fill=X, pady=3)
        
        # 干员列表（调整高度）
        self.operator_listbox = tk.Listbox(operator_frame, height=6, selectmode=tk.MULTIPLE)
        operator_scrollbar = ttk.Scrollbar(operator_frame, orient=VERTICAL, command=self.operator_listbox.yview)
        self.operator_listbox.configure(yscrollcommand=operator_scrollbar.set)
        
        self.operator_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        operator_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 干员操作按钮（使用更小的按钮）
        operator_btn_frame = ttk.Frame(operator_frame)
        operator_btn_frame.pack(fill=X, pady=3)
        
        ttk.Button(operator_btn_frame, text="刷新", bootstyle=INFO,
                  command=self.refresh_operator_list, width=6).pack(side=LEFT, padx=1)
        ttk.Button(operator_btn_frame, text="全选", bootstyle=SUCCESS,
                  command=self.select_all_operators, width=6).pack(side=LEFT, padx=1)
        ttk.Button(operator_btn_frame, text="清空", bootstyle=SECONDARY,
                  command=self.clear_operator_selection, width=6).pack(side=LEFT, padx=1)
        
        # 图表类型选择器（新组件）
        chart_selector_frame = ttk.LabelFrame(scrollable_frame, text="图表类型选择", padding=8)
        chart_selector_frame.pack(fill=X, pady=3)
        
        self.chart_type_selector = ChartTypeSelector(chart_selector_frame, 
                                                   callback=self.on_chart_type_changed)
        self.chart_type_selector.pack(fill=BOTH, expand=True)
        
        # 图表预览（新组件）
        preview_frame = ttk.LabelFrame(scrollable_frame, text="图表预览", padding=8)
        preview_frame.pack(fill=X, pady=3)
        
        self.chart_preview = ChartPreview(preview_frame, chart_factory=self.chart_factory)
        self.chart_preview.pack(fill=BOTH, expand=True)
        
        # 参数设置（使用更紧凑的滑块）
        param_frame = ttk.LabelFrame(scrollable_frame, text="参数设置", padding=6)
        param_frame.pack(fill=X, pady=3)
        
        # 敌人防御力
        ttk.Label(param_frame, text="敌人防御力:", font=("微软雅黑", 9)).pack(anchor=W)
        def_frame = ttk.Frame(param_frame)
        def_frame.pack(fill=X, pady=1)
        
        def_scale = ttk.Scale(def_frame, from_=0, to=1000, variable=self.enemy_def_var,
                             orient=HORIZONTAL, command=self.on_params_changed)
        def_scale.pack(side=LEFT, fill=X, expand=True)
        
        self.enemy_def_label = ttk.Label(def_frame, text="300", width=4, font=("微软雅黑", 8))
        self.enemy_def_label.pack(side=RIGHT)
        
        # 敌人法抗
        ttk.Label(param_frame, text="敌人法抗(%):", font=("微软雅黑", 9)).pack(anchor=W, pady=(3, 0))
        mdef_frame = ttk.Frame(param_frame)
        mdef_frame.pack(fill=X, pady=1)
        
        mdef_scale = ttk.Scale(mdef_frame, from_=0, to=100, variable=self.enemy_mdef_var,
                              orient=HORIZONTAL, command=self.on_params_changed)
        mdef_scale.pack(side=LEFT, fill=X, expand=True)
        
        self.enemy_mdef_label = ttk.Label(mdef_frame, text="30%", width=4, font=("微软雅黑", 8))
        self.enemy_mdef_label.pack(side=RIGHT)
        
        # 分析时长
        ttk.Label(param_frame, text="分析时长(秒):", font=("微软雅黑", 9)).pack(anchor=W, pady=(3, 0))
        duration_frame = ttk.Frame(param_frame)
        duration_frame.pack(fill=X, pady=1)
        
        duration_scale = ttk.Scale(duration_frame, from_=10, to=300, variable=self.duration_var,
                                  orient=HORIZONTAL, command=self.on_params_changed)
        duration_scale.pack(side=LEFT, fill=X, expand=True)
        
        self.duration_label = ttk.Label(duration_frame, text="60秒", width=4, font=("微软雅黑", 8))
        self.duration_label.pack(side=RIGHT)
        
        # 显示模式（更紧凑）
        display_frame = ttk.LabelFrame(scrollable_frame, text="显示模式", padding=6)
        display_frame.pack(fill=X, pady=3)
        
        ttk.Radiobutton(display_frame, text="嵌入显示", variable=self.display_mode_var,
                       value="embedded").pack(anchor=W, pady=1)
        ttk.Radiobutton(display_frame, text="独立窗口", variable=self.display_mode_var,
                       value="standalone").pack(anchor=W, pady=1)
        ttk.Radiobutton(display_frame, text="多图分栏", variable=self.display_mode_var,
                       value="subplot").pack(anchor=W, pady=1)
        
        # 操作按钮（固定在底部）
        action_frame = ttk.LabelFrame(scrollable_frame, text="操作", padding=6)
        action_frame.pack(fill=X, pady=3)
        
        button_grid = ttk.Frame(action_frame)
        button_grid.pack(fill=X)
        
        # 使用网格布局的按钮，每行两个
        ttk.Button(button_grid, text="生成图表", bootstyle=PRIMARY,
                  command=self.generate_comparison_chart).grid(row=0, column=0, sticky="ew", padx=2, pady=1)
        ttk.Button(button_grid, text="保存图表", bootstyle=SUCCESS,
                  command=self.save_current_chart).grid(row=0, column=1, sticky="ew", padx=2, pady=1)
        ttk.Button(button_grid, text="刷新图表", bootstyle=INFO,
                  command=self.refresh_chart).grid(row=1, column=0, sticky="ew", padx=2, pady=1)
        ttk.Button(button_grid, text="清空图表", bootstyle=DANGER,
                  command=self.clear_chart).grid(row=1, column=1, sticky="ew", padx=2, pady=1)
        
        # 配置网格权重
        button_grid.columnconfigure(0, weight=1)
        button_grid.columnconfigure(1, weight=1)
        
        # 数据表格（新组件）
        table_frame = ttk.LabelFrame(scrollable_frame, text="数据表格", padding=6)
        table_frame.pack(fill=X, pady=3)
        
        self.data_table = DataTable(table_frame, db_manager=self.db_manager)
        self.data_table.pack(fill=BOTH, expand=True)
        
        # 图表历史
        history_frame = ttk.LabelFrame(scrollable_frame, text="图表历史", padding=6)
        history_frame.pack(fill=X, pady=3)
        
        self.history_listbox = tk.Listbox(history_frame, height=3, font=("微软雅黑", 8))
        history_scrollbar = ttk.Scrollbar(history_frame, orient=VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        history_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.history_listbox.bind('<Double-Button-1>', self.load_from_history)
        
        # 历史操作按钮
        history_btn_frame = ttk.Frame(history_frame)
        history_btn_frame.pack(fill=X, pady=(3, 0))
        
        ttk.Button(history_btn_frame, text="加载", command=self.load_from_history, width=8).pack(side=LEFT, padx=2)
        ttk.Button(history_btn_frame, text="删除", command=self.delete_from_history, width=8).pack(side=LEFT, padx=2)
        ttk.Button(history_btn_frame, text="清空", command=self.clear_history, width=8).pack(side=LEFT, padx=2)
    
    def setup_chart_display(self, parent):
        """设置图表显示区域"""
        # 创建主要显示框架 - 修复display_frame未初始化问题
        self.display_frame = ttk.Frame(parent)
        self.display_frame.pack(fill=BOTH, expand=True)
        
        # 创建空白状态标签
        self.empty_label = ttk.Label(self.display_frame, text="请选择干员并点击生成图表", 
                                    font=("微软雅黑", 14), foreground="gray")
        self.empty_label.pack(expand=True)
        
        # 创建图表工具栏
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=X, pady=(0, 5))
        
        # 左侧图表操作按钮
        left_buttons = ttk.Frame(toolbar_frame)
        left_buttons.pack(side=LEFT)
        
        ttk.Button(left_buttons, text="生成图表", bootstyle=PRIMARY,
                  command=self.generate_comparison_chart, width=10).pack(side=LEFT, padx=2)
        ttk.Button(left_buttons, text="刷新", bootstyle=INFO,
                  command=self.refresh_chart, width=8).pack(side=LEFT, padx=2)
        ttk.Button(left_buttons, text="清空", bootstyle=SECONDARY,
                  command=self.clear_chart, width=8).pack(side=LEFT, padx=2)
        
        # 缩放控制按钮组
        zoom_frame = ttk.Frame(toolbar_frame)
        zoom_frame.pack(side=LEFT, padx=(20, 0))
        
        ttk.Button(zoom_frame, text="自适应缩放", bootstyle=SUCCESS,
                  command=self.auto_fit_current_chart, width=12).pack(side=LEFT, padx=2)
        ttk.Button(zoom_frame, text="重置缩放", bootstyle=WARNING,
                  command=self.reset_chart_zoom, width=10).pack(side=LEFT, padx=2)
        ttk.Button(zoom_frame, text="缩放历史", bootstyle=INFO,
                  command=self.show_zoom_history, width=10).pack(side=LEFT, padx=2)
        
        # 右侧保存按钮
        right_buttons = ttk.Frame(toolbar_frame)
        right_buttons.pack(side=RIGHT)
        
        ttk.Button(right_buttons, text="保存图表", bootstyle=SUCCESS,
                  command=self.save_current_chart, width=10).pack(side=LEFT, padx=2)
        
        # 创建图表显示容器
        self.chart_container = ttk.Frame(parent)
        self.chart_container.pack(fill=BOTH, expand=True)
        
        # 创建历史记录区域（初始隐藏）
        self.history_frame = ttk.LabelFrame(parent, text="图表历史", padding=5)
        # 不立即pack，在需要时显示
        
        self.history_listbox = tk.Listbox(self.history_frame, height=4)
        history_scrollbar = ttk.Scrollbar(self.history_frame, orient=VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        history_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定历史记录双击事件
        self.history_listbox.bind('<Double-1>', self.load_from_history)
        
        # 历史记录操作按钮
        history_btn_frame = ttk.Frame(self.history_frame)
        history_btn_frame.pack(fill=X, pady=(5, 0))
        
        ttk.Button(history_btn_frame, text="加载", bootstyle=PRIMARY,
                  command=self.load_from_history, width=8).pack(side=LEFT, padx=2)
        ttk.Button(history_btn_frame, text="删除", bootstyle=DANGER,
                  command=self.delete_from_history, width=8).pack(side=LEFT, padx=2)
        ttk.Button(history_btn_frame, text="清空", bootstyle=SECONDARY,
                  command=self.clear_history, width=8).pack(side=LEFT, padx=2)
        
        # 初始化缩放管理器
        self.zoom_manager = None
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.chart_zoom_manager import ChartZoomManager
            self.zoom_manager = ChartZoomManager()
        except Exception as e:
            print(f"初始化缩放管理器失败: {e}")
    
    def auto_fit_current_chart(self):
        """自适应缩放当前图表"""
        try:
            if not self.current_figure:
                messagebox.showwarning("警告", "没有图表需要缩放")
                return
            
            # 获取当前图表类型
            chart_type = self.chart_type_selector.get_selected_type()
            
            if self.zoom_manager:
                success = self.zoom_manager.auto_fit_chart(self.current_figure, chart_type)
                if success:
                    self.update_status("✅ 图表自适应缩放完成")
                else:
                    self.update_status("❌ 图表缩放失败")
            else:
                # 回退到基础缩放
                if self.chart_factory:
                    self.chart_factory.smart_auto_adjust_axes(self.current_figure, chart_type)
                    self.update_status("✅ 图表基础缩放完成")
                
        except Exception as e:
            messagebox.showerror("错误", f"自适应缩放失败: {str(e)}")
            self.update_status(f"❌ 缩放失败: {str(e)}")
    
    def reset_chart_zoom(self):
        """重置图表缩放"""
        try:
            if not self.current_figure:
                messagebox.showwarning("警告", "没有图表需要重置")
                return
            
            if self.zoom_manager and self.zoom_manager.zoom_history:
                # 恢复到最初状态（历史记录的最后一个）
                last_index = len(self.zoom_manager.zoom_history) - 1
                success = self.zoom_manager.restore_zoom_state(self.current_figure, last_index)
                if success:
                    self.update_status("✅ 图表缩放已重置")
                else:
                    # 如果恢复失败，使用默认重置
                    self._default_reset_zoom()
            else:
                self._default_reset_zoom()
                
        except Exception as e:
            messagebox.showerror("错误", f"重置缩放失败: {str(e)}")
            self.update_status(f"❌ 重置失败: {str(e)}")
    
    def _default_reset_zoom(self):
        """默认的缩放重置方法"""
        try:
            for ax in self.current_figure.get_axes():
                ax.autoscale()
                ax.relim()
                ax.autoscale_view()
            
            self.current_figure.canvas.draw_idle()
            self.update_status("✅ 图表缩放已重置（默认方式）")
            
        except Exception as e:
            print(f"默认重置缩放失败: {e}")
    
    def show_zoom_history(self):
        """显示/隐藏缩放历史面板"""
        try:
            if self.history_frame.winfo_viewable():
                # 隐藏历史面板
                self.history_frame.pack_forget()
                self.update_status("缩放历史面板已隐藏")
            else:
                # 显示历史面板
                self.history_frame.pack(fill=X, pady=(5, 0))
                self.update_zoom_history_display()
                self.update_status("缩放历史面板已显示")
                
        except Exception as e:
            messagebox.showerror("错误", f"显示缩放历史失败: {str(e)}")
    
    def update_zoom_history_display(self):
        """更新缩放历史显示"""
        try:
            self.history_listbox.delete(0, tk.END)
            
            if self.zoom_manager:
                history_info = self.zoom_manager.get_zoom_history_info()
                for info in history_info:
                    display_text = f"{info['index'] + 1}. {info['timestamp']} ({info['axes_count']}轴)"
                    self.history_listbox.insert(tk.END, display_text)
            
        except Exception as e:
            print(f"更新缩放历史显示失败: {e}")
    
    def load_from_history(self, event=None):
        """从历史记录加载缩放状态"""
        try:
            selection = self.history_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要加载的缩放状态")
                return
            
            if not self.current_figure:
                messagebox.showwarning("警告", "没有当前图表")
                return
            
            index = selection[0]
            if self.zoom_manager:
                success = self.zoom_manager.restore_zoom_state(self.current_figure, index)
                if success:
                    self.update_status(f"✅ 已加载缩放状态 #{index + 1}")
                else:
                    self.update_status(f"❌ 加载缩放状态失败")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载缩放状态失败: {str(e)}")
    
    def delete_from_history(self):
        """删除选中的历史记录"""
        try:
            selection = self.history_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要删除的历史记录")
                return
            
            index = selection[0]
            if self.zoom_manager and index < len(self.zoom_manager.zoom_history):
                self.zoom_manager.zoom_history.pop(index)
                self.update_zoom_history_display()
                self.update_status(f"✅ 已删除缩放历史 #{index + 1}")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除历史记录失败: {str(e)}")
    
    def clear_history(self):
        """清空缩放历史"""
        try:
            if self.zoom_manager:
                self.zoom_manager.clear_zoom_history()
                self.update_zoom_history_display()
                self.update_status("✅ 缩放历史已清空")
            
        except Exception as e:
            messagebox.showerror("错误", f"清空历史记录失败: {str(e)}")
    
    def clear_zoom_history(self):
        """清空所有缩放历史"""
        try:
            if self.zoom_manager:
                self.zoom_manager.clear_zoom_history()
                self.update_zoom_history_display()
                self.update_status("✅ 缩放历史已清空")
            
        except Exception as e:
            messagebox.showerror("错误", f"清空历史记录失败: {str(e)}")
    
    def refresh_operator_list(self):
        """刷新干员列表 - 虚拟化优化版本"""
        try:
            # 获取所有干员数据，但不立即渲染
            operators = self.db_manager.get_all_operators()
            
            # 缓存干员数据
            self._cached_operators = operators
            self._cached_operator_display = []
            
            # 预处理显示文本（异步生成）
            for operator in operators:
                display_text = f"{operator['name']} ({operator['class_type']}) - 攻击:{operator['atk']}"
                self._cached_operator_display.append(display_text)
            
            # 实现虚拟列表 - 只渲染可见区域
            self._render_visible_operators()
            
            self.update_status(f"已加载 {len(operators)} 个干员（虚拟化）")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新干员列表失败：{str(e)}")
    
    def _render_visible_operators(self):
        """渲染可见的干员列表项"""
        if not hasattr(self, '_cached_operator_display'):
            return
        
        # 清空现有列表
        self.operator_listbox.delete(0, tk.END)
        
        # 计算可见区域（简化版虚拟化）
        total_items = len(self._cached_operator_display)
        
        if total_items <= 100:
            # 少于100项时直接全部显示
            for display_text in self._cached_operator_display:
                self.operator_listbox.insert(tk.END, display_text)
        else:
            # 超过100项时分批加载
            self._load_batch_operators(0, min(50, total_items))
            
            # 设置滚动事件监听，动态加载更多项目
            if not hasattr(self.operator_listbox, '_scroll_bound'):
                self._bind_virtual_scroll()
    
    def _load_batch_operators(self, start_index: int, count: int):
        """分批加载干员列表项"""
        if not hasattr(self, '_cached_operator_display'):
            return
        
        end_index = min(start_index + count, len(self._cached_operator_display))
        
        for i in range(start_index, end_index):
            if i < len(self._cached_operator_display):
                self.operator_listbox.insert(tk.END, self._cached_operator_display[i])
    
    def _bind_virtual_scroll(self):
        """绑定虚拟滚动事件"""
        def on_scroll(*args):
            # 检查是否需要加载更多项目
            total_items = len(self._cached_operator_display)
            current_items = self.operator_listbox.size()
            
            if current_items < total_items:
                # 获取滚动位置
                try:
                    view_top, view_bottom = self.operator_listbox.yview()
                    if view_bottom > 0.8:  # 滚动到80%时加载更多
                        self._load_batch_operators(current_items, min(25, total_items - current_items))
                except:
                    pass
        
        # 绑定滚动事件
        self.operator_listbox.configure(yscrollcommand=lambda *args: (
            self.operator_listbox.master.children.get('!scrollbar', tk.Scrollbar()).set(*args),
            on_scroll(*args)
        ))
        self.operator_listbox._scroll_bound = True
    
    def select_all_operators(self):
        """选择所有干员"""
        self.operator_listbox.select_set(0, tk.END)
    
    def clear_operator_selection(self):
        """清空干员选择"""
        self.operator_listbox.selection_clear(0, tk.END)
    
    def on_chart_type_changed(self, chart_type=None):
        """图表类型改变事件"""
        if chart_type is None:
            chart_type = self.chart_type_selector.get_selected_type()
        
        self.current_chart_type = chart_type
        
        # 更新预览
        self.chart_preview.update_preview(chart_type)
        
        # 更新状态
        chart_info = self.chart_type_selector.get_chart_info(chart_type)
        if chart_info:
            self.update_status(f"选择图表类型：{chart_info['name']}")
    
    def on_params_changed(self, value=None):
        """参数改变事件"""
        self.enemy_def_label.configure(text=str(int(self.enemy_def_var.get())))
        self.enemy_mdef_label.configure(text=f"{int(self.enemy_mdef_var.get())}%")
        self.duration_label.configure(text=f"{int(self.duration_var.get())}秒")
    
    def get_chart_type_name(self):
        """获取当前图表类型名称"""
        chart_type = self.chart_type_selector.get_selected_type()
        chart_info = self.chart_type_selector.get_chart_info(chart_type)
        return chart_info['name'] if chart_info else "未知图表"
    
    def get_selected_operators(self):
        """获取选中的干员"""
        selected_indices = self.operator_listbox.curselection()
        selected_operators = []
        
        for index in selected_indices:
            if index < len(self.operators_data):
                selected_operators.append(self.operators_data[index])
        
        return selected_operators
    
    def generate_comparison_chart(self):
        """生成对比图表"""
        try:
            # 获取选中的干员
            selected_operators = self.get_selected_operators()
            
            if not selected_operators:
                messagebox.showwarning("警告", "请至少选择一个干员")
                return
            
            # 获取图表类型
            chart_type = self.chart_type_selector.get_selected_type()
            
            # 根据图表类型生成相应图表
            if chart_type == "damage_curve":
                fig = self.generate_damage_curve(selected_operators)
            elif chart_type == "radar_chart":
                fig = self.generate_radar_chart(selected_operators)
            elif chart_type == "bar_chart":
                fig = self.generate_bar_chart(selected_operators)
            elif chart_type == "pie_chart":
                fig = self.generate_pie_chart(selected_operators)
            elif chart_type == "heatmap":
                fig = self.generate_heatmap(selected_operators)
            elif chart_type == "timeline":
                fig = self.generate_timeline_chart(selected_operators)
            elif chart_type == "area_chart":
                fig = self.generate_area_chart(selected_operators)
            elif chart_type == "stacked_bar":
                fig = self.generate_stacked_bar_chart(selected_operators)
            elif chart_type == "box_plot":
                fig = self.generate_box_plot(selected_operators)
            elif chart_type == "scatter_plot":
                fig = self.generate_scatter_plot(selected_operators)
            elif chart_type == "3d_bar":
                fig = self.generate_3d_bar_chart(selected_operators)
            elif chart_type == "3d_scatter":
                fig = self.generate_3d_scatter_chart(selected_operators)
            else:
                messagebox.showwarning("警告", f"不支持的图表类型: {chart_type}")
                return
            
            if fig:
                self.display_chart(fig)
                self.update_status(f"已生成{self.get_chart_type_name()}图表")
                
                # 添加到历史记录
                self.add_to_history(chart_type, selected_operators)
                
                # 自动保存
                self.auto_save_chart(fig, chart_type)
                
                # 记录图表生成操作到数据库
                try:
                    if hasattr(self, 'db_manager') and self.db_manager:
                        # 准备参数
                        parameters = {
                            'chart_type': chart_type,
                            'operator_count': len(selected_operators),
                            'operator_names': [op.get('name', '未知') for op in selected_operators],
                            'enemy_defense': getattr(self, 'enemy_def', 0),
                            'enemy_magic_defense': getattr(self, 'enemy_mdef', 0)
                        }
                        
                        # 准备结果
                        chart_results = {
                            'chart_generated': True,
                            'chart_type_name': self.get_chart_type_name(),
                            'operators_analyzed': len(selected_operators)
                        }
                        
                        # 记录操作（图表生成通常没有单一干员ID，设为None）
                        self.db_manager.record_calculation(
                            operator_id=None,
                            calculation_type=f"图表生成_{chart_type}",
                            parameters=parameters,
                            results=chart_results
                        )
                        
                        # 刷新统计显示
                        self.refresh_statistics_display()
                        
                except Exception as e:
                    print(f"记录图表生成操作失败: {e}")
                    # 记录失败不影响主要功能
                
            else:
                messagebox.showerror("错误", "图表生成失败")
                
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            messagebox.showerror("错误", f"生成图表失败:\n{str(e)}")
    
    def generate_area_chart(self, operators):
        """生成面积图"""
        try:
            # 准备数据
            multiple_series = {}
            defense_range = np.arange(0, 1001, 50)
            
            for op in operators:
                damage_data = []
                for def_val in defense_range:
                    # 计算伤害
                    damage = self.calculate_damage_against_defense(op, def_val)
                    damage_data.append((def_val, damage))
                
                multiple_series[op['name']] = damage_data
            
            # 使用增强图表工厂生成面积图
            fig = self.chart_factory.create_area_chart(
                data=[],
                title="干员伤害面积图",
                xlabel="敌人防御力",
                ylabel="伤害值",
                multiple_series=multiple_series,
                stacked=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成面积图失败: {e}")
            return None
    
    def generate_stacked_bar_chart(self, operators):
        """生成堆叠柱状图"""
        try:
            # 准备数据
            data = {}
            
            for op in operators:
                data[op['name']] = {
                    '攻击力': op.get('atk', 0),
                    '生命值': op.get('hp', 0) / 100,  # 缩放以便显示
                    '防御力': op.get('def', 0),
                    'DPS': self.calculate_operator_dps(op)
                }
            
            # 使用增强图表工厂生成堆叠柱状图
            fig = self.chart_factory.create_stacked_bar_chart(
                data=data,
                title="干员属性堆叠对比"
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成堆叠柱状图失败: {e}")
            return None
    
    def generate_box_plot(self, operators):
        """生成箱线图"""
        try:
            # 准备数据
            data = {}
            
            # 模拟不同防御值下的伤害分布
            defense_values = [0, 200, 400, 600, 800]
            
            for op in operators:
                damage_values = []
                for def_val in defense_values:
                    damage = self.calculate_damage_against_defense(op, def_val)
                    damage_values.append(damage)
                
                data[op['name']] = damage_values
            
            # 使用增强图表工厂生成箱线图
            fig = self.chart_factory.create_box_plot(
                data=data,
                title="干员伤害分布箱线图"
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成箱线图失败: {e}")
            return None
    
    def generate_scatter_plot(self, operators):
        """生成散点图"""
        try:
            # 准备数据
            data = []
            categories = []
            
            for op in operators:
                x = op.get('atk', 0)  # X轴：攻击力
                y = self.calculate_operator_dps(op)  # Y轴：DPS
                data.append((x, y))
                categories.append(op.get('class_type', '未知'))
            
            # 使用增强图表工厂生成散点图
            fig = self.chart_factory.create_scatter_plot(
                data=data,
                title="攻击力 vs DPS 散点图",
                xlabel="攻击力",
                ylabel="DPS",
                categories=categories
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成散点图失败: {e}")
            return None
    
    def generate_3d_bar_chart(self, operators):
        """生成3D柱状图"""
        try:
            # 准备数据
            data = {}
            
            for op in operators:
                data[op['name']] = {
                    '攻击力': op.get('atk', 0),
                    '生命值': op.get('hp', 0) / 100,  # 缩放
                    '防御力': op.get('def', 0),
                    'DPS': self.calculate_operator_dps(op)
                }
            
            # 使用增强图表工厂生成3D柱状图
            fig = self.chart_factory.create_3d_bar_chart(
                data=data,
                title="干员属性3D对比"
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成3D柱状图失败: {e}")
            return None
    
    def generate_3d_scatter_chart(self, operators):
        """生成3D散点图"""
        try:
            # 准备数据
            data = []
            categories = []
            
            for op in operators:
                x = op.get('atk', 0)  # X轴：攻击力
                y = op.get('hp', 0) / 100  # Y轴：生命值（缩放）
                z = self.calculate_operator_dps(op)  # Z轴：DPS
                data.append((x, y, z))
                categories.append(op.get('class_type', '未知'))
            
            # 使用增强图表工厂生成3D散点图
            fig = self.chart_factory.create_3d_scatter_plot(
                data=data,
                title="干员属性3D散点图",
                categories=categories
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成3D散点图失败: {e}")
            return None
    
    def calculate_damage_against_defense(self, operator, defense):
        """计算对抗指定防御力的伤害"""
        try:
            atk = operator.get('atk', 0)
            atk_type = operator.get('atk_type', '物理伤害')
            
            if atk_type in ['物伤', '物理伤害']:
                # 物理伤害计算
                damage = max(atk - defense, atk * 0.05)
            else:
                # 法术伤害计算
                mdef_percent = self.enemy_mdef_var.get() / 100
                damage = atk * (1 - mdef_percent)
            
            return max(damage, 0)
            
        except Exception as e:
            logger.error(f"计算伤害失败: {e}")
            return 0
    
    def calculate_operator_dps(self, operator):
        """计算干员DPS"""
        try:
            atk = operator.get('atk', 0)
            atk_speed = operator.get('atk_speed', 1.0)
            
            # 简化的DPS计算
            if atk_speed > 0:
                dps = atk / atk_speed
            else:
                dps = 0
            
            return dps
            
        except Exception as e:
            logger.error(f"计算DPS失败: {e}")
            return 0
    
    def add_to_history(self, chart_type, operators):
        """添加到历史记录"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            operator_names = [op['name'] for op in operators]
            chart_info = self.chart_type_selector.get_chart_info(chart_type)
            chart_name = chart_info['name'] if chart_info else chart_type
            
            history_item = {
                'timestamp': timestamp,
                'chart_type': chart_type,
                'chart_name': chart_name,
                'operators': operators,
                'operator_names': operator_names,
                'params': self.get_current_chart_params()
            }
            
            self.chart_history.append(history_item)
            
            # 更新历史列表显示
            display_text = f"{timestamp} - {chart_name} ({len(operators)}个干员)"
            self.history_listbox.insert(tk.END, display_text)
            
            # 限制历史记录数量
            if len(self.chart_history) > 50:
                self.chart_history.pop(0)
                self.history_listbox.delete(0)
                
        except Exception as e:
            logger.error(f"添加历史记录失败: {e}")
    
    def generate_damage_curve(self, operators):
        """生成伤害-防御曲线图"""
        display_mode = self.display_mode_var.get()
        
        if len(operators) == 1:
            # 单个干员的伤害曲线
            operator = operators[0]
            figure = self.chart_factory.create_damage_curve(operator)
            self.display_chart(figure)
        else:
            # 多个干员对比
            multiple_series = {}
            for operator in operators:
                curve_data = self.damage_calculator.get_damage_curve(operator, 1000, 25)
                multiple_series[operator['name']] = curve_data
            
            figure = self.chart_factory.create_line_chart(
                [], 
                title="干员伤害-防御对比曲线",
                xlabel="敌人防御力", 
                ylabel="DPS",
                multiple_series=multiple_series
            )
            self.display_chart(figure)
    
    def generate_heatmap(self, operators):
        """生成热力图"""
        import numpy as np
        
        if len(operators) < 2:
            messagebox.showwarning("警告", "热力图需要至少2个干员进行对比")
            return
        
        # 构建热力图数据矩阵
        metrics = ['DPS', 'DPH', 'HPS', '破甲线', '性价比']
        data_matrix = []
        operator_names = []
        
        enemy_def = self.enemy_def_var.get()
        enemy_mdef = self.enemy_mdef_var.get()
        
        for operator in operators:
            performance = self.damage_calculator.calculate_operator_performance(operator, enemy_def, enemy_mdef)
            row_data = [
                performance['dps'],
                performance['dph'], 
                performance.get('hps', 0),
                performance['armor_break_point'],
                performance['cost_efficiency']
            ]
            data_matrix.append(row_data)
            operator_names.append(operator['name'])
        
        data_array = np.array(data_matrix)
        figure = self.chart_factory.create_heatmap(data_array, operator_names, metrics, "干员性能热力图")
        self.display_chart(figure)
    
    def generate_timeline_chart(self, operators):
        """生成时间轴伤害图"""
        duration = self.duration_var.get()
        enemy_def = self.enemy_def_var.get()
        enemy_mdef = self.enemy_mdef_var.get()
        
        timeline_data = {}
        for operator in operators:
            timeline = self.damage_calculator.calculate_timeline_damage(operator, duration, enemy_def, enemy_mdef)
            timeline_data[operator['name']] = timeline
        
        figure = self.chart_factory.create_timeline_chart(timeline_data, "干员时间轴伤害分析")
        self.display_chart(figure)
    
    def save_current_chart(self):
        """保存当前图表"""
        try:
            if hasattr(self, 'current_figure') and self.current_figure:
                # 获取当前图表
                figure = self.current_figure
                chart_id = f"current_{self.current_chart_type}"
                matplotlib_backend._save_figure(figure, chart_id)
            else:
                messagebox.showwarning("警告", "没有可保存的图表")
        except Exception as e:
            messagebox.showerror("错误", f"保存图表失败：{str(e)}")
    
    def refresh_chart(self):
        """刷新当前图表"""
        if self.current_figure:
            self.generate_comparison_chart()
        else:
            messagebox.showinfo("提示", "没有可刷新的图表")
    
    def clear_chart(self):
        """清空当前图表"""
        try:
            # 清理旧的渲染任务（简化版）
            self._cleanup_old_render_tasks()
            
            # 清理UI组件
            if self.current_figure:
                self.current_figure = None
            
            # 显示空状态
            if hasattr(self, 'display_frame') and self.display_frame:
                self.empty_label = ttk.Label(
                    self.display_frame, 
                    text="请选择干员并生成图表",
                    font=("微软雅黑", 12),
                    foreground="gray"
                )
                self.empty_label.pack(expand=True)
            
            self.update_status("图表已清空")
            
        except Exception as e:
            logger.error(f"清空图表失败: {e}")
            self.update_status("清空图表时发生错误")
    
    def update_status(self, message):
        """更新状态栏"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(f"状态: {message}")

    def get_current_chart(self) -> Optional[Tuple[str, Any]]:
        """获取当前显示的图表"""
        try:
            if self.current_figure:
                chart_name = f"{self.get_chart_type_name()}_{datetime.datetime.now().strftime('%H%M%S')}"
                return (chart_name, self.current_figure)
            return None
        except Exception as e:
            print(f"获取当前图表失败: {e}")
            return None
    
    def get_current_charts(self) -> List[Tuple[str, Any]]:
        """获取所有当前图表"""
        charts = []
        try:
            # 获取当前图表
            current = self.get_current_chart()
            if current:
                charts.append(current)
            
            # 获取历史图表
            if hasattr(self, 'chart_history') and self.chart_history:
                for history_item in self.chart_history:
                    if 'figure' in history_item and 'title' in history_item:
                        charts.append((history_item['title'], history_item['figure']))
            
        except Exception as e:
            print(f"获取图表列表失败: {e}")
        
        return charts
    
    def get_chart_history(self) -> List[Tuple[str, Any]]:
        """获取图表历史记录"""
        charts = []
        try:
            if hasattr(self, 'chart_history') and self.chart_history:
                for i, history_item in enumerate(self.chart_history):
                    if 'figure' in history_item and 'title' in history_item:
                        chart_name = f"{history_item['title']}_{i+1}"
                        charts.append((chart_name, history_item['figure']))
        except Exception as e:
            print(f"获取图表历史失败: {e}")
        
        return charts
    
    def prepare_charts_for_export(self) -> List[Tuple[str, Any]]:
        """准备图表用于导出"""
        export_charts = []
        
        try:
            # 获取当前所有图表
            charts = self.get_current_charts()
            
            for chart_name, figure in charts:
                # 优化图表用于导出
                if self.chart_factory:
                    self.chart_factory.optimize_chart_for_export(figure, export_dpi=300)
                
                export_charts.append((chart_name, figure))
                
        except Exception as e:
            print(f"准备导出图表失败: {e}")
        
        return export_charts
    
    def export_current_chart_data(self) -> Dict[str, Any]:
        """导出当前图表的数据和设置"""
        try:
            chart_data = {
                'chart_type': self.chart_type_selector.get_selected_type(),
                'selected_operators': self.get_selected_operators(),
                'chart_params': self.get_current_chart_params(),
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            return chart_data
            
        except Exception as e:
            print(f"导出图表数据失败: {e}")
            return {}
    
    def get_current_chart_params(self) -> Dict[str, Any]:
        """获取当前图表参数"""
        try:
            params = {}
            
            # 获取基本参数
            if hasattr(self, 'param_entries'):
                for param_name, entry in self.param_entries.items():
                    try:
                        value = entry.get()
                        if value:
                            params[param_name] = float(value) if value.replace('.', '').isdigit() else value
                    except Exception:
                        pass
            
            # 添加图表类型特定参数
            chart_type = self.chart_type_selector.get_selected_type()
            if chart_type == "伤害曲线":
                params.update({
                    'time_range': 300,  # 默认5分钟
                    'interval': 1,      # 默认1秒间隔
                    'include_healing': True
                })
            elif chart_type == "雷达图":
                params.update({
                    'attributes': ['攻击力', '生命值', '防御力', '法术抗性', '攻击速度'],
                    'normalize': True
                })
            
            return params
            
        except Exception as e:
            print(f"获取图表参数失败: {e}")
            return {}
    
    def set_chart_for_export(self, chart_type: str, operators: List[Dict], params: Dict = None):
        """为导出设置图表"""
        try:
            # 设置图表类型
            self.chart_type_selector.set_selected_type(chart_type)
            
            # 设置干员选择
            if hasattr(self, 'operator_listbox'):
                # 清除当前选择
                self.operator_listbox.selection_clear(0, tk.END)
                
                # 选择指定干员
                for i, operator in enumerate(self.operators):
                    if operator in operators:
                        self.operator_listbox.selection_set(i)
            
            # 设置参数
            if params and hasattr(self, 'param_entries'):
                for param_name, value in params.items():
                    if param_name in self.param_entries:
                        self.param_entries[param_name].delete(0, tk.END)
                        self.param_entries[param_name].insert(0, str(value))
            
            # 生成图表
            self.generate_comparison_chart()
            
        except Exception as e:
            print(f"设置导出图表失败: {e}")
    
    def auto_save_chart(self, figure: Figure, chart_type: str) -> None:
        """自动保存图表到缓存"""
        try:
            chart_name = f"{self.get_chart_type_name()}_{datetime.datetime.now().strftime('%H%M%S')}"
            
            # 保存到内存缓存
            self.chart_cache[chart_name] = {
                'figure': figure,
                'type': chart_type,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # ... existing code ...
        except Exception as e:
            print(f"自动保存图表失败: {e}")
    
    def refresh_statistics_display(self):
        """刷新统计显示"""
        try:
            # 尝试刷新父窗口的统计显示
            parent_window = self.winfo_toplevel()
            if hasattr(parent_window, 'panels') and 'sidebar' in parent_window.panels:
                parent_window.panels['sidebar'].refresh_stats()
            if hasattr(parent_window, 'panels') and 'overview' in parent_window.panels:
                parent_window.panels['overview'].refresh_data()
        except Exception as e:
            print(f"刷新统计显示失败: {e}")

    # ... existing code ... 