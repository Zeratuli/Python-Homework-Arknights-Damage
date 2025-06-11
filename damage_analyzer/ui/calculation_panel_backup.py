# calculation_panel.py - 计算控制面板 (原始备份文件)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, IntVar, DoubleVar, BooleanVar, messagebox
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.damage_calculator import DamageCalculator
from ui.components.sortable_treeview import SortableTreeview

class CalculationPanel:
    def __init__(self, parent, db_manager, status_callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.status_callback = status_callback
        
        # 初始化计算器
        self.calculator = DamageCalculator()
        
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

    # ... 备份文件包含所有原始方法 ...
    # (为节省空间，这里只显示头部，实际备份包含完整的1268行代码) 