# sortable_treeview.py - 支持排序的Treeview组件

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, List, Optional, Any, Callable
import re

class SortableTreeview(ttk.Treeview):
    """支持列排序的Treeview组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 排序状态
        self.sort_columns = {}  # 存储列的排序状态
        self.sort_ascending = {}  # 存储排序方向
        self.current_sort_column = None
        
        # 原始数据存储
        self.original_data = []
        
        # 原始标题文本缓存
        self.original_headings = {}
        
        # 排序指示器
        self.sort_indicators = {
            'asc': ' ▲',
            'desc': ' ▼',
            'none': ''
        }
    
    def enable_sorting(self, columns: Optional[List[str]] = None):
        """为指定列启用排序功能
        
        Args:
            columns: 要启用排序的列名列表，None表示为所有列启用
        """
        if columns is None:
            # 为所有列启用排序
            columns = list(self['columns'])
        
        for column in columns:
            self.sort_columns[column] = True
            self.sort_ascending[column] = True
            
            # 保存原始标题文本
            original_text = self.heading(column, 'text')
            if original_text:
                self.original_headings[column] = original_text
            
            # 绑定表头点击事件
            self.heading(column, command=lambda col=column: self.sort_by_column(col))
    
    def sort_by_column(self, column: str, ascending: Optional[bool] = None):
        """按指定列排序
        
        Args:
            column: 列名
            ascending: 排序方向，None表示切换当前方向
        """
        if column not in self.sort_columns:
            return
        
        # 确定排序方向
        if ascending is None:
            if self.current_sort_column == column:
                # 如果是同一列，切换方向
                ascending = not self.sort_ascending[column]
            else:
                # 如果是新列，默认升序
                ascending = True
        
        self.sort_ascending[column] = ascending
        self.current_sort_column = column
        
        # 获取所有项目
        items = [(self.set(item, column), item) for item in self.get_children('')]
        
        # 排序
        items.sort(key=lambda x: self.get_sort_key(x[0]), reverse=not ascending)
        
        # 重新插入项目
        for index, (value, item) in enumerate(items):
            self.move(item, '', index)
        
        # 更新表头显示
        self.update_heading_indicators()
    
    def get_sort_key(self, value: Any):
        """获取排序键值，智能识别数值/文本
        
        Args:
            value: 要排序的值
            
        Returns:
            排序键值
        """
        if value is None:
            return (1, 0)  # None值排在最后
        
        # 尝试转换为数值
        if isinstance(value, (int, float)):
            return (0, value)
        
        # 字符串处理
        str_value = str(value).strip()
        if not str_value:
            return (1, 0)  # 空字符串排在最后
        
        # 尝试解析数字（包括带单位的）
        numeric_match = re.match(r'^([-+]?\d*\.?\d+)', str_value)
        if numeric_match:
            try:
                num_value = float(numeric_match.group(1))
                return (0, num_value)
            except ValueError:
                pass
        
        # 处理百分比
        if str_value.endswith('%'):
            try:
                num_value = float(str_value[:-1])
                return (0, num_value)
            except ValueError:
                pass
        
        # 普通字符串排序（不区分大小写）
        return (0, str_value.lower())
    
    def update_heading_indicators(self):
        """更新表头排序指示器"""
        # 重置所有列标题为原始文本
        for column in self.sort_columns:
            if column in self.original_headings:
                self.heading(column, text=self.original_headings[column])
        
        # 为当前排序列添加指示器
        if self.current_sort_column and self.current_sort_column in self.sort_columns:
            if self.current_sort_column in self.original_headings:
                original_text = self.original_headings[self.current_sort_column]
                if self.sort_ascending[self.current_sort_column]:
                    indicator = self.sort_indicators['asc']
                else:
                    indicator = self.sort_indicators['desc']
                self.heading(self.current_sort_column, text=original_text + indicator)
    
    def insert_sorted(self, parent: str, index: str, **kwargs):
        """插入项目并保持排序状态
        
        Args:
            parent: 父项目ID
            index: 插入位置
            **kwargs: 其他插入参数
        """
        item_id = self.insert(parent, index, **kwargs)
        
        # 如果当前有排序，重新排序
        if self.current_sort_column:
            self.sort_by_column(self.current_sort_column, self.sort_ascending[self.current_sort_column])
        
        return item_id
    
    def set_sorted(self, item: str, column: str, value: Any):
        """设置项目值并保持排序状态
        
        Args:
            item: 项目ID
            column: 列名
            value: 新值
        """
        self.set(item, column, value)
        
        # 如果修改的是排序列，重新排序
        if column == self.current_sort_column:
            self.sort_by_column(self.current_sort_column, self.sort_ascending[self.current_sort_column])
    
    def clear_sort(self):
        """清除排序状态"""
        self.current_sort_column = None
        self.update_heading_indicators()
    
    def get_sort_info(self) -> Dict[str, Any]:
        """获取当前排序信息
        
        Returns:
            排序信息字典
        """
        return {
            'column': self.current_sort_column,
            'ascending': self.sort_ascending.get(self.current_sort_column, True) if self.current_sort_column else None,
            'sortable_columns': list(self.sort_columns.keys())
        }
    
    def apply_sort_info(self, sort_info: Dict[str, Any]):
        """应用排序信息
        
        Args:
            sort_info: 排序信息字典
        """
        if sort_info.get('column') and sort_info['column'] in self.sort_columns:
            self.sort_by_column(sort_info['column'], sort_info.get('ascending', True))

class NumericSortableTreeview(SortableTreeview):
    """专门用于数值数据的排序Treeview"""
    
    def __init__(self, parent, numeric_columns: List[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.numeric_columns = numeric_columns or []
    
    def get_sort_key(self, value: Any):
        """数值优先的排序键值"""
        if value is None:
            return (1, 0)
        
        str_value = str(value).strip()
        if not str_value:
            return (1, 0)
        
        # 强制数值处理
        if self.current_sort_column in self.numeric_columns:
            try:
                # 移除非数字字符（除了小数点和负号）
                clean_value = re.sub(r'[^\d.-]', '', str_value)
                if clean_value:
                    return (0, float(clean_value))
            except ValueError:
                pass
        
        return super().get_sort_key(value)

class MultiColumnSortableTreeview(SortableTreeview):
    """支持多列排序的Treeview"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.sort_priority = []  # 排序优先级列表
    
    def sort_by_column(self, column: str, ascending: Optional[bool] = None):
        """支持多列排序"""
        if column not in self.sort_columns:
            return
        
        # 更新排序优先级
        if column in self.sort_priority:
            self.sort_priority.remove(column)
        self.sort_priority.insert(0, column)
        
        # 限制最多3列排序
        if len(self.sort_priority) > 3:
            self.sort_priority = self.sort_priority[:3]
        
        # 确定排序方向
        if ascending is None:
            if self.current_sort_column == column:
                ascending = not self.sort_ascending[column]
            else:
                ascending = True
        
        self.sort_ascending[column] = ascending
        self.current_sort_column = column
        
        # 多列排序
        items = []
        for item in self.get_children(''):
            sort_keys = []
            for sort_col in self.sort_priority:
                value = self.set(item, sort_col)
                key = self.get_sort_key(value)
                if not self.sort_ascending[sort_col]:
                    # 对于数值，反转排序
                    if isinstance(key, tuple) and len(key) == 2:
                        key = (key[0], -key[1] if isinstance(key[1], (int, float)) else key[1])
                sort_keys.append(key)
            items.append((sort_keys, item))
        
        # 排序
        items.sort(key=lambda x: x[0])
        
        # 重新插入项目
        for index, (sort_keys, item) in enumerate(items):
            self.move(item, '', index)
        
        # 更新表头显示
        self.update_heading_indicators()
    
    def get_sort_priority_info(self) -> List[Dict[str, Any]]:
        """获取排序优先级信息"""
        return [
            {
                'column': col,
                'ascending': self.sort_ascending.get(col, True),
                'priority': idx + 1
            }
            for idx, col in enumerate(self.sort_priority)
        ] 