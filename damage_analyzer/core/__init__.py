"""
Core模块初始化
包含伤害计算等核心功能
"""

# 导入核心组件
from .damage_calculator import DamageCalculator, calculator

__all__ = [
    'DamageCalculator',
    'DataManager',
    'calculator'
] 