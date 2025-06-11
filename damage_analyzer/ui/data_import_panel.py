# data_import_panel.py - 数据导入面板

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import csv
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Callable

# 添加项目根目录到路径，确保能够导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入统一的导入导出管理器 - 修复：使用项目内导入
from data.import_export_manager import ImportExportManager

logger = logging.getLogger(__name__)

class DataImportPanel:
    """数据导入面板"""
    
    def __init__(self, parent, db_manager, status_callback: Optional[Callable] = None):
        """
        初始化数据导入面板
        
        Args:
            parent: 父窗口
            db_manager: 数据库管理器实例
            status_callback: 状态回调函数
        """
        self.parent = parent
        self.db_manager = db_manager
        self.status_callback = status_callback
        
        # 创建统一的导入导出管理器
        self.import_export_manager = ImportExportManager(db_manager)
        self.import_export_manager.set_status_callback(status_callback)
        
        # 创建日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化UI
        self.setup_ui()
        
        # 刷新数据显示
        self.refresh_data_list()
    
    def set_refresh_callback(self, callback: Callable[[], None]):
        """设置刷新回调函数"""
        if self.import_export_manager:
            self.import_export_manager.set_refresh_callback(callback)
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📊 数据导入管理", 
                               font=("微软雅黑", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 创建导入操作区域
        self.create_import_section(main_frame)
        
        # 创建数据显示区域
        self.create_data_display_section(main_frame)
        
        # 创建操作按钮区域
        self.create_action_buttons_section(main_frame)
    
    def create_import_section(self, parent):
        """创建导入操作区域"""
        import_frame = ttk.LabelFrame(parent, text="📥 导入数据", padding=15)
        import_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 导入按钮网格
        button_frame = ttk.Frame(import_frame)
        button_frame.pack(fill=tk.X)
        
        # Excel导入
        excel_btn = ttk.Button(button_frame, text="📋 导入Excel", 
                              bootstyle="primary", width=15,
                              command=self.import_excel_data)
        excel_btn.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        
        # JSON导入
        json_btn = ttk.Button(button_frame, text="📄 导入JSON", 
                             bootstyle="info", width=15,
                             command=self.import_json_data)
        json_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # CSV导入
        csv_btn = ttk.Button(button_frame, text="📊 导入CSV", 
                            bootstyle="success", width=15,
                            command=self.import_csv_data)
        csv_btn.grid(row=0, column=2, padx=(10, 0), pady=5, sticky="ew")
        
        # 配置列权重
        for i in range(3):
            button_frame.grid_columnconfigure(i, weight=1)
        
        # 导入提示
        tips_label = ttk.Label(import_frame, 
                              text="支持Excel (.xlsx/.xls)、JSON (.json)、CSV (.csv) 格式的干员数据文件",
                              font=("微软雅黑", 9))
        tips_label.pack(pady=(10, 0))
    
    def create_data_display_section(self, parent):
        """创建数据显示区域"""
        display_frame = ttk.LabelFrame(parent, text="📋 当前数据", padding=15)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建数据表格
        self.create_data_table(display_frame)
    
    def create_data_table(self, parent):
        """创建数据表格"""
        # 表格框架
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 定义列
        columns = ("ID", "名称", "职业", "攻击力", "生命值", "防御力")
        
        # 创建Treeview
        self.data_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题和宽度
        self.data_tree.heading("ID", text="ID")
        self.data_tree.heading("名称", text="干员名称")
        self.data_tree.heading("职业", text="职业")
        self.data_tree.heading("攻击力", text="攻击力")
        self.data_tree.heading("生命值", text="生命值")
        self.data_tree.heading("防御力", text="防御力")
        
        self.data_tree.column("ID", width=50, anchor="center")
        self.data_tree.column("名称", width=120, anchor="w")
        self.data_tree.column("职业", width=80, anchor="center")
        self.data_tree.column("攻击力", width=80, anchor="center")
        self.data_tree.column("生命值", width=80, anchor="center")
        self.data_tree.column("防御力", width=80, anchor="center")
        
        # 创建滚动条
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
        
        self.data_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 配置权重
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定双击事件
        self.data_tree.bind("<Double-1>", self.on_item_double_click)
    
    def create_action_buttons_section(self, parent):
        """创建操作按钮区域"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X)
        
        # 左侧按钮
        left_frame = ttk.Frame(action_frame)
        left_frame.pack(side=tk.LEFT)
        
        refresh_btn = ttk.Button(left_frame, text="🔄 刷新数据", 
                                bootstyle="info", width=12,
                                command=self.refresh_data_list)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # ID管理按钮
        id_manage_btn = ttk.Button(left_frame, text="🔢 重排ID", 
                                  bootstyle="warning", width=12,
                                  command=self.reorder_ids)
        id_manage_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧按钮
        right_frame = ttk.Frame(action_frame)
        right_frame.pack(side=tk.RIGHT)
        
        delete_btn = ttk.Button(right_frame, text="🗑️ 删除选中", 
                               bootstyle="danger", width=12,
                               command=self.delete_selected_operator)
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        edit_btn = ttk.Button(right_frame, text="✏️ 编辑选中", 
                             bootstyle="warning", width=12,
                             command=self.edit_selected_operator)
        edit_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    def import_excel_data(self):
        """导入Excel数据 - 使用统一的ImportExportManager"""
        try:
            self.logger.info("用户点击Excel导入按钮")
            
            # 使用统一的导入管理器
            result = self.import_export_manager.import_excel_data(status_callback=self.status_callback)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新数据显示
                self.refresh_data_list()
                
                self.logger.info(f"Excel导入成功: {result}")
                
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                self.logger.info("用户取消了Excel导入")
                
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                self.logger.error(f"Excel导入失败: {result}")
                
        except Exception as e:
            self.logger.error(f"Excel导入异常: {e}")
            messagebox.showerror("导入失败", f"Excel导入失败：\n{str(e)}")
            if self.status_callback:
                self.status_callback("Excel导入失败", "error")
    
    def import_json_data(self):
        """导入JSON数据 - 使用统一的ImportExportManager"""
        try:
            self.logger.info("用户点击JSON导入按钮")
            
            # 使用统一的导入管理器
            result = self.import_export_manager.import_json_data(status_callback=self.status_callback)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新数据显示
                self.refresh_data_list()
                
                self.logger.info(f"JSON导入成功: {result}")
                
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                self.logger.info("用户取消了JSON导入")
                
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                self.logger.error(f"JSON导入失败: {result}")
                
        except Exception as e:
            self.logger.error(f"JSON导入异常: {e}")
            messagebox.showerror("导入失败", f"JSON导入失败：\n{str(e)}")
            if self.status_callback:
                self.status_callback("JSON导入失败", "error")
    
    def import_csv_data(self):
        """导入CSV数据 - 使用统一的ImportExportManager"""
        try:
            self.logger.info("用户点击CSV导入按钮")
            
            # 使用统一的导入管理器
            result = self.import_export_manager.import_csv_data(status_callback=self.status_callback)
            
            if result.get('success'):
                # 显示成功消息
                messagebox.showinfo("导入成功", result.get('message', '导入完成'))
                
                # 刷新数据显示
                self.refresh_data_list()
                
                self.logger.info(f"CSV导入成功: {result}")
                
            elif result.get('cancelled'):
                # 用户取消，不显示任何消息
                self.logger.info("用户取消了CSV导入")
                
            else:
                # 导入失败的情况已经在管理器中处理了messagebox
                self.logger.error(f"CSV导入失败: {result}")
                
        except Exception as e:
            self.logger.error(f"CSV导入异常: {e}")
            messagebox.showerror("导入失败", f"CSV导入失败：\n{str(e)}")
            if self.status_callback:
                self.status_callback("CSV导入失败", "error")
    
    def refresh_data_list(self):
        """刷新数据列表"""
        try:
            # 清空现有数据
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # 获取所有干员数据
            operators = self.db_manager.get_all_operators()
            
            # 填充数据
            for operator in operators:
                self.data_tree.insert("", "end", values=(
                    operator.get('id', ''),
                    operator.get('name', ''),
                    operator.get('class_type', ''),
                    operator.get('atk', ''),
                    operator.get('hp', ''),
                    operator.get('def', '')
                ))
            
            # 更新状态
            if self.status_callback:
                self.status_callback(f"数据已刷新，共 {len(operators)} 个干员")
                
        except Exception as e:
            self.logger.error(f"刷新数据列表失败: {e}")
            if self.status_callback:
                self.status_callback("数据刷新失败", "error")
    
    def on_item_double_click(self, event):
        """处理双击事件"""
        try:
            selection = self.data_tree.selection()
            if selection:
                item = self.data_tree.item(selection[0])
                operator_id = item['values'][0]
                
                # 这里可以打开编辑对话框
                self.edit_operator(operator_id)
                
        except Exception as e:
            self.logger.error(f"处理双击事件失败: {e}")
    
    def edit_selected_operator(self):
        """编辑选中的干员"""
        try:
            selection = self.data_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请先选择要编辑的干员")
                return
            
            item = self.data_tree.item(selection[0])
            operator_id = item['values'][0]
            
            self.edit_operator(operator_id)
            
        except Exception as e:
            self.logger.error(f"编辑干员失败: {e}")
    
    def edit_operator(self, operator_id):
        """编辑指定ID的干员"""
        try:
            # 获取干员数据
            operator = self.db_manager.get_operator(operator_id)
            if not operator:
                messagebox.showerror("错误", "未找到指定的干员")
                return
            
            # 这里可以打开编辑对话框
            # 简化实现：显示干员信息
            info = f"干员信息：\n"
            info += f"ID: {operator.get('id')}\n"
            info += f"名称: {operator.get('name')}\n"
            info += f"职业: {operator.get('class_type')}\n"
            info += f"攻击力: {operator.get('atk')}\n"
            info += f"生命值: {operator.get('hp')}\n"
            info += f"防御力: {operator.get('def')}"
            
            messagebox.showinfo("干员信息", info)
            
        except Exception as e:
            self.logger.error(f"编辑干员失败: {e}")
            messagebox.showerror("错误", f"编辑干员失败：\n{str(e)}")
    
    def delete_selected_operator(self):
        """删除选中的干员"""
        try:
            selection = self.data_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请先选择要删除的干员")
                return
            
            item = self.data_tree.item(selection[0])
            operator_id = item['values'][0]
            operator_name = item['values'][1]
            
            # 确认删除
            result = messagebox.askyesno("确认删除", 
                                       f"确定要删除干员 '{operator_name}' 吗？\n此操作不可撤销。")
            
            if result:
                # 执行删除
                success = self.db_manager.delete_operator(operator_id)
                
                if success:
                    messagebox.showinfo("删除成功", f"干员 '{operator_name}' 已删除")
                    # 刷新数据显示
                    self.refresh_data_list()
                    
                    if self.status_callback:
                        self.status_callback(f"已删除干员: {operator_name}", "success")
                else:
                    messagebox.showerror("删除失败", f"删除干员 '{operator_name}' 失败")
                    
        except Exception as e:
            self.logger.error(f"删除干员失败: {e}")
            messagebox.showerror("错误", f"删除干员失败：\n{str(e)}")
            if self.status_callback:
                self.status_callback("删除操作失败", "error")
    
    def refresh_data(self):
        """刷新数据（供外部调用）"""
        self.refresh_data_list()
    
    def reorder_ids(self):
        """重排ID功能"""
        try:
            # 先获取当前ID空缺信息
            gaps = self.db_manager.get_id_gaps()
            
            if not gaps:
                messagebox.showinfo("ID检查", "当前ID序列已经是连续的，无需重排")
                return
            
            # 显示确认对话框
            gap_info = f"发现 {len(gaps)} 个ID空缺: {gaps[:10]}"
            if len(gaps) > 10:
                gap_info += f" ... (还有 {len(gaps) - 10} 个)"
            
            confirm_msg = f"""ID重排操作

{gap_info}

此操作将：
1. 重新安排所有干员ID从1开始连续编号
2. 自动更新相关的计算记录
3. 确保数据一致性

是否继续？

⚠️ 建议在操作前备份数据库"""
            
            result = messagebox.askyesno("确认ID重排", confirm_msg)
            
            if not result:
                return
            
            # 执行ID重排
            self.logger.info("开始执行ID重排操作")
            
            # 显示进度信息
            if self.status_callback:
                self.status_callback("正在重排ID...", "info")
            
            # 调用数据库管理器的重排方法
            reorder_result = self.db_manager.reorder_operator_ids()
            
            if reorder_result['success']:
                # 显示成功信息
                success_msg = f"""ID重排成功！

{reorder_result['message']}

重排的干员数量: {reorder_result['reordered_count']}

现在所有干员ID都是从1开始的连续编号"""
                
                messagebox.showinfo("重排成功", success_msg)
                
                # 刷新数据显示
                self.refresh_data_list()
                
                # 如果有刷新回调，触发全局刷新
                if hasattr(self.import_export_manager, 'refresh_callback') and self.import_export_manager.refresh_callback:
                    self.import_export_manager.refresh_callback()
                
                if self.status_callback:
                    self.status_callback(f"ID重排完成: {reorder_result['reordered_count']} 个干员", "success")
                    
                self.logger.info(f"ID重排成功: {reorder_result}")
                
            else:
                # 显示失败信息
                messagebox.showerror("重排失败", f"ID重排失败：\n{reorder_result['message']}")
                
                if self.status_callback:
                    self.status_callback("ID重排失败", "error")
                    
                self.logger.error(f"ID重排失败: {reorder_result}")
            
        except Exception as e:
            self.logger.error(f"ID重排异常: {e}")
            messagebox.showerror("操作失败", f"ID重排操作失败：\n{str(e)}")
            if self.status_callback:
                self.status_callback("ID重排操作失败", "error") 