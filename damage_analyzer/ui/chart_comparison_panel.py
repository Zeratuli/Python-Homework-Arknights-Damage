# -*- coding: utf-8 -*-
"""
图表对比分析面板 - 重新设计的现代化图表分析界面
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List, Optional, Callable, Tuple
import threading
import json
import os
from datetime import datetime

# matplotlib相关导入
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# 导入核心模块（使用安全导入）
try:
    from core.damage_calculator import DamageCalculator
except ImportError:
    DamageCalculator = None

try:
    from data.database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from visualization.enhanced_chart_factory import EnhancedChartFactory
except ImportError:
    EnhancedChartFactory = None

try:
    from utils.event_manager import get_event_manager
except ImportError:
    get_event_manager = lambda: None

try:
    from config.config_manager import config_manager
except ImportError:
    config_manager = None

# 导入隐形滚动框架
try:
    from ui.invisible_scroll_frame import InvisibleScrollFrame
except ImportError:
    InvisibleScrollFrame = None

logger = logging.getLogger(__name__)

class ChartComparisonPanel(ttk.Frame):
    """图表对比分析面板 - 现代化设计"""
    
    def __init__(self, parent, db_manager=None, **kwargs):
        """
        初始化图表对比分析面板
        
        Args:
            parent: 父窗口组件
            db_manager: 数据库管理器
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        
        # 最优先初始化的属性 - 防止AttributeError
        self.preview_figure = None
        self.preview_canvas = None
        self.main_figure = None
        self.main_canvas = None
        
        # 存储核心组件（安全初始化）
        self.db_manager = db_manager
        
        # 安全初始化组件
        try:
            self.chart_factory = EnhancedChartFactory(parent) if EnhancedChartFactory else None
        except:
            self.chart_factory = None
            
        try:
            self.damage_calculator = DamageCalculator() if DamageCalculator else None
        except:
            self.damage_calculator = None
            
        try:
            self.event_manager = get_event_manager() if get_event_manager else None
        except:
            self.event_manager = None
        
        # 状态变量
        self.current_chart = None
        self.current_figure = None
        self.chart_canvas = None
        self.chart_toolbar = None
        self.charts_cache = {}
        self.selected_chart_type = tk.StringVar(value="line")
        
        # 新增UI控制变量
        self.x_axis_mode = tk.StringVar(value="time")
        self.auto_preview_var = tk.BooleanVar(value=True)
        self.chart_quality_var = tk.StringVar(value="高")
        
        # 参数变量
        self.enemy_def_var = tk.DoubleVar(value=300)
        self.enemy_mdef_var = tk.DoubleVar(value=30)
        self.time_range_var = tk.DoubleVar(value=60)
        
        # 数据变量
        self.chart_data = []
        self.operators_data = []
        
        # 搜索和筛选变量
        self.search_var = tk.StringVar()
        self.selected_classes = set(['先锋', '近卫', '重装', '狙击', '术师', '辅助', '医疗', '特种'])  # 默认全选
        self.damage_type_filter_var = tk.StringVar(value="全部")
        self.all_operators = []
        self.filtered_operators = []
        self.class_vars = {}  # 存储每个职业的BooleanVar
        self.select_all_var = tk.BooleanVar(value=True)
        
        # 初始化职业复选框变量
        classes = ['先锋', '近卫', '重装', '狙击', '术师', '辅助', '医疗', '特种']
        for class_name in classes:
            self.class_vars[class_name] = tk.BooleanVar(value=True)
        
        # 状态标签变量 - 移除表格相关的标签
        self.chart_title_label = None
        self.chart_status_label = None
        self.chart_desc_label = None
        
        # 创建界面
        try:
            self.create_ui()
            self.load_initial_data()
        except Exception as e:
            logger.error(f"创建界面失败: {e}")
            self.create_error_ui()
        
        logger.info("图表对比分析面板初始化完成")
    
    def create_error_ui(self):
        """创建错误界面"""
        error_frame = ttk.Frame(self)
        error_frame.pack(expand=True, fill=tk.BOTH)
        
        # 使用更友好的提示信息，而不是红色错误文字
        info_label = ttk.Label(
            error_frame, 
            text="图表对比分析功能正在加载中...\n请稍后或检查相关依赖",
            font=("Arial", 12),
            foreground="gray",
            justify=tk.CENTER
        )
        info_label.pack(expand=True)
        
        # 添加重试按钮
        retry_button = ttk.Button(
            error_frame,
            text="重新加载",
            command=self.retry_initialization
        )
        retry_button.pack(pady=10)
    
    def retry_initialization(self):
        """重新初始化"""
        try:
            # 清除错误界面
            for widget in self.winfo_children():
                widget.destroy()
            
            # 重新创建界面
            self.create_ui()
            self.load_initial_data()
            
        except Exception as e:
            logger.error(f"重新初始化失败: {e}")
    
    def create_ui(self):
        """创建用户界面 - 按照设计布局"""
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建水平分割的主布局
        main_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧控制面板
        self.create_left_panel(main_paned)
        
        # 右侧主显示区域
        self.create_right_panel(main_paned)
        
        # 设置分割比例
        main_paned.add(self.left_panel, weight=1)
        main_paned.add(self.right_panel, weight=3)
        
        # 延迟选择默认图表类型，避免方法调用顺序问题
        self.after_idle(self._setup_default_chart_type)
    
    def _setup_default_chart_type(self):
        """延迟设置默认图表类型"""
        try:
            self.select_chart_type("line")
        except Exception as e:
            logger.warning(f"设置默认图表类型失败: {e}")
    
    def create_left_panel(self, parent):
        """创建左侧控制面板 - 集成隐形滚动功能"""
        self.left_panel = ttk.LabelFrame(parent, text="图表对比分析面板", padding=10)
        
        # 创建隐形滚动容器（如果可用）
        if InvisibleScrollFrame:
            self.left_scroll_frame = InvisibleScrollFrame(self.left_panel, scroll_speed=3)
            self.left_scroll_frame.pack(fill=tk.BOTH, expand=True)
            
            # 在滚动容器中创建内容
            content_frame = self.left_scroll_frame.scrollable_frame
            self.left_content_frame = content_frame
        else:
            # 如果隐形滚动框架不可用，直接使用left_panel
            self.left_content_frame = self.left_panel
        
        # 在内容框架中创建各个区域
        self.create_chart_selector()
        self.create_parameter_controls()
        self.create_chart_preview()
    
    def create_chart_selector(self):
        """创建图表选择器 - 重新设计UI布局"""
        selector_frame = ttk.LabelFrame(self.left_content_frame, text="📈 图表类型选择", padding=10)
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建图表类型网格布局
        charts_grid = ttk.Frame(selector_frame)
        charts_grid.pack(fill=tk.X)
        
        # 扩展的图表类型，使用更直观的图标
        chart_types = [
            ("📈 折线图", "line", "显示数据趋势变化", 0, 0),
            ("📊 柱状图", "bar", "比较不同项目数值", 0, 1),
            ("🥧 饼图", "pie", "显示数据占比关系", 1, 0),
            ("📡 雷达图", "radar", "多维度属性对比", 1, 1),
            ("🔥 热力图", "heatmap", "数据分布可视化", 2, 0),
            ("📦 箱线图", "boxplot", "数据分布统计", 2, 1),
            ("🌊 面积图", "area", "堆叠数据展示", 3, 0),
            ("💠 散点图", "scatter", "数据点分布关系", 3, 1)
        ]
        
        self.chart_buttons = {}
        
        for text, chart_type, tooltip, row, col in chart_types:
            btn = ttk.Button(
                charts_grid,
                text=text,
                command=lambda ct=chart_type: self.select_chart_type(ct),
                width=12,
                bootstyle="outline"
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            
            self.chart_buttons[chart_type] = btn
            self.create_tooltip(btn, tooltip)
        
        # 配置网格权重
        charts_grid.grid_columnconfigure(0, weight=1)
        charts_grid.grid_columnconfigure(1, weight=1)
        
        # 添加图表描述标签
        self.chart_desc_label = ttk.Label(
            selector_frame,
            text="选择图表类型以预览效果",
            font=("微软雅黑", 9),
            foreground="gray"
        )
        self.chart_desc_label.pack(anchor="w")
        
        # 初始化时直接选择默认图表类型
        # 不使用after_idle，因为这在初始化时可能还没有准备好
    
    def create_parameter_controls(self):
        """创建参数控制区域 - 不包含干员选择"""
        param_frame = ttk.LabelFrame(self.left_content_frame, text="⚙️ 参数控制", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 横坐标模式选择区域
        axis_frame = ttk.LabelFrame(param_frame, text="📊 横坐标模式", padding=8)
        axis_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 使用网格布局的单选按钮
        axis_options = [
            ("⏱️ 时间轴", "time", "显示随时间变化的伤害曲线"),
            ("🛡️ 防御力", "defense", "显示不同防御力下的DPS"),
            ("🔮 法术抗性", "magic_defense", "显示不同法抗下的DPS")
        ]
        
        for i, (text, mode, tooltip) in enumerate(axis_options):
            radio_btn = ttk.Radiobutton(
                axis_frame,
                text=text,
                variable=self.x_axis_mode,
                value=mode,
                command=self.on_axis_mode_changed
            )
            radio_btn.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
            self.create_tooltip(radio_btn, tooltip)
        
        # 参数调节区域
        params_frame = ttk.LabelFrame(param_frame, text="⚙️ 参数设置", padding=8)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 防御力参数
        self.create_parameter_slider(
            params_frame, 
            "🛡️ 敌人防御力:", 
            self.enemy_def_var, 
            0, 1000, 50,
            row=0
        )
        
        # 法抗参数  
        self.create_parameter_slider(
            params_frame,
            "🔮 敌人法抗:",
            self.enemy_mdef_var,
            0, 100, 5,
            row=1
        )
        
        # 时间范围参数
        self.create_parameter_slider(
            params_frame,
            "⏱️ 时间范围(秒):",
            self.time_range_var,
            10, 300, 10,
            row=2
        )
        
        # 实时预览开关
        preview_frame = ttk.Frame(param_frame)
        preview_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Checkbutton(
            preview_frame,
            text="🔄 实时预览",
            variable=self.auto_preview_var,
            command=self.toggle_auto_preview
        ).pack(side=tk.LEFT)
        
        # 重置按钮
        ttk.Button(
            preview_frame,
            text="↩️ 重置",
            command=self.reset_parameters,
            bootstyle="warning",
            width=8
        ).pack(side=tk.RIGHT)

    def create_operator_selection_area(self, parent):
        """创建干员选择区域 - 使用完整的属性表格"""
        self.operator_selection_area = ttk.LabelFrame(parent, text="👥 干员选择与操作", padding=10)
        self.operator_selection_area.pack(fill=tk.BOTH, expand=True)
        
        # 控制按钮区域
        control_frame = ttk.Frame(self.operator_selection_area)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 左侧选择按钮
        left_btns = ttk.Frame(control_frame)
        left_btns.pack(side=tk.LEFT)
        
        ttk.Button(
            left_btns,
            text="✅ 全选",
            command=self.select_all_operators,
            width=6
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            left_btns,
            text="❌ 清空",
            command=self.deselect_all_operators,
            width=6
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            left_btns,
            text="🔄 刷新",
            command=self.refresh_operator_list,
            width=6
        ).pack(side=tk.LEFT, padx=1)
        
        # 中间状态显示
        self.selection_status_label = ttk.Label(
            control_frame, 
            text="已选择 0 个", 
            font=("微软雅黑", 9),
            bootstyle="info"
        )
        self.selection_status_label.pack(side=tk.LEFT, padx=(10, 10))
        
        # 右侧功能按钮
        right_btns = ttk.Frame(control_frame)
        right_btns.pack(side=tk.RIGHT)
        
        ttk.Button(
            right_btns,
            text="📊 生成图表",
            command=self.generate_main_chart,
            bootstyle="primary",
            width=10
        ).pack(side=tk.RIGHT, padx=2)
        
        # 创建搜索筛选区域
        self.create_search_filter_area(self.operator_selection_area)
        
        # 干员表格区域
        list_container = ttk.Frame(self.operator_selection_area)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # 导入SortableTreeview组件
        try:
            from ui.components.sortable_treeview import NumericSortableTreeview
            
            # 定义完整的干员表格列 - 列为属性，行为干员
            columns = ('id', 'name', 'class_type', 'hp', 'atk', 'def', 'mdef', 'atk_speed', 'atk_type', 
                      'block_count', 'cost')
            
            # 指定数值列用于排序
            numeric_columns = ['id', 'hp', 'atk', 'def', 'mdef', 'atk_speed', 'block_count', 'cost']
            
            # 创建可排序的表格
            self.operator_treeview = NumericSortableTreeview(
                list_container,
                columns=columns,
                show='tree headings',
                height=8,
                selectmode='extended',
                numeric_columns=numeric_columns
            )
            
            # 设置列标题和宽度
            self.operator_treeview.heading('#0', text='', anchor='w')
            self.operator_treeview.column('#0', width=0, stretch=False)  # 隐藏第一列
            
            # 基础信息列
            self.operator_treeview.heading('id', text='ID', anchor='center')
            self.operator_treeview.column('id', width=35, anchor='center')
            
            self.operator_treeview.heading('name', text='名称', anchor='w')
            self.operator_treeview.column('name', width=80, anchor='w')
            
            self.operator_treeview.heading('class_type', text='职业', anchor='center')
            self.operator_treeview.column('class_type', width=50, anchor='center')
            
            # 基础属性列
            self.operator_treeview.heading('hp', text='生命值', anchor='center')
            self.operator_treeview.column('hp', width=60, anchor='center')
            
            self.operator_treeview.heading('atk', text='攻击力', anchor='center')
            self.operator_treeview.column('atk', width=60, anchor='center')
            
            self.operator_treeview.heading('def', text='防御力', anchor='center')
            self.operator_treeview.column('def', width=60, anchor='center')
            
            self.operator_treeview.heading('mdef', text='法抗', anchor='center')
            self.operator_treeview.column('mdef', width=45, anchor='center')
            
            self.operator_treeview.heading('atk_speed', text='攻速', anchor='center')
            self.operator_treeview.column('atk_speed', width=50, anchor='center')
            
            self.operator_treeview.heading('atk_type', text='攻击类型', anchor='center')
            self.operator_treeview.column('atk_type', width=70, anchor='center')
            
            self.operator_treeview.heading('block_count', text='阻挡', anchor='center')
            self.operator_treeview.column('block_count', width=45, anchor='center')
            
            self.operator_treeview.heading('cost', text='费用', anchor='center')
            self.operator_treeview.column('cost', width=45, anchor='center')
            
            # 启用所有列的排序功能
            self.operator_treeview.enable_sorting()
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.operator_treeview.yview)
            self.operator_treeview.configure(yscrollcommand=scrollbar.set)
            
            # 布局
            self.operator_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 绑定选择事件
            self.operator_treeview.bind('<<TreeviewSelect>>', self.on_operator_selection_changed)
            
            # 保持向后兼容性，创建一个假的listbox属性
            self.operator_listbox = self.operator_treeview
            
        except ImportError:
            # 如果导入失败，回退到原来的Listbox
            self.operator_listbox = tk.Listbox(
                list_container,
                height=8,
                selectmode=tk.MULTIPLE,
                font=("微软雅黑", 9)
            )
            
            # 滚动条
            scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.operator_listbox.yview)
            self.operator_listbox.configure(yscrollcommand=scrollbar.set)
            
            # 布局
            self.operator_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 绑定选择事件
            self.operator_listbox.bind('<<ListboxSelect>>', self.on_operator_selection_changed)
        
        # 初始化干员列表
        self.refresh_operator_list()
    
    def create_search_filter_area(self, parent):
        """创建搜索和筛选区域"""
        # 搜索筛选容器
        filter_frame = ttk.LabelFrame(parent, text="🔍 搜索与筛选", padding=8)
        filter_frame.pack(fill=tk.X, pady=(10, 10))
        
        # 第一行：搜索框
        search_row = ttk.Frame(filter_frame)
        search_row.pack(fill=tk.X, pady=(0, 6))
        
        ttk.Label(search_row, text="搜索干员：").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=(5, 8))
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 添加搜索提示
        ttk.Label(search_row, text="(输入干员名称)", 
                 font=("微软雅黑", 8), foreground="gray").pack(side=tk.LEFT, padx=(3, 0))
        
        # 搜索按钮
        ttk.Button(search_row, text="🔍", width=3, 
                  command=self.filter_operators).pack(side=tk.LEFT, padx=2)
        
        # 第二行：职业多选
        class_row = ttk.Frame(filter_frame)  
        class_row.pack(fill=tk.X, pady=(0, 6))
        self.create_class_filter_area(class_row)
        
        # 第三行：伤害类型和统计信息
        info_row = ttk.Frame(filter_frame)
        info_row.pack(fill=tk.X)
        
        # 伤害类型过滤
        ttk.Label(info_row, text="伤害类型：").pack(side=tk.LEFT)
        damage_type_combo = ttk.Combobox(info_row, textvariable=self.damage_type_filter_var,
                                       values=["全部", "物伤", "法伤"], state="readonly", width=6,
                                       style="Apple.TCombobox")
        damage_type_combo.pack(side=tk.LEFT, padx=(3, 15))
        damage_type_combo.bind('<<ComboboxSelected>>', self.on_damage_type_filter_changed)
        
        # 筛选结果统计
        self.filter_stats_label = ttk.Label(info_row, text="", 
                                          font=("微软雅黑", 8), foreground="blue")
        self.filter_stats_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 重置按钮
        ttk.Button(info_row, text="重置筛选", 
                  command=self.reset_filters).pack(side=tk.RIGHT)
    
    def create_class_filter_area(self, parent):
        """创建职业多选复选框"""
        ttk.Label(parent, text="职业筛选：").pack(side=tk.LEFT)
        
        classes = ['先锋', '近卫', '重装', '狙击', '术师', '辅助', '医疗', '特种']
        
        # 全选控制
        select_all_cb = ttk.Checkbutton(parent, text="全选", variable=self.select_all_var,
                                       command=self.toggle_select_all)
        select_all_cb.pack(side=tk.LEFT, padx=(3, 8))
        
        # 各职业复选框
        for class_name in classes:
            cb = ttk.Checkbutton(parent, text=class_name, variable=self.class_vars[class_name],
                               command=self.on_class_selection_changed)
            cb.pack(side=tk.LEFT, padx=1)
    
    def determine_attack_type(self, operator):
        """判断干员攻击类型"""
        # 攻击类型映射表（基于职业判断）
        CLASS_ATTACK_TYPE = {
            '先锋': '物伤', '近卫': '物伤', '重装': '物伤', '狙击': '物伤',
            '术师': '法伤', '辅助': '法伤', '医疗': '法伤', '特种': '物伤'
        }
        
        # 优先检查数据库中的攻击类型字段
        if 'atk_type' in operator and operator['atk_type']:
            return operator['atk_type']
        
        # 根据职业类型判断
        class_type = operator.get('class_type', '')
        return CLASS_ATTACK_TYPE.get(class_type, '物伤')
    
    def filter_operators(self):
        """根据当前筛选条件过滤干员列表"""
        if not self.all_operators:
            return
        
        search_text = self.search_var.get().lower().strip()
        selected_classes = {cls for cls, var in self.class_vars.items() if var.get()}
        damage_type = self.damage_type_filter_var.get()
        
        self.filtered_operators = []
        
        for operator in self.all_operators:
            # 名称搜索筛选
            if search_text and search_text not in operator['name'].lower():
                continue
                
            # 职业筛选 (多选OR逻辑)
            if not selected_classes or operator['class_type'] not in selected_classes:
                continue
                
            # 伤害类型筛选
            if damage_type != "全部":
                operator_damage_type = self.determine_attack_type(operator)
                if (damage_type == "物伤" and operator_damage_type not in ['物伤', '物理伤害']) or \
                   (damage_type == "法伤" and operator_damage_type not in ['法伤', '法术伤害']):
                    continue
                    
            self.filtered_operators.append(operator)
        
        self.update_operator_display()
        self.update_filter_statistics()
    
    def update_operator_display(self):
        """更新干员列表显示"""
        # 清空现有数据
        if hasattr(self, 'operator_treeview'):
            for item in self.operator_treeview.get_children():
                self.operator_treeview.delete(item)
            
            # 添加筛选后的数据
            if self.filtered_operators:
                for operator in self.filtered_operators:
                    values = (
                        operator.get('id', ''),
                        operator.get('name', ''),
                        operator.get('class_type', ''),
                        operator.get('hp', ''),
                        operator.get('atk', ''),
                        operator.get('def', ''),
                        operator.get('mdef', ''),
                        operator.get('atk_speed', ''),
                        operator.get('atk_type', ''),
                        operator.get('block_count', ''),
                        operator.get('cost', '')
                    )
                    self.operator_treeview.insert('', 'end', values=values)
            else:
                # 无结果时显示友好提示
                self.operator_treeview.insert('', 'end', values=(
                    '', '未找到符合条件的干员', '', '', '', '', '', '', '', '', ''
                ))
    
    def on_search_changed(self, event=None):
        """搜索条件变化"""
        # 添加防抖动处理
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self.filter_operators)
    
    def on_class_selection_changed(self):
        """处理职业复选框变化事件"""
        # 更新全选状态
        selected_count = sum(1 for var in self.class_vars.values() if var.get())
        total_count = len(self.class_vars)
        
        if selected_count == total_count:
            self.select_all_var.set(True)
        elif selected_count == 0:
            self.select_all_var.set(False)
        else:
            # 部分选中，设置为False但不影响显示
            self.select_all_var.set(False)
        
        self.filter_operators()
    
    def toggle_select_all(self):
        """处理全选复选框逻辑"""
        select_all = self.select_all_var.get()
        for var in self.class_vars.values():
            var.set(select_all)
        
        # 更新选中的职业集合
        if select_all:
            self.selected_classes = set(self.class_vars.keys())
        else:
            self.selected_classes.clear()
        
        self.filter_operators()
    
    def on_damage_type_filter_changed(self, event=None):
        """处理伤害类型筛选变化"""
        self.filter_operators()
    
    def reset_filters(self):
        """重置所有筛选条件"""
        # 重置搜索框
        self.search_var.set("")
        
        # 重置职业选择为全选
        self.select_all_var.set(True)
        for var in self.class_vars.values():
            var.set(True)
        self.selected_classes = set(self.class_vars.keys())
        
        # 重置伤害类型
        self.damage_type_filter_var.set("全部")
        
        # 重新筛选
        self.filter_operators()
    
    def update_filter_statistics(self):
        """更新筛选统计信息显示"""
        total = len(self.all_operators)
        filtered = len(self.filtered_operators)
        
        if total == filtered:
            stats_text = f"显示全部 {total} 个干员"
        else:
            stats_text = f"显示 {filtered}/{total} 个干员"
            
        if hasattr(self, 'filter_stats_label'):
            self.filter_stats_label.config(text=stats_text)
        
        # 同时更新选择状态标签，显示当前筛选结果
        if hasattr(self, 'selection_status_label'):
            selected_count = len(self.get_selected_operators())
            self.selection_status_label.config(text=f"已选择 {selected_count} 个")

    def create_data_table_area(self, parent):
        """创建数据表格区域"""
        self.table_area = ttk.LabelFrame(parent, text="📊 数据分析区域", padding=10)
        
        # 直接创建数据表格组件，不再重复创建干员选择区域
        self.create_data_table_widget(self.table_area)

    def create_data_table_widget(self, parent):
        """创建数据表格组件 - 简化功能"""
        self.data_table_widget = ttk.Frame(parent)  # 改为Frame，因为parent已经是LabelFrame
        self.data_table_widget.pack(fill=tk.BOTH, expand=True)
        
        # 创建表格容器
        table_container = ttk.Frame(self.data_table_widget)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建表格
        columns = ("干员名称", "职业", "DPS", "攻击力", "生命值", "技能倍率")
        self.data_tree = ttk.Treeview(table_container, columns=columns, show="headings", height=8)
        
        # 设置列标题和宽度
        column_widths = {"干员名称": 80, "职业": 60, "DPS": 70, "攻击力": 70, "生命值": 70, "技能倍率": 80}
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=column_widths.get(col, 80), anchor=tk.CENTER)
        
        # 添加滚动条
        table_scrollbar_y = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.data_tree.yview)
        table_scrollbar_x = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=table_scrollbar_y.set, xscrollcommand=table_scrollbar_x.set)
        
        # 正确布局表格和滚动条
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        table_scrollbar_y.grid(row=0, column=1, sticky="ns")
        table_scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        # 配置网格权重
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # 表格操作按钮
        table_btn_frame = ttk.Frame(self.data_table_widget)
        table_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 只保留必要的按钮
        ttk.Button(
            table_btn_frame,
            text="📋 导出数据",
            command=self.export_table_data
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            table_btn_frame,
            text="🔄 刷新数据", 
            command=self.refresh_table_data
        ).pack(side=tk.RIGHT, padx=2)

    def update_data_table(self, operators):
        """更新数据表格 - 优化显示内容"""
        # 清空现有数据
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # 插入新数据
        for op in operators:
            self.data_tree.insert('', 'end', values=(
                op.get('name', '')[:8],  # 限制名称长度
                op.get('class_type', '')[:6],  # 限制职业长度
                f"{op.get('dps', 0):.0f}",
                f"{op.get('attack', 0):.0f}",
                f"{op.get('hp', 0):.0f}",
                f"{op.get('skill_mult', 0):.1f}"
            ))
    
    def load_initial_data(self):
        """加载初始数据"""
        try:
            # 初始化干员数据为空列表
            self.operators_data = []
            
            # 尝试从数据库加载干员数据
            if self.db_manager:
                try:
                    operators = self.db_manager.get_all_operators()
                    self.operators_data = operators or []
                except Exception as e:
                    logger.warning(f"从数据库加载干员数据失败: {e}")
                    self.operators_data = []
            
            # 安全的预览刷新
            try:
                self.refresh_preview()
            except Exception as e:
                logger.warning(f"刷新预览失败: {e}")
            
        except Exception as e:
            logger.error(f"加载初始数据失败: {e}")
    
    # 工具栏功能实现
    def refresh_main_chart(self):
        """刷新主图表"""
        self.generate_main_chart()
    
    def save_chart(self):
        """保存图表"""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showwarning("警告", "matplotlib未安装，无法保存图表")
            return
            
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG 文件", "*.png"),
                    ("PDF 文件", "*.pdf"),
                    ("SVG 文件", "*.svg")
                ]
            )
            if filename and self.main_figure:
                self.main_figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("保存成功", f"图表已保存到: {filename}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存图表失败: {e}")

    def export_image(self):
        """导出图表图像"""
        self.save_chart()

    def show_chart_settings(self):
        """显示图表设置"""
        messagebox.showinfo("图表设置", "图表设置功能开发中...")

    def copy_chart_data(self):
        """复制图表数据"""
        try:
            chart_data = self.get_chart_data()
            if chart_data:
                import json
                self.clipboard_clear()
                self.clipboard_append(json.dumps(chart_data, ensure_ascii=False, indent=2))
                messagebox.showinfo("复制成功", "图表数据已复制到剪贴板")
            else:
                messagebox.showwarning("警告", "没有可复制的图表数据")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制图表数据失败: {e}")

    def toggle_zoom(self):
        """切换缩放模式"""
        messagebox.showinfo("缩放模式", "使用matplotlib工具栏进行缩放操作")

    def toggle_measure(self):
        """切换测量模式"""
        messagebox.showinfo("测量模式", "测量功能开发中...")

    def get_chart_data(self):
        """获取当前图表数据，用于导出功能 - 简化版本"""
        try:
            # 获取当前选中的干员数据
            operators = self.get_selected_operators()
            if not operators:
                return []
            
            chart_data = []
            chart_type = self.selected_chart_type.get()
            x_axis_mode = self.x_axis_mode.get()
            
            # 根据图表类型生成基础数据
            if chart_type == "line":
                if x_axis_mode == "time":
                    # 时间轴数据
                    time_range = int(self.time_range_var.get())
                    for t in range(0, time_range + 1, 5):  # 每5秒一个数据点
                        data_point = {"time": t}
                        for op in operators:
                            dps = self.calculate_dps(op)
                            cumulative_damage = dps * t
                            data_point[op.get('name', 'Unknown')] = cumulative_damage
                        chart_data.append(data_point)
                else:
                    # 防御力轴数据
                    for defense in range(0, 1001, 50):
                        data_point = {"defense": defense}
                        for op in operators:
                            dps = self.calculate_dps_vs_defense(op, defense)
                            data_point[op.get('name', 'Unknown')] = dps
                        chart_data.append(data_point)
                        
            elif chart_type == "bar":
                # 柱状图数据
                for op in operators:
                    chart_data.append({
                        "operator": op.get('name', 'Unknown'),
                        "dps": self.calculate_dps(op),
                        "dph": self.calculate_dph(op),
                        "attack": op.get('atk', 0),
                        "hp": op.get('hp', 0)
                    })
            
            else:
                # 其他图表类型的基础数据
                for op in operators:
                    chart_data.append({
                        "operator": op.get('name', 'Unknown'),
                        "value": self.calculate_dps(op)
                    })
            
            return chart_data
            
        except Exception as e:
            logger.error(f"获取图表数据失败: {e}")
            return []
    
    def get_chart_metadata(self):
        """获取图表元数据"""
        try:
            return {
                "图表类型": self.selected_chart_type.get(),
                "X轴模式": self.x_axis_mode.get(),
                "敌人防御力": self.enemy_def_var.get(),
                "敌人法抗": self.enemy_mdef_var.get(),
                "时间范围": self.time_range_var.get(),
                "选中干员数量": len(self.get_selected_operators()),
                "数据点数量": len(self.get_chart_data()),
                "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"获取图表元数据失败: {e}")
            return {}
    
    def export_chart_data_to_excel(self):
        """导出图表数据到Excel"""
        try:
            chart_data = self.get_chart_data()
            if not chart_data:
                messagebox.showwarning("警告", "没有可导出的图表数据")
                return
            
            filename = filedialog.asksaveasfilename(
                title="导出图表数据",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx")]
            )
            
            if not filename:
                return
            
            try:
                import pandas as pd
                
                # 创建DataFrame
                df = pd.DataFrame(chart_data)
                
                # 创建Excel写入器
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # 写入图表数据
                    df.to_excel(writer, sheet_name='图表数据', index=False)
                    
                    # 写入元数据
                    metadata = self.get_chart_metadata()
                    metadata_df = pd.DataFrame(list(metadata.items()), columns=['属性', '值'])
                    metadata_df.to_excel(writer, sheet_name='图表信息', index=False)
                
                messagebox.showinfo("导出成功", f"图表数据已导出到: {filename}")
                
            except ImportError:
                messagebox.showerror("错误", "需要安装pandas库才能导出Excel文件")
                
        except Exception as e:
            logger.error(f"导出图表数据失败: {e}")
            messagebox.showerror("导出失败", f"导出图表数据失败: {e}")

    def save_current_chart(self):
        """保存当前图表 - 自动命名和保存"""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showwarning("警告", "matplotlib未安装，无法保存图表")
            return
            
        try:
            # 确保charts目录存在
            charts_dir = os.path.join(os.path.dirname(__file__), '..', 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_type = self.selected_chart_type.get()
            x_mode = self.x_axis_mode.get()
            filename = f"chart_{chart_type}_{x_mode}_{timestamp}.png"
            filepath = os.path.join(charts_dir, filename)
            
            # 保存主图表
            if self.main_figure is not None:
                self.main_figure.savefig(filepath, dpi=300, bbox_inches='tight', 
                                       facecolor='white', edgecolor='none')
                
                # 同时保存预览图
                if self.preview_figure is not None:
                    preview_filename = f"preview_{chart_type}_{x_mode}_{timestamp}.png"
                    preview_filepath = os.path.join(charts_dir, preview_filename)
                    self.preview_figure.savefig(preview_filepath, dpi=200, bbox_inches='tight',
                                              facecolor='white', edgecolor='none')
                
                logger.info(f"图表已保存: {filepath}")
                messagebox.showinfo("保存成功", f"图表已自动保存到:\n{filepath}")
                
                return filepath  # 返回文件路径供其他功能使用
            else:
                messagebox.showwarning("警告", "没有图表可以保存")
                return None
                
        except Exception as e:
            logger.error(f"保存图表失败: {e}")
            messagebox.showerror("保存失败", f"保存图表时出现错误：\n{str(e)}")
            return None

    def create_tooltip(self, widget, text):
        """创建工具提示"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def apply_preview(self):
        """应用预览到主图表"""
        self.generate_main_chart()

    def create_right_panel(self, parent):
        """创建右侧主显示区域"""
        self.right_panel = ttk.Frame(parent)
        
        # 创建垂直分割的右侧布局
        right_paned = ttk.PanedWindow(self.right_panel, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分：主图表显示区域
        self.create_main_chart_area(right_paned)
        
        # 下半部分：干员选择区域（简化后）
        self.create_bottom_area(right_paned)
        
        # 设置分割比例 - 给图表区域更多空间
        right_paned.add(self.chart_area, weight=3)  # 从2改为3
        right_paned.add(self.operator_selection_area, weight=1)  # 修改为operator_selection_area
    
    def create_main_chart_area(self, parent):
        """创建主图表显示区域"""
        self.chart_area = ttk.LabelFrame(parent, text="📊 图表显示区域", padding=10)
        
        # 图表工具栏
        toolbar_frame = ttk.Frame(self.chart_area)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 图表标题
        self.chart_title_label = ttk.Label(
            toolbar_frame,
            text="📈 折线图 - 伤害趋势分析",
            font=("微软雅黑", 12, "bold"),
            bootstyle="primary"
        )
        self.chart_title_label.pack(side=tk.LEFT)
        
        # 图表操作按钮
        btn_frame = ttk.Frame(toolbar_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            btn_frame,
            text="🔄 刷新",
            command=self.refresh_main_chart,
            bootstyle="outline-primary",
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="💾 保存",
            command=self.save_chart,
            bootstyle="outline-success",
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="📤 导出",
            command=self.export_image,
            bootstyle="outline-info",
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # 主图表画布区域
        canvas_frame = ttk.Frame(self.chart_area)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建matplotlib图表
        self.create_main_chart_canvas(canvas_frame)
        
        # 图表状态标签
        self.chart_status_label = ttk.Label(
            self.chart_area,
            text="📊 准备就绪 - 请选择图表类型和参数",
            font=("微软雅黑", 9),
            bootstyle="secondary"
        )
        self.chart_status_label.pack(pady=(5, 0))
    
    def create_main_chart_canvas(self, parent):
        """创建主图表画布"""
        try:
            # 创建matplotlib图形
            self.main_figure = plt.Figure(figsize=(10, 6), dpi=100)
            self.main_figure.patch.set_facecolor('white')
            
            # 创建画布
            self.main_canvas = FigureCanvasTkAgg(self.main_figure, parent)
            self.main_canvas.draw()
            self.main_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # 添加工具栏
            self.chart_toolbar = NavigationToolbar2Tk(self.main_canvas, parent)
            self.chart_toolbar.update()
            
            # 初始化空图表
            self.create_empty_chart()
            
        except Exception as e:
            logger.error(f"创建主图表画布失败: {e}")
            # 创建错误提示
            error_label = ttk.Label(
                parent,
                text=f"图表创建失败: {str(e)}",
                font=("Arial", 10),
                foreground="red"
            )
            error_label.pack(expand=True)
    
    def create_empty_chart(self):
        """创建空的初始图表"""
        try:
            self.main_figure.clear()
            ax = self.main_figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS', 'SimHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            ax.text(0.5, 0.5, '📊 选择图表类型开始分析\n\n👈 请在左侧选择图表类型和参数', 
                   ha='center', va='center', fontsize=14, 
                   transform=ax.transAxes, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            self.main_figure.tight_layout()
            self.main_canvas.draw()
            
        except Exception as e:
            logger.error(f"创建空图表失败: {e}")
    
    def create_bottom_area(self, parent):
        """创建底部区域 - 简化为仅包含干员选择"""
        # 创建干员选择区域
        self.create_operator_selection_area(parent)
    
    def create_chart_preview(self):
        """创建图表预览"""
        preview_frame = ttk.LabelFrame(self.left_content_frame, text="📊 图表预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        try:
            if MATPLOTLIB_AVAILABLE:
                # 创建matplotlib图表
                from matplotlib.figure import Figure
                # 调整预览图表尺寸，使其更适合左侧面板
                self.preview_figure = Figure(figsize=(3.5, 2.5), dpi=80)
                self.preview_figure.patch.set_facecolor('white')
                
                # 创建画布
                self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, preview_frame)
                self.preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
                
                # 创建初始预览图表
                self.create_preview_chart()
            else:
                # matplotlib不可用时的备用方案
                fallback_label = ttk.Label(
                    preview_frame,
                    text="预览功能需要matplotlib库\n请安装后重启应用",
                    justify=tk.CENTER
                )
                fallback_label.pack(expand=True)
                
        except Exception as e:
            logger.error(f"创建图表预览失败: {e}")
            # 创建备用预览
            fallback_label = ttk.Label(
                preview_frame,
                text="预览暂时不可用",
                justify=tk.CENTER
            )
            fallback_label.pack(expand=True)
    
    def create_preview_chart(self):
        """创建预览图表"""
        try:
            if hasattr(self, 'preview_figure') and self.preview_figure is not None:
                # 清除现有内容
                self.preview_figure.clear()
                
                # 设置中文字体
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS', 'SimHei']
                plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                plt.rcParams['axes.unicode_minus'] = False
                
                # 创建子图，调整边距以改善比例
                ax = self.preview_figure.add_subplot(111)
                
                # 创建示例数据
                chart_type = self.selected_chart_type.get()
                
                if chart_type == "line":
                    x = [0, 200, 400, 600, 800]
                    y = [100, 80, 60, 40, 20]
                    ax.plot(x, y, 'b-', linewidth=2, marker='o')
                    ax.set_title("折线图预览", fontsize=10)
                    ax.set_xlabel("防御力", fontsize=8)
                    ax.set_ylabel("DPS", fontsize=8)
                    
                elif chart_type == "bar":
                    categories = ['干员A', '干员B', '干员C', '干员D']
                    values = [300, 250, 400, 350]
                    bars = ax.bar(categories, values, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
                    ax.set_title("柱状图预览", fontsize=10)
                    ax.set_ylabel("DPS", fontsize=8)
                    ax.tick_params(axis='x', labelsize=7)
                    
                elif chart_type == "pie":
                    labels = ['干员A', '干员B', '干员C', '干员D']
                    sizes = [25, 30, 20, 25]
                    ax.pie(sizes, labels=labels, autopct='%1.1f%%', textprops={'fontsize': 7})
                    ax.set_title("饼图预览", fontsize=10)
                    
                elif chart_type == "radar":
                    import numpy as np
                    categories = ['攻击', '生命', '防御', '速度']
                    values = [0.8, 0.6, 0.7, 0.5]
                    
                    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
                    values += values[:1]
                    angles += angles[:1]
                    
                    ax.plot(angles, values, 'o-', linewidth=2, color='blue')
                    ax.fill(angles, values, alpha=0.25, color='blue')
                    ax.set_xticks(angles[:-1])
                    ax.set_xticklabels(categories, fontsize=7)
                    ax.set_title("雷达图预览", fontsize=10)
                    
                elif chart_type == "heatmap":
                    import numpy as np
                    data = np.random.rand(4, 5)
                    im = ax.imshow(data, cmap='viridis', aspect='auto')
                    ax.set_title("热力图预览", fontsize=10)
                    ax.set_xlabel("参数", fontsize=8)
                    ax.set_ylabel("干员", fontsize=8)
                    
                elif chart_type == "boxplot":
                    data = [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6], [1, 3, 5, 7, 9]]
                    ax.boxplot(data, labels=['职业A', '职业B', '职业C'])
                    ax.set_title("箱线图预览", fontsize=10)
                    ax.set_ylabel("DPS", fontsize=8)
                    ax.tick_params(axis='x', labelsize=7)
                    
                elif chart_type == "area":
                    x = range(5)
                    y1 = [1, 2, 3, 4, 5]
                    y2 = [2, 3, 4, 5, 6]
                    ax.fill_between(x, y1, alpha=0.5, label='干员A')
                    ax.fill_between(x, y1, [y1[i] + y2[i] for i in range(len(y1))], alpha=0.5, label='干员B')
                    ax.set_title("面积图预览", fontsize=10)
                    ax.set_xlabel("时间", fontsize=8)
                    ax.set_ylabel("伤害", fontsize=8)
                    ax.legend(fontsize=7)
                    
                elif chart_type == "scatter":
                    x = [100, 200, 300, 400, 500]
                    y = [1000, 2000, 1500, 2500, 3000]
                    ax.scatter(x, y, s=50, alpha=0.6, c=['red', 'blue', 'green', 'orange', 'purple'])
                    ax.set_title("散点图预览", fontsize=10)
                    ax.set_xlabel("攻击力", fontsize=8)
                    ax.set_ylabel("生命值", fontsize=8)
                    
                else:
                    # 默认显示
                    x = [0, 200, 400, 600, 800]
                    y = [100, 80, 60, 40, 20]
                    ax.plot(x, y, 'b-', linewidth=2)
                    ax.set_title("图表预览", fontsize=10)
                
                # 调整子图参数以改善显示比例
                ax.tick_params(labelsize=7)
                
                # 调整布局，减少边距
                self.preview_figure.subplots_adjust(left=0.15, right=0.95, top=0.85, bottom=0.15)
                
                # 更新画布
                if hasattr(self, 'preview_canvas') and self.preview_canvas:
                    self.preview_canvas.draw()
                    
        except Exception as e:
            logger.error(f"创建预览图表失败: {e}")
    
    def select_chart_type(self, chart_type):
        """选择图表类型"""
        try:
            self.selected_chart_type.set(chart_type)
            
            # 更新按钮样式
            for btn_type, btn in self.chart_buttons.items():
                if btn_type == chart_type:
                    btn.configure(bootstyle="primary")
                else:
                    btn.configure(bootstyle="outline")
            
            # 更新描述
            descriptions = {
                "line": "📈 折线图：显示数据趋势变化",
                "bar": "📊 柱状图：比较不同项目数值",
                "pie": "🥧 饼图：显示数据占比关系",
                "radar": "📡 雷达图：多维度属性对比",
                "heatmap": "🔥 热力图：数据分布可视化",
                "boxplot": "📦 箱线图：数据分布统计",
                "area": "🌊 面积图：堆叠数据展示",
                "scatter": "💠 散点图：数据点分布关系"
            }
            
            if self.chart_desc_label:
                self.chart_desc_label.configure(text=descriptions.get(chart_type, "图表类型"))
            
            # 更新图表标题
            if self.chart_title_label:
                chart_names = {
                    "line": "📈 折线图 - 伤害趋势分析",
                    "bar": "📊 柱状图 - 数值对比分析",
                    "pie": "🥧 饼图 - 占比分析",
                    "radar": "📡 雷达图 - 多维度对比",
                    "heatmap": "🔥 热力图 - 分布分析",
                    "boxplot": "📦 箱线图 - 统计分析",
                    "area": "🌊 面积图 - 堆叠分析",
                    "scatter": "💠 散点图 - 关系分析"
                }
                self.chart_title_label.configure(text=chart_names.get(chart_type, "图表分析"))
            
            # 自动刷新预览
            if self.auto_preview_var.get():
                self.refresh_preview()
                
        except Exception as e:
            logger.error(f"选择图表类型失败: {e}")
    
    def on_axis_mode_changed(self):
        """横坐标模式改变事件"""
        try:
            mode = self.x_axis_mode.get()
            logger.info(f"横坐标模式切换到: {mode}")
            
            # 刷新主图表
            self.generate_main_chart()
            
            # 自动刷新预览
            if self.auto_preview_var.get():
                self.refresh_preview()
                
        except Exception as e:
            logger.error(f"横坐标模式改变处理失败: {e}")
    
    def on_auto_preview_changed(self):
        """自动预览设置改变事件"""
        if self.auto_preview_var.get():
            self.refresh_preview()
    
    def refresh_preview(self):
        """刷新预览图表"""
        try:
            self.create_preview_chart()
        except Exception as e:
            logger.error(f"刷新预览失败: {e}")

    def create_parameter_slider(self, parent, label_text, variable, from_, to, step, row):
        """创建参数调节滑块"""
        # 创建标签
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        
        # 创建滑块
        scale = ttk.Scale(
            parent,
            from_=from_,
            to=to,
            variable=variable,
            orient=tk.HORIZONTAL,
            length=200
        )
        scale.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        
        # 创建数值显示标签
        value_label = ttk.Label(parent, text=f"{variable.get():.0f}")
        value_label.grid(row=row, column=2, sticky="w", padx=5, pady=2)
        
        # 绑定值变化事件
        def on_value_changed(*args):
            value_label.config(text=f"{variable.get():.0f}")
            if self.auto_preview_var.get():
                self.refresh_preview()
        
        variable.trace('w', on_value_changed)
        
        # 配置列权重
        parent.columnconfigure(1, weight=1)

    def toggle_auto_preview(self):
        """切换自动预览模式"""
        if self.auto_preview_var.get():
            self.refresh_preview()
    
    def reset_parameters(self):
        """重置参数到默认值"""
        self.enemy_def_var.set(300)
        self.enemy_mdef_var.set(30)
        self.time_range_var.set(60)
        self.x_axis_mode.set("time")
        if self.auto_preview_var.get():
            self.refresh_preview()
    
    def select_all_operators(self):
        """选择所有干员 - 适配表格结构"""
        try:
            if hasattr(self, 'operator_treeview'):
                # 新的表格结构
                for item in self.operator_treeview.get_children():
                    self.operator_treeview.selection_add(item)
            elif hasattr(self, 'operator_listbox'):
                # 原来的Listbox结构
                self.operator_listbox.select_set(0, tk.END)
            self.update_selection_status()
        except Exception as e:
            logger.error(f"全选干员失败: {e}")
    
    def deselect_all_operators(self):
        """取消选择所有干员 - 适配表格结构"""
        try:
            if hasattr(self, 'operator_treeview'):
                # 新的表格结构
                self.operator_treeview.selection_remove(*self.operator_treeview.selection())
            elif hasattr(self, 'operator_listbox'):
                # 原来的Listbox结构
                self.operator_listbox.selection_clear(0, tk.END)
            self.update_selection_status()
        except Exception as e:
            logger.error(f"取消选择干员失败: {e}")
    
    def refresh_operator_list(self):
        """刷新干员列表 - 支持搜索筛选功能"""
        try:
            if self.db_manager:
                # 获取所有干员数据
                operators = self.db_manager.get_all_operators()
                
                # 存储原始数据和筛选数据
                self.all_operators = operators or []
                self.operators_data = self.all_operators  # 保持向后兼容
                
                # 初始化筛选结果为全部数据
                self.filtered_operators = self.all_operators.copy()
                
                # 如果已有筛选条件，应用筛选
                if hasattr(self, 'search_var') and (self.search_var.get().strip() or 
                    any(not var.get() for var in self.class_vars.values()) or 
                    self.damage_type_filter_var.get() != "全部"):
                    self.filter_operators()
                else:
                    # 否则直接更新显示
                    self.update_operator_display()
                    self.update_filter_statistics()
                
                # 更新状态
                self.update_selection_status()
                
        except Exception as e:
            logger.error(f"刷新干员列表失败: {e}")

    def calculate_damage_over_time(self, operator, time):
        """计算随时间变化的伤害"""
        try:
            # 使用当前设置的防御力计算DPS
            defense = self.enemy_def_var.get()
            dps = self.calculate_dps_vs_defense(operator, defense)
            return dps * time
        except Exception as e:
            logger.error(f"计算时间伤害失败: {e}")
            return 0
    
    def calculate_dps(self, operator):
        """计算DPS"""
        try:
            attack = operator.get('atk', 0)
            interval = operator.get('atk_speed', 1.0)
            skill_mult = operator.get('skill_mult', 1.0)
            
            # 基础DPS = 攻击力 * 技能倍率 / 攻击间隔
            dps = (attack * skill_mult) / interval
            return max(0, dps)
        except Exception as e:
            logger.error(f"计算DPS失败: {e}")
            return 0
    
    def calculate_dps_vs_defense(self, operator, defense):
        """计算对抗指定防御力的DPS"""
        try:
            attack = operator.get('atk', 0)
            interval = operator.get('atk_speed', 1.0)
            skill_mult = operator.get('skill_mult', 1.0)
            atk_type = operator.get('atk_type', '物理伤害')
            
            # 根据攻击类型计算实际伤害 - 修复：统一使用完整中文标识
            if atk_type in ['法伤', '法术伤害']:
                # 法术伤害不受物理防御影响，但受法抗影响
                effective_attack = attack * skill_mult
                mdef = self.enemy_mdef_var.get()
                damage_reduction = min(90, mdef)  # 法抗最多减少90%伤害
                effective_attack = effective_attack * (100 - damage_reduction) / 100
            else:
                # 物理伤害 - 正确实现5%保底伤害机制
                total_attack = attack * skill_mult
                # 计算基础伤害（攻击力-防御力）
                base_damage = total_attack - defense
                # 计算保底伤害（攻击力的5%）
                min_damage = total_attack * 0.05
                # 取较大值，确保至少造成保底伤害
                effective_attack = max(base_damage, min_damage)
            
            dps = effective_attack / interval
            return max(0, dps)
        except Exception as e:
            logger.error(f"计算DPS vs 防御失败: {e}")
            return 0
    
    def calculate_dps_vs_mdefense(self, operator, mdef):
        """计算对抗指定法术防御的DPS"""
        try:
            attack = operator.get('atk', 0)
            interval = operator.get('atk_speed', 1.0)
            skill_mult = operator.get('skill_mult', 1.0)
            atk_type = operator.get('atk_type', '物理伤害')
            
            # 修复：统一使用完整中文标识
            if atk_type in ['法伤', '法术伤害']:
                # 法术伤害受法抗影响
                damage_reduction = min(90, mdef)
                effective_attack = (attack * skill_mult) * (100 - damage_reduction) / 100
            else:
                # 物理伤害不受法抗影响，但受物防影响 - 正确实现5%保底伤害
                defense = self.enemy_def_var.get()
                total_attack = attack * skill_mult
                # 计算基础伤害（攻击力-防御力）
                base_damage = total_attack - defense
                # 计算保底伤害（攻击力的5%）
                min_damage = total_attack * 0.05
                # 取较大值，确保至少造成保底伤害
                effective_attack = max(base_damage, min_damage)
            
            dps = effective_attack / interval
            return max(0, dps)
        except Exception as e:
            logger.error(f"计算DPS vs 法抗失败: {e}")
            return 0
    
    def calculate_dph(self, operator):
        """计算DPH (每次攻击伤害) - 考虑防御力和保底伤害"""
        try:
            attack = operator.get('atk', 0)
            skill_mult = operator.get('skill_mult', 1.0)
            atk_type = operator.get('atk_type', '物理伤害')
            
            # 根据攻击类型计算实际伤害
            if atk_type in ['法伤', '法术伤害']:
                # 法术伤害受法抗影响
                mdef = self.enemy_mdef_var.get()
                damage_reduction = min(90, mdef)  # 法抗最多减少90%伤害
                effective_attack = (attack * skill_mult) * (100 - damage_reduction) / 100
            else:
                # 物理伤害考虑防御力和5%保底伤害
                defense = self.enemy_def_var.get()
                total_attack = attack * skill_mult
                # 计算基础伤害（攻击力-防御力）
                base_damage = total_attack - defense
                # 计算保底伤害（攻击力的5%）
                min_damage = total_attack * 0.05
                # 取较大值，确保至少造成保底伤害
                effective_attack = max(base_damage, min_damage)
            
            return max(0, effective_attack)
        except Exception as e:
            logger.error(f"计算DPH失败: {e}")
            return 0
    
    def get_selected_operators(self):
        """获取选中的干员数据 - 支持筛选功能"""
        try:
            if hasattr(self, 'operator_treeview'):
                # 新的表格结构
                selected_items = self.operator_treeview.selection()
                selected_operators = []
                
                for item in selected_items:
                    values = self.operator_treeview.item(item, 'values')
                    if values and len(values) > 1:
                        operator_name = values[1]  # 第二列是名称
                        # 从筛选后的数据中找到对应的干员
                        for operator in self.filtered_operators:
                            if operator.get('name') == operator_name:
                                selected_operators.append(operator)
                                break
                
                return selected_operators
            elif hasattr(self, 'operator_listbox'):
                # 原来的Listbox结构 - 也要支持筛选
                selected_indices = self.operator_listbox.curselection()
                selected_operators = []
                
                for index in selected_indices:
                    if index < len(self.filtered_operators):
                        selected_operators.append(self.filtered_operators[index])
                
                return selected_operators
            return []
        except Exception as e:
            logger.error(f"获取选中干员失败: {e}")
            return []
    
    def update_selection_status(self):
        """更新选择状态显示 - 适配表格结构"""
        try:
            if hasattr(self, 'operator_treeview'):
                # 新的表格结构
                selected_count = len(self.operator_treeview.selection())
            elif hasattr(self, 'operator_listbox'):
                # 原来的Listbox结构
                selected_count = len(self.operator_listbox.curselection())
            else:
                selected_count = 0
            
            if hasattr(self, 'selection_status_label'):
                self.selection_status_label.config(text=f"已选择 {selected_count} 个")
        except Exception as e:
            logger.error(f"更新选择状态失败: {e}")
    
    def create_line_chart(self, ax, operators):
        """创建折线图"""
        try:
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            # 根据X轴模式创建不同的折线图
            x_axis_mode = self.x_axis_mode.get()
            
            if x_axis_mode == "time":
                # 时间轴折线图
                time_range = range(0, int(self.time_range_var.get()) + 1, 5)
                for operator in operators:
                    damage_values = []
                    for t in time_range:
                        damage = self.calculate_damage_over_time(operator, t)
                        damage_values.append(damage)
                    ax.plot(time_range, damage_values, label=operator['name'], linewidth=2, marker='o')
                ax.set_xlabel('时间 (秒)')
                ax.set_ylabel('累积伤害')
                ax.set_title('干员伤害随时间变化')
                
            elif x_axis_mode == "defense":
                # 防御力轴折线图
                defense_range = range(0, 1001, 50)
                for operator in operators:
                    dps_values = []
                    for defense in defense_range:
                        dps = self.calculate_dps_vs_defense(operator, defense)
                        dps_values.append(dps)
                    ax.plot(defense_range, dps_values, label=operator['name'], linewidth=2, marker='o')
                ax.set_xlabel('敌人防御力')
                ax.set_ylabel('DPS')
                ax.set_title('干员DPS vs 敌人防御力')
                
            elif x_axis_mode == "magic_defense":
                # 法术抗性轴折线图 - 新增
                mdef_range = range(0, 101, 5)  # 法抗0-100%，每5%采样
                for operator in operators:
                    dps_values = []
                    for mdef in mdef_range:
                        dps = self.calculate_dps_vs_mdefense(operator, mdef)
                        dps_values.append(dps)
                    ax.plot(mdef_range, dps_values, label=operator['name'], linewidth=2, marker='o')
                ax.set_xlabel('敌人法术抗性 (%)')
                ax.set_ylabel('DPS')
                ax.set_title('干员DPS vs 敌人法术抗性')
                
            else:
                # 默认防御力模式
                defense_range = range(0, 1001, 50)
                for operator in operators:
                    dps_values = []
                    for defense in defense_range:
                        dps = self.calculate_dps_vs_defense(operator, defense)
                        dps_values.append(dps)
                    ax.plot(defense_range, dps_values, label=operator['name'], linewidth=2, marker='o')
                ax.set_xlabel('敌人防御力')
                ax.set_ylabel('DPS')
                ax.set_title('干员DPS对比')
            
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            logger.error(f"创建折线图失败: {e}")
            ax.text(0.5, 0.5, f'折线图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_bar_chart(self, ax, operators):
        """创建柱状图"""
        try:
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            names = [op['name'][:6] for op in operators]  # 限制名称长度
            dps_values = []
            
            # 计算当前参数下的DPS
            defense = self.enemy_def_var.get()
            for operator in operators:
                dps = self.calculate_dps_vs_defense(operator, defense)
                dps_values.append(dps)
            
            # 创建柱状图
            colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold', 'lightpink', 'lightyellow', 'lightgray', 'orange']
            bars = ax.bar(names, dps_values, color=[colors[i % len(colors)] for i in range(len(names))])
            
            # 添加数值标签
            for bar, dps in zip(bars, dps_values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{dps:.0f}', ha='center', va='bottom', fontsize=9)
            
            ax.set_xlabel('干员')
            ax.set_ylabel('DPS')
            ax.set_title(f'干员DPS对比 (防御力: {int(defense)})')
            ax.tick_params(axis='x', rotation=45)
            
        except Exception as e:
            logger.error(f"创建柱状图失败: {e}")
            ax.text(0.5, 0.5, f'柱状图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_pie_chart(self, ax, operators):
        """创建饼图"""
        try:
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            # 计算DPS数据
            names = [op['name'][:6] for op in operators]  # 限制名称长度
            defense = self.enemy_def_var.get()
            dps_values = []
            
            for operator in operators:
                dps = self.calculate_dps_vs_defense(operator, defense)
                dps_values.append(max(1, dps))  # 确保值为正数
            
            # 创建饼图
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'gold', 'lightpink', 'lightyellow', 'lightgray', 'orange']
            wedges, texts, autotexts = ax.pie(dps_values, labels=names, autopct='%1.1f%%', 
                                            colors=[colors[i % len(colors)] for i in range(len(names))],
                                            startangle=90)
            
            # 美化文字
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(8)
            
            for text in texts:
                text.set_fontsize(9)
            
            ax.set_title(f'干员DPS占比分析 (防御力: {int(defense)})')
            
        except Exception as e:
            logger.error(f"创建饼图失败: {e}")
            ax.text(0.5, 0.5, f'饼图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_radar_chart(self, ax, operators):
        """创建雷达图"""
        try:
            import numpy as np
            
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
                
            # 定义属性标签
            attributes = ['攻击力', '生命值', '防御力', '攻击速度', 'DPS', '费用']
            
            # 角度计算
            angles = np.linspace(0, 2 * np.pi, len(attributes), endpoint=False).tolist()
            angles += angles[:1]  # 闭合雷达图
            
            # 为每个干员计算数据
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
            
            for i, operator in enumerate(operators[:8]):  # 最多显示8个干员
                # 获取并归一化数据
                values = [
                    operator.get('atk', 0) / 1000,  # 攻击力归一化到0-1
                    operator.get('hp', 0) / 5000,   # 生命值归一化到0-1
                    operator.get('def', 0) / 500,   # 防御力归一化到0-1
                    operator.get('atk_speed', 1.0) / 3.0,  # 攻击速度归一化到0-1
                    self.calculate_dps(operator) / 2000,    # DPS归一化到0-1
                    1 - (operator.get('cost', 0) / 30)     # 费用归一化（低费用好）
                ]
                
                # 确保数据在0-1范围内
                values = [max(0, min(1, v)) for v in values]
                values += values[:1]  # 闭合数据
                
                # 绘制雷达图
                color = colors[i % len(colors)]
                ax.plot(angles, values, 'o-', linewidth=2, label=operator['name'], color=color)
                ax.fill(angles, values, alpha=0.25, color=color)
            
            # 设置属性标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(attributes)
            ax.set_ylim(0, 1)
            ax.set_title('干员综合能力雷达图')
            ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
            ax.grid(True)
            
        except Exception as e:
            logger.error(f"创建雷达图失败: {e}")
            ax.text(0.5, 0.5, f'雷达图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_heatmap_chart(self, ax, operators):
        """创建热力图"""
        try:
            import numpy as np
            
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            # 创建防御力 vs DPS的热力图数据
            defense_values = np.arange(0, 1001, 100)  # 0-1000防御，每100一个点
            operator_names = [op['name'][:6] for op in operators[:10]]  # 最多10个干员，名称截短
            
            # 计算DPS矩阵
            dps_matrix = []
            for operator in operators[:10]:
                dps_row = []
                for defense in defense_values:
                    dps = self.calculate_dps_vs_defense(operator, defense)
                    dps_row.append(dps)
                dps_matrix.append(dps_row)
            
            # 绘制热力图
            im = ax.imshow(dps_matrix, cmap='viridis', aspect='auto', interpolation='nearest')
            
            # 设置轴标签
            ax.set_xticks(range(len(defense_values)))
            ax.set_xticklabels([f'{int(d)}' for d in defense_values])
            ax.set_yticks(range(len(operator_names)))
            ax.set_yticklabels(operator_names)
            
            ax.set_xlabel('敌人防御力')
            ax.set_ylabel('干员')
            ax.set_title('干员DPS热力图')
            
            # 添加颜色条
            self.main_figure.colorbar(im, ax=ax, label='DPS')
            
        except Exception as e:
            logger.error(f"创建热力图失败: {e}")
            ax.text(0.5, 0.5, f'热力图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_boxplot_chart(self, ax, operators):
        """创建箱线图"""
        try:
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            # 按职业分组数据
            class_groups = {}
            for operator in operators:
                class_type = operator.get('class_type', '未知')
                if class_type not in class_groups:
                    class_groups[class_type] = []
                
                dps = self.calculate_dps(operator)
                class_groups[class_type].append(dps)
            
            # 准备箱线图数据
            data_to_plot = []
            labels = []
            for class_type, dps_values in class_groups.items():
                if dps_values:  # 确保有数据
                    data_to_plot.append(dps_values)
                    labels.append(class_type)
            
            if data_to_plot:
                # 绘制箱线图
                bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
                
                # 美化箱线图
                colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
                for patch, color in zip(bp['boxes'], colors):
                    patch.set_facecolor(color)
                
                ax.set_xlabel('职业')
                ax.set_ylabel('DPS')
                ax.set_title('各职业DPS分布箱线图')
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '没有足够的数据绘制箱线图', ha='center', va='center', transform=ax.transAxes)
            
        except Exception as e:
            logger.error(f"创建箱线图失败: {e}")
            ax.text(0.5, 0.5, f'箱线图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_area_chart(self, ax, operators):
        """创建面积图"""
        try:
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            # 创建时间轴数据
            time_range = range(0, int(self.time_range_var.get()) + 1, 5)
            
            # 计算累积伤害数据
            cumulative_damage = [0] * len(time_range)
            colors = ['red', 'blue', 'green', 'orange', 'purple']
            
            for i, operator in enumerate(operators[:5]):  # 最多显示5个干员
                operator_damage = []
                for t in time_range:
                    damage = self.calculate_damage_over_time(operator, t)
                    operator_damage.append(damage)
                
                # 绘制堆叠面积图
                ax.fill_between(time_range, cumulative_damage, 
                              [cd + od for cd, od in zip(cumulative_damage, operator_damage)],
                              alpha=0.7, label=operator['name'], 
                              color=colors[i % len(colors)])
                
                # 更新累积伤害
                cumulative_damage = [cd + od for cd, od in zip(cumulative_damage, operator_damage)]
            
            ax.set_xlabel('时间 (秒)')
            ax.set_ylabel('累积伤害')
            ax.set_title('干员累积伤害面积图')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            logger.error(f"创建面积图失败: {e}")
            ax.text(0.5, 0.5, f'面积图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_scatter_chart(self, ax, operators):
        """创建散点图"""
        try:
            if not operators:
                ax.text(0.5, 0.5, '请选择干员', ha='center', va='center', transform=ax.transAxes)
                return
            
            # 按职业分类
            class_colors = {
                '近卫': 'red',
                '狙击': 'blue', 
                '重装': 'green',
                '医疗': 'pink',
                '辅助': 'orange',
                '术师': 'purple',
                '特种': 'brown',
                '先锋': 'gray'
            }
            
            # 绘制散点图
            plotted_classes = set()
            for operator in operators:
                atk = operator.get('atk', 0)
                hp = operator.get('hp', 0)
                dps = self.calculate_dps(operator)
                class_type = operator.get('class_type', '未知')
                
                color = class_colors.get(class_type, 'black')
                size = max(20, dps / 10)  # 根据DPS调整点的大小
                
                # 只为新职业添加图例
                label = class_type if class_type not in plotted_classes else ""
                if class_type not in plotted_classes:
                    plotted_classes.add(class_type)
                
                ax.scatter(atk, hp, s=size, c=color, alpha=0.6, label=label)
                
                # 添加干员名称标注
                ax.annotate(operator['name'][:4], (atk, hp), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.8)
            
            ax.set_xlabel('攻击力')
            ax.set_ylabel('生命值')
            ax.set_title('干员攻击力 vs 生命值散点图')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            logger.error(f"创建散点图失败: {e}")
            ax.text(0.5, 0.5, f'散点图创建失败: {str(e)}', ha='center', va='center', transform=ax.transAxes)

    def create_main_chart(self, operators, chart_type):
        """创建主图表"""
        try:
            # 导入matplotlib.pyplot在方法开始处
            import matplotlib.pyplot as plt
            
            if hasattr(self, 'main_canvas') and self.main_canvas:
                # 清除现有图表
                if hasattr(self, 'main_figure'):
                    self.main_figure.clear()
                else:
                    self.main_figure = plt.Figure(figsize=(10, 7), dpi=100)
                
                # 设置中文字体
                plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                plt.rcParams['axes.unicode_minus'] = False
                
                # 创建子图
                ax = self.main_figure.add_subplot(111)
                
                # 根据图表类型生成不同的图表
                if chart_type == "line":
                    self.create_line_chart(ax, operators)
                elif chart_type == "bar":
                    self.create_bar_chart(ax, operators)
                elif chart_type == "pie":
                    self.create_pie_chart(ax, operators)
                elif chart_type == "radar":
                    self.create_radar_chart(ax, operators)
                elif chart_type == "heatmap":
                    self.create_heatmap_chart(ax, operators)
                elif chart_type == "boxplot":
                    self.create_boxplot_chart(ax, operators)
                elif chart_type == "area":
                    self.create_area_chart(ax, operators)
                elif chart_type == "scatter":
                    self.create_scatter_chart(ax, operators)
                else:
                    # 默认创建折线图
                    self.create_line_chart(ax, operators)
                
                # 调整布局
                self.main_figure.tight_layout()
                
                # 更新画布
                self.main_canvas.draw()
                
                # 记录今日计算
                if self.db_manager:
                    try:
                        # 检查方法是否存在
                        if hasattr(self.db_manager, 'increment_today_calculations'):
                            self.db_manager.increment_today_calculations()
                        else:
                            logger.debug("数据库管理器不支持计算统计功能")
                    except Exception as e:
                        logger.debug(f"记录图表生成时出现小问题: {e}")
                
        except Exception as e:
            logger.error(f"创建主图表失败: {e}")
            messagebox.showerror("错误", f"创建图表失败: {str(e)}")

    def generate_main_chart(self):
        """生成主图表"""
        try:
            # 获取选中的干员 - 适配新的表格结构
            selected_operators = self.get_selected_operators()
            
            if not selected_operators:
                messagebox.showwarning("警告", "请至少选择一个干员")
                return
            
            # 获取图表类型
            chart_type = self.selected_chart_type.get()
            
            # 生成图表
            self.create_main_chart(selected_operators, chart_type)
            
            # 更新图表状态
            if hasattr(self, 'chart_status_label') and self.chart_status_label:
                self.chart_status_label.configure(
                    text=f"📊 已生成 {chart_type} 图表 - {len(selected_operators)} 个干员"
                )
            
        except Exception as e:
            logger.error(f"生成主图表失败: {e}")
            messagebox.showerror("错误", f"生成图表失败: {str(e)}")
    
    def on_operator_selection_changed(self, event=None):
        """处理干员选择事件 - 适配表格结构"""
        try:
            self.update_selection_status()
        except Exception as e:
            logger.error(f"处理干员选择事件失败: {e}")

    def get_current_chart_figure(self):
        """获取当前显示的图表图形对象"""
        if hasattr(self, 'main_figure') and self.main_figure is not None:
            return self.main_figure
        elif hasattr(self, 'current_figure') and self.current_figure is not None:
            return self.current_figure
        return None
    
    def get_all_chart_figures(self):
        """获取所有可用的图表图形对象"""
        charts = []
        
        # 主图表
        if hasattr(self, 'main_figure') and self.main_figure is not None:
            charts.append({
                'figure': self.main_figure,
                'title': f'主图表_{self.selected_chart_type.get()}',
                'type': 'main_chart'
            })
        
        # 预览图表
        if hasattr(self, 'preview_figure') and self.preview_figure is not None:
            charts.append({
                'figure': self.preview_figure,
                'title': f'预览图表_{self.selected_chart_type.get()}',
                'type': 'preview_chart'
            })
        
        return charts
    
    def export_current_charts(self):
        """导出当前图表为文件并返回路径信息"""
        exported_charts = []
        
        try:
            # 确保charts目录存在
            charts_dir = os.path.join(os.path.dirname(__file__), '..', 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_type = self.selected_chart_type.get()
            x_mode = self.x_axis_mode.get()
            
            # 导出主图表
            if hasattr(self, 'main_figure') and self.main_figure is not None:
                main_filename = f"main_chart_{chart_type}_{x_mode}_{timestamp}.png"
                main_filepath = os.path.join(charts_dir, main_filename)
                
                self.main_figure.savefig(main_filepath, dpi=300, bbox_inches='tight', 
                                       facecolor='white', edgecolor='none')
                
                exported_charts.append({
                    'figure': self.main_figure,
                    'title': f'主图表_{chart_type}',
                    'type': 'main_chart',
                    'filepath': main_filepath
                })
            
            # 导出预览图表
            if hasattr(self, 'preview_figure') and self.preview_figure is not None:
                preview_filename = f"preview_chart_{chart_type}_{x_mode}_{timestamp}.png"
                preview_filepath = os.path.join(charts_dir, preview_filename)
                
                self.preview_figure.savefig(preview_filepath, dpi=200, bbox_inches='tight',
                                          facecolor='white', edgecolor='none')
                
                exported_charts.append({
                    'figure': self.preview_figure,
                    'title': f'预览图表_{chart_type}',
                    'type': 'preview_chart',
                    'filepath': preview_filepath
                })
            
            logger.info(f"导出了 {len(exported_charts)} 个图表")
            
        except Exception as e:
            logger.error(f"导出当前图表失败: {e}")
        
        return exported_charts