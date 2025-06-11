# comparison_panel.py - 对比分析面板

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, IntVar, DoubleVar, BooleanVar, messagebox
import sys
import os
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import numpy as np

# 设置matplotlib后端
matplotlib.use('TkAgg')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.damage_calculator import DamageCalculator
from visualization.chart_factory import ChartFactory
from ui.components.sortable_treeview import SortableTreeview, NumericSortableTreeview
from ui.invisible_scroll_frame import InvisibleScrollFrame

class ComparisonPanel:
    def __init__(self, parent, db_manager, status_callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.status_callback = status_callback
        
        # 初始化计算器和图表工厂
        self.damage_calculator = DamageCalculator()
        self.chart_factory = ChartFactory(parent)
        
        # 状态变量
        self.selected_operators = []
        self.enemy_def_var = IntVar(value=300)
        self.enemy_mdef_var = IntVar(value=30)
        self.time_range_var = IntVar(value=30)
        self.comparison_results = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置对比分析面板UI - 创建四栏布局界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 创建四栏分窗格（增加已选干员列表）
        self.paned_window = ttk.PanedWindow(main_frame, orient=HORIZONTAL)
        self.paned_window.pack(fill=BOTH, expand=True)
        
        # 左栏：干员选择区域
        self.operator_selection_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.operator_selection_frame, weight=1)
        self.create_operator_selection_area()
        
        # 左中栏：已选干员列表
        self.selected_operators_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.selected_operators_frame, weight=1)
        self.create_selected_operators_area()
        
        # 右中栏：参数设置区域
        self.scenario_settings_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.scenario_settings_frame, weight=1)
        self.create_scenario_settings_area()
        
        # 右栏：结果显示区域
        self.results_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.results_frame, weight=2)
        self.create_comparison_results_area()
    
    def create_operator_selection_area(self):
        """实现干员多选功能"""
        # 标题框架
        title_frame = ttk.LabelFrame(self.operator_selection_frame, text="干员选择", padding=10)
        title_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 搜索框
        search_frame = ttk.Frame(title_frame)
        search_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索：").pack(side=LEFT)
        self.search_var = StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        self.search_var.trace_add("write", self.filter_operators)
        
        # 干员列表框架
        list_frame = ttk.Frame(title_frame)
        list_frame.pack(fill=BOTH, expand=True)
        
        # 创建多选列表框
        self.operator_listbox = SortableTreeview(list_frame, columns=('name', 'class', 'atk', 'hp'), 
                                           show='headings', height=12, selectmode='extended')
        
        # 设置列标题
        self.operator_listbox.heading('name', text='名称')
        self.operator_listbox.heading('class', text='职业')
        self.operator_listbox.heading('atk', text='攻击')
        self.operator_listbox.heading('hp', text='生命')
        
        # 设置列宽度
        self.operator_listbox.column('name', width=100)
        self.operator_listbox.column('class', width=80)
        self.operator_listbox.column('atk', width=60)
        self.operator_listbox.column('hp', width=60)
        
        # 启用排序功能
        self.operator_listbox.enable_sorting()
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.operator_listbox.yview)
        self.operator_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.operator_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定双击事件添加干员
        self.operator_listbox.bind('<Double-Button-1>', self.add_selected_operator)
        
        # 操作按钮
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(button_frame, text="添加选中", bootstyle=SUCCESS,
                  command=self.add_selected_operator, width=10).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="刷新", bootstyle=INFO,
                  command=self.refresh_operator_list, width=10).pack(side=LEFT, padx=2)
        
        # 加载干员列表
        self.refresh_operator_list()
    
    def create_selected_operators_area(self):
        """创建已选干员列表区域 - 使用完整的属性表格"""
        # 标题框架
        selected_frame = ttk.LabelFrame(self.selected_operators_frame, text="已选干员", padding=10)
        selected_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 已选干员表格
        list_frame = ttk.Frame(selected_frame)
        list_frame.pack(fill=BOTH, expand=True)
        
        # 定义完整的已选干员表格列 - 列为属性，行为干员
        columns = ('id', 'name', 'class_type', 'hp', 'atk', 'def', 'mdef', 'atk_speed', 'atk_type', 
                  'block_count', 'cost')
        
        # 指定数值列用于排序
        numeric_columns = ['id', 'hp', 'atk', 'def', 'mdef', 'atk_speed', 'block_count', 'cost']
        
        self.selected_listbox = NumericSortableTreeview(list_frame, columns=columns, 
                                           show='tree headings', height=12, numeric_columns=numeric_columns)
        
        # 设置列标题和宽度
        self.selected_listbox.heading('#0', text='', anchor='w')
        self.selected_listbox.column('#0', width=0, stretch=False)  # 隐藏第一列
        
        # 基础信息列
        self.selected_listbox.heading('id', text='ID', anchor='center')
        self.selected_listbox.column('id', width=35, anchor='center')
        
        self.selected_listbox.heading('name', text='名称', anchor='w')
        self.selected_listbox.column('name', width=80, anchor='w')
        
        self.selected_listbox.heading('class_type', text='职业', anchor='center')
        self.selected_listbox.column('class_type', width=50, anchor='center')
        
        # 基础属性列
        self.selected_listbox.heading('hp', text='生命值', anchor='center')
        self.selected_listbox.column('hp', width=60, anchor='center')
        
        self.selected_listbox.heading('atk', text='攻击力', anchor='center')
        self.selected_listbox.column('atk', width=60, anchor='center')
        
        self.selected_listbox.heading('def', text='防御力', anchor='center')
        self.selected_listbox.column('def', width=60, anchor='center')
        
        self.selected_listbox.heading('mdef', text='法抗', anchor='center')
        self.selected_listbox.column('mdef', width=45, anchor='center')
        
        self.selected_listbox.heading('atk_speed', text='攻速', anchor='center')
        self.selected_listbox.column('atk_speed', width=50, anchor='center')
        
        self.selected_listbox.heading('atk_type', text='攻击类型', anchor='center')
        self.selected_listbox.column('atk_type', width=70, anchor='center')
        
        self.selected_listbox.heading('block_count', text='阻挡', anchor='center')
        self.selected_listbox.column('block_count', width=45, anchor='center')
        
        self.selected_listbox.heading('cost', text='费用', anchor='center')
        self.selected_listbox.column('cost', width=45, anchor='center')
        
        # 启用所有列的排序功能
        self.selected_listbox.enable_sorting()
        
        # 添加滚动条
        selected_scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        
        self.selected_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        selected_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定双击事件移除干员
        self.selected_listbox.bind('<Double-Button-1>', self.remove_selected_operator)
        
        # 操作按钮
        selected_button_frame = ttk.Frame(selected_frame)
        selected_button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(selected_button_frame, text="🗑️ 移除选中", bootstyle=WARNING,
                  command=self.remove_selected_operator, width=12).pack(side=LEFT, padx=2)
        ttk.Button(selected_button_frame, text="🗑️ 清空全部", bootstyle=DANGER,
                  command=self.clear_all_selected, width=12).pack(side=LEFT, padx=2)
        ttk.Button(selected_button_frame, text="📊 生成图表", bootstyle=SUCCESS,
                  command=self.calculate_comparison, width=12).pack(side=LEFT, padx=2)
        
        # 显示选中数量的标签
        self.selected_count_label = ttk.Label(selected_button_frame, text="已选择: 0 个干员", 
                                            font=("微软雅黑", 8), foreground="blue")
        self.selected_count_label.pack(side=RIGHT)

    def create_scenario_settings_area(self):
        """添加敌人参数滑块"""
        # 标题框架
        settings_frame = ttk.LabelFrame(self.scenario_settings_frame, text="敌人场景设置", padding=10)
        settings_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 敌人防御值滑块（0-1000）
        def_frame = ttk.Frame(settings_frame)
        def_frame.pack(fill=X, pady=5)
        
        ttk.Label(def_frame, text="敌人防御：").pack(anchor=W)
        self.def_scale = ttk.Scale(def_frame, from_=0, to=1000, variable=self.enemy_def_var, 
                                  orient=HORIZONTAL, command=self.on_parameter_changed)
        self.def_scale.pack(fill=X, pady=2)
        
        self.def_value_label = ttk.Label(def_frame, text="300")
        self.def_value_label.pack(anchor=W)
        
        # 法抗滑块（0-100%）
        mdef_frame = ttk.Frame(settings_frame)
        mdef_frame.pack(fill=X, pady=5)
        
        ttk.Label(mdef_frame, text="敌人法抗：").pack(anchor=W)
        self.mdef_scale = ttk.Scale(mdef_frame, from_=0, to=100, variable=self.enemy_mdef_var,
                                   orient=HORIZONTAL, command=self.on_parameter_changed)
        self.mdef_scale.pack(fill=X, pady=2)
        
        self.mdef_value_label = ttk.Label(mdef_frame, text="30%")
        self.mdef_value_label.pack(anchor=W)
        
        # 时间范围控制（0-90秒）
        time_frame = ttk.Frame(settings_frame)
        time_frame.pack(fill=X, pady=5)
        
        ttk.Label(time_frame, text="时间范围：").pack(anchor=W)
        self.time_scale = ttk.Scale(time_frame, from_=0, to=90, variable=self.time_range_var,
                                   orient=HORIZONTAL, command=self.on_parameter_changed)
        self.time_scale.pack(fill=X, pady=2)
        
        self.time_value_label = ttk.Label(time_frame, text="30秒")
        self.time_value_label.pack(anchor=W)
        
        # 计算模式选择器
        mode_frame = ttk.LabelFrame(settings_frame, text="计算模式", padding=10)
        mode_frame.pack(fill=X, pady=10)
        
        self.calc_mode_var = StringVar(value="dps")
        
        ttk.Radiobutton(mode_frame, text="DPS (每秒伤害)", variable=self.calc_mode_var, 
                       value="dps", command=self.on_parameter_changed).pack(anchor=W)
        ttk.Radiobutton(mode_frame, text="DPH (单次伤害)", variable=self.calc_mode_var, 
                       value="dph", command=self.on_parameter_changed).pack(anchor=W)
        ttk.Radiobutton(mode_frame, text="总伤害", variable=self.calc_mode_var, 
                       value="total", command=self.on_parameter_changed).pack(anchor=W)
        ttk.Radiobutton(mode_frame, text="性价比", variable=self.calc_mode_var, 
                       value="efficiency", command=self.on_parameter_changed).pack(anchor=W)
        
        # 计算按钮
        calc_button_frame = ttk.Frame(settings_frame)
        calc_button_frame.pack(fill=X, pady=10)
        
        ttk.Button(calc_button_frame, text="开始对比计算", bootstyle=PRIMARY,
                  command=self.calculate_comparison).pack(fill=X)
        
        # 更新初始标签值
        self.on_parameter_changed()
    
    def create_comparison_results_area(self):
        """添加结果显示区域 - 使用完整的干员属性对比表格"""
        # 标题框架
        results_frame = ttk.LabelFrame(self.results_frame, text="对比结果", padding=10)
        results_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建隐形滚动容器包装结果表格
        result_scroll_frame = InvisibleScrollFrame(results_frame, scroll_speed=3)
        result_scroll_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 定义完整的对比表格列 - 列为属性，行为干员
        columns = ('id', 'name', 'class_type', 'hp', 'atk', 'def', 'mdef', 'atk_speed', 'atk_type', 
                  'block_count', 'cost', 'dps', 'dph', 'hps', 'survivability', 'cost_efficiency')
        
        # 指定数值列用于排序
        numeric_columns = ['id', 'hp', 'atk', 'def', 'mdef', 'atk_speed', 'block_count', 'cost', 
                          'dps', 'dph', 'hps', 'survivability', 'cost_efficiency']
        
        self.results_tree = NumericSortableTreeview(result_scroll_frame.scrollable_frame, 
                                        columns=columns, show='tree headings', height=10, 
                                        numeric_columns=numeric_columns)
        
        # 设置列标题和宽度
        self.results_tree.heading('#0', text='', anchor='w')
        self.results_tree.column('#0', width=0, stretch=False)  # 隐藏第一列
        
        # 基础信息列
        self.results_tree.heading('id', text='ID', anchor='center')
        self.results_tree.column('id', width=40, anchor='center')
        
        self.results_tree.heading('name', text='名称', anchor='w')
        self.results_tree.column('name', width=100, anchor='w')
        
        self.results_tree.heading('class_type', text='职业', anchor='center')
        self.results_tree.column('class_type', width=60, anchor='center')
        
        # 基础属性列
        self.results_tree.heading('hp', text='生命值', anchor='center')
        self.results_tree.column('hp', width=70, anchor='center')
        
        self.results_tree.heading('atk', text='攻击力', anchor='center')
        self.results_tree.column('atk', width=70, anchor='center')
        
        self.results_tree.heading('def', text='防御力', anchor='center')
        self.results_tree.column('def', width=70, anchor='center')
        
        self.results_tree.heading('mdef', text='法抗', anchor='center')
        self.results_tree.column('mdef', width=50, anchor='center')
        
        self.results_tree.heading('atk_speed', text='攻速', anchor='center')
        self.results_tree.column('atk_speed', width=60, anchor='center')
        
        self.results_tree.heading('atk_type', text='攻击类型', anchor='center')
        self.results_tree.column('atk_type', width=80, anchor='center')
        
        self.results_tree.heading('block_count', text='阻挡', anchor='center')
        self.results_tree.column('block_count', width=50, anchor='center')
        
        self.results_tree.heading('cost', text='费用', anchor='center')
        self.results_tree.column('cost', width=50, anchor='center')
        
        # 计算结果列
        self.results_tree.heading('dps', text='DPS', anchor='center')
        self.results_tree.column('dps', width=70, anchor='center')
        
        self.results_tree.heading('dph', text='DPH', anchor='center')
        self.results_tree.column('dph', width=70, anchor='center')
        
        self.results_tree.heading('hps', text='HPS', anchor='center')
        self.results_tree.column('hps', width=70, anchor='center')
        
        self.results_tree.heading('survivability', text='生存能力', anchor='center')
        self.results_tree.column('survivability', width=80, anchor='center')
        
        self.results_tree.heading('cost_efficiency', text='性价比', anchor='center')
        self.results_tree.column('cost_efficiency', width=80, anchor='center')
        
        # 启用所有列的排序功能
        self.results_tree.enable_sorting()
        
        # 直接打包表格（无需额外滚动条）
        self.results_tree.pack(fill=BOTH, expand=True)
        
        # 为表格绑定滚轮事件
        result_scroll_frame.bind_mousewheel_recursive(self.results_tree)
        
        # 快速图表按钮
        chart_frame = ttk.Frame(results_frame)
        chart_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(chart_frame, text="🔄 刷新计算", bootstyle=SUCCESS,
                  command=self.calculate_comparison, width=12).pack(side=LEFT, padx=2)
        ttk.Button(chart_frame, text="📊 生成图表", bootstyle=INFO,
                  command=self.generate_comparison_chart, width=12).pack(side=LEFT, padx=2)
        ttk.Button(chart_frame, text="📤 导出结果", bootstyle=WARNING,
                  command=self.export_comparison_results, width=12).pack(side=LEFT, padx=2)
        ttk.Button(chart_frame, text="🗑️ 清空结果", bootstyle=SECONDARY,
                  command=self.clear_results, width=12).pack(side=LEFT, padx=2)
        
        # 状态信息显示
        self.comparison_status_label = ttk.Label(chart_frame, text="", 
                                               font=("微软雅黑", 8), foreground="blue")
        self.comparison_status_label.pack(side=RIGHT)
        
        # 结果表格和按钮后添加图表显示区域
        self.chart_display_frame = ttk.Frame(results_frame)
        self.chart_display_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
        self.chart_canvas = None
        self.chart_fig = None
    
    def on_operator_selection_changed(self, event=None):
        """响应干员选择变化"""
        self.selected_operators = []
        for item in self.operator_listbox.selection():
            operator_data = self.operator_listbox.item(item)['values']
            if operator_data:
                self.selected_operators.append({
                    'name': operator_data[0],
                    'class': operator_data[1],
                    'atk': operator_data[2],
                    'hp': operator_data[3]
                })
        
        # 更新状态
        if self.status_callback:
            self.status_callback(f"已选择 {len(self.selected_operators)} 个干员")
    
    def calculate_comparison(self):
        """执行对比计算逻辑"""
        if not self.selected_operators:
            messagebox.showwarning("警告", "请先选择要对比的干员")
            return
        
        if self.status_callback:
            self.status_callback("正在计算对比数据...")
        
        # 在后台线程执行计算
        def calc_thread():
            try:
                self.comparison_results = {}
                
                for operator in self.selected_operators:
                    # 处理不同的数据结构
                    if isinstance(operator, dict):
                        operator_name = operator['name']
                    else:
                        operator_name = str(operator)
                    
                    # 获取完整的干员数据
                    full_operator_data = self.get_operator_full_data(operator_name)
                    if not full_operator_data:
                        continue
                    
                    # 执行计算
                    results = self.damage_calculator.calculate_operator_performance(
                        full_operator_data,
                        self.enemy_def_var.get(),
                        self.enemy_mdef_var.get()
                    )
                    
                    self.comparison_results[operator_name] = results
                
                # 在主线程更新UI
                self.parent.after(0, self.update_results_display)
                
            except Exception as e:
                error_msg = f"计算出错: {str(e)}"
                print(error_msg)  # 调试输出
                if self.status_callback:
                    self.status_callback(error_msg)
        
        threading.Thread(target=calc_thread, daemon=True).start()
    
    def update_results_display(self):
        """更新结果显示 - 适配完整的表格结构"""
        # 清空现有结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 添加新结果 - 每个干员一行，包含所有属性
        for operator_name in self.selected_operators:
            if isinstance(operator_name, dict):
                operator_name = operator_name['name']
            
            # 获取干员的完整数据
            full_operator_data = self.get_operator_full_data(operator_name)
            if not full_operator_data:
                continue
            
            # 获取计算结果
            calc_results = self.comparison_results.get(operator_name, {})
            
            # 构建表格行数据
            row_values = (
                full_operator_data.get('id', ''),
                full_operator_data.get('name', ''),
                full_operator_data.get('class_type', ''),
                full_operator_data.get('hp', 0),
                full_operator_data.get('atk', 0),
                full_operator_data.get('def', 0),
                full_operator_data.get('mdef', 0),
                f"{full_operator_data.get('atk_speed', 1.0):.2f}",
                full_operator_data.get('atk_type', '物伤'),
                full_operator_data.get('block_count', 1),
                full_operator_data.get('cost', 0),
                f"{calc_results.get('dps', 0):.1f}",
                f"{calc_results.get('dph', 0):.1f}",
                f"{calc_results.get('hps', 0):.1f}",
                f"{calc_results.get('survivability', 0):.1f}",
                f"{calc_results.get('cost_efficiency', 0):.2f}"
            )
            
            self.results_tree.insert('', 'end', values=row_values)
        
        # 更新状态信息
        count = len(self.comparison_results)
        if hasattr(self, 'comparison_status_label'):
            self.comparison_status_label.config(text=f"对比完成: {count}个干员")
        
        if self.status_callback:
            self.status_callback(f"对比计算完成，共 {count} 个干员")
    
    def on_parameter_changed(self, value=None):
        """参数变化时更新标签"""
        self.def_value_label.config(text=str(self.enemy_def_var.get()))
        self.mdef_value_label.config(text=f"{self.enemy_mdef_var.get()}%")
        self.time_value_label.config(text=f"{self.time_range_var.get()}秒")
    
    def filter_operators(self, *args):
        """过滤干员列表"""
        search_text = self.search_var.get().lower()
        # 这里应该重新加载并过滤干员列表
        # 暂时保持简单实现
        pass
    
    def refresh_operator_list(self):
        """刷新干员列表"""
        try:
            # 清空现有列表
            for item in self.operator_listbox.get_children():
                self.operator_listbox.delete(item)
            
            # 从数据库获取所有干员
            operators = self.db_manager.get_all_operators()
            
            if not operators:
                # 如果没有数据，显示提示
                self.operator_listbox.insert('', 'end', values=('暂无数据', '-', '-', '-'))
                if self.status_callback:
                    self.status_callback("提示：当前数据库中没有干员数据，请先导入数据")
                return
            
            # 填充列表
            for operator in operators:
                name = operator.get('name', '未知')
                class_type = operator.get('class_type', '未知')
                atk = operator.get('atk', 0)
                hp = operator.get('hp', 0)
                
                self.operator_listbox.insert('', 'end', values=(name, class_type, atk, hp))
            
            if self.status_callback:
                self.status_callback(f"已加载 {len(operators)} 个干员数据")
                
        except Exception as e:
            error_msg = f"加载干员列表失败: {str(e)}"
            print(error_msg)
            if self.status_callback:
                self.status_callback(error_msg)
            
            # 显示错误信息
            self.operator_listbox.insert('', 'end', values=('加载失败', str(e)[:20], '-', '-'))
    
    def get_operator_full_data(self, operator_name):
        """根据名称获取完整的干员数据"""
        try:
            return self.db_manager.get_operator_by_name(operator_name)
        except Exception as e:
            print(f"获取干员数据失败: {e}")
            return None
    
    def select_all_operators(self):
        """全选干员"""
        for item in self.operator_listbox.get_children():
            self.operator_listbox.selection_add(item)
        self.on_operator_selection_changed()
    
    def clear_selection(self):
        """清空选择"""
        self.operator_listbox.selection_remove(*self.operator_listbox.selection())
        self.on_operator_selection_changed()
    
    def generate_comparison_chart(self):
        """生成对比图表并嵌入下方"""
        if not self.selected_operators:
            messagebox.showwarning("警告", "请先选择要对比的干员")
            return
            
        try:
            # 获取计算模式
            calc_mode = self.calc_mode_var.get()
            enemy_def = self.enemy_def_var.get()
            enemy_mdef = self.enemy_mdef_var.get()
            time_range = self.time_range_var.get()
            
            # 准备数据
            chart_data = {}
            
            if calc_mode == "total":
                # 时间轴伤害图：横坐标时间，纵坐标累计伤害
                for operator in self.selected_operators:
                    full_operator_data = self.get_operator_full_data(operator['name'])
                    if full_operator_data:
                        timeline_data = []
                        for t in range(0, time_range + 1, 2):  # 每2秒采样
                            cumulative_damage = self.damage_calculator.calculate_cumulative_damage(
                                full_operator_data, t, enemy_def, enemy_mdef)
                            timeline_data.append((t, cumulative_damage))
                        chart_data[operator['name']] = timeline_data
                
                # 生成时间轴图表
                chart_fig = self.chart_factory.create_line_chart(
                    [], 
                    title="干员时间轴伤害对比",
                    xlabel="时间 (秒)", 
                    ylabel="累计伤害",
                    multiple_series=chart_data
                )
            else:
                # DPS曲线图：横坐标防御/法抗，纵坐标DPS
                for operator in self.selected_operators:
                    full_operator_data = self.get_operator_full_data(operator['name'])
                    if full_operator_data:
                        curve_data = []
                        class_type = full_operator_data.get('class_type', '')
                        
                        if '术' in class_type or '医' in class_type:
                            # 法术干员：生成DPS-法抗曲线
                            for mdef in range(0, 101, 5):  # 法抗0-100%，每5%采样
                                performance = self.damage_calculator.calculate_operator_performance(
                                    full_operator_data, enemy_def, mdef)
                                dps = performance.get('dps', 0)
                                curve_data.append((mdef, dps))
                            
                            chart_data[operator['name']] = curve_data
                            xlabel = "敌人法抗 (%)"
                            title = "干员DPS-法抗对比曲线"
                        else:
                            # 物理干员：生成DPS-防御曲线
                            for defense in range(0, 1001, 25):  # 防御0-1000，每25采样
                                performance = self.damage_calculator.calculate_operator_performance(
                                    full_operator_data, defense, enemy_mdef)
                                dps = performance.get('dps', 0)
                                curve_data.append((defense, dps))
                            
                            chart_data[operator['name']] = curve_data
                            xlabel = "敌人防御力"
                            title = "干员DPS-防御对比曲线"
                
                # 生成DPS曲线图表
                chart_fig = self.chart_factory.create_line_chart(
                    [], 
                    title=title,
                    xlabel=xlabel, 
                    ylabel="DPS",
                    multiple_series=chart_data
                )
            
            self.chart_fig = chart_fig
            
            # 清理旧的canvas
            for widget in self.chart_display_frame.winfo_children():
                widget.destroy()
                
            # 嵌入新图表
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            canvas = FigureCanvasTkAgg(chart_fig, master=self.chart_display_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=BOTH, expand=True)
            self.chart_canvas = canvas
            
            if self.status_callback:
                self.status_callback("对比曲线图已生成")
                
        except Exception as e:
            messagebox.showerror("错误", f"生成图表失败: {str(e)}")
    
    def export_comparison_results(self):
        """导出对比结果（保存当前图表为图片）"""
        if not self.chart_fig:
            messagebox.showwarning("警告", "没有可导出的图表，请先生成图表")
            return
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[('PNG图片', '*.png'), ('所有文件', '*.*')],
                title='保存对比图表为图片')
            if file_path:
                self.chart_fig.savefig(file_path, dpi=300)
                messagebox.showinfo("导出成功", f"图表已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出图表失败: {str(e)}")
    
    def clear_results(self):
        """清空结果显示"""
        # 清空表格
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 清空计算结果
        self.comparison_results = {}
        
        # 清空图表显示
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            self.chart_canvas = None
        if self.chart_fig:
            plt.close(self.chart_fig)
            self.chart_fig = None
        
        # 更新状态
        if hasattr(self, 'comparison_status_label'):
            self.comparison_status_label.config(text="")
        
        if self.status_callback:
            self.status_callback("已清空对比结果")

    def add_selected_operator(self, event=None):
        """添加选中干员到已选列表"""
        selection = self.operator_listbox.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个干员")
            return
        
        for selected_item in selection:
            operator_data = self.operator_listbox.item(selected_item)['values']
            if operator_data and operator_data[0] != '暂无数据' and operator_data[0] != '加载失败':
                # 检查是否已经添加
                already_added = any(op['name'] == operator_data[0] for op in self.selected_operators)
                if not already_added:
                    self.selected_operators.append({
                        'name': operator_data[0],
                        'class': operator_data[1],
                        'atk': operator_data[2],
                        'hp': operator_data[3]
                    })
        
        self.update_selected_display()
    
    def remove_selected_operator(self, event=None):
        """从已选列表移除干员 - 适配新的表格结构"""
        selection = self.selected_listbox.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移除的干员")
            return
        
        for selected_item in selection:
            operator_data = self.selected_listbox.item(selected_item)['values']
            if operator_data and len(operator_data) > 1:
                operator_name = operator_data[1]  # 第二列是名称
                # 从已选列表中移除
                self.selected_operators = [op for op in self.selected_operators if op['name'] != operator_name]
        
        self.update_selected_display()
    
    def clear_all_selected(self):
        """清空所有选中干员"""
        self.selected_operators = []
        self.update_selected_display()
        
        if self.status_callback:
            self.status_callback("已清空所有选中干员")
    
    def update_selected_display(self):
        """更新已选干员显示 - 适配完整的表格结构"""
        # 清空已选干员列表
        for item in self.selected_listbox.get_children():
            self.selected_listbox.delete(item)
        
        # 重新填充已选干员列表 - 每个干员一行，包含所有属性
        for op in self.selected_operators:
            # 获取干员的完整数据
            full_operator_data = self.get_operator_full_data(op['name'])
            if full_operator_data:
                # 构建表格行数据
                row_values = (
                    full_operator_data.get('id', ''),
                    full_operator_data.get('name', ''),
                    full_operator_data.get('class_type', ''),
                    full_operator_data.get('hp', 0),
                    full_operator_data.get('atk', 0),
                    full_operator_data.get('def', 0),
                    full_operator_data.get('mdef', 0),
                    f"{full_operator_data.get('atk_speed', 1.0):.2f}",
                    full_operator_data.get('atk_type', '物伤'),
                    full_operator_data.get('block_count', 1),
                    full_operator_data.get('cost', 0)
                )
                
                self.selected_listbox.insert('', 'end', values=row_values)
            else:
                # 如果获取不到完整数据，使用基础数据
                self.selected_listbox.insert('', 'end', values=(
                    '', op['name'], op.get('class', ''), op.get('hp', 0), 
                    op.get('atk', 0), '', '', '', '', '', ''
                ))
        
        # 更新计数标签
        self.selected_count_label.config(text=f"已选择: {len(self.selected_operators)} 个干员")
        
        # 更新状态
        if self.status_callback:
            self.status_callback(f"已选择 {len(self.selected_operators)} 个干员") 