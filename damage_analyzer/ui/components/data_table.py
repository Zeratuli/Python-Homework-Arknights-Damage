# data_table.py - 增强的数据表格组件

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, List, Optional, Any, Callable
import pandas as pd
import logging
from .sortable_treeview import SortableTreeview

logger = logging.getLogger(__name__)

class DataTable(ttk.Frame):
    """增强的数据表格组件"""
    
    def __init__(self, parent, db_manager=None, **kwargs):
        """
        初始化数据表格组件
        
        Args:
            parent: 父容器
            db_manager: 数据库管理器
        """
        super().__init__(parent, **kwargs)
        
        self.db_manager = db_manager
        self.data = []
        self.filtered_data = []
        self.columns = []
        self.sort_column = None
        self.sort_reverse = False
        
        # 筛选变量
        self.filter_vars = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建标题和工具栏
        self.create_header()
        
        # 创建筛选区域
        self.create_filter_area()
        
        # 创建表格区域
        self.create_table_area()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_header(self):
        """创建标题和工具栏"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0, 10))
        
        # 标题
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill=X)
        
        ttk.Label(title_frame, text="📊 数据表格", 
                 font=("微软雅黑", 12, "bold")).pack(side=LEFT)
        
        # 工具栏
        toolbar_frame = ttk.Frame(header_frame)
        toolbar_frame.pack(fill=X, pady=(5, 0))
        
        ttk.Button(toolbar_frame, text="🔄 刷新", bootstyle=INFO,
                  command=self.refresh_data, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar_frame, text="📊 导出Excel", bootstyle=SUCCESS,
                  command=self.export_to_excel, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar_frame, text="📄 导出CSV", bootstyle=SECONDARY,
                  command=self.export_to_csv, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🔍 高级筛选", bootstyle=PRIMARY,
                  command=self.show_advanced_filter, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar_frame, text="❌ 清除筛选", bootstyle=WARNING,
                  command=self.clear_filters, width=10).pack(side=LEFT, padx=2)
    
    def create_filter_area(self):
        """创建筛选区域"""
        filter_frame = ttk.LabelFrame(self, text="快速筛选", padding=5)
        filter_frame.pack(fill=X, pady=(0, 10))
        
        # 搜索框
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(fill=X)
        
        ttk.Label(search_frame, text="搜索:").pack(side=LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(5, 10))
        
        # 职业筛选
        ttk.Label(search_frame, text="职业:").pack(side=LEFT)
        self.class_filter_var = tk.StringVar(value="全部")
        class_combo = ttk.Combobox(search_frame, textvariable=self.class_filter_var,
                                  values=["全部", "先锋", "近卫", "重装", "狙击", "术士", "医疗", "辅助", "特种"],
                                  width=10, state="readonly")
        class_combo.pack(side=LEFT, padx=(5, 10))
        class_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # 攻击类型筛选
        ttk.Label(search_frame, text="攻击类型:").pack(side=LEFT)
        self.atk_type_filter_var = tk.StringVar(value="全部")
        atk_type_combo = ttk.Combobox(search_frame, textvariable=self.atk_type_filter_var,
                                     values=["全部", "物伤", "法伤"],
                                     width=8, state="readonly")
        atk_type_combo.pack(side=LEFT, padx=(5, 0))
        atk_type_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
    
    def create_table_area(self):
        """创建表格区域"""
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=BOTH, expand=True)
        
        # 定义列
        self.columns = [
            ("name", "干员名称", 120),
            ("class_type", "职业", 80),
            ("atk", "攻击力", 80),
            ("hp", "生命值", 80),
            ("def", "防御力", 80),
            ("atk_type", "攻击类型", 80),
            ("atk_speed", "攻击速度", 80),
            ("cost", "部署费用", 80),
            ("dps", "DPS", 80),
            ("cost_efficiency", "性价比", 80)
        ]
        
        # 创建可排序的Treeview
        self.tree = SortableTreeview(table_frame, 
                                   columns=[col[0] for col in self.columns],
                                   show='tree headings',
                                   height=15)
        
        # 配置列
        self.tree.heading('#0', text='ID', anchor=W)
        self.tree.column('#0', width=50, minwidth=50)
        
        for col_id, col_name, col_width in self.columns:
            self.tree.heading(col_id, text=col_name, anchor=W)
            self.tree.column(col_id, width=col_width, minwidth=60)
        
        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定事件
        self.tree.bind('<Double-1>', self.on_row_double_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_row_select)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪", 
                                     font=("微软雅黑", 9), bootstyle="secondary")
        self.status_label.pack(side=LEFT)
        
        self.count_label = ttk.Label(status_frame, text="总计: 0 项", 
                                    font=("微软雅黑", 9), bootstyle="info")
        self.count_label.pack(side=RIGHT)
    
    def load_data(self, data: List[Dict[str, Any]]):
        """
        加载数据到表格
        
        Args:
            data: 数据列表
        """
        self.data = data
        self.filtered_data = data.copy()
        self.refresh_table()
    
    def refresh_data(self):
        """刷新数据"""
        if self.db_manager:
            try:
                # 从数据库获取干员数据
                operators = self.db_manager.get_all_operators()
                
                # 计算DPS和性价比
                from core.damage_calculator import DamageCalculator
                calculator = DamageCalculator()
                
                enhanced_data = []
                for op in operators:
                    # 计算性能指标
                    performance = calculator.calculate_operator_performance(op)
                    
                    # 合并数据
                    enhanced_op = op.copy()
                    enhanced_op.update({
                        'dps': round(performance.get('dps', 0), 1),
                        'cost_efficiency': round(performance.get('cost_efficiency', 0), 2)
                    })
                    enhanced_data.append(enhanced_op)
                
                self.load_data(enhanced_data)
                self.update_status("数据已刷新")
                
            except Exception as e:
                logger.error(f"刷新数据失败: {e}")
                self.update_status(f"刷新失败: {str(e)}")
        else:
            self.update_status("无数据源")
    
    def refresh_table(self):
        """刷新表格显示"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 插入筛选后的数据
        for i, row in enumerate(self.filtered_data):
            values = []
            for col_id, _, _ in self.columns:
                value = row.get(col_id, '')
                if isinstance(value, (int, float)):
                    if col_id in ['dps', 'cost_efficiency']:
                        values.append(f"{value:.1f}")
                    else:
                        values.append(str(value))
                else:
                    values.append(str(value))
            
            self.tree.insert('', 'end', iid=str(i), text=str(row.get('id', i+1)), values=values)
        
        # 更新计数
        self.count_label.configure(text=f"显示: {len(self.filtered_data)} / 总计: {len(self.data)} 项")
    
    def on_search_changed(self, *args):
        """搜索变化处理"""
        self.apply_filters()
    
    def on_filter_changed(self, event=None):
        """筛选变化处理"""
        self.apply_filters()
    
    def apply_filters(self):
        """应用筛选条件"""
        search_text = self.search_var.get().lower()
        class_filter = self.class_filter_var.get()
        atk_type_filter = self.atk_type_filter_var.get()
        
        self.filtered_data = []
        
        for row in self.data:
            # 搜索筛选
            if search_text:
                searchable_text = f"{row.get('name', '')} {row.get('class_type', '')}".lower()
                if search_text not in searchable_text:
                    continue
            
            # 职业筛选
            if class_filter != "全部" and row.get('class_type', '') != class_filter:
                continue
            
            # 攻击类型筛选
            if atk_type_filter != "全部" and row.get('atk_type', '') != atk_type_filter:
                continue
            
            self.filtered_data.append(row)
        
        self.refresh_table()
    
    def clear_filters(self):
        """清除所有筛选条件"""
        self.search_var.set("")
        self.class_filter_var.set("全部")
        self.atk_type_filter_var.set("全部")
        self.apply_filters()
        self.update_status("筛选已清除")
    
    def show_advanced_filter(self):
        """显示高级筛选对话框"""
        # TODO: 实现高级筛选对话框
        messagebox.showinfo("提示", "高级筛选功能开发中...")
    
    def export_to_excel(self):
        """导出到Excel"""
        if not self.filtered_data:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="导出Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            
            if file_path:
                # 创建DataFrame
                df = pd.DataFrame(self.filtered_data)
                
                # 重新排列列顺序
                column_order = [col[0] for col in self.columns if col[0] in df.columns]
                df = df[column_order]
                
                # 重命名列
                column_names = {col[0]: col[1] for col in self.columns}
                df = df.rename(columns=column_names)
                
                # 导出到Excel
                df.to_excel(file_path, index=False, engine='openpyxl')
                
                self.update_status(f"已导出 {len(self.filtered_data)} 条记录到 {file_path}")
                messagebox.showinfo("成功", f"数据已导出到:\n{file_path}")
                
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")
    
    def export_to_csv(self):
        """导出到CSV"""
        if not self.filtered_data:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="导出CSV文件",
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            
            if file_path:
                # 创建DataFrame
                df = pd.DataFrame(self.filtered_data)
                
                # 重新排列列顺序
                column_order = [col[0] for col in self.columns if col[0] in df.columns]
                df = df[column_order]
                
                # 重命名列
                column_names = {col[0]: col[1] for col in self.columns}
                df = df.rename(columns=column_names)
                
                # 导出到CSV
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                
                self.update_status(f"已导出 {len(self.filtered_data)} 条记录到 {file_path}")
                messagebox.showinfo("成功", f"数据已导出到:\n{file_path}")
                
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")
    
    def on_row_double_click(self, event):
        """行双击事件"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            try:
                row_index = int(item_id)
                if 0 <= row_index < len(self.filtered_data):
                    row_data = self.filtered_data[row_index]
                    self.show_row_details(row_data)
            except (ValueError, IndexError):
                pass
    
    def on_row_select(self, event):
        """行选择事件"""
        selection = self.tree.selection()
        if selection:
            self.update_status(f"已选择 {len(selection)} 行")
        else:
            self.update_status("就绪")
    
    def show_row_details(self, row_data: Dict[str, Any]):
        """显示行详细信息"""
        # 创建详细信息窗口
        detail_window = tk.Toplevel(self)
        detail_window.title(f"干员详情 - {row_data.get('name', '未知')}")
        detail_window.geometry("400x500")
        detail_window.resizable(False, False)
        
        # 创建滚动文本框
        text_frame = ttk.Frame(detail_window)
        text_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 插入详细信息
        details = []
        for col_id, col_name, _ in self.columns:
            value = row_data.get(col_id, 'N/A')
            details.append(f"{col_name}: {value}")
        
        text_widget.insert(tk.END, "\n".join(details))
        text_widget.configure(state=tk.DISABLED)
        
        # 关闭按钮
        ttk.Button(detail_window, text="关闭", 
                  command=detail_window.destroy).pack(pady=10)
    
    def get_selected_data(self) -> List[Dict[str, Any]]:
        """获取选中的数据"""
        selection = self.tree.selection()
        selected_data = []
        
        for item_id in selection:
            try:
                row_index = int(item_id)
                if 0 <= row_index < len(self.filtered_data):
                    selected_data.append(self.filtered_data[row_index])
            except (ValueError, IndexError):
                continue
        
        return selected_data
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.configure(text=message)
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """获取所有数据"""
        return self.data.copy()
    
    def get_filtered_data(self) -> List[Dict[str, Any]]:
        """获取筛选后的数据"""
        return self.filtered_data.copy() 