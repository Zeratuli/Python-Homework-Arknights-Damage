#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证所有UI和计算修改是否正确应用
"""

import os
import sys

def verify_ui_changes():
    """验证UI修改"""
    print("=== 验证UI样式修改 ===")
    
    # 检查main_window.py中的Apple.TCombobox样式
    main_window_path = "damage_analyzer/ui/main_window.py"
    if os.path.exists(main_window_path):
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "Apple.TCombobox" in content:
                print("✅ main_window.py: Apple.TCombobox样式已添加")
            else:
                print("❌ main_window.py: 缺少Apple.TCombobox样式")
    
    # 检查operator_editor.py中的样式应用
    operator_editor_path = "damage_analyzer/ui/operator_editor.py"
    if os.path.exists(operator_editor_path):
        with open(operator_editor_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'style="Apple.TCombobox"' in content:
                print("✅ operator_editor.py: Combobox样式已应用")
            else:
                print("❌ operator_editor.py: Combobox样式未应用")
    
    # 检查chart_comparison_panel.py中的样式应用
    chart_panel_path = "damage_analyzer/ui/chart_comparison_panel.py"
    if os.path.exists(chart_panel_path):
        with open(chart_panel_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'style="Apple.TCombobox"' in content:
                print("✅ chart_comparison_panel.py: Combobox样式已应用")
            else:
                print("❌ chart_comparison_panel.py: Combobox样式未应用")

def verify_damage_calculation():
    """验证伤害计算修改"""
    print("\n=== 验证伤害计算修改 ===")
    
    chart_panel_path = "damage_analyzer/ui/chart_comparison_panel.py"
    if os.path.exists(chart_panel_path):
        with open(chart_panel_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查保底伤害计算
            if "min_damage = total_attack * 0.05" in content:
                count = content.count("min_damage = total_attack * 0.05")
                print(f"✅ chart_comparison_panel.py: 保底伤害5%计算已修复 ({count}处)")
            else:
                print("❌ chart_comparison_panel.py: 保底伤害5%计算未修复")
            
            # 检查max函数的使用
            if "max(base_damage, min_damage)" in content:
                count = content.count("max(base_damage, min_damage)")
                print(f"✅ chart_comparison_panel.py: 保底伤害逻辑已修复 ({count}处)")
            else:
                print("❌ chart_comparison_panel.py: 保底伤害逻辑未修复")

def verify_core_calculator():
    """验证核心计算器"""
    print("\n=== 验证核心计算器 ===")
    
    calculator_path = "damage_analyzer/core/damage_calculator.py"
    if os.path.exists(calculator_path):
        with open(calculator_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if "min_damage_rate" in content and "0.05" in content:
                print("✅ damage_calculator.py: 核心计算器保底伤害正确")
            else:
                print("❌ damage_calculator.py: 核心计算器可能有问题")
    else:
        print("❌ 未找到damage_calculator.py")

def main():
    print("🔍 开始验证所有修改...")
    print("=" * 50)
    
    verify_ui_changes()
    verify_damage_calculation()
    verify_core_calculator()
    
    print("\n" + "=" * 50)
    print("验证完成！")

if __name__ == "__main__":
    main() 