# csv_handler.py - CSV数据处理模块

import csv
import os
from typing import List, Dict, Any, Optional, Tuple
from tkinter import filedialog, messagebox
import logging

logger = logging.getLogger(__name__)

class CsvHandler:
    """CSV处理器"""
    
    def __init__(self):
        # 基本字段映射
        self.field_mapping = {
            'name': ['name', '名称', '干员名称', '姓名'],
            'class_type': ['class_type', '职业', '职业类型', 'class', 'type'],
            'atk': ['atk', 'attack', '攻击力', '攻击'],
            'hp': ['hp', 'health', '生命值', '血量', '生命'],
            'def': ['def', 'defense', '防御', '防御力'],
            'atk_speed': ['atk_speed', 'attack_speed', '攻击速度', '攻速'],
            'cost': ['cost', '费用', '部署费用', 'deploy_cost'],
            'block_count': ['block_count', 'block', '阻挡', '阻挡数'],
            'atk_type': ['atk_type', 'attack_type', '攻击类型', '伤害类型'],
            'mdef': ['mdef', 'magic_defense', '法抗', '法术抗性']
        }
    
    def import_from_csv(self, file_path: str = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """从CSV文件导入数据"""
        if file_path is None:
            file_path = filedialog.askopenfilename(
                title="选择CSV文件",
                filetypes=[("CSV 文件", "*.csv")]
            )
            if not file_path:
                return [], []
        
        try:
            operators = []
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # 尝试自动检测分隔符
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                # 检测分隔符
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ','  # 默认使用逗号
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # 从第2行开始计数（第1行是标题）
                    try:
                        operator = self._parse_csv_row(row)
                        if operator:
                            operators.append(operator)
                    except Exception as e:
                        errors.append(f"第{row_num}行: {str(e)}")
            
            return operators, errors
            
        except Exception as e:
            return [], [f"读取CSV文件失败: {str(e)}"]
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """解析CSV行数据"""
        operator = {}
        
        # 映射字段
        for target_field, possible_names in self.field_mapping.items():
            for name in possible_names:
                if name in row and row[name] and row[name].strip():
                    value = row[name].strip()
                    
                    # 数据类型转换
                    try:
                        if target_field in ['atk', 'hp', 'def', 'cost', 'block_count', 'mdef']:
                            operator[target_field] = int(float(value))
                        elif target_field == 'atk_speed':
                            operator[target_field] = float(value)
                        else:
                            operator[target_field] = value
                    except (ValueError, TypeError):
                        # 如果转换失败，跳过这个字段
                        continue
                    break
        
        # 检查必要字段
        if not operator.get('name'):
            raise ValueError("缺少干员名称")
        
        # 设置默认值
        operator.setdefault('class_type', '未知')
        operator.setdefault('atk', 0)
        operator.setdefault('hp', 0)
        operator.setdefault('def', 0)
        operator.setdefault('mdef', 0)
        operator.setdefault('atk_speed', 1.0)
        operator.setdefault('cost', 10)
        operator.setdefault('block_count', 1)
        operator.setdefault('atk_type', '物伤')
        
        return operator
    
    def export_to_csv(self, operators: List[Dict[str, Any]], file_path: str = None) -> bool:
        """导出数据到CSV文件"""
        if not operators:
            messagebox.showwarning("警告", "没有数据可导出")
            return False
        
        if file_path is None:
            file_path = filedialog.asksaveasfilename(
                title="保存CSV文件",
                defaultextension=".csv",
                filetypes=[("CSV 文件", "*.csv")]
            )
            if not file_path:
                return False
        
        try:
            # 定义CSV字段顺序
            fieldnames = [
                'name', 'class_type', 'hp', 'atk', 'def', 'mdef',
                'atk_speed', 'atk_type', 'cost', 'block_count'
            ]
            
            # 中文字段名映射
            chinese_fieldnames = {
                'name': '名称',
                'class_type': '职业类型',
                'hp': '生命值',
                'atk': '攻击力',
                'def': '防御力',
                'mdef': '法抗',
                'atk_speed': '攻击速度',
                'atk_type': '攻击类型',
                'cost': '部署费用',
                'block_count': '阻挡数'
            }
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 写入中文标题行
                chinese_header = {field: chinese_fieldnames.get(field, field) for field in fieldnames}
                writer.writerow(chinese_header)
                
                # 写入数据
                for operator in operators:
                    # 确保所有字段都存在
                    row_data = {}
                    for field in fieldnames:
                        row_data[field] = operator.get(field, '')
                    writer.writerow(row_data)
            
            return True
            
        except Exception as e:
            messagebox.showerror("错误", f"导出CSV失败: {str(e)}")
            return False
    
    def generate_template(self, file_path: str = None) -> bool:
        """生成CSV模板"""
        if file_path is None:
            file_path = filedialog.asksaveasfilename(
                title="保存CSV模板文件",
                defaultextension=".csv",
                filetypes=[("CSV 文件", "*.csv")]
            )
            if not file_path:
                return False
        
        try:
            # 创建示例数据
            template_data = [{
                'name': '示例干员',
                'class_type': '狙击',
                'hp': 1000,
                'atk': 500,
                'def': 100,
                'mdef': 0,
                'atk_speed': 1.0,
                'atk_type': '物伤',
                'cost': 15,
                'block_count': 1
            }]
            
            return self.export_to_csv(template_data, file_path)
            
        except Exception as e:
            messagebox.showerror("错误", f"生成CSV模板失败: {str(e)}")
            return False 