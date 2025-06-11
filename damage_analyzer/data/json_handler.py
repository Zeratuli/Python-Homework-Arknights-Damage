# json_handler.py - 简化的JSON数据处理模块

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from tkinter import filedialog, messagebox
import logging

logger = logging.getLogger(__name__)

class JsonHandler:
    """
    简化的JSON处理器，支持干员数据的导入、导出与字段映射、类型校验。
    主要功能：
    - 从JSON文件导入干员数据，支持多种字段命名和嵌套格式
    - 导出干员数据为JSON文件
    - 字段自动映射与类型转换
    """
    
    def __init__(self):
        # 必要字段和可选字段
        self.required_fields = ['name', 'class_type', 'hp', 'atk', 'atk_type', 'atk_speed']
        self.optional_fields = ['def', 'mdef', 'cost', 'block_count']
    
    def import_from_json(self, file_path: str = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        从JSON文件导入干员数据。
        支持用户交互选择文件，自动处理数组或单对象格式。
        Args:
            file_path: JSON文件路径，可选
        Returns:
            (干员数据列表, 错误信息列表)
        """
        if file_path is None:
            file_path = filedialog.askopenfilename(
                title="选择JSON文件",
                filetypes=[("JSON 文件", "*.json")]
            )
            if not file_path:
                return [], []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            operators = []
            errors = []
            operator_id = 1  # ID从1开始
            # 支持数组或单对象
            if isinstance(data, list):
                for i, operator_data in enumerate(data):
                    try:
                        parsed = self._parse_operator(operator_data)
                        if parsed:
                            parsed['id'] = operator_id  # 分配顺序ID
                            operators.append(parsed)
                            operator_id += 1
                    except Exception as e:
                        errors.append(f"索引{i}: {str(e)}")
            elif isinstance(data, dict):
                try:
                    parsed = self._parse_operator(data)
                    if parsed:
                        parsed['id'] = operator_id
                        operators.append(parsed)
                except Exception as e:
                    errors.append(f"文件解析错误: {str(e)}")
            logger.info(f"JSON导入完成: 成功{len(operators)}个，错误{len(errors)}个")
            return operators, errors
        except Exception as e:
            return [], [f"读取JSON文件失败: {str(e)}"]
    
    def _parse_operator(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析单个干员数据，支持嵌套form格式和多种字段命名。
        字段自动映射，缺失必要字段时报错。
        Args:
            data: 干员原始数据字典
        Returns:
            干员信息字典
        Raises:
            ValueError: 缺少必要字段或类型转换失败
        """
        operator = {}
        # 检查是否是嵌套格式 (有form字段)
        if 'form' in data and isinstance(data['form'], dict):
            source_data = data['form']
        else:
            source_data = data
        # 字段映射表 - 兼容不同命名
        field_mapping = {
            'name': ['name', 'id'],
            'class_type': ['class_type', 'class'],
            'hp': ['hp', 'health'],
            'atk': ['atk', 'attack', 'damage'],
            'def': ['def', 'defense'],
            'mdef': ['mdef', 'magic_defense', 'resist'],
            'atk_speed': ['atk_speed', 'attack_speed', 'speed'],
            'atk_type': ['atk_type', 'attack_type', 'damage_type'],
            'cost': ['cost', 'deploy_cost'],
            'block_count': ['block_count', 'block']
        }
        for target_field, possible_fields in field_mapping.items():
            for field in possible_fields:
                if field in source_data:
                    operator[target_field] = source_data[field]
                    break
        # 特殊处理：如果没有name但有id字段作为名称
        if 'name' not in operator and 'id' in source_data:
            operator['name'] = source_data['id']
        # 检查必要字段
        required_fields = ['name', 'class_type', 'hp', 'atk', 'atk_speed']
        for field in required_fields:
            if field not in operator:
                available_fields = list(source_data.keys())
                raise ValueError(f"缺少必要字段: {field}。可用字段: {available_fields}")
        # 设置默认值
        operator.setdefault('def', 0)
        operator.setdefault('mdef', 0)
        operator.setdefault('cost', 10)
        operator.setdefault('block_count', 1)
        operator.setdefault('atk_type', '物伤')
        # 类型转换与校验
        try:
            operator['hp'] = int(float(operator['hp']))
            operator['atk'] = int(float(operator['atk']))
            operator['def'] = int(float(operator.get('def', 0)))
            operator['mdef'] = int(float(operator.get('mdef', 0)))
            operator['atk_speed'] = float(operator['atk_speed'])
            operator['cost'] = int(float(operator.get('cost', 10)))
            operator['block_count'] = int(float(operator.get('block_count', 1)))
        except (ValueError, TypeError) as e:
            raise ValueError(f"数据类型转换失败: {e}")
        return operator
    
    def export_to_json(self, operators: List[Dict[str, Any]], file_path: str = None) -> bool:
        """
        导出干员数据到JSON文件。
        支持用户交互选择保存路径。
        Args:
            operators: 干员数据列表
            file_path: 保存路径，可选
        Returns:
            bool: 是否导出成功
        """
        if file_path is None:
            file_path = filedialog.asksaveasfilename(
                title="保存JSON文件",
                defaultextension=".json",
                filetypes=[("JSON 文件", "*.json")]
            )
            if not file_path:
                return False
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(operators, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            messagebox.showerror("错误", f"导出JSON失败: {str(e)}")
            return False 