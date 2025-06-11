# operator_editor.py - 干员属性编辑界面

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, StringVar, BooleanVar
import sys
import os
from typing import Dict, Optional, Callable, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.damage_calculator import calculator
from ui.invisible_scroll_frame import InvisibleScrollFrame
from ui.components.sortable_treeview import SortableTreeview

class OperatorEditor:
    """干员属性编辑界面"""
    
    def __init__(self, parent, db_manager, status_callback: Optional[Callable] = None):
        self.parent = parent
        self.db_manager = db_manager
        self.status_callback = status_callback
        
        # 数据变量
        self.operator_vars = {}
        self.operator_inputs = {}
        self.current_operator_id = None
        self.is_editing = False
        
        # 搜索和筛选变量
        self.search_var = StringVar()
        self.selected_classes = set(['先锋', '近卫', '重装', '狙击', '术师', '辅助', '医疗', '特种'])  # 默认全选
        self.damage_type_filter_var = StringVar(value="全部")
        self.all_operators = []
        self.filtered_operators = []
        self.class_vars = {}  # 存储每个职业的BooleanVar
        
        # 字段分组定义
        self.field_groups = {
            '基础信息': {
                'name': '干员名称',
                'class_type': '职业类型'
            },
            '战斗属性': {
                'hp': '生命值',
                'atk': '攻击力',
                'atk_type': '攻击类型',
                'def': '防御力',
                'mdef': '法抗',
                'atk_speed': '攻击速度',
                'heal_amount': '治疗量',
                'hit_count': '打数',
                'block_count': '阻挡数'
            },
            '部署配置': {
                'cost': '部署费用'
            }
        }
        
        # 初始化变量（必须在创建界面之前）
        self.initialize_variables()
        
        # 创建界面
        self.setup_ui()
        
        # 刷新干员列表
        self.refresh_operator_list()
    
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
                    operator.get('cost', '')
                )
                self.operator_treeview.insert('', 'end', values=values)
        else:
            # 无结果时显示友好提示
            self.operator_treeview.insert('', 'end', values=(
                '', '未找到符合条件的干员', '', '', '', '', ''
            ))
    
    def on_search_changed(self, event=None):
        """搜索条件变化"""
        # 添加防抖动处理
        if hasattr(self, '_search_after_id'):
            self.parent.after_cancel(self._search_after_id)
        self._search_after_id = self.parent.after(300, self.filter_operators)
    
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
            
        self.filter_stats_label.config(text=stats_text)
        self.operator_count_label.config(text=f"共 {filtered} 个干员")
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右分栏
        paned_window = ttk.PanedWindow(main_frame, orient=HORIZONTAL)
        paned_window.pack(fill=BOTH, expand=True)
        
        # 左侧：干员列表
        list_frame = ttk.LabelFrame(paned_window, text="干员列表", padding=10)
        paned_window.add(list_frame, weight=1)
        
        # 右侧：编辑表单
        edit_frame = ttk.LabelFrame(paned_window, text="属性编辑", padding=10)
        paned_window.add(edit_frame, weight=2)
        
        self.setup_operator_list(list_frame)
        self.setup_edit_form(edit_frame)
    
    def setup_operator_list(self, parent):
        """设置干员列表"""
        # 工具栏 - 只保留基本操作按钮
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=X, pady=(0, 10))
        
        # 基本操作按钮
        basic_row = ttk.Frame(toolbar_frame)
        basic_row.pack(fill=X, pady=2)
        
        ttk.Button(basic_row, text="🔄 刷新", bootstyle=INFO,
                  command=self.refresh_operator_list).pack(side=LEFT, padx=2)
        ttk.Button(basic_row, text="➕ 新建", bootstyle=SUCCESS,
                  command=self.new_operator).pack(side=LEFT, padx=2)
        ttk.Button(basic_row, text="🗑️ 删除", bootstyle=DANGER,
                  command=self.delete_selected_operator).pack(side=LEFT, padx=2)
        ttk.Button(basic_row, text="🗑️ 清空所有", bootstyle=DANGER,
                  command=self.delete_all_operators_ui).pack(side=LEFT, padx=2)
        
        # 操作提示和统计信息
        ttk.Label(basic_row, text="💡 双击干员进行编辑", 
                 font=("微软雅黑", 8), foreground="gray").pack(side=RIGHT, padx=(10, 0))
        
        self.operator_count_label = ttk.Label(basic_row, text="", 
                                            font=("微软雅黑", 8), foreground="blue")
        self.operator_count_label.pack(side=RIGHT)
        
        # 创建搜索筛选区域
        self.create_search_filter_area(parent)
        
        # 干员表格
        list_container = ttk.Frame(parent)
        list_container.pack(fill=BOTH, expand=True)
        
        # 定义表格列
        columns = ('id', 'name', 'class_type', 'hp', 'atk', 'def', 'cost')
        self.operator_treeview = SortableTreeview(list_container, columns=columns, show='tree headings', height=15)
        
        # 设置列标题和宽度
        self.operator_treeview.heading('#0', text='', anchor='w')
        self.operator_treeview.column('#0', width=0, stretch=False)  # 隐藏第一列
        
        self.operator_treeview.heading('id', text='ID', anchor='center')
        self.operator_treeview.column('id', width=50, anchor='center')
        
        self.operator_treeview.heading('name', text='名称', anchor='w')
        self.operator_treeview.column('name', width=120, anchor='w')
        
        self.operator_treeview.heading('class_type', text='职业', anchor='center')
        self.operator_treeview.column('class_type', width=80, anchor='center')
        
        self.operator_treeview.heading('hp', text='生命值', anchor='center')
        self.operator_treeview.column('hp', width=80, anchor='center')
        
        self.operator_treeview.heading('atk', text='攻击力', anchor='center')
        self.operator_treeview.column('atk', width=80, anchor='center')
        
        self.operator_treeview.heading('def', text='防御力', anchor='center')
        self.operator_treeview.column('def', width=80, anchor='center')
        
        self.operator_treeview.heading('cost', text='费用', anchor='center')
        self.operator_treeview.column('cost', width=60, anchor='center')
        
        # 启用所有列的排序功能
        self.operator_treeview.enable_sorting()
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(list_container, orient=VERTICAL, command=self.operator_treeview.yview)
        self.operator_treeview.configure(yscrollcommand=tree_scrollbar.set)
        
        self.operator_treeview.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定选择事件
        self.operator_treeview.bind('<<TreeviewSelect>>', self.on_operator_selected)
        # 双击进入编辑模式
        self.operator_treeview.bind('<Double-Button-1>', lambda e: self.edit_selected_operator())
        
        # 添加右键菜单
        self.create_context_menu()
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.operator_treeview, tearoff=0)
        self.context_menu.add_command(label="📝 编辑", command=self.edit_selected_operator)
        self.context_menu.add_command(label="📋 复制", command=self.copy_selected_operator)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ 删除", command=self.delete_selected_operator)
        
        # 绑定右键菜单
        def show_context_menu(event):
            try:
                # 选中右键点击的项目
                item = self.operator_treeview.identify_row(event.y)
                if item:
                    self.operator_treeview.selection_set(item)
                    self.operator_treeview.focus(item)
                    
                    # 显示菜单
                    self.context_menu.post(event.x_root, event.y_root)
            except:
                pass
        
        self.operator_treeview.bind('<Button-3>', show_context_menu)
    
    def create_search_filter_area(self, parent):
        """创建搜索和筛选区域"""
        # 搜索筛选容器
        filter_frame = ttk.LabelFrame(parent, text="搜索与筛选", padding=10)
        filter_frame.pack(fill=X, pady=(10, 10))
        
        # 第一行：搜索框
        search_row = ttk.Frame(filter_frame)
        search_row.pack(fill=X, pady=(0, 8))
        
        ttk.Label(search_row, text="搜索干员：").pack(side=LEFT)
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=20)
        search_entry.pack(side=LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 添加搜索提示
        ttk.Label(search_row, text="(输入干员名称)", 
                 font=("微软雅黑", 8), foreground="gray").pack(side=LEFT, padx=(5, 0))
        
        # 搜索按钮
        ttk.Button(search_row, text="🔍", width=3, 
                  command=self.filter_operators).pack(side=LEFT, padx=2)
        
        # 第二行：职业多选
        class_row = ttk.Frame(filter_frame)  
        class_row.pack(fill=X, pady=(0, 8))
        self.create_class_filter_area(class_row)
        
        # 第三行：伤害类型和统计信息
        info_row = ttk.Frame(filter_frame)
        info_row.pack(fill=X)
        
        # 伤害类型过滤
        ttk.Label(info_row, text="伤害类型：").pack(side=LEFT)
        damage_type_combo = ttk.Combobox(info_row, textvariable=self.damage_type_filter_var,
                                         values=["全部", "物伤", "法伤"], state="readonly", width=8,
                                         style="Apple.TCombobox")
        damage_type_combo.pack(side=LEFT, padx=(5, 20))
        damage_type_combo.bind('<<ComboboxSelected>>', self.on_damage_type_filter_changed)
        
        # 筛选结果统计
        self.filter_stats_label = ttk.Label(info_row, text="", 
                                          font=("微软雅黑", 8), foreground="blue")
        self.filter_stats_label.pack(side=LEFT, padx=(0, 20))
        
        # 重置按钮
        ttk.Button(info_row, text="重置筛选", bootstyle="outline-secondary",
                  command=self.reset_filters).pack(side=RIGHT)
    
    def create_class_filter_area(self, parent):
        """创建职业多选复选框"""
        ttk.Label(parent, text="职业筛选：").pack(side=LEFT)
        
        classes = ['先锋', '近卫', '重装', '狙击', '术师', '辅助', '医疗', '特种']
        
        # 全选控制（变量已在initialize_variables中初始化）
        select_all_cb = ttk.Checkbutton(parent, text="全选", variable=self.select_all_var,
                                       command=self.toggle_select_all)
        select_all_cb.pack(side=LEFT, padx=(5, 10))
        
        # 各职业复选框（变量已在initialize_variables中初始化）
        for class_name in classes:
            cb = ttk.Checkbutton(parent, text=class_name, variable=self.class_vars[class_name],
                               command=self.on_class_selection_changed)
            cb.pack(side=LEFT, padx=2)
    
    def setup_edit_form(self, parent):
        """设置编辑表单"""
        # 简化表单工具栏
        form_toolbar = ttk.Frame(parent)
        form_toolbar.pack(fill=X, pady=(0, 10))
        
        # 左侧：保存和取消按钮
        save_frame = ttk.Frame(form_toolbar)
        save_frame.pack(side=LEFT)
        
        ttk.Button(save_frame, text="💾 保存", bootstyle=SUCCESS,
                  command=self.save_operator).pack(side=LEFT, padx=2)
        ttk.Button(save_frame, text="❌ 取消", bootstyle=SECONDARY,
                  command=self.cancel_edit).pack(side=LEFT, padx=2)
        
        # 中间：辅助功能
        aux_frame = ttk.Frame(form_toolbar)
        aux_frame.pack(side=LEFT, padx=(20, 0))
        
        ttk.Button(aux_frame, text="🔄 重置", bootstyle=WARNING,
                  command=self.reset_form).pack(side=LEFT, padx=2)
        ttk.Button(aux_frame, text="📊 预览", bootstyle=INFO,
                  command=self.show_live_preview).pack(side=LEFT, padx=2)
        
        # 右侧：编辑状态指示
        self.edit_status_frame = ttk.Frame(form_toolbar)
        self.edit_status_frame.pack(side=RIGHT)
        
        self.edit_status_label = ttk.Label(self.edit_status_frame, text="查看模式", 
                                          font=("微软雅黑", 9), foreground="blue")
        self.edit_status_label.pack(side=RIGHT)
        
        # 滚动框架
        self.create_scrollable_form(parent)
    
    def create_scrollable_form(self, parent):
        """创建可滚动的表单 - 使用隐形滚动框架"""
        # 使用隐形滚动框架替代Canvas+Scrollbar
        self.scroll_frame = InvisibleScrollFrame(parent, scroll_speed=4)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        
        # 获取滚动容器中的frame
        self.scrollable_frame = self.scroll_frame.scrollable_frame
        
        # 创建表单字段
        self.create_form_fields()
    
    def create_form_fields(self):
        """创建表单字段"""
        current_row = 0
        
        for group_name, fields in self.field_groups.items():
            # 创建分组框
            group_frame = ttk.LabelFrame(self.scrollable_frame, text=group_name, padding=10)
            group_frame.grid(row=current_row, column=0, columnspan=2, sticky='ew', pady=10, padx=5)
            
            field_row = 0
            for key, label in fields.items():
                # 创建标签
                ttk.Label(group_frame, text=label).grid(row=field_row, column=0, sticky='e', pady=5, padx=(0, 10))
                
                # 创建输入控件
                if key == 'class_type':
                    widget = ttk.Combobox(group_frame, textvariable=self.operator_vars[key],
                                        values=['先锋', '近卫', '重装', '狙击', '术师', '医疗', '辅助', '特种'],
                                        width=24, state='readonly')
                    widget.bind('<<ComboboxSelected>>', self.on_class_type_changed)
                    
                elif key == 'atk_type':
                    widget = ttk.Combobox(group_frame, textvariable=self.operator_vars[key],
                                        values=['物伤', '法伤'], width=24, state='readonly')
                    
                elif key == 'heal_amount':
                    widget = ttk.Entry(group_frame, textvariable=self.operator_vars[key], width=24)
                    # 初始状态根据职业类型决定
                    if self.operator_vars['class_type'].get() != '医疗':
                        widget.configure(state='disabled')
                    
                elif key == 'hit_count':
                    widget = ttk.Entry(group_frame, textvariable=self.operator_vars[key], width=24)
                    # 绑定验证事件
                    self.operator_vars[key].trace_add("write", self.validate_hit_count)
                    
                else:
                    widget = ttk.Entry(group_frame, textvariable=self.operator_vars[key], width=24)
                
                widget.grid(row=field_row, column=1, pady=5, sticky='w')
                self.operator_inputs[key] = widget
                
                field_row += 1
            
            current_row += 1
        
        # 配置列权重
        self.scrollable_frame.columnconfigure(0, weight=1)
        for i in range(len(self.field_groups)):
            self.scrollable_frame.grid_rowconfigure(i, weight=0)
    
    def initialize_variables(self):
        """初始化变量"""
        # 为每个字段创建StringVar或IntVar
        for group_fields in self.field_groups.values():
            for key in group_fields.keys():
                if key in ['hp', 'atk', 'def', 'mdef', 'block_count', 'cost', 'heal_amount']:
                    self.operator_vars[key] = tk.IntVar()
                elif key in ['atk_speed', 'hit_count']:
                    self.operator_vars[key] = tk.DoubleVar()
                else:
                    self.operator_vars[key] = tk.StringVar()
        
        # 设置默认值
        self.operator_vars['hit_count'].set(1.0)
        self.operator_vars['class_type'].set('狙击')
        self.operator_vars['atk_type'].set('物伤')
        self.operator_vars['block_count'].set(1)
        self.operator_vars['cost'].set(10)
        
        # 初始化搜索筛选变量
        classes = ['先锋', '近卫', '重装', '狙击', '术师', '辅助', '医疗', '特种']
        for class_name in classes:
            self.class_vars[class_name] = BooleanVar(value=True)
        
        # 初始化其他筛选变量
        self.select_all_var = BooleanVar(value=True)
    
    def refresh_operator_list(self):
        """刷新干员列表"""
        try:
            # 先加载所有数据到all_operators
            self.all_operators = self.db_manager.get_all_operators()
            
            # 如果筛选变量已初始化，则应用筛选
            if hasattr(self, 'class_vars') and self.class_vars:
                self.filter_operators()
            else:
                # 首次加载，直接显示所有数据
                self.filtered_operators = self.all_operators.copy()
                self.update_operator_display()
                
                # 更新统计信息
                if hasattr(self, 'operator_count_label'):
                    id_gaps = self.db_manager.get_id_gaps()
                    if id_gaps:
                        gap_info = f" | 间隙: {len(id_gaps)}个"
                    else:
                        gap_info = " | ID连续"
                    self.operator_count_label.config(text=f"总数: {len(self.all_operators)}个{gap_info}")
            
            self.update_status(f"已加载 {len(self.all_operators)} 个干员")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新干员列表失败：{str(e)}")
            if hasattr(self, 'operator_count_label'):
                self.operator_count_label.config(text="加载失败")
    
    def on_operator_selected(self, event):
        """干员选择事件"""
        selection = self.operator_treeview.selection()
        if selection:
            item_id = selection[0]
            # 获取选中行的数据
            values = self.operator_treeview.item(item_id, 'values')
            if values:
                operator_id = int(values[0])  # 第一列是ID
                operator = self.db_manager.get_operator(operator_id)
                if operator:
                    self.load_operator_data(operator)
    
    def load_operator_data(self, operator):
        """加载干员数据到表单"""
        self.current_operator_id = operator['id']
        
        # 加载数据到变量
        for key, var in self.operator_vars.items():
            value = operator.get(key)
            if value is not None:
                if isinstance(var, (tk.IntVar, tk.DoubleVar)):
                    var.set(value)
                else:
                    var.set(str(value))
            else:
                # 设置默认值
                if key == 'hit_count':
                    var.set(1.0)
                elif key == 'heal_amount':
                    var.set(0)
                elif isinstance(var, (tk.IntVar, tk.DoubleVar)):
                    var.set(0)
                else:
                    var.set('')
        
        # 更新字段状态
        self.update_heal_amount_state()
        
        # 如果不在编辑模式，更新状态为查看模式
        if not self.is_editing:
            self.update_edit_status("查看模式", "blue")
        
        self.update_status(f"已加载干员：{operator['name']}")
    
    def new_operator(self):
        """新建干员"""
        self.current_operator_id = None
        self.is_editing = True
        
        # 清空表单
        self.reset_form()
        self.update_edit_status("新建模式", "green")
        self.update_status("创建新干员")
    
    def edit_selected_operator(self):
        """编辑选中的干员"""
        selection = self.operator_treeview.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个干员")
            return
        
        self.is_editing = True
        self.update_edit_status("编辑模式", "red")
        self.update_status("编辑模式")
    
    def copy_selected_operator(self):
        """复制选中的干员"""
        selection = self.operator_treeview.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个干员")
            return
        
        try:
            item_id = selection[0]
            values = self.operator_treeview.item(item_id, 'values')
            if values:
                operator_id = int(values[0])
                original_operator = self.db_manager.get_operator(operator_id)
                
                if original_operator:
                    # 复制数据
                    copied_data = original_operator.copy()
                    
                    # 修改名称以区分
                    original_name = copied_data['name']
                    copied_data['name'] = f"{original_name}_副本"
                    
                    # 移除ID，创建新记录
                    if 'id' in copied_data:
                        del copied_data['id']
                    
                    # 插入新干员
                    new_id = self.db_manager.insert_operator(copied_data)
                    if new_id:
                        messagebox.showinfo("成功", f"已复制干员：{original_name} -> {copied_data['name']}")
                        self.refresh_operator_list()
                        
                        # 选中新创建的干员
                        for item in self.operator_treeview.get_children():
                            values = self.operator_treeview.item(item, 'values')
                            if values and int(values[0]) == new_id:
                                self.operator_treeview.selection_set(item)
                                self.operator_treeview.focus(item)
                                operator = self.db_manager.get_operator(new_id)
                                if operator:
                                    self.load_operator_data(operator)
                                break
                        
                        self.update_status(f"已复制干员：{copied_data['name']}")
                    else:
                        messagebox.showerror("错误", "复制干员失败")
                        
        except Exception as e:
            messagebox.showerror("错误", f"复制干员失败：{str(e)}")
    
    def update_edit_status(self, status_text, color="blue"):
        """更新编辑状态指示"""
        if hasattr(self, 'edit_status_label'):
            self.edit_status_label.configure(text=status_text, foreground=color)
    
    def save_operator(self):
        """保存干员"""
        try:
            # 验证必填字段
            if not self.operator_vars['name'].get().strip():
                messagebox.showerror("错误", "干员名称不能为空")
                return
            
            # 准备数据
            operator_data = {}
            for key, var in self.operator_vars.items():
                value = var.get()
                if isinstance(var, tk.StringVar):
                    operator_data[key] = value.strip()
                else:
                    operator_data[key] = value
            
            # 特殊处理治疗量字段
            if operator_data['class_type'] != '医疗':
                operator_data['heal_amount'] = 0
            
            # 保存到数据库
            if self.current_operator_id:
                # 更新现有干员
                success = self.db_manager.update_operator(self.current_operator_id, operator_data)
                if success:
                    messagebox.showinfo("成功", "干员更新成功")
                    self.update_status(f"已更新干员：{operator_data['name']}")
                else:
                    messagebox.showerror("错误", "更新干员失败")
                    return
            else:
                # 创建新干员
                operator_id = self.db_manager.insert_operator(operator_data)
                if operator_id:
                    self.current_operator_id = operator_id
                    messagebox.showinfo("成功", "干员创建成功")
                    self.update_status(f"已创建干员：{operator_data['name']}")
                else:
                    messagebox.showerror("错误", "创建干员失败")
                    return
            
            # 刷新列表
            self.refresh_operator_list()
            self.is_editing = False
            self.update_edit_status("查看模式", "blue")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存干员失败：{str(e)}")
    
    def cancel_edit(self):
        """取消编辑"""
        self.is_editing = False
        self.update_edit_status("查看模式", "blue")
        
        if self.current_operator_id:
            # 重新加载当前干员数据
            operator = self.db_manager.get_operator(self.current_operator_id)
            if operator:
                self.load_operator_data(operator)
        else:
            self.reset_form()
        self.update_status("已取消编辑")
    
    def reset_form(self):
        """重置表单"""
        for key, var in self.operator_vars.items():
            if key == 'hit_count':
                var.set(1.0)
            elif key == 'class_type':
                var.set('狙击')
            elif key == 'atk_type':
                var.set('物伤')
            elif key == 'block_count':
                var.set(1)
            elif key == 'cost':
                var.set(10)
            elif isinstance(var, (tk.IntVar, tk.DoubleVar)):
                var.set(0)
            else:
                var.set('')
        
        self.update_heal_amount_state()
    
    def delete_selected_operator(self):
        """删除选中的干员"""
        selection = self.operator_treeview.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个干员")
            return
        
        # 确认删除
        result = messagebox.askyesno("确认删除", "确定要删除选中的干员吗？此操作不可恢复。")
        if not result:
            return
        
        try:
            item_id = selection[0]
            values = self.operator_treeview.item(item_id, 'values')
            if values:
                operator_id = int(values[0])
                operator = self.db_manager.get_operator(operator_id)
                
                if operator:
                    success = self.db_manager.delete_operator(operator_id)
                    
                    if success:
                        messagebox.showinfo("成功", f"已删除干员：{operator['name']}")
                        self.refresh_operator_list()
                        self.reset_form()
                        self.current_operator_id = None
                        self.is_editing = False
                        self.update_edit_status("查看模式", "blue")
                        self.update_status(f"已删除干员：{operator['name']}")
                    else:
                        messagebox.showerror("错误", "删除干员失败")
                        
        except Exception as e:
            messagebox.showerror("错误", f"删除干员失败：{str(e)}")
    
    def on_class_type_changed(self, event=None):
        """职业类型改变事件"""
        self.update_heal_amount_state()
        # 如果是医疗干员且治疗量为空，自动填入攻击力
        if (self.operator_vars['class_type'].get() == '医疗' and 
            self.operator_vars['heal_amount'].get() == 0 and
            self.operator_vars['atk'].get() > 0):
            self.operator_vars['heal_amount'].set(self.operator_vars['atk'].get())
    
    def update_heal_amount_state(self):
        """更新治疗量字段状态"""
        if 'heal_amount' in self.operator_inputs:
            widget = self.operator_inputs['heal_amount']
            if self.operator_vars['class_type'].get() == '医疗':
                widget.configure(state='normal')
            else:
                widget.configure(state='disabled')
                self.operator_vars['heal_amount'].set(0)
    
    def validate_hit_count(self, *args):
        """验证打数字段"""
        try:
            value = self.operator_vars['hit_count'].get()
            if value <= 0:
                self.operator_vars['hit_count'].set(1.0)
        except (ValueError, tk.TclError):
            self.operator_vars['hit_count'].set(1.0)
    
    def show_live_preview(self):
        """显示实时计算预览"""
        try:
            # 获取当前表单数据
            operator_data = {}
            for key, var in self.operator_vars.items():
                if isinstance(var, tk.StringVar):
                    operator_data[key] = var.get().strip()
                else:
                    operator_data[key] = var.get()
            
            # 计算性能指标
            performance = calculator.calculate_operator_performance(operator_data)
            
            # 创建预览窗口
            preview_window = tk.Toplevel(self.parent)
            preview_window.title(f"实时预览 - {operator_data.get('name', '未命名干员')}")
            preview_window.geometry("400x300")
            
            # 创建预览内容
            preview_frame = ttk.LabelFrame(preview_window, text="性能指标", padding=10)
            preview_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            metrics = [
                ("DPS", f"{performance['dps']:.1f}"),
                ("DPH", f"{performance['dph']:.1f}"),
                ("HPS", f"{performance.get('hps', 0):.1f}"),
                ("HPH", f"{performance.get('hph', 0):.1f}"),
                ("破甲线", f"{performance['armor_break_point']}"),
                ("生存能力", f"{performance['survivability']:.1f}"),
                ("性价比", f"{performance['cost_efficiency']:.2f}")
            ]
            
            for i, (label, value) in enumerate(metrics):
                ttk.Label(preview_frame, text=f"{label}:", font=("微软雅黑", 10, "bold")).grid(
                    row=i, column=0, sticky='e', pady=3, padx=(0, 10))
                ttk.Label(preview_frame, text=value, font=("微软雅黑", 10)).grid(
                    row=i, column=1, sticky='w', pady=3)
            
            # 关闭按钮
            ttk.Button(preview_window, text="关闭", command=preview_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("错误", f"生成预览失败：{str(e)}")
    
    def update_status(self, message):
        """更新状态信息"""
        if self.status_callback:
            self.status_callback(message)
        print(f"OperatorEditor: {message}")  # 调试输出
    
    def get_edit_mode_info(self):
        """获取当前编辑模式信息"""
        if self.is_editing:
            if self.current_operator_id:
                return "编辑现有干员"
            else:
                return "新建干员"
        else:
            return "查看模式"
    
    def enable_bulk_operations(self):
        """启用批量操作功能"""
        # 在工具栏添加批量操作按钮
        bulk_frame = ttk.Frame(self.parent)
        bulk_frame.pack(fill=X, pady=5)
        
        ttk.Label(bulk_frame, text="批量操作：").pack(side=LEFT)
        ttk.Button(bulk_frame, text="批量导入", bootstyle=INFO,
                  command=self.batch_import).pack(side=LEFT, padx=2)
        ttk.Button(bulk_frame, text="批量导出", bootstyle=INFO,
                  command=self.batch_export).pack(side=LEFT, padx=2)
        ttk.Button(bulk_frame, text="批量删除", bootstyle=DANGER,
                  command=self.batch_delete).pack(side=LEFT, padx=2)
    
    def batch_import(self):
        """批量导入干员"""
        messagebox.showinfo("提示", "批量导入功能开发中...")
    
    def batch_export(self):
        """批量导出干员"""
        messagebox.showinfo("提示", "批量导出功能开发中...")
    
    def batch_delete(self):
        """批量删除干员"""
        messagebox.showinfo("提示", "批量删除功能开发中...")

    def delete_all_operators_ui(self):
        """清空所有干员"""
        # 获取当前干员数量
        operators = self.db_manager.get_all_operators()
        operator_count = len(operators)
        
        if operator_count == 0:
            messagebox.showinfo("提示", "当前没有干员数据需要删除")
            return
        
        # 第一次确认
        first_confirm = messagebox.askyesno(
            "危险操作确认", 
            f"⚠️ 您即将删除所有 {operator_count} 个干员数据！\n\n"
            "此操作将：\n"
            "• 删除所有干员信息\n"
            "• 删除相关的计算记录\n"
            "• 重置ID序列\n\n"
            "⚠️ 此操作不可恢复！\n\n"
            "确定要继续吗？"
        )
        
        if not first_confirm:
            return
        
        # 第二次确认 - 输入确认文本
        from tkinter import simpledialog
        confirm_text = simpledialog.askstring(
            "最终确认",
            "请输入 'DELETE ALL' 来确认删除所有干员：",
            show='*'
        )
        
        if confirm_text != 'DELETE ALL':
            messagebox.showinfo("取消操作", "确认文本不正确，操作已取消")
            return
        
        try:
            # 执行删除操作
            result = self.db_manager.delete_all_operators()
            
            if result['success']:
                messagebox.showinfo("删除成功", result['message'])
                
                # 刷新界面
                self.refresh_operator_list()
                self.reset_form()
                self.current_operator_id = None
                self.is_editing = False
                self.update_edit_status("查看模式", "blue")
                self.update_status("已清空所有干员数据")
                
            else:
                messagebox.showerror("删除失败", result['message'])
                
        except Exception as e:
            messagebox.showerror("错误", f"删除所有干员失败：{str(e)}") 