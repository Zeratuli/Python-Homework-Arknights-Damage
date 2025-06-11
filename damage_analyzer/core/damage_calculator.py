# damage_calculator.py - 明日方舟伤害计算核心引擎
"""
明日方舟伤害计算核心引擎

本模块实现了明日方舟游戏中的核心伤害计算逻辑，包括：
- 物理伤害计算（考虑防御力和保底伤害）
- 法术伤害计算（考虑法术抗性和保底伤害）
- DPS/DPH性能指标计算
- 破甲线分析
- 伤害曲线生成
- 时间轴伤害分析

算法基于明日方舟官方伤害计算公式：
- 物理伤害 = max(攻击力 - 防御力, 攻击力 × 5%)
- 法术伤害 = 攻击力 × (1 - 法抗%) 且不低于攻击力 × 5%

作者: Zhengziyi
版本: 1.0.0
"""

import math
from typing import Dict, List, Tuple, Optional, Any

class DamageCalculator:
    """
    明日方舟伤害计算引擎
    
    负责处理所有与伤害计算相关的核心逻辑，包括单次伤害、DPS计算、
    性能分析等功能。所有计算都基于明日方舟的官方伤害公式。
    
    Attributes:
        min_damage_rate (float): 保底伤害比例，固定为5%（0.05）
    
    Example:
        >>> calculator = DamageCalculator()
        >>> damage = calculator.calculate_physical_damage(500, 300)
        >>> print(f"物理伤害: {damage}")
    """
    
    def __init__(self):
        """
        初始化伤害计算器
        
        设置保底伤害比例为5%，这是明日方舟游戏中的固定机制，
        确保即使在极高防御/法抗情况下也能造成最低伤害。
        """
        # 明日方舟保底伤害机制：无论防御多高，至少造成攻击力5%的伤害
        self.min_damage_rate = 0.05
    
    def calculate_physical_damage(self, atk: int, defense: int, hit_count: float = 1.0) -> float:
        """
        计算物理伤害
        
        基于明日方舟物理伤害公式：max(攻击力-防御力, 攻击力×5%) × 打数
        当攻击力低于或等于防御力时，触发保底伤害机制。
        
        Args:
            atk (int): 干员攻击力，通常范围100-2000
            defense (int): 敌人防御力，通常范围0-1500
            hit_count (float, optional): 攻击打数，支持小数. Defaults to 1.0.
        
        Returns:
            float: 计算后的物理伤害值，保证非负
        
        Example:
            >>> calc = DamageCalculator()
            >>> # 高攻击vs低防御：正常伤害
            >>> damage1 = calc.calculate_physical_damage(500, 200)  # 返回 300.0
            >>> # 低攻击vs高防御：保底伤害
            >>> damage2 = calc.calculate_physical_damage(300, 400)  # 返回 15.0 (300*0.05)
        """
        # 输入验证：攻击力必须为正数
        if atk <= 0:
            return 0.0
            
        # 步骤1：计算基础伤害（攻击力减去防御力）
        base_damage = atk - defense
        
        # 步骤2：计算保底伤害（攻击力的5%）
        min_damage = atk * self.min_damage_rate
        
        # 步骤3：取较大值，确保至少造成保底伤害
        damage_per_hit = max(base_damage, min_damage)
        
        # 步骤4：乘以打数（支持多段攻击）
        total_damage = damage_per_hit * hit_count
        
        # 确保返回值非负
        return max(0.0, total_damage)
    
    def calculate_magical_damage(self, atk: int, magic_resist: float, hit_count: float = 1.0) -> float:
        """
        计算法术伤害
        
        基于明日方舟法术伤害公式：攻击力×(1-法抗%) × 打数
        当法抗过高时同样触发保底伤害机制。
        
        Args:
            atk (int): 干员攻击力，通常范围100-2000
            magic_resist (float): 敌人法术抗性百分比，如30表示30%法抗
            hit_count (float, optional): 攻击打数. Defaults to 1.0.
        
        Returns:
            float: 计算后的法术伤害值，保证非负
        
        Example:
            >>> calc = DamageCalculator()
            >>> # 正常法抗情况
            >>> damage1 = calc.calculate_magical_damage(500, 30)  # 返回 350.0 (500*0.7)
            >>> # 极高法抗触发保底
            >>> damage2 = calc.calculate_magical_damage(500, 95)  # 返回 25.0 (500*0.05)
        """
        # 输入验证：攻击力必须为正数
        if atk <= 0:
            return 0.0
            
        # 步骤1：将百分比法抗转换为小数（30% -> 0.3）
        resist_rate = magic_resist / 100.0
        
        # 步骤2：根据法抗计算伤害
        if resist_rate >= 1.0:  
            # 法抗大于等于100%时直接触发保底伤害
            damage_per_hit = atk * self.min_damage_rate
        else:
            # 正常情况：攻击力 × (1 - 法抗比例)
            damage_per_hit = atk * (1 - resist_rate)
            
            # 步骤3：确保不低于保底伤害
            min_damage = atk * self.min_damage_rate
            damage_per_hit = max(damage_per_hit, min_damage)
        
        # 步骤4：乘以打数
        total_damage = damage_per_hit * hit_count
        
        # 确保返回值非负
        return max(0.0, total_damage)
    
    def calculate_dps(self, damage_per_hit: float, attack_speed: float) -> float:
        """
        计算每秒伤害输出（DPS）
        
        DPS = 单次伤害 × 攻击速度，是衡量干员输出能力的核心指标。
        
        Args:
            damage_per_hit (float): 单次攻击伤害
            attack_speed (float): 攻击速度（次/秒），通常范围0.5-3.0
        
        Returns:
            float: 每秒伤害输出值
        
        Note:
            攻击速度为0或负数时返回0，避免除零错误
        """
        # 输入验证：攻击速度必须为正数
        if attack_speed <= 0:
            return 0.0
            
        # 计算DPS：单次伤害 × 攻击频率
        return damage_per_hit * attack_speed
    
    def calculate_dph(self, atk: int, atk_type: str, defense: int, magic_resist: float, hit_count: float = 1.0) -> float:
        """
        计算每次攻击伤害（DPH）
        
        根据攻击类型自动选择物理或法术伤害计算方式。
        
        Args:
            atk (int): 攻击力
            atk_type (str): 攻击类型，'物伤'/'物理伤害'或'法伤'/'法术伤害'
            defense (int): 敌人防御力
            magic_resist (float): 敌人法术抗性
            hit_count (float, optional): 打数. Defaults to 1.0.
        
        Returns:
            float: 每次攻击的伤害值
        
        Note:
            不支持的攻击类型将返回0
        """
        # 根据攻击类型分发到对应的计算方法 - 支持简写和完整格式
        if atk_type in ['物伤', '物理伤害']:
            return self.calculate_physical_damage(atk, defense, hit_count)
        elif atk_type in ['法伤', '法术伤害']:
            return self.calculate_magical_damage(atk, magic_resist, hit_count)
        else:
            # 未知攻击类型，返回0并可能需要记录警告
            return 0.0
    
    def find_armor_break_point(self, attack_power: int) -> int:
        """
        计算破甲线
        
        破甲线是指当敌人防御力等于攻击力95%时的防御值，
        超过此值后伤害将显著下降至保底伤害。
        
        Args:
            attack_power (int): 干员攻击力
        
        Returns:
            int: 破甲线防御值
        
        Example:
            >>> calc = DamageCalculator()
            >>> break_point = calc.find_armor_break_point(500)  # 返回 475
            >>> # 意味着敌人防御力超过475时，该干员伤害大幅下降
        """
        # 破甲线 = 攻击力 × 95%
        # 这是因为当防御力 = 攻击力×95%时，伤害 = 攻击力×5%（保底）
        return int(attack_power * 0.95)
    
    def get_damage_curve(self, operator_data: Dict[str, Any], max_defense: int = 1000, step: int = 25) -> List[Tuple[int, float]]:
        """
        生成伤害-防御曲线数据
        
        计算干员在不同敌人防御力下的DPS表现，用于绘制伤害曲线图。
        
        Args:
            operator_data (Dict[str, Any]): 干员数据字典，包含攻击力、攻击类型等
            max_defense (int, optional): 最大防御值. Defaults to 1000.
            step (int, optional): 计算步长. Defaults to 25.
        
        Returns:
            List[Tuple[int, float]]: 曲线数据列表 [(防御值, DPS), ...]
        
        Note:
            步长越小曲线越平滑，但计算量也越大
        """
        curve_data = []
        
        # 遍历防御值范围，计算每个点的DPS
        for defense in range(0, max_defense + 1, step):
            # 计算该防御值下的干员性能
            performance = self.calculate_operator_performance(operator_data, defense, 0)
            dps = performance.get('dps', 0)
            
            # 添加数据点到曲线
            curve_data.append((defense, dps))
            
        return curve_data
    
    def calculate_timeline_damage(self, operator_data: Dict[str, Any], duration: float, enemy_def: int = 0, enemy_mdef: float = 0) -> List[Tuple[float, float]]:
        """
        计算时间轴累计伤害
        
        生成干员在指定时间段内的累计伤害数据，用于时间轴分析。
        
        Args:
            operator_data (Dict[str, Any]): 干员数据字典
            duration (float): 分析持续时间（秒）
            enemy_def (int, optional): 敌人防御力. Defaults to 0.
            enemy_mdef (float, optional): 敌人法抗. Defaults to 0.
        
        Returns:
            List[Tuple[float, float]]: 时间轴数据 [(时间, 累计伤害), ...]
        
        Note:
            数据点间隔为5秒，可根据需要调整精度
        """
        timeline = []
        
        # 计算该敌人配置下的DPS
        performance = self.calculate_operator_performance(operator_data, enemy_def, enemy_mdef)
        dps = performance.get('dps', 0)
        
        # 生成时间点（每5秒一个数据点）
        time_points = [i for i in range(0, int(duration) + 1, 5)]
        
        # 计算每个时间点的累计伤害
        for time_point in time_points:
            cumulative_damage = dps * time_point
            timeline.append((time_point, cumulative_damage))
            
        return timeline

    def calculate_operator_performance(self, operator_data: Dict[str, Any], enemy_def: int = 0, enemy_mdef: float = 0) -> Dict[str, float]:
        """
        计算干员综合性能指标
        
        基于干员数据和敌人配置，计算包括DPS、DPH、破甲线、性价比等
        在内的全面性能指标。
        
        Args:
            operator_data (Dict[str, Any]): 干员数据字典，必须包含基础属性
            enemy_def (int, optional): 敌人防御力. Defaults to 0.
            enemy_mdef (float, optional): 敌人法抗. Defaults to 0.
        
        Returns:
            Dict[str, float]: 性能指标字典，包含以下键值：
                - dph: 每次攻击伤害
                - dps: 每秒伤害输出
                - armor_break_point: 破甲线
                - cost_efficiency: 性价比（DPS/部署费用）
                - hps: 每秒治疗量（医疗干员）
                - hph: 每次治疗量（医疗干员）
                - survivability: 生存能力指标
        
        Note:
            对于缺失的数据会使用默认值，确保计算的稳定性
        """
        results = {}
        
        # 数据提取与默认值处理
        atk = operator_data.get('atk', 0) or 0  # 攻击力，默认0
        atk_type = operator_data.get('atk_type', '物伤')  # 攻击类型，默认物伤
        atk_speed = operator_data.get('atk_speed', 1.0) or 1.0  # 攻击速度，默认1.0
        hit_count = operator_data.get('hit_count', 1.0) or 1.0  # 打数，默认1.0
        cost = operator_data.get('cost', 1) or 1  # 部署费用，默认1（避免除零）
        class_type = operator_data.get('class_type', '')  # 职业类型
        heal_amount = operator_data.get('heal_amount', 0) or 0  # 治疗量
        
        # 核心伤害指标计算
        dph = self.calculate_dph(atk, atk_type, enemy_def, enemy_mdef, hit_count)
        results['dph'] = dph
        
        # DPS计算：每次伤害 × 攻击速度
        dps = self.calculate_dps(dph, atk_speed)
        results['dps'] = dps
        
        # 破甲线分析
        results['armor_break_point'] = self.find_armor_break_point(atk)
        
        # 性价比计算：DPS除以部署费用
        results['cost_efficiency'] = dps / max(cost, 1)
        
        # 治疗相关指标初始化
        results['hps'] = 0.0  # 每秒治疗量
        results['hph'] = 0.0  # 每次治疗量
        
        # 医疗干员特殊处理
        if class_type == '医疗' and heal_amount > 0:
            # 计算治疗性能指标
            results['hps'] = heal_amount * atk_speed  # 每秒治疗量
            results['hph'] = heal_amount * hit_count   # 每次治疗量
        
        # 生存能力计算
        hp = operator_data.get('hp', 0) or 0  # 生命值
        defense = operator_data.get('def', 0) or 0  # 防御力
        
        # 简化的生存能力公式：生命值 × (1 + 防御力/100)
        # 这里假设防御力每100点提供100%的有效生命值
        results['survivability'] = hp * (1 + defense / 100)
        
        return results

    def calculate_cumulative_damage(self, operator_data: Dict[str, Any], time_seconds: float, enemy_def: int = 0, enemy_mdef: float = 0) -> float:
        """
        计算指定时间点的累计伤害
        
        基于DPS计算干员在特定时间点造成的总伤害量。
        
        Args:
            operator_data (Dict[str, Any]): 干员数据字典
            time_seconds (float): 目标时间点（秒）
            enemy_def (int, optional): 敌人防御力. Defaults to 0.
            enemy_mdef (float, optional): 敌人法抗. Defaults to 0.
        
        Returns:
            float: 累计伤害值
        
        Note:
            时间为0或负数时返回0
        """
        # 输入验证：时间必须为正数
        if time_seconds <= 0:
            return 0.0
            
        # 计算DPS
        performance = self.calculate_operator_performance(operator_data, enemy_def, enemy_mdef)
        dps = performance.get('dps', 0)
        
        # 累计伤害 = DPS × 时间
        return dps * time_seconds

# 全局计算器实例
# 提供单例模式的计算器，避免重复初始化
calculator = DamageCalculator() 