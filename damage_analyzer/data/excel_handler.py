# excel_handler.py - 简化的Excel数据处理模块

import pandas as pd
import os
from typing import List, Dict, Any, Optional, Tuple
from tkinter import filedialog, messagebox
import openpyxl

class ExcelHandler:
    """简化的Excel处理器，支持干员数据的导入、导出与模板生成。"""
    
    def __init__(self):
        # 必要字段和可选字段
        self.required_fields = ['名称', '职业类型', '生命值', '攻击力', '攻击速度', '攻击类型']
        self.optional_fields = ['防御力', '法抗', '部署费用', '阻挡数']
    
    def import_from_excel(self, file_path: str = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        从Excel文件导入干员数据。
        支持用户交互选择文件，自动校验字段完整性。
        Args:
            file_path: Excel文件路径，可选
        Returns:
            (干员数据列表, 错误信息列表)
        """
        if file_path is None:
            file_path = filedialog.askopenfilename(
                title="选择Excel文件",
                filetypes=[("Excel 文件", "*.xlsx"), ("Excel 文件", "*.xls")]
            )
            if not file_path:
                return [], []
        
        try:
            df = pd.read_excel(file_path)
            if df.empty:
                return [], ["Excel文件为空"]
            operators = []
            errors = []
            for index, row in df.iterrows():
                try:
                    operator = self._parse_row(row)
                    if operator:
                        operators.append(operator)
                except Exception as e:
                    errors.append(f"第{index+2}行: {str(e)}")
            return operators, errors
        except Exception as e:
            return [], [f"读取Excel文件失败: {str(e)}"]
    
    def _parse_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        解析Excel单行数据为干员字典。
        字段自动映射，缺失必要字段时报错。
        Args:
            row: Excel行数据
        Returns:
            干员信息字典
        Raises:
            ValueError: 缺少必要字段
        """
        operator = {}
        field_map = {
            '名称': 'name',
            '职业类型': 'class_type',
            '生命值': 'hp',
            '攻击力': 'atk',
            '攻击速度': 'atk_speed',
            '攻击类型': 'atk_type',
            '防御力': 'def',
            '法抗': 'mdef',
            '部署费用': 'cost',
            '阻挡数': 'block_count'
        }
        for excel_field, db_field in field_map.items():
            if excel_field in row and pd.notna(row[excel_field]):
                operator[db_field] = row[excel_field]
        required_db_fields = ['name', 'class_type', 'hp', 'atk', 'atk_speed', 'atk_type']
        for field in required_db_fields:
            if field not in operator:
                raise ValueError(f"缺少必要字段: {field}")
        operator.setdefault('def', 0)
        operator.setdefault('mdef', 0)
        operator.setdefault('cost', 10)
        operator.setdefault('block_count', 1)
        return operator
    
    def export_to_excel(self, operators: List[Dict[str, Any]], file_path: str = None) -> bool:
        """
        导出干员数据到Excel文件。
        支持用户交互选择保存路径。
        Args:
            operators: 干员数据列表
            file_path: 保存路径，可选
        Returns:
            bool: 是否导出成功
        """
        if not operators:
            messagebox.showwarning("警告", "没有数据可导出")
            return False
        if file_path is None:
            file_path = filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel 文件", "*.xlsx")]
            )
            if not file_path:
                return False
        try:
            data = []
            for op in operators:
                row = {
                    '名称': op.get('name', ''),
                    '职业类型': op.get('class_type', ''),
                    '生命值': op.get('hp', 0),
                    '攻击力': op.get('atk', 0),
                    '攻击速度': op.get('atk_speed', 0),
                    '攻击类型': op.get('atk_type', ''),
                    '防御力': op.get('def', 0),
                    '法抗': op.get('mdef', 0),
                    '部署费用': op.get('cost', 10),
                    '阻挡数': op.get('block_count', 1)
                }
                data.append(row)
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"导出Excel失败: {str(e)}")
            return False
    
    def generate_template(self, file_path: str = None) -> bool:
        """
        生成干员数据Excel模板。
        支持用户交互选择保存路径，模板包含示例数据。
        Args:
            file_path: 保存路径，可选
        Returns:
            bool: 是否生成成功
        """
        if file_path is None:
            file_path = filedialog.asksaveasfilename(
                title="保存模板文件",
                defaultextension=".xlsx",
                filetypes=[("Excel 文件", "*.xlsx")]
            )
            if not file_path:
                return False
        try:
            template_data = [{
                '名称': '示例干员',
                '职业类型': '狙击',
                '生命值': 1000,
                '攻击力': 500,
                '攻击速度': 1.0,
                '攻击类型': '物伤',
                '防御力': 100,
                '法抗': 0,
                '部署费用': 15,
                '阻挡数': 1
            }]
            df = pd.DataFrame(template_data)
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"生成模板失败: {str(e)}")
            return False 