# calculation_panel.py - 计算控制面板

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, IntVar, DoubleVar, BooleanVar, messagebox
import os
import sys
from typing import Dict, Any, List
from datetime import datetime
import re
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.damage_calculator import DamageCalculator
from ui.components.sortable_treeview import SortableTreeview
from ui.invisible_scroll_frame import InvisibleScrollFrame

class CalculationPanel:
    def __init__(self, parent, db_manager, status_callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.status_callback = status_callback
        
        # 初始化计算器
        self.calculator = DamageCalculator()
        
        # 攻击类型映射表（基于职业判断）
        self.CLASS_ATTACK_TYPE = {
            '先锋': '物伤', '近卫': '物伤', '重装': '物伤', '狙击': '物伤',
            '术师': '法伤', '辅助': '法伤', '医疗': '法伤', '特种': '物伤'
        }
        
        # 分析模式相关变量（新增）
        self.analysis_mode = StringVar(value="single")  # "single" or "multi"
        self.selected_operators_list = []  # 多选干员列表
        self.multi_comparison_results = {}  # 多干员对比结果
        
        # 控制变量
        self.enemy_def_var = IntVar(value=0)
        self.enemy_mdef_var = IntVar(value=0)
        self.time_range_var = IntVar(value=90)
        self.calc_mode_var = StringVar(value="basic_damage")
        self.auto_update_var = BooleanVar(value=True)
        
        # 结果变量
        self.selected_operator_var = StringVar(value="请选择干员")
        self.dps_result_var = StringVar(value="0.0")
        self.dph_result_var = StringVar(value="0.0")
        self.hps_result_var = StringVar(value="0.0")
        self.hph_result_var = StringVar(value="0.0")
        self.armor_break_var = StringVar(value="0")
        
        # 技能相关变量（在这里初始化，避免在create_control_area中重复定义）
        self.skill_duration_var = IntVar(value=10)
        self.skill_multiplier_var = IntVar(value=150)
        self.skill_cooldown_var = IntVar(value=30)
        
        # 新增：技能触发相关变量
        self.skill_trigger_mode_var = StringVar(value="manual")  # manual/auto
        self.skill_charges_var = IntVar(value=1)  # 技能次数
        self.skill_sp_cost_var = IntVar(value=30)  # SP消耗
        
        # 新增：高级参数变量
        self.atk_bonus_var = IntVar(value=0)  # 攻击力加成
        self.aspd_bonus_var = IntVar(value=0)  # 攻速加成
        self.crit_rate_var = IntVar(value=0)  # 暴击率
        self.crit_damage_var = IntVar(value=150)  # 暴击伤害
        
        self.current_operator = None
        
        self.setup_ui()
        
        # 初始化操作
        self.refresh_operator_list()
    
    def determine_attack_type(self, operator):
        """确定干员的攻击类型"""
        # 优先检查数据库中的攻击类型字段
        if 'atk_type' in operator and operator['atk_type']:
            return operator['atk_type']
        
        # 根据职业类型判断
        class_type = operator.get('class_type', '')
        return self.CLASS_ATTACK_TYPE.get(class_type, '物伤')
    
    def calculate_damage_with_correct_type(self, operator, enemy_def, enemy_mdef):
        """使用正确的攻击类型计算伤害"""
        atk = operator.get('atk', 0)
        atk_type = self.determine_attack_type(operator)
        atk_speed = operator.get('atk_speed', 1.0)
        hit_count = operator.get('hit_count', 1.0)
        
        if atk_type in ['物伤', '物理伤害']:
            # 物理攻击：受防御力影响，不受法抗影响
            dph = self.calculator.calculate_physical_damage(atk, enemy_def, hit_count)
        else:
            # 法术攻击：受法抗影响，不受防御力影响
            dph = self.calculator.calculate_magical_damage(atk, enemy_mdef, hit_count)
        
        dps = self.calculator.calculate_dps(dph, atk_speed)
        armor_break = self.calculator.find_armor_break_point(atk)
        
        return {
            'dps': dps,
            'dph': dph,
            'armor_break': armor_break,
            'atk_type': atk_type,
            'type': 'damage'
        }
    
    def create_advanced_scale_with_entry(self, parent, variable, from_, to, label_text, step=1, 
                                       unit="", tooltip="", dual_mode=False):
        """
        创建增强版带输入框的滑块控件
        
        Args:
            parent: 父容器
            variable: 绑定的变量
            from_: 最小值
            to: 最大值
            label_text: 标签文本
            step: 步长
            unit: 单位
            tooltip: 提示信息
            dual_mode: 是否启用双向选择模式
            
        Returns:
            tuple: (container_frame, scale, entry, dual_frame) 控件元组
        """
        # 创建主容器
        container_frame = ttk.Frame(parent)
        
        # 标签行
        label_frame = ttk.Frame(container_frame)
        label_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(label_frame, text=label_text, font=("微软雅黑", 9, "bold")).pack(side=LEFT)
        if unit:
            ttk.Label(label_frame, text=f"({unit})", 
                     font=("微软雅黑", 8), foreground="gray").pack(side=LEFT, padx=(5, 0))
        
        # 双向选择模式
        dual_frame = None
        if dual_mode:
            dual_frame = ttk.Frame(container_frame)
            dual_frame.pack(fill=X, pady=(0, 5))
            
            # 预设值按钮
            presets = self._get_parameter_presets(label_text)
            for i, (preset_name, preset_value) in enumerate(presets):
                btn = ttk.Button(dual_frame, text=preset_name, width=8,
                               bootstyle="outline-secondary",
                               command=lambda v=preset_value: self._set_preset_value(variable, v))
                btn.pack(side=LEFT, padx=(0, 5))
        
        # 滑块和输入框行
        control_frame = ttk.Frame(container_frame)
        control_frame.pack(fill=X, pady=(0, 5))
        
        # 滑块
        scale = ttk.Scale(control_frame, from_=from_, to=to, variable=variable,
                         orient=HORIZONTAL, command=self.on_parameter_changed)
        scale.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        # 输入框容器
        entry_frame = ttk.Frame(control_frame)
        entry_frame.pack(side=RIGHT)
        
        # 数值输入框
        entry = ttk.Entry(entry_frame, textvariable=variable, width=8, justify=CENTER)
        entry.pack(side=LEFT)
        
        # 快速调整按钮
        adj_frame = ttk.Frame(entry_frame)
        adj_frame.pack(side=LEFT, padx=(5, 0))
        
        ttk.Button(adj_frame, text="▲", width=2, 
                  command=lambda: self._adjust_value(variable, step, to)).pack(side=TOP)
        ttk.Button(adj_frame, text="▼", width=2,
                  command=lambda: self._adjust_value(variable, -step, from_)).pack(side=BOTTOM)
        
        # 绑定输入验证
        def validate_input():
            try:
                value = variable.get()
                if value < from_:
                    variable.set(from_)
                elif value > to:
                    variable.set(to)
            except:
                variable.set(from_)
        
        entry.bind('<FocusOut>', lambda e: validate_input())
        entry.bind('<Return>', lambda e: validate_input())
        
        # 提示信息
        if tooltip:
            info_label = ttk.Label(container_frame, text=f"💡 {tooltip}", 
                                 font=("微软雅黑", 8), foreground="blue")
            info_label.pack(fill=X, pady=(0, 5))
        
        return container_frame, scale, entry, dual_frame
    
    def _get_parameter_presets(self, param_name):
        """获取参数预设值"""
        presets = {
            "技能持续时间": [("短", 5), ("中", 15), ("长", 30)],
            "伤害倍率": [("低", 120), ("中", 200), ("高", 400)],
            "回转时间": [("快", 15), ("中", 30), ("慢", 60)],
            "敌人防御力": [("无甲", 0), ("轻甲", 300), ("重甲", 800)],
            "敌人法抗": [("无抗", 0), ("中抗", 30), ("高抗", 70)]
        }
        return presets.get(param_name, [])
    
    def _set_preset_value(self, variable, value):
        """设置预设值"""
        variable.set(value)
        if self.auto_update_var.get() and self.current_operator:
            self.calculate_now()
    
    def _adjust_value(self, variable, delta, limit):
        """调整数值"""
        current = variable.get()
        new_value = current + delta
        
        if delta > 0:  # 增加
            new_value = min(new_value, limit)
        else:  # 减少
            new_value = max(new_value, limit)
        
        variable.set(new_value)
        if self.auto_update_var.get() and self.current_operator:
            self.calculate_now()

    def create_scale_with_entry(self, parent, variable, from_, to, label_text=None, row=None, width=8):
        """
        创建带输入框的滑块控件（保留兼容性）
        
        Args:
            parent: 父容器
            variable: 绑定的变量
            from_: 最小值
            to: 最大值
            label_text: 标签文本（可选）
            row: 行号（用于grid布局，可选）
            width: 输入框宽度
            
        Returns:
            tuple: (frame, scale, entry) 控件元组
        """
        # 创建容器框架
        frame = ttk.Frame(parent)
        
        # 创建滑块
        scale = ttk.Scale(frame, from_=from_, to=to, variable=variable,
                         orient=HORIZONTAL, command=self.on_parameter_changed)
        scale.pack(side=LEFT, fill=X, expand=True)
        
        # 创建输入框
        entry = ttk.Entry(frame, textvariable=variable, width=width)
        entry.pack(side=RIGHT, padx=(5, 0))
        
        # 绑定输入验证
        def validate_input():
            try:
                value = variable.get()
                if value < from_:
                    variable.set(from_)
                elif value > to:
                    variable.set(to)
            except:
                variable.set(from_)
        
        entry.bind('<FocusOut>', lambda e: validate_input())
        entry.bind('<Return>', lambda e: validate_input())
        
        return frame, scale, entry
    
    def create_compact_scale_with_entry(self, parent, variable, from_, to, label_text, step=1, 
                                      unit="", tooltip="", show_presets=False):
        """
        创建紧凑版带输入框的滑块控件（新的简化版本）
        
        Args:
            parent: 父容器
            variable: 绑定的变量
            from_: 最小值
            to: 最大值
            label_text: 标签文本
            step: 步长
            unit: 单位
            tooltip: 提示信息
            show_presets: 是否显示预设按钮
            
        Returns:
            tuple: (container_frame, scale, entry) 控件元组
        """
        # 创建主容器
        container_frame = ttk.Frame(parent)
        
        # 标签行 - 更紧凑的布局
        label_frame = ttk.Frame(container_frame)
        label_frame.pack(fill=X, pady=(0, 2))
        
        # 标签和单位在同一行
        label_text_with_unit = label_text
        if unit:
            label_text_with_unit += f" ({unit})"
        
        ttk.Label(label_frame, text=label_text_with_unit, 
                 font=("微软雅黑", 9)).pack(side=LEFT)
        
        # 可选的预设按钮 - 只显示关键预设
        if show_presets:
            preset_frame = ttk.Frame(label_frame)
            preset_frame.pack(side=RIGHT)
            
            presets = self._get_parameter_presets(label_text)
            # 只显示前3个预设，减少空间占用
            for i, (preset_name, preset_value) in enumerate(presets[:3]):
                btn = ttk.Button(preset_frame, text=preset_name, width=6,
                               bootstyle="outline-secondary",
                               command=lambda v=preset_value: self._set_preset_value(variable, v))
                btn.pack(side=LEFT, padx=(2, 0))
        
        # 滑块和输入框行 - 紧凑布局
        control_frame = ttk.Frame(container_frame)
        control_frame.pack(fill=X, pady=(0, 2))
        
        # 滑块
        scale = ttk.Scale(control_frame, from_=from_, to=to, variable=variable,
                         orient=HORIZONTAL, command=self.on_parameter_changed)
        scale.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        
        # 数值输入框
        entry = ttk.Entry(control_frame, textvariable=variable, width=6, justify=CENTER)
        entry.pack(side=RIGHT)
        
        # 绑定输入验证（保持与原版相同的验证逻辑）
        def validate_input():
            try:
                value = variable.get()
                if value < from_:
                    variable.set(from_)
                elif value > to:
                    variable.set(to)
            except:
                variable.set(from_)
        
        entry.bind('<FocusOut>', lambda e: validate_input())
        entry.bind('<Return>', lambda e: validate_input())
        
        # 简化的提示信息（如果需要）
        if tooltip:
            info_label = ttk.Label(container_frame, text=f"💡 {tooltip}", 
                                 font=("微软雅黑", 7), foreground="gray")
            info_label.pack(fill=X, pady=(0, 2))
        
        return container_frame, scale, entry
    
    def setup_ui(self):
        """设置计算面板UI - 集成隐形滚动功能"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制栏 - 模式切换区域（新增）
        mode_control_frame = ttk.Frame(main_frame)
        mode_control_frame.pack(fill=X, pady=(0, 10))
        
        # 模式选择
        ttk.Label(mode_control_frame, text="分析模式：", font=("微软雅黑", 10, "bold")).pack(side=LEFT)
        ttk.Radiobutton(mode_control_frame, text="单干员分析", 
                       variable=self.analysis_mode, value="single",
                       command=self.switch_analysis_mode).pack(side=LEFT, padx=(5, 15))
        ttk.Radiobutton(mode_control_frame, text="多干员对比", 
                       variable=self.analysis_mode, value="multi",
                       command=self.switch_analysis_mode).pack(side=LEFT)
        
        # 操作按钮
        ttk.Button(mode_control_frame, text="重置参数", bootstyle=WARNING,
                  command=self.reset_parameters).pack(side=RIGHT, padx=(0, 5))
        ttk.Button(mode_control_frame, text="导出结果", bootstyle=SUCCESS,
                  command=self.export_results).pack(side=RIGHT, padx=(0, 5))
        
        # 创建左右分栏
        paned_window = ttk.PanedWindow(main_frame, orient=HORIZONTAL)
        paned_window.pack(fill=BOTH, expand=True)
        
        # 左侧：控制面板（使用隐形滚动）
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        # 创建隐形滚动容器
        self.scroll_frame = InvisibleScrollFrame(left_frame, scroll_speed=4)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        
        # 右侧：结果显示
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        # 在隐形滚动容器中创建控制区域
        self.create_control_area(self.scroll_frame.scrollable_frame)
        
        # 创建结果显示区域
        self.create_result_area(right_frame)
    
    def create_result_area(self, parent):
        """创建自适应的结果显示区域"""
        # 结果容器
        self.result_container = parent
        
        # 单选模式结果显示
        self.single_result_frame = ttk.Frame(self.result_container)
        self.create_single_operator_results(self.single_result_frame)
        
        # 多选模式结果显示
        self.multi_result_frame = ttk.Frame(self.result_container)
        self.create_multi_operator_results(self.multi_result_frame)
        
        # 根据当前模式显示对应结果
        self.update_result_display_mode()
    
    def create_single_operator_results(self, parent):
        """创建单干员结果显示区域（横向布局）"""
        # 基础结果显示
        basic_frame = ttk.LabelFrame(parent, text="基础计算结果", padding=10)
        basic_frame.pack(fill=X, pady=(0, 10))
        
        # 创建结果网格
        result_grid = ttk.Frame(basic_frame)
        result_grid.pack(fill=X)
        
        # 动态结果显示区域（根据干员职业类型显示不同内容）
        self.result_labels = {}
        
        # DPS/HPS结果
        self.dps_hps_label = ttk.Label(result_grid, text="DPS：", font=("微软雅黑", 10, "bold"))
        self.dps_hps_label.grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.result_labels['dps_hps'] = ttk.Label(result_grid, textvariable=self.dps_result_var, 
                                                 foreground="green", font=("微软雅黑", 10))
        self.result_labels['dps_hps'].grid(row=0, column=1, sticky=W, padx=5, pady=2)
        
        # DPH/HPH结果
        self.dph_hph_label = ttk.Label(result_grid, text="DPH：", font=("微软雅黑", 10, "bold"))
        self.dph_hph_label.grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.result_labels['dph_hph'] = ttk.Label(result_grid, textvariable=self.dph_result_var, 
                                                 foreground="blue", font=("微软雅黑", 10))
        self.result_labels['dph_hph'].grid(row=1, column=1, sticky=W, padx=5, pady=2)
        
        # 总伤害（时间轴模式）
        self.total_damage_var = StringVar(value="0.0")
        self.total_damage_label = ttk.Label(result_grid, text="总伤害：", font=("微软雅黑", 10, "bold"))
        self.result_labels['total_damage'] = ttk.Label(result_grid, textvariable=self.total_damage_var,
                                                      foreground="red", font=("微软雅黑", 10))
        
        # 破甲线结果
        ttk.Label(result_grid, text="破甲线：", font=("微软雅黑", 10, "bold")).grid(row=4, column=0, sticky=W, padx=5, pady=2)
        ttk.Label(result_grid, textvariable=self.armor_break_var, foreground="red", 
                 font=("微软雅黑", 10)).grid(row=4, column=1, sticky=W, padx=5, pady=2)
        
        # 详细结果显示 - 改为横向布局
        detail_frame = ttk.LabelFrame(parent, text="详细计算结果 (横向显示)", padding=10)
        detail_frame.pack(fill=BOTH, expand=True)
        
        # 创建隐形滚动容器包装结果表格
        result_scroll_frame = InvisibleScrollFrame(detail_frame, scroll_speed=3)
        result_scroll_frame.pack(fill=BOTH, expand=True)
        
        # 在隐形滚动容器中创建结果表格 - 横向布局准备
        # 注意：这里我们先创建一个空的表格，实际的横向数据将在update_detail_results中填充
        self.result_tree = SortableTreeview(result_scroll_frame.scrollable_frame, show='headings', height=3)
        
        # 启用排序功能
        self.result_tree.enable_sorting()
        
        # 直接打包表格（无需额外滚动条）
        self.result_tree.pack(fill=BOTH, expand=True)
        
        # 为表格绑定滚轮事件
        result_scroll_frame.bind_mousewheel_recursive(self.result_tree)
    
    def create_multi_operator_results(self, parent):
        """创建多干员对比结果表格"""
        # 基础统计显示
        summary_frame = ttk.LabelFrame(parent, text="对比概览", padding=10)
        summary_frame.pack(fill=X, pady=(0, 10))
        
        # 统计信息标签
        self.summary_labels = {}
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=X)
        
        # 对比统计信息
        ttk.Label(summary_grid, text="选中干员数：", font=("微软雅黑", 9, "bold")).grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.summary_labels['count'] = ttk.Label(summary_grid, text="0", foreground="blue", font=("微软雅黑", 9))
        self.summary_labels['count'].grid(row=0, column=1, sticky=W, padx=5, pady=2)
        
        ttk.Label(summary_grid, text="最高DPS：", font=("微软雅黑", 9, "bold")).grid(row=0, column=2, sticky=W, padx=5, pady=2)
        self.summary_labels['max_dps'] = ttk.Label(summary_grid, text="0.0", foreground="green", font=("微软雅黑", 9))
        self.summary_labels['max_dps'].grid(row=0, column=3, sticky=W, padx=5, pady=2)
        
        ttk.Label(summary_grid, text="平均DPS：", font=("微软雅黑", 9, "bold")).grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.summary_labels['avg_dps'] = ttk.Label(summary_grid, text="0.0", foreground="orange", font=("微软雅黑", 9))
        self.summary_labels['avg_dps'].grid(row=1, column=1, sticky=W, padx=5, pady=2)
        
        ttk.Label(summary_grid, text="最高性价比：", font=("微软雅黑", 9, "bold")).grid(row=1, column=2, sticky=W, padx=5, pady=2)
        self.summary_labels['max_efficiency'] = ttk.Label(summary_grid, text="0.0", foreground="purple", font=("微软雅黑", 9))
        self.summary_labels['max_efficiency'].grid(row=1, column=3, sticky=W, padx=5, pady=2)
        
        # 详细对比表格
        detail_frame = ttk.LabelFrame(parent, text="详细对比 (纵向显示，点击列标题排序)", padding=10)
        detail_frame.pack(fill=BOTH, expand=True)
        
        # 对比结果表格（动态列生成）
        self.comparison_tree = SortableTreeview(
            detail_frame,
            show='headings',
            height=15
        )
        self.comparison_tree.pack(fill=BOTH, expand=True)
    
    def update_result_display_mode(self):
        """根据分析模式切换结果显示"""
        mode = self.analysis_mode.get()
        
        if mode == "single":
            # 显示单选结果，隐藏多选结果
            self.single_result_frame.pack(fill=BOTH, expand=True)
            self.multi_result_frame.pack_forget()
        elif mode == "multi":
            # 显示多选结果，隐藏单选结果
            self.single_result_frame.pack_forget()
            self.multi_result_frame.pack(fill=BOTH, expand=True)
    
    def switch_analysis_mode(self):
        """切换分析模式（单选/多选）"""
        mode = self.analysis_mode.get()
        
        if mode == "single":
            # 切换到单干员模式
            self.update_operator_selection_display()
            self.update_result_display_mode()
            self.update_status("已切换到单干员分析模式")
        elif mode == "multi":
            # 切换到多干员对比模式
            self.update_operator_selection_display()
            self.update_result_display_mode()
            self.update_status("已切换到多干员对比模式")
        
        # 清空当前结果
        self.clear_current_results()
    
    def calculate_multi_operators(self):
        """批量计算多个干员的数据"""
        if not self.selected_operators_list:
            self.update_status("请先选择要对比的干员")
            return {}
        
        results = {}
        enemy_def = self.enemy_def_var.get()
        enemy_mdef = self.enemy_mdef_var.get()
        time_range = self.time_range_var.get()
        calc_mode = self.calc_mode_var.get()
        
        try:
            for operator in self.selected_operators_list:
                # 临时设置当前干员
                original_operator = self.current_operator
                self.current_operator = operator
                
                # 根据计算模式执行不同的计算
                if calc_mode == "basic_damage":
                    operator_result = self.calculate_basic_damage(enemy_def, enemy_mdef)
                elif calc_mode == "timeline_damage":
                    operator_result = self.calculate_timeline_damage(enemy_def, enemy_mdef, time_range)
                elif calc_mode == "skill_cycle":
                    operator_result = self.calculate_skill_cycle(enemy_def, enemy_mdef, time_range)
                else:
                    operator_result = self.calculate_basic_damage(enemy_def, enemy_mdef)
                
                # 添加基础干员信息
                operator_result.update({
                    'name': operator['name'],
                    'class_type': operator['class_type'],
                    'atk': operator['atk'],
                    'hp': operator['hp'],
                    'cost': operator.get('cost', 1),
                    'atk_speed': operator.get('atk_speed', 1.0),
                    'atk_type': self.determine_attack_type(operator)
                })
                
                # 计算性价比
                cost = operator.get('cost', 1)
                if operator_result.get('type') == 'damage':
                    cost_efficiency = operator_result.get('dps', 0) / max(cost, 1)
                else:
                    cost_efficiency = operator_result.get('hps', 0) / max(cost, 1)
                operator_result['cost_efficiency'] = cost_efficiency
                
                results[operator['name']] = operator_result
                
                # 恢复原始干员
                self.current_operator = original_operator
            
            # 存储对比结果
            self.multi_comparison_results = results
            
            # 生成对比表格数据
            self.generate_comparison_table_data(results)
            
            # 更新概览统计
            self.update_comparison_summary(results)
            
            return results
            
        except Exception as e:
            self.update_status(f"多干员计算失败: {str(e)}")
            return {}
    
    def generate_comparison_table_data(self, results):
        """生成纵向对比表格数据（每个干员一行，指标作为列）"""
        if not results or not hasattr(self, 'comparison_tree'):
            return
        
        # 清空现有数据
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        
        # 定义对比指标作为列
        comparison_columns = [
            '干员名称', '职业类型', '攻击类型', '攻击力', 
            '攻击速度', '生命值', '部署费用', 'DPS', 'DPH', 
            '破甲线', '性价比'
        ]
        
        # 配置表格列
        self.comparison_tree.configure(columns=comparison_columns)
        
        # 设置列标题
        for col in comparison_columns:
            self.comparison_tree.heading(col, text=col)
            if col == '干员名称':
                self.comparison_tree.column(col, width=100, anchor=W)
            else:
                self.comparison_tree.column(col, width=80, anchor=CENTER)
        
        # 填充数据：每个干员一行
        for operator_name, operator_result in results.items():
            row_data = []
            
            # 按列顺序填充数据
            row_data.append(operator_result.get('name', operator_name))
            row_data.append(operator_result.get('class_type', 'N/A'))
            row_data.append(operator_result.get('atk_type', 'N/A'))
            row_data.append(self.format_display_value(operator_result.get('atk', 0), 'atk'))
            row_data.append(self.format_display_value(operator_result.get('atk_speed', 0), 'atk_speed'))
            row_data.append(self.format_display_value(operator_result.get('hp', 0), 'hp'))
            row_data.append(self.format_display_value(operator_result.get('cost', 0), 'cost'))
            row_data.append(self.format_display_value(operator_result.get('dps', 0), 'dps'))
            row_data.append(self.format_display_value(operator_result.get('dph', 0), 'dph'))
            row_data.append(self.format_display_value(operator_result.get('armor_break', 0), 'armor_break'))
            row_data.append(self.format_display_value(operator_result.get('cost_efficiency', 0), 'cost_efficiency'))
            
            # 插入数据行
            self.comparison_tree.insert('', 'end', values=row_data)
        
        # 为所有列启用排序
        self.comparison_tree.enable_sorting(comparison_columns)
        
        # 设置自定义排序规则，优化数值排序
        def custom_sort_key(value):
            """自定义排序键，优化数值排序"""
            if isinstance(value, str):
                # 处理带单位的数值
                numeric_match = re.match(r'([\d.]+)', value)
                if numeric_match:
                    try:
                        return float(numeric_match.group(1))
                    except ValueError:
                        pass
            return value
        
        # 应用自定义排序
        if hasattr(self.comparison_tree, 'get_sort_key'):
            original_get_sort_key = self.comparison_tree.get_sort_key
            self.comparison_tree.get_sort_key = custom_sort_key
    
    def format_display_value(self, value, metric_key):
        """格式化显示值"""
        if value == 'N/A' or value is None:
            return 'N/A'
        
        try:
            if metric_key in ['dps', 'dph', 'hps', 'hph', 'cost_efficiency']:
                return f"{float(value):.2f}"
            elif metric_key in ['atk', 'hp', 'cost', 'armor_break']:
                return f"{int(value)}"
            elif metric_key == 'atk_speed':
                return f"{float(value):.1f}"
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def update_comparison_summary(self, results):
        """更新对比概览统计"""
        if not results or not hasattr(self, 'summary_labels'):
            return
        
        try:
            # 统计干员数量
            count = len(results)
            self.summary_labels['count'].config(text=str(count))
            
            # 统计DPS相关数据
            dps_values = [r.get('dps', 0) for r in results.values() if r.get('dps', 0) > 0]
            if dps_values:
                max_dps = max(dps_values)
                avg_dps = sum(dps_values) / len(dps_values)
                self.summary_labels['max_dps'].config(text=f"{max_dps:.2f}")
                self.summary_labels['avg_dps'].config(text=f"{avg_dps:.2f}")
            else:
                self.summary_labels['max_dps'].config(text="0.0")
                self.summary_labels['avg_dps'].config(text="0.0")
            
            # 统计性价比数据
            efficiency_values = [r.get('cost_efficiency', 0) for r in results.values() if r.get('cost_efficiency', 0) > 0]
            if efficiency_values:
                max_efficiency = max(efficiency_values)
                self.summary_labels['max_efficiency'].config(text=f"{max_efficiency:.2f}")
            else:
                self.summary_labels['max_efficiency'].config(text="0.0")
                
        except Exception as e:
            print(f"更新对比概览失败: {e}")
    
    def refresh_operator_list(self):
        """刷新干员列表（单选模式）"""
        try:
            operators = self.db_manager.get_all_operators()
            operator_names = [f"{op['name']} ({op['class_type']})" for op in operators]
            
            if hasattr(self, 'operator_combo'):
                self.operator_combo['values'] = operator_names
                
                if operator_names:
                    self.operator_combo.set(operator_names[0])
                    self.on_operator_selected()
            
            if self.status_callback:
                self.status_callback(f"已加载 {len(operators)} 个干员")
                
        except Exception as e:
            messagebox.showerror("错误", f"刷新干员列表失败：{str(e)}")
    
    def clear_current_results(self):
        """清空当前计算结果"""
        # 清空单干员结果
        self.dps_result_var.set("0.0")
        self.dph_result_var.set("0.0")
        self.hps_result_var.set("0.0")
        self.hph_result_var.set("0.0")
        self.armor_break_var.set("0")
        
        # 清空多干员对比结果
        self.multi_comparison_results.clear()
        
        # 清空详细结果表格
        if hasattr(self, 'result_tree'):
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
    
    def create_control_area(self, parent):
        """创建控制区域 - 在隐形滚动框架中"""
        # 创建干员选择区域
        self.create_operator_selection_area(parent)
        
        # 敌人参数与计算选项合并区域
        params_frame = ttk.LabelFrame(parent, text="计算参数", padding=8)
        params_frame.pack(fill=X, pady=(0, 8))
        
        # 敌人参数区域（上下堆叠布局）
        enemy_params_frame = ttk.Frame(params_frame)
        enemy_params_frame.pack(fill=X, pady=(0, 8))
        
        # 敌人防御力（上方）
        def_container, self.def_scale, self.def_entry = self.create_compact_scale_with_entry(
            enemy_params_frame, self.enemy_def_var, 0, 1000, "敌人防御力", step=50, unit="点",
            tooltip="物理防御力，只影响物理伤害计算", show_presets=False
        )
        def_container.pack(fill=X, pady=(0, 3))
        
        # 敌人法抗（下方）
        mdef_container, self.mdef_scale, self.mdef_entry = self.create_compact_scale_with_entry(
            enemy_params_frame, self.enemy_mdef_var, 0, 100, "敌人法抗", step=5, unit="%",
            tooltip="法术抗性，只影响法术伤害计算", show_presets=False
        )
        mdef_container.pack(fill=X, pady=(3, 0))
        self.mdef_container = mdef_container  # 保存引用
        
        # 计算精度和自动更新选项
        options_frame = ttk.Frame(params_frame)
        options_frame.pack(fill=X, pady=(8, 0))
        
        ttk.Label(options_frame, text="计算精度：", font=("微软雅黑", 9)).pack(side=LEFT)
        self.precision_var = StringVar(value="normal")
        ttk.Radiobutton(options_frame, text="快速", variable=self.precision_var, value="fast").pack(side=LEFT, padx=(8, 0))
        ttk.Radiobutton(options_frame, text="正常", variable=self.precision_var, value="normal").pack(side=LEFT, padx=(8, 0))
        ttk.Radiobutton(options_frame, text="精确", variable=self.precision_var, value="precise").pack(side=LEFT, padx=(8, 0))
        
        # 自动更新选项
        ttk.Checkbutton(options_frame, text="自动更新计算结果", 
                       variable=self.auto_update_var).pack(side=RIGHT)
        
        # 时间范围控制区域
        time_frame = ttk.LabelFrame(parent, text="时间范围", padding=8)
        self.time_frame_widget = time_frame  # 保存widget引用
        self.time_frame = time_frame  # 保存引用供技能参数使用
        
        time_container, self.time_scale, self.time_entry = self.create_compact_scale_with_entry(
            time_frame, self.time_range_var, 1, 300, "计算时长", step=10, unit="秒",
            tooltip="计算伤害的时间范围，用于时间轴分析", show_presets=False
        )
        time_container.pack(fill=X, pady=(0, 5))
        
        # 初始状态下隐藏时间范围（默认模式是基础伤害）
        self.time_frame_widget.pack_forget()
        
        # 计算模式选择区域
        mode_frame = ttk.LabelFrame(parent, text="计算模式", padding=8)
        mode_frame.pack(fill=X, pady=(0, 8))
        
        # 新的3种计算模式 - 使用更紧凑的布局
        calc_modes = [
            ("基础伤害", "basic_damage", "计算基础DPS和DPH"),
            ("时间轴伤害", "timeline_damage", "计算指定时间内的总伤害"),
            ("开启技能伤害", "skill_cycle", "包含技能的完整伤害周期")
        ]
        
        # 使用网格布局，每行最多显示2个模式
        for i, (mode_text, mode_value, mode_desc) in enumerate(calc_modes):
            mode_container = ttk.Frame(mode_frame)
            mode_container.pack(fill=X, pady=1)
            
            # 单选按钮和简化的描述
            mode_radio = ttk.Radiobutton(mode_container, text=mode_text, variable=self.calc_mode_var, 
                           value=mode_value, command=self.on_mode_changed)
            mode_radio.pack(side=LEFT)
            
            # 简化描述文字，使用更小的字体
            desc_label = ttk.Label(mode_container, text=f"- {mode_desc}", 
                     font=("微软雅黑", 7), foreground="gray")
            desc_label.pack(side=LEFT, padx=(8, 0))
        
        # 技能参数控制区域（仅在技能周期模式下显示）
        self.skill_frame = ttk.LabelFrame(parent, text="技能参数", padding=8)
        
        # 技能触发模式选择 - 保持原有布局
        trigger_frame = ttk.Frame(self.skill_frame)
        trigger_frame.pack(fill=X, pady=(0, 8))
        
        ttk.Label(trigger_frame, text="技能触发模式：", font=("微软雅黑", 9, "bold")).pack(side=LEFT)
        ttk.Radiobutton(trigger_frame, text="手动触发", variable=self.skill_trigger_mode_var, 
                       value="manual").pack(side=LEFT, padx=(10, 0))
        ttk.Radiobutton(trigger_frame, text="自动触发", variable=self.skill_trigger_mode_var, 
                       value="auto").pack(side=LEFT, padx=(10, 0))
        
        # 技能基础参数 - 使用左右并排布局
        basic_params_frame = ttk.Frame(self.skill_frame)
        basic_params_frame.pack(fill=X, pady=(0, 8))
        
        # 左侧：技能持续时间
        duration_frame = ttk.Frame(basic_params_frame)
        duration_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        
        skill_duration_container, self.skill_duration_scale, self.skill_duration_entry = self.create_compact_scale_with_entry(
            duration_frame, self.skill_duration_var, 1, 60, "技能持续时间", step=1, unit="秒",
            tooltip="技能效果持续的时间", show_presets=True
        )
        skill_duration_container.pack(fill=X)
        
        # 右侧：伤害倍率
        multiplier_frame = ttk.Frame(basic_params_frame)
        multiplier_frame.pack(side=RIGHT, fill=X, expand=True, padx=(3, 0))
        
        skill_multiplier_container, self.skill_multiplier_scale, self.skill_multiplier_entry = self.create_compact_scale_with_entry(
            multiplier_frame, self.skill_multiplier_var, 100, 800, "伤害倍率", step=10, unit="%",
            tooltip="技能期间的伤害倍率增幅", show_presets=True
        )
        skill_multiplier_container.pack(fill=X)
        
        # 回转时间 - 单独一行
        cooldown_frame = ttk.Frame(self.skill_frame)
        cooldown_frame.pack(fill=X, pady=(0, 8))
        
        skill_cooldown_container, self.skill_cooldown_scale, self.skill_cooldown_entry = self.create_compact_scale_with_entry(
            cooldown_frame, self.skill_cooldown_var, 5, 180, "回转时间", step=5, unit="秒",
            tooltip="技能冷却时间，影响技能循环", show_presets=True
        )
        skill_cooldown_container.pack(fill=X)
        
        # 技能高级参数 - 更紧凑的布局
        advanced_skill_frame = ttk.LabelFrame(self.skill_frame, text="高级技能参数", padding=5)
        advanced_skill_frame.pack(fill=X, pady=(8, 0))
        
        # 技能次数和SP消耗 - 保持原有布局
        charges_frame = ttk.Frame(advanced_skill_frame)
        charges_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(charges_frame, text="技能次数：").pack(side=LEFT)
        charges_spinbox = ttk.Spinbox(charges_frame, from_=1, to=10, textvariable=self.skill_charges_var, width=8)
        charges_spinbox.pack(side=LEFT, padx=(5, 20))
        
        ttk.Label(charges_frame, text="SP消耗：").pack(side=LEFT)
        sp_spinbox = ttk.Spinbox(charges_frame, from_=10, to=100, textvariable=self.skill_sp_cost_var, width=8)
        sp_spinbox.pack(side=LEFT, padx=(5, 0))
        
        # 攻击加成参数 - 使用左右并排布局
        bonus_params_frame = ttk.Frame(advanced_skill_frame)
        bonus_params_frame.pack(fill=X, pady=(5, 0))
        
        # 左侧：攻击力加成
        atk_bonus_frame = ttk.Frame(bonus_params_frame)
        atk_bonus_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        
        atk_bonus_container, _, _ = self.create_compact_scale_with_entry(
            atk_bonus_frame, self.atk_bonus_var, 0, 2000, "攻击力加成", step=50, unit="点",
            tooltip="技能期间增加的攻击力数值", show_presets=False
        )
        atk_bonus_container.pack(fill=X)
        
        # 右侧：攻速加成
        aspd_bonus_frame = ttk.Frame(bonus_params_frame)
        aspd_bonus_frame.pack(side=RIGHT, fill=X, expand=True, padx=(3, 0))
        
        aspd_bonus_container, _, _ = self.create_compact_scale_with_entry(
            aspd_bonus_frame, self.aspd_bonus_var, 0, 200, "攻速加成", step=5, unit="%",
            tooltip="技能期间的攻击速度增幅", show_presets=False
        )
        aspd_bonus_container.pack(fill=X)
        
        # 计算按钮区域
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, pady=(8, 0))
        
        ttk.Button(button_frame, text="立即计算", bootstyle=PRIMARY, 
                  command=self.calculate_now).pack(side=LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="重置参数", bootstyle=WARNING,
                  command=self.reset_parameters).pack(side=LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出结果", bootstyle=SUCCESS,
                  command=self.export_results).pack(side=LEFT, padx=(0, 5))
        
        # 预设管理
        preset_frame = ttk.Frame(button_frame)
        preset_frame.pack(side=RIGHT)
        
        ttk.Button(preset_frame, text="保存预设", bootstyle="outline-info",
                  command=self.save_preset).pack(side=LEFT, padx=(0, 2))
        ttk.Button(preset_frame, text="加载预设", bootstyle="outline-info",
                  command=self.load_preset).pack(side=LEFT)
        
        # 初始隐藏技能参数
        self.skill_frame.pack_forget()
    
    def create_operator_selection_area(self, parent):
        """创建自适应的干员选择区域"""
        # 容器框架
        self.operator_frame = ttk.LabelFrame(parent, text="干员选择", padding=10)
        self.operator_frame.pack(fill=X, pady=(0, 10))
        
        # 单选模式组件
        self.single_mode_frame = ttk.Frame(self.operator_frame)
        
        # 干员选择下拉框
        ttk.Label(self.single_mode_frame, text="选择干员：").pack(anchor=W)
        self.operator_combo = ttk.Combobox(self.single_mode_frame, textvariable=self.selected_operator_var, 
                                          state="readonly", width=30)
        self.operator_combo.pack(fill=X, pady=5)
        self.operator_combo.bind('<<ComboboxSelected>>', self.on_operator_selected)
        
        # 刷新按钮
        ttk.Button(self.single_mode_frame, text="刷新干员列表", bootstyle=INFO,
                  command=self.refresh_operator_list).pack(pady=5)
        
        # 多选模式组件
        self.multi_mode_frame = ttk.Frame(self.operator_frame)
        self.create_multi_operator_interface(self.multi_mode_frame)
        
        # 根据当前模式显示对应组件
        self.update_operator_selection_display()
    
    def update_operator_selection_display(self):
        """根据分析模式切换干员选择显示"""
        mode = self.analysis_mode.get()
        
        if mode == "single":
            # 显示单选组件，隐藏多选组件
            self.single_mode_frame.pack(fill=BOTH, expand=True)
            self.multi_mode_frame.pack_forget()
        elif mode == "multi":
            # 显示多选组件，隐藏单选组件
            self.single_mode_frame.pack_forget()
            self.multi_mode_frame.pack(fill=BOTH, expand=True)
            # 刷新可选干员列表
            self.refresh_available_operators()
    
    def on_operator_selected(self, event=None):
        """干员选择事件处理（单选模式）"""
        try:
            selection = self.operator_combo.get()
            if not selection or selection == "请选择干员":
                return
            
            # 从选择字符串中提取干员名称（格式：名称 (职业)）
            name_end = selection.find(' (')
            if name_end > 0:
                operator_name = selection[:name_end]
            else:
                operator_name = selection
            
            # 从数据库获取干员信息
            operators = self.db_manager.get_all_operators()
            selected_operator = None
            
            for op in operators:
                if op['name'] == operator_name:
                    selected_operator = op
                    break
            
            if selected_operator:
                self.current_operator = selected_operator
                
                # 根据干员职业类型调整显示内容
                class_type = selected_operator.get('class_type', '')
                if class_type == '医疗':
                    # 医疗干员显示治疗相关数据
                    self.dps_hps_label.configure(text="HPS：")
                    self.dph_hph_label.configure(text="HPH：")
                    self.result_labels['dps_hps'].configure(textvariable=self.hps_result_var, foreground="orange")
                    self.result_labels['dph_hph'].configure(textvariable=self.hph_result_var, foreground="purple")
                else:
                    # 攻击干员显示伤害相关数据
                    self.dps_hps_label.configure(text="DPS：")
                    self.dph_hph_label.configure(text="DPH：")
                    self.result_labels['dps_hps'].configure(textvariable=self.dps_result_var, foreground="green")
                    self.result_labels['dph_hph'].configure(textvariable=self.dph_result_var, foreground="blue")
                
                # 如果开启了自动更新，立即计算
                if self.auto_update_var.get():
                    self.calculate_now()
            
        except Exception as e:
            self.update_status(f"选择干员失败: {str(e)}")
    
    def on_parameter_changed(self, value=None):
        """参数变化事件处理"""
        if self.auto_update_var.get():
            mode = self.analysis_mode.get()
            if mode == "single" and self.current_operator:
                self.calculate_now()
            elif mode == "multi" and self.selected_operators_list:
                self.calculate_now()
    
    def on_mode_changed(self):
        """计算模式变更事件"""
        mode = self.calc_mode_var.get()
        
        # 根据模式显示/隐藏时间范围控件
        if mode == "timeline_damage":
            self.time_frame_widget.pack(fill=X, pady=(0, 8), after=self.mdef_container)
        else:
            self.time_frame_widget.pack_forget()
        
        # 根据模式显示/隐藏技能参数
        if mode == "skill_cycle":
            self.skill_frame.pack(fill=X, pady=(0, 8), after=self.mdef_container)
        else:
            self.skill_frame.pack_forget()
        
        # 根据模式调整结果显示
        if mode == "timeline_damage":
            # 时间轴模式显示总伤害
            self.total_damage_label.grid(row=2, column=0, sticky=W, padx=5, pady=2)
            self.result_labels['total_damage'].grid(row=2, column=1, sticky=W, padx=5, pady=2)
        else:
            # 其他模式隐藏总伤害
            self.total_damage_label.grid_remove()
            self.result_labels['total_damage'].grid_remove()
        
        # 自动重新计算
        if self.auto_update_var.get():
            self.calculate_now()
    
    def calculate_basic_damage(self, enemy_def, enemy_mdef):
        """计算基础伤害"""
        operator = self.current_operator
        class_type = operator.get('class_type', '')
        
        if class_type == '医疗':
            # 医疗干员计算治疗量
            heal_per_hit = operator.get('atk', 0)
            atk_speed = operator.get('atk_speed', 1.0)
            hps = heal_per_hit * atk_speed
            
            return {
                'hps': hps,
                'hph': heal_per_hit,
                'armor_break': 0,
                'type': 'healing'
            }
        else:
            # 攻击干员计算伤害
            return self.calculate_damage_with_correct_type(operator, enemy_def, enemy_mdef)
    
    def calculate_timeline_damage(self, enemy_def, enemy_mdef, time_range):
        """计算时间轴伤害"""
        basic_result = self.calculate_basic_damage(enemy_def, enemy_mdef)
        
        if basic_result.get('type') == 'damage':
            total_damage = basic_result.get('dps', 0) * time_range
            basic_result['total_damage'] = total_damage
        elif basic_result.get('type') == 'healing':
            total_heal = basic_result.get('hps', 0) * time_range
            basic_result['total_heal'] = total_heal
        
        return basic_result
    
    def calculate_skill_cycle(self, enemy_def, enemy_mdef, time_range):
        """计算技能循环伤害"""
        operator = self.current_operator
        
        # 获取技能参数
        skill_duration = self.skill_duration_var.get()
        skill_multiplier = self.skill_multiplier_var.get() / 100.0
        skill_cooldown = self.skill_cooldown_var.get()
        atk_bonus = self.atk_bonus_var.get()
        aspd_bonus = self.aspd_bonus_var.get() / 100.0
        
        # 基础数据
        base_atk = operator.get('atk', 0)
        base_atk_speed = operator.get('atk_speed', 1.0)
        
        # 计算平常状态和技能状态的数据
        # 平常状态
        normal_result = self.calculate_basic_damage(enemy_def, enemy_mdef)
        
        # 技能状态
        skill_atk = base_atk + atk_bonus
        skill_atk_speed = base_atk_speed * (1 + aspd_bonus)
        
        # 临时修改干员数据计算技能状态
        original_atk = operator['atk']
        original_speed = operator['atk_speed']
        
        operator['atk'] = int(skill_atk * skill_multiplier)
        operator['atk_speed'] = skill_atk_speed
        
        skill_result = self.calculate_basic_damage(enemy_def, enemy_mdef)
        
        # 恢复原始数据
        operator['atk'] = original_atk
        operator['atk_speed'] = original_speed
        
        # 计算技能循环中的平均性能
        cycle_time = skill_duration + skill_cooldown
        skill_weight = skill_duration / cycle_time
        normal_weight = skill_cooldown / cycle_time
        
        if normal_result.get('type') == 'damage':
            avg_dps = (skill_result.get('dps', 0) * skill_weight + 
                      normal_result.get('dps', 0) * normal_weight)
            avg_dph = (skill_result.get('dph', 0) * skill_weight + 
                      normal_result.get('dph', 0) * normal_weight)
            
            result = {
                'dps': avg_dps,
                'dph': avg_dph,
                'armor_break': normal_result.get('armor_break', 0),
                'skill_dps': skill_result.get('dps', 0),
                'normal_dps': normal_result.get('dps', 0),
                'type': 'damage'
            }
        else:
            avg_hps = (skill_result.get('hps', 0) * skill_weight + 
                      normal_result.get('hps', 0) * normal_weight)
            avg_hph = (skill_result.get('hph', 0) * skill_weight + 
                      normal_result.get('hph', 0) * normal_weight)
            
            result = {
                'hps': avg_hps,
                'hph': avg_hph,
                'skill_hps': skill_result.get('hps', 0),
                'normal_hps': normal_result.get('hps', 0),
                'type': 'healing'
            }
        
        return result
    
    def update_result_display(self, results, calc_mode):
        """更新基础结果显示"""
        if results.get('type') == 'damage':
            self.dps_result_var.set(f"{results.get('dps', 0):.2f}")
            self.dph_result_var.set(f"{results.get('dph', 0):.2f}")
            self.armor_break_var.set(f"{results.get('armor_break', 0)}")
        elif results.get('type') == 'healing':
            self.hps_result_var.set(f"{results.get('hps', 0):.2f}")
            self.hph_result_var.set(f"{results.get('hph', 0):.2f}")
            self.armor_break_var.set("N/A")
        
        if calc_mode == "timeline_damage" and 'total_damage' in results:
            self.total_damage_var.set(f"{results['total_damage']:.0f}")
    
    def update_detail_results(self, results, enemy_def, enemy_mdef, time_range, calc_mode):
        """更新详细结果表格 - 单干员横向显示"""
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 定义横向显示的列（指标作为列）
        horizontal_columns = [
            '干员名称', '职业类型', '攻击类型', '攻击力', 
            '攻击速度', '敌人防御', '敌人法抗'
        ]
        
        # 根据结果类型添加相应的列
        if results.get('type') == 'damage':
            horizontal_columns.extend(['DPS', 'DPH', '破甲线'])
        elif results.get('type') == 'healing':
            horizontal_columns.extend(['HPS', 'HPH'])
        
        # 如果是时间轴模式，添加总伤害/总治疗列
        if calc_mode == "timeline_damage":
            if results.get('type') == 'damage' and 'total_damage' in results:
                horizontal_columns.append('总伤害')
            elif results.get('type') == 'healing' and 'total_heal' in results:
                horizontal_columns.append('总治疗')
        
        # 配置表格列
        self.result_tree.configure(columns=horizontal_columns)
        
        # 设置列标题
        for col in horizontal_columns:
            self.result_tree.heading(col, text=col, anchor=CENTER)
            self.result_tree.column(col, width=80, anchor=CENTER)
        
        # 准备数据行
        row_data = []
        
        # 基础信息
        row_data.append(self.current_operator['name'])
        row_data.append(self.current_operator['class_type'])
        
        # 攻击类型
        if results.get('type') == 'damage':
            atk_type = results.get('atk_type', self.determine_attack_type(self.current_operator))
            row_data.append(atk_type)
        else:
            row_data.append('治疗')
        
        # 干员属性
        row_data.append(str(self.current_operator['atk']))
        row_data.append(f"{self.current_operator['atk_speed']:.1f}")
        
        # 敌人参数
        row_data.append(str(enemy_def))
        row_data.append(f"{enemy_mdef}%")
        
        # 计算结果
        if results.get('type') == 'damage':
            row_data.append(f"{results.get('dps', 0):.2f}")
            row_data.append(f"{results.get('dph', 0):.2f}")
            row_data.append(str(results.get('armor_break', 0)))
        elif results.get('type') == 'healing':
            row_data.append(f"{results.get('hps', 0):.2f}")
            row_data.append(f"{results.get('hph', 0):.2f}")
        
        # 时间轴模式的总数值
        if calc_mode == "timeline_damage":
            if results.get('type') == 'damage' and 'total_damage' in results:
                row_data.append(f"{results['total_damage']:.0f}")
            elif results.get('type') == 'healing' and 'total_heal' in results:
                row_data.append(f"{results['total_heal']:.0f}")
        
        # 插入数据行
        self.result_tree.insert('', 'end', values=row_data)
        
        # 启用排序（对横向显示的各列）
        self.result_tree.enable_sorting(horizontal_columns)
    
    def reset_parameters(self):
        """重置参数"""
        self.enemy_def_var.set(0)
        self.enemy_mdef_var.set(0)
        self.time_range_var.set(90)
        self.calc_mode_var.set("basic_damage")
        
        # 重置技能参数
        self.reset_skill_parameters()
        
        # 清空结果
        self.clear_current_results()
        
        self.update_status("参数已重置")
    
    def export_results(self):
        """导出计算结果"""
        mode = self.analysis_mode.get()
        
        if mode == "single":
            if not self.current_operator:
                messagebox.showwarning("警告", "没有计算结果可导出")
                return
            self.export_single_results()
        elif mode == "multi":
            if not self.multi_comparison_results:
                messagebox.showwarning("警告", "没有对比结果可导出")
                return
            self.export_multi_results()
    
    def export_single_results(self):
        """导出单干员结果"""
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"{self.current_operator['name']}_计算结果.txt"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"干员伤害计算结果\n")
                    f.write(f"=" * 30 + "\n")
                    f.write(f"干员名称：{self.current_operator['name']}\n")
                    f.write(f"职业类型：{self.current_operator['class_type']}\n")
                    f.write(f"敌人防御：{self.enemy_def_var.get()}\n")
                    f.write(f"敌人法抗：{self.enemy_mdef_var.get()}%\n")
                    f.write(f"计算模式：{self.calc_mode_var.get()}\n")
                    f.write(f"\n计算结果：\n")
                    f.write(f"DPS：{self.dps_result_var.get()}\n")
                    f.write(f"DPH：{self.dph_result_var.get()}\n")
                    f.write(f"破甲线：{self.armor_break_var.get()}\n")
                
                messagebox.showinfo("成功", f"结果已导出到：{file_path}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")

    def export_multi_results(self):
        """导出多干员对比结果"""
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile="多干员对比结果.csv"
            )
            
            if file_path:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # 写入标题行
                    headers = ['指标'] + list(self.multi_comparison_results.keys())
                    writer.writerow(headers)
                    
                    # 写入数据行
                    metrics = [
                        ('干员名称', 'name'),
                        ('职业类型', 'class_type'),
                        ('攻击类型', 'atk_type'),
                        ('DPS', 'dps'),
                        ('DPH', 'dph'),
                        ('性价比', 'cost_efficiency')
                    ]
                    
                    for metric_name, metric_key in metrics:
                        row = [metric_name]
                        for operator_result in self.multi_comparison_results.values():
                            value = operator_result.get(metric_key, 'N/A')
                            row.append(self.format_display_value(value, metric_key))
                        writer.writerow(row)
                
                messagebox.showinfo("成功", f"对比结果已导出到：{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def update_status(self, message):
        """更新状态栏"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(f"状态: {message}")
    
    def save_preset(self):
        """保存参数预设"""
        try:
            from tkinter import simpledialog
            preset_name = simpledialog.askstring("保存预设", "请输入预设名称：")
            if not preset_name:
                return
            
            # 获取当前所有参数
            preset_data = {
                'enemy_def': self.enemy_def_var.get(),
                'enemy_mdef': self.enemy_mdef_var.get(),
                'time_range': self.time_range_var.get(),
                'calc_mode': self.calc_mode_var.get(),
                'precision': self.precision_var.get(),
                'auto_update': self.auto_update_var.get(),
                'skill_duration': self.skill_duration_var.get(),
                'skill_multiplier': self.skill_multiplier_var.get(),
                'skill_cooldown': self.skill_cooldown_var.get(),
                'skill_trigger_mode': self.skill_trigger_mode_var.get(),
                'skill_charges': self.skill_charges_var.get(),
                'skill_sp_cost': self.skill_sp_cost_var.get(),
                'atk_bonus': self.atk_bonus_var.get(),
                'aspd_bonus': self.aspd_bonus_var.get()
            }
            
            # 保存到文件
            import json
            preset_file = f"presets/{preset_name}.json"
            os.makedirs("presets", exist_ok=True)
            
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("成功", f"预设'{preset_name}'已保存")
            self.update_status(f"预设'{preset_name}'已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存预设失败：{str(e)}")
    
    def load_preset(self):
        """加载参数预设"""
        try:
            # 列出所有预设文件
            if not os.path.exists("presets"):
                messagebox.showwarning("警告", "没有找到预设文件")
                return
            
            preset_files = [f.replace('.json', '') for f in os.listdir("presets") if f.endswith('.json')]
            
            if not preset_files:
                messagebox.showwarning("警告", "没有可用的预设")
                return
            
            # 让用户选择预设
            import tkinter as tk
            
            dialog = tk.Toplevel(self.parent)
            dialog.title("选择预设")
            dialog.geometry("300x200")
            dialog.resizable(False, False)
            
            # 居中显示
            dialog.transient(self.parent)
            dialog.grab_set()
            
            ttk.Label(dialog, text="选择要加载的预设：", font=("微软雅黑", 10)).pack(pady=10)
            
            preset_var = StringVar()
            preset_combo = ttk.Combobox(dialog, textvariable=preset_var, values=preset_files, state="readonly")
            preset_combo.pack(pady=10, padx=20, fill=X)
            preset_combo.set(preset_files[0] if preset_files else "")
            
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=20)
            
            def load_selected():
                selected = preset_var.get()
                if selected:
                    try:
                        import json
                        preset_file = f"presets/{selected}.json"
                        
                        with open(preset_file, 'r', encoding='utf-8') as f:
                            preset_data = json.load(f)
                        
                        # 加载参数
                        self.enemy_def_var.set(preset_data.get('enemy_def', 0))
                        self.enemy_mdef_var.set(preset_data.get('enemy_mdef', 0))
                        self.time_range_var.set(preset_data.get('time_range', 90))
                        self.calc_mode_var.set(preset_data.get('calc_mode', 'basic_damage'))
                        self.precision_var.set(preset_data.get('precision', 'normal'))
                        self.auto_update_var.set(preset_data.get('auto_update', True))
                                    
                        # 技能参数
                        self.skill_duration_var.set(preset_data.get('skill_duration', 10))
                        self.skill_multiplier_var.set(preset_data.get('skill_multiplier', 150))
                        self.skill_cooldown_var.set(preset_data.get('skill_cooldown', 30))
                        self.skill_trigger_mode_var.set(preset_data.get('skill_trigger_mode', 'manual'))
                        self.skill_charges_var.set(preset_data.get('skill_charges', 1))
                        self.skill_sp_cost_var.set(preset_data.get('skill_sp_cost', 30))
                        self.atk_bonus_var.set(preset_data.get('atk_bonus', 0))
                        self.aspd_bonus_var.set(preset_data.get('aspd_bonus', 0))
            
                        dialog.destroy()
                        messagebox.showinfo("成功", f"预设'{selected}'已加载")
                        self.update_status(f"预设'{selected}'已加载")
            
                        # 如果开启自动更新，重新计算
                        if self.auto_update_var.get():
                            self.calculate_now()
            
                    except Exception as e:
                        messagebox.showerror("错误", f"加载预设失败：{str(e)}")
            
            ttk.Button(button_frame, text="加载", command=load_selected).pack(side=LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载预设失败：{str(e)}")
    
    def get_skill_parameters(self) -> Dict[str, Any]:
        """获取技能参数"""
        return {
            'duration': self.skill_duration_var.get(),
            'multiplier': self.skill_multiplier_var.get() / 100.0,  # 转换为小数
            'cooldown': self.skill_cooldown_var.get(),
            'trigger_mode': self.skill_trigger_mode_var.get(),
            'charges': self.skill_charges_var.get(),
            'sp_cost': self.skill_sp_cost_var.get(),
            'atk_bonus': self.atk_bonus_var.get(),
            'aspd_bonus': self.aspd_bonus_var.get() / 100.0  # 转换为小数
        }
    
    def validate_skill_parameters(self) -> bool:
        """验证技能参数的有效性"""
        try:
            # 检查基础参数范围
            if not (1 <= self.skill_duration_var.get() <= 60):
                messagebox.showerror("参数错误", "技能持续时间必须在1-60秒之间")
                return False
            
            if not (100 <= self.skill_multiplier_var.get() <= 800):
                messagebox.showerror("参数错误", "伤害倍率必须在100%-800%之间")
                return False
            
            if not (5 <= self.skill_cooldown_var.get() <= 180):
                messagebox.showerror("参数错误", "回转时间必须在5-180秒之间")
                return False
            
            # 检查逻辑合理性
            if self.skill_duration_var.get() > self.skill_cooldown_var.get():
                result = messagebox.askyesno("参数警告", 
                    "技能持续时间大于回转时间，这在现实中不太可能。是否继续？")
                if not result:
                    return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("验证错误", f"参数验证失败：{str(e)}")
            return False
    
    def reset_skill_parameters(self):
        """重置技能参数"""
        self.skill_duration_var.set(10)
        self.skill_multiplier_var.set(150)
        self.skill_cooldown_var.set(30)
        self.skill_trigger_mode_var.set("manual")
        self.skill_charges_var.set(1)
        self.skill_sp_cost_var.set(30)
        self.atk_bonus_var.set(0)
        self.aspd_bonus_var.set(0)
        
        if self.auto_update_var.get() and self.current_operator:
            self.calculate_now()
    
    def get_calculation_complexity(self) -> str:
        """获取当前计算复杂度"""
        mode = self.calc_mode_var.get()
        precision = self.precision_var.get()
        
        if mode == "basic_damage":
            complexity = "简单"
        elif mode == "timeline_damage":
            complexity = "中等"
        elif mode == "skill_cycle":
            complexity = "复杂"
        else:
            complexity = "未知"
        
        if precision == "precise":
            complexity += "·精确"
        elif precision == "fast":
            complexity += "·快速"
        
        return complexity
    
    def update_ui_for_operator_class(self, class_type: str):
        """根据干员职业更新UI显示"""
        if class_type == "医疗":
            # 医疗干员特殊处理
            self.skill_multiplier_scale.configure(to=300)  # 医疗干员倍率较低
            # 可以添加更多医疗干员特定的UI调整
        elif class_type in ["先锋", "重装"]:
            # 坦克类干员
            self.skill_duration_scale.configure(to=90)  # 可能有长时间技能
        elif class_type in ["狙击", "术师"]:
            # 输出类干员
            self.skill_multiplier_scale.configure(to=800)  # 高倍率技能
        else:
            # 默认设置
            self.skill_multiplier_scale.configure(to=500)
            self.skill_duration_scale.configure(to=60)
    
    def export_current_parameters(self) -> Dict[str, Any]:
        """导出当前参数配置"""
        return {
            'calculation_parameters': {
                'enemy_def': self.enemy_def_var.get(),
                'enemy_mdef': self.enemy_mdef_var.get(),
                'time_range': self.time_range_var.get(),
                'calc_mode': self.calc_mode_var.get(),
                'precision': self.precision_var.get(),
                'auto_update': self.auto_update_var.get()
            },
            'skill_parameters': self.get_skill_parameters(),
            'operator_info': {
                'name': self.current_operator['name'] if self.current_operator else None,
                'class_type': self.current_operator['class_type'] if self.current_operator else None
            },
            'export_timestamp': datetime.now().isoformat(),
            'calculation_complexity': self.get_calculation_complexity()
        }
    
    def refresh_statistics_display(self):
        """刷新统计显示"""
        try:
            # 通过parent获取主窗口，而不是使用self.winfo_toplevel()
            parent_window = self.parent
            # 向上查找到顶级窗口
            while hasattr(parent_window, 'master') and parent_window.master:
                parent_window = parent_window.master
            
            # 尝试刷新父窗口的统计显示
            if hasattr(parent_window, 'panels'):
                if 'sidebar' in parent_window.panels:
                    parent_window.panels['sidebar'].refresh_stats()
                if 'overview' in parent_window.panels:
                    parent_window.panels['overview'].refresh_data()
            # 如果没有panels属性，尝试直接查找sidebar_panel属性
            elif hasattr(parent_window, 'sidebar_panel'):
                parent_window.sidebar_panel.refresh_data()
        except Exception as e:
            print(f"刷新统计显示失败: {e}") 
    
    def calculate_now(self):
        """立即计算 - 支持单选和多选模式"""
        mode = self.analysis_mode.get()
        
        if mode == "single":
            # 单干员计算
            if not self.current_operator:
                self.update_status("请先选择干员")
                return
            
            try:
                enemy_def = self.enemy_def_var.get()
                enemy_mdef = self.enemy_mdef_var.get()
                time_range = self.time_range_var.get()
                calc_mode = self.calc_mode_var.get()
                
                # 根据计算模式执行不同的计算
                if calc_mode == "basic_damage":
                    results = self.calculate_basic_damage(enemy_def, enemy_mdef)
                elif calc_mode == "timeline_damage":
                    results = self.calculate_timeline_damage(enemy_def, enemy_mdef, time_range)
                elif calc_mode == "skill_cycle":
                    results = self.calculate_skill_cycle(enemy_def, enemy_mdef, time_range)
                else:
                    results = self.calculate_basic_damage(enemy_def, enemy_mdef)
                
                # 更新结果显示
                self.update_result_display(results, calc_mode)
                self.update_detail_results(results, enemy_def, enemy_mdef, time_range, calc_mode)
                
                # 记录关键计算数据到数据库
                try:
                    # 准备关键参数
                    key_parameters = {
                        'calc_mode': calc_mode,
                        'enemy_def': enemy_def,
                        'enemy_mdef': enemy_mdef,
                        'operator_class': self.current_operator.get('class_type', ''),
                        'attack_type': results.get('atk_type', self.determine_attack_type(self.current_operator))
                    }
                    
                    # 添加模式特定参数
                    if calc_mode in ['timeline_damage', 'skill_cycle']:
                        key_parameters['time_range'] = time_range
                    
                    if calc_mode == 'skill_cycle':
                        key_parameters['skill_duration'] = self.skill_duration_var.get()
                        key_parameters['skill_multiplier'] = self.skill_multiplier_var.get()
                    
                    # 准备关键结果
                    key_results = {}
                    if results.get('type') == 'damage':
                        key_results = {
                            'dps': round(results.get('dps', 0), 2),
                            'dph': round(results.get('dph', 0), 2),
                            'armor_break': results.get('armor_break', 0)
                        }
                        if calc_mode == 'timeline_damage' and 'total_damage' in results:
                            key_results['total_damage'] = round(results['total_damage'], 0)
                    elif results.get('type') == 'healing':
                        key_results = {
                            'hps': round(results.get('hps', 0), 2),
                            'hph': round(results.get('hph', 0), 2)
                        }
                    
                    # 保存计算记录
                    calculation_type = f"单干员_{calc_mode}"
                    operator_id = self.current_operator.get('id')
                    
                    self.db_manager.record_calculation(
                        operator_id=operator_id,
                        calculation_type=calculation_type,
                        parameters=key_parameters,
                        results=key_results
                    )
                    
                    # 通知界面刷新统计数据
                    self.refresh_statistics_display()
                    
                    # 推送实时活动记录
                    operator_name = self.current_operator.get('name', '未知干员')
                    self.push_activity_record(f"计算了{operator_name}的{self._get_calc_mode_display_name(calc_mode)}")
                    
                except Exception as record_error:
                    # 记录失败不影响主要功能，只输出日志
                    logger = logging.getLogger(__name__)
                    logger.error(f"保存计算记录失败: {record_error}")
                
                self.update_status("单干员计算完成")
                
            except Exception as e:
                self.update_status(f"单干员计算失败: {str(e)}")
        
        elif mode == "multi":
            # 多干员对比计算
            try:
                results = self.calculate_multi_operators()
                if results:
                    # 记录多干员对比计算
                    try:
                        # 准备完整的计算结果表格数据
                        detailed_results = []
                        for operator_name, operator_result in results.items():
                            detailed_row = {
                                '干员名称': operator_result.get('name', operator_name),
                                '职业类型': operator_result.get('class_type', 'N/A'),
                                '攻击类型': operator_result.get('atk_type', 'N/A'),
                                '攻击力': operator_result.get('atk', 0),
                                '攻击速度': operator_result.get('atk_speed', 0),
                                '生命值': operator_result.get('hp', 0),
                                '部署费用': operator_result.get('cost', 0),
                                'DPS': operator_result.get('dps', 0),
                                'DPH': operator_result.get('dph', 0),
                                '破甲线': operator_result.get('armor_break', 0),
                                '性价比': operator_result.get('cost_efficiency', 0)
                            }
                            detailed_results.append(detailed_row)
                        
                        # 准备计算参数
                        calculation_parameters = {
                            'calc_mode': self.calc_mode_var.get(),
                            'enemy_def': self.enemy_def_var.get(),
                            'enemy_mdef': self.enemy_mdef_var.get(),
                            'time_range': self.time_range_var.get(),
                            'operator_count': len(results),
                            'operator_names': list(results.keys()),
                            'calc_mode_display': self._get_calc_mode_display_name(self.calc_mode_var.get())
                        }
                        
                        # 准备汇总结果
                        dps_values = [r.get('dps', 0) for r in results.values() if r.get('dps', 0) > 0]
                        efficiency_values = [r.get('cost_efficiency', 0) for r in results.values() if r.get('cost_efficiency', 0) > 0]
                        
                        summary_results = {
                            'detailed_table': detailed_results,  # 完整的表格数据
                            'max_dps': round(max(dps_values), 2) if dps_values else 0,
                            'avg_dps': round(sum(dps_values) / len(dps_values), 2) if dps_values else 0,
                            'max_efficiency': round(max(efficiency_values), 2) if efficiency_values else 0,
                            'operators_analyzed': len(results)
                        }
                        
                        # 保存完整的计算记录（包括详细表格数据）
                        self.db_manager.record_calculation(
                            operator_id=None,  # 多干员对比没有单一干员ID
                            calculation_type=f"多干员对比_{self.calc_mode_var.get()}",
                            parameters=calculation_parameters,
                            results=summary_results
                        )
                        
                        # 通知界面刷新统计数据
                        self.refresh_statistics_display()
                        
                        # 推送实时活动记录
                        self.push_activity_record(f"对比了{len(results)}个干员的{self._get_calc_mode_display_name(self.calc_mode_var.get())}")
                        
                    except Exception as record_error:
                        logger = logging.getLogger(__name__)
                        logger.error(f"保存多干员计算记录失败: {record_error}")
                    
                    self.update_status(f"多干员对比完成，共对比 {len(results)} 个干员")
                else:
                    self.update_status("多干员对比失败，请检查选择的干员")
            except Exception as e:
                self.update_status(f"多干员对比失败: {str(e)}")
    
    def _get_calc_mode_display_name(self, calc_mode):
        """获取计算模式的显示名称"""
        mode_names = {
            'basic_damage': '基础伤害',
            'timeline_damage': '时间轴伤害', 
            'skill_cycle': '技能循环伤害'
        }
        return mode_names.get(calc_mode, calc_mode)
    
    def push_activity_record(self, activity_description):
        """推送实时活动记录到概览面板"""
        try:
            # 通过parent查找主窗口，然后通知概览面板更新
            parent_window = self.parent
            while hasattr(parent_window, 'master') and parent_window.master:
                parent_window = parent_window.master
            
            # 尝试找到概览面板并推送活动记录
            if hasattr(parent_window, 'panels') and 'overview' in parent_window.panels:
                overview_panel = parent_window.panels['overview']
                if hasattr(overview_panel, 'push_real_time_activity'):
                    overview_panel.push_real_time_activity(activity_description)
                elif hasattr(overview_panel, 'update_activity_timeline'):
                    # 如果没有实时推送方法，强制刷新活动时间线
                    overview_panel.update_activity_timeline()
                    
        except Exception as e:
            # 推送失败不影响主要功能
            pass
    
    def create_multi_operator_interface(self, parent):
        """创建多干员选择界面"""
        # 搜索和过滤区域
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=X, pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索干员：").pack(side=LEFT)
        self.search_var = StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=15)
        search_entry.pack(side=LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 职业过滤
        ttk.Label(search_frame, text="职业过滤：").pack(side=LEFT)
        self.class_filter_var = StringVar(value="全部")
        class_combo = ttk.Combobox(search_frame, textvariable=self.class_filter_var, 
                                  values=["全部", "先锋", "近卫", "重装", "狙击", "术师", "辅助", "医疗", "特种"],
                                  state="readonly", width=8)
        class_combo.pack(side=LEFT, padx=(5, 10))
        class_combo.bind('<<ComboboxSelected>>', self.on_class_filter_changed)
        
        # 伤害类型过滤
        ttk.Label(search_frame, text="伤害类型：").pack(side=LEFT)
        self.damage_type_filter_var = StringVar(value="全部")
        damage_type_combo = ttk.Combobox(search_frame, textvariable=self.damage_type_filter_var,
                                       values=["全部", "物伤", "法伤"], state="readonly", width=8)
        damage_type_combo.pack(side=LEFT, padx=(5, 0))
        damage_type_combo.bind('<<ComboboxSelected>>', self.on_damage_type_filter_changed)
        
        # 左右分栏布局
        paned = ttk.PanedWindow(parent, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        # 左侧：可选干员列表
        left_frame = ttk.LabelFrame(paned, text="可选干员", padding=5)
        paned.add(left_frame, weight=1)
        
        # 可选干员列表框
        import tkinter as tk
        self.available_listbox = tk.Listbox(left_frame, selectmode=tk.EXTENDED, height=12)
        available_scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.available_listbox.yview)
        self.available_listbox.configure(yscrollcommand=available_scrollbar.set)
        
        self.available_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        available_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 双击添加绑定
        self.available_listbox.bind('<Double-1>', self.on_available_double_click)
        
        # 中间：操作按钮
        button_frame = ttk.Frame(paned)
        paned.add(button_frame, weight=0)
        
        # 添加按钮
        ttk.Button(button_frame, text="添加 →", command=self.add_selected_operators).pack(pady=5, fill=X)
        ttk.Button(button_frame, text="← 移除", command=self.remove_selected_operators).pack(pady=5, fill=X)
        ttk.Button(button_frame, text="全部添加", command=self.add_all_operators).pack(pady=5, fill=X)
        ttk.Button(button_frame, text="全部移除", command=self.clear_selected_operators).pack(pady=5, fill=X)
        
        # 右侧：已选干员列表
        right_frame = ttk.LabelFrame(paned, text="已选干员 (0)", padding=5)
        paned.add(right_frame, weight=1)
        
        # 已选干员列表框
        self.selected_listbox = tk.Listbox(right_frame, selectmode=tk.EXTENDED, height=12)
        selected_scrollbar = ttk.Scrollbar(right_frame, orient=VERTICAL, command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        
        self.selected_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        selected_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 双击移除绑定
        self.selected_listbox.bind('<Double-1>', self.on_selected_double_click)
        
        # 记录已选框架用于更新标题
        self.selected_frame = right_frame
    
    def refresh_available_operators(self):
        """刷新可选干员列表"""
        try:
            operators = self.db_manager.get_all_operators()
            self.available_operators = operators
            self.filter_available_operators()
        except Exception as e:
            self.update_status(f"刷新干员列表失败: {str(e)}")
    
    def filter_available_operators(self):
        """根据搜索和过滤条件筛选可选干员"""
        if not hasattr(self, 'available_operators'):
            return
        
        # 清空列表
        import tkinter as tk
        self.available_listbox.delete(0, tk.END)
        
        search_text = self.search_var.get().lower()
        class_filter = self.class_filter_var.get()
        damage_type_filter = self.damage_type_filter_var.get()
        
        for operator in self.available_operators:
            # 检查是否已选择
            if operator in self.selected_operators_list:
                continue
            
            # 搜索过滤
            if search_text and search_text not in operator['name'].lower():
                continue
            
            # 职业过滤
            if class_filter != "全部" and operator['class_type'] != class_filter:
                continue
            
            # 伤害类型过滤 - 修复：支持格式转换
            if damage_type_filter != "全部":
                operator_damage_type = self.determine_attack_type(operator)
                
                # 将数据库格式转换为下拉框格式进行比较
                if operator_damage_type in ['物伤', '物理伤害']:
                    operator_filter_type = '物伤'
                elif operator_damage_type in ['法伤', '法术伤害']:
                    operator_filter_type = '法伤'
                else:
                    operator_filter_type = '物伤'  # 默认为物伤
                
                if operator_filter_type != damage_type_filter:
                    continue
            
            # 添加到列表
            display_text = f"{operator['name']} ({operator['class_type']})"
            self.available_listbox.insert(tk.END, display_text)
    
    def on_search_changed(self, event=None):
        """搜索条件变化"""
        self.filter_available_operators()
    
    def on_class_filter_changed(self, event=None):
        """职业过滤变化"""
        self.filter_available_operators()
    
    def on_damage_type_filter_changed(self, event=None):
        """伤害类型过滤变化"""
        self.filter_available_operators()
    
    def on_available_double_click(self, event):
        """双击可选干员列表"""
        selection = self.available_listbox.curselection()
        if selection:
            self.add_selected_operators()
    
    def on_selected_double_click(self, event):
        """双击已选干员列表"""
        selection = self.selected_listbox.curselection()
        if selection:
            self.remove_selected_operators()
    
    def add_selected_operators(self):
        """添加选中的干员到对比列表"""
        selections = self.available_listbox.curselection()
        if not selections:
            return
        
        for index in reversed(selections):  # 从后往前删除，避免索引变化
            item_text = self.available_listbox.get(index)
            operator_name = item_text.split(' (')[0]
            
            # 查找对应的干员对象
            for operator in self.available_operators:
                if operator['name'] == operator_name and operator not in self.selected_operators_list:
                    self.selected_operators_list.append(operator)
                    break
        
        self.update_selected_list_display()
        self.filter_available_operators()
    
    def remove_selected_operators(self):
        """从对比列表中移除选中的干员"""
        selections = self.selected_listbox.curselection()
        if not selections:
            return
        
        # 获取要移除的干员名称
        operators_to_remove = []
        for index in selections:
            item_text = self.selected_listbox.get(index)
            operator_name = item_text.split(' (')[0]
            operators_to_remove.append(operator_name)
        
        # 从列表中移除
        self.selected_operators_list = [op for op in self.selected_operators_list 
                                       if op['name'] not in operators_to_remove]
        
        self.update_selected_list_display()
        self.filter_available_operators()
    
    def add_all_operators(self):
        """添加所有可见的干员"""
        for i in range(self.available_listbox.size()):
            item_text = self.available_listbox.get(i)
            operator_name = item_text.split(' (')[0]
            
            # 查找对应的干员对象
            for operator in self.available_operators:
                if operator['name'] == operator_name and operator not in self.selected_operators_list:
                    self.selected_operators_list.append(operator)
                    break
        
        self.update_selected_list_display()
        self.filter_available_operators()
    
    def clear_selected_operators(self):
        """清空已选干员列表"""
        self.selected_operators_list.clear()
        self.update_selected_list_display()
        self.filter_available_operators()
    
    def update_selected_list_display(self):
        """更新已选干员列表显示"""
        # 清空列表
        import tkinter as tk
        self.selected_listbox.delete(0, tk.END)
        
        # 添加已选干员
        for operator in self.selected_operators_list:
            display_text = f"{operator['name']} ({operator['class_type']})"
            self.selected_listbox.insert(tk.END, display_text)
        
        # 更新标题
        count = len(self.selected_operators_list)
        self.selected_frame.configure(text=f"已选干员 ({count})")
        
        # 如果开启自动更新且有已选干员，自动计算
        if self.auto_update_var.get() and self.selected_operators_list:
            self.calculate_now()