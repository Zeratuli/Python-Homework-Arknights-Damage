# chart_factory.py - 图表创建工厂

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd
from datetime import datetime
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入字体管理器
try:
    from ui.font_manager import FontManager
    FONT_MANAGER_AVAILABLE = True
except ImportError:
    FONT_MANAGER_AVAILABLE = False

# 设置中文字体支持Unicode字符
def setup_font_support():
    """设置支持Unicode字符的字体"""
    # 尝试多种支持Unicode的字体
    font_candidates = [
        'Microsoft YaHei',  # 微软雅黑，支持更多Unicode字符
        'SimHei',           # 黑体
        'DejaVu Sans',      # 开源字体，Unicode支持好
        'Arial Unicode MS', # Arial Unicode版本
        'Noto Sans CJK SC', # Google Noto字体
        'PingFang SC',      # 苹果系统字体
        'sans-serif'        # 系统默认
    ]
    
    # 检查可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    selected_font = 'sans-serif'  # 默认字体
    
    for font in font_candidates:
        if font in available_fonts:
            selected_font = font
            break
    
    # 设置matplotlib字体参数
    plt.rcParams['font.sans-serif'] = [selected_font] + font_candidates
    plt.rcParams['axes.unicode_minus'] = False
    
    return selected_font

# 初始化字体支持
CURRENT_FONT = setup_font_support()

class ChartFactory:
    """图表工厂类"""
    
    def __init__(self, root_widget=None):
        # 初始化字体管理器
        self.font_manager = None
        if FONT_MANAGER_AVAILABLE and root_widget:
            try:
                self.font_manager = FontManager(root_widget)
            except Exception as e:
                print(f"字体管理器初始化失败: {e}")
        
        self.color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#AED6F1', '#F1948A', '#D7BDE2',
            '#A9DFBF', '#F9E79F', '#AEB6BF', '#D5A6BD', '#85C1E9'
        ]
        
        # 简化：固定DPI设置
        self.figure_size = (12, 8)
        self.dpi = 300  # 固定高质量DPI
        
        # 设置matplotlib默认参数
        self._setup_matplotlib_defaults()
        
    def _setup_matplotlib_defaults(self):
        """设置matplotlib默认参数"""
        plt.rcParams['figure.dpi'] = self.dpi
        plt.rcParams['savefig.dpi'] = self.dpi
        plt.rcParams['axes.linewidth'] = 1.2
        plt.rcParams['lines.linewidth'] = 2.0
        
        # 字体大小设置 - 使用字体管理器或默认值
        if self.font_manager:
            plt.rcParams['font.size'] = self.font_manager.get_font_size('default')
        else:
            plt.rcParams['font.size'] = 10
    
    def get_font_size(self, font_type: str = 'default') -> int:
        """获取字体大小"""
        if self.font_manager:
            return self.font_manager.get_font_size(font_type)
        
        # 默认字体大小
        size_map = {
            'title': 14,
            'header': 12,
            'default': 10,
            'small': 8
        }
        return size_map.get(font_type, 10)
    
    def get_font_config(self, font_type: str = 'default') -> Dict[str, Any]:
        """获取字体配置"""
        if self.font_manager:
            family, size, weight = self.font_manager.get_font_config(font_type, CURRENT_FONT)
            return {
                'fontsize': size,
                'fontfamily': family,
                'fontweight': weight
            }
        
        # 默认配置
        return {
            'fontsize': self.get_font_size(font_type),
            'fontfamily': CURRENT_FONT,
            'fontweight': 'normal'
        }
    
    def set_title_with_font(self, ax: Axes, title: str, font_type: str = 'title', **kwargs):
        """设置带字体管理的标题"""
        font_config = self.get_font_config(font_type)
        font_config.update(kwargs)  # 允许覆盖配置
        ax.set_title(title, **font_config, pad=20)
    
    def set_labels_with_font(self, ax: Axes, xlabel: str = None, ylabel: str = None, font_type: str = 'default'):
        """设置带字体管理的坐标轴标签"""
        font_config = self.get_font_config(font_type)
        
        if xlabel:
            ax.set_xlabel(xlabel, **font_config)
        if ylabel:
            ax.set_ylabel(ylabel, **font_config)
    
    def get_color_for_index(self, index: int) -> str:
        """
        为指定索引获取颜色，如果超出调色板范围则生成新颜色
        """
        if index < len(self.color_palette):
            return self.color_palette[index]
        else:
            # 动态生成颜色
            import matplotlib.cm as cm
            colormap = cm.get_cmap('tab20')
            return colormap(index % 20)
    
    def create_line_chart(self, data: List[Tuple], title: str = "折线图", 
                         xlabel: str = "X轴", ylabel: str = "Y轴",
                         multiple_series: Optional[Dict[str, List[Tuple]]] = None) -> Figure:
        """
        创建折线图
        
        Args:
            data: 单条线的数据 [(x1, y1), (x2, y2), ...]
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            multiple_series: 多条线数据 {'series1': [(x,y)...], 'series2': [...]}
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        if multiple_series:
            for i, (series_name, series_data) in enumerate(multiple_series.items()):
                if series_data:
                    x_vals, y_vals = zip(*series_data)
                    color = self.get_color_for_index(i)
                    ax.plot(x_vals, y_vals, label=series_name, color=color, 
                           marker='o', markersize=4, linewidth=2)
            
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
        else:
            if data:
                x_vals, y_vals = zip(*data)
                ax.plot(x_vals, y_vals, color=self.get_color_for_index(0), 
                       marker='o', markersize=4, linewidth=2)
        
        self.set_title_with_font(ax, title)
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def create_damage_curve(self, operator_data: Dict[str, Any], 
                          max_defense: int = 1000, step: int = 25) -> Figure:
        """
        创建伤害-防御曲线图
        
        Args:
            operator_data: 干员数据字典
            max_defense: 最大防御值
            step: 步长
            
        Returns:
            matplotlib Figure对象
        """
        from core.damage_calculator import calculator
        
        # 生成曲线数据
        curve_data = calculator.get_damage_curve(operator_data, max_defense, step)
        
        # 计算破甲点
        armor_break_point = calculator.find_armor_break_point(operator_data.get('atk', 0))
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        if curve_data:
            x_vals, y_vals = zip(*curve_data)
            ax.plot(x_vals, y_vals, color=self.get_color_for_index(0), 
                   linewidth=3, label=f"{operator_data.get('name', '干员')} DPS")
            
            # 标注破甲点
            if armor_break_point > 0:
                # 找到破甲点对应的DPS值
                break_dps = None
                for defense, dps in curve_data:
                    if defense >= armor_break_point:
                        break_dps = dps
                        break
                
                if break_dps:
                    ax.axvline(x=armor_break_point, color='red', linestyle='--', 
                             label=f'破甲线 (防御:{armor_break_point})')
                    ax.plot(armor_break_point, break_dps, 'ro', markersize=8)
                    ax.annotate(f'破甲点\n({armor_break_point}, {break_dps:.1f})',
                              xy=(armor_break_point, break_dps),
                              xytext=(armor_break_point + 100, break_dps + 50),
                              arrowprops=dict(arrowstyle='->', color='red'),
                              fontsize=10, ha='center')
        
        self.set_title_with_font(ax, f"{operator_data.get('name', '干员')} - 伤害防御曲线")
        ax.set_xlabel("敌人防御力", fontsize=self.get_font_size('header'))
        ax.set_ylabel("DPS", fontsize=self.get_font_size('header'))
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def create_radar_chart(self, operator_data: List[Dict[str, Any]], 
                          attributes: List[str] = None) -> Figure:
        """
        创建雷达图
        
        Args:
            operator_data: 干员数据列表
            attributes: 属性列表
            
        Returns:
            matplotlib Figure对象
        """
        if not attributes:
            attributes = ['攻击力', '生命值', '防御力', 'DPS', '性价比']
        
        # 设置雷达图
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'), dpi=self.dpi)
        
        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(attributes), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        # 为每个干员绘制雷达图
        for i, operator in enumerate(operator_data):
            values = []
            
            # 归一化数据
            for attr in attributes:
                if attr == '攻击力':
                    values.append(operator.get('atk', 0) / 1000 * 100)
                elif attr == '生命值':
                    values.append(operator.get('hp', 0) / 5000 * 100)
                elif attr == '防御力':
                    values.append(operator.get('def', 0) / 1000 * 100)
                elif attr == 'DPS':
                    # 需要计算DPS
                    from core.damage_calculator import calculator
                    performance = calculator.calculate_operator_performance(operator)
                    values.append(performance.get('dps', 0) / 2000 * 100)
                elif attr == '性价比':
                    from core.damage_calculator import calculator
                    performance = calculator.calculate_operator_performance(operator)
                    values.append(performance.get('cost_efficiency', 0) / 100 * 100)
                else:
                    values.append(0)
            
            values += values[:1]  # 闭合图形
            
            color = self.get_color_for_index(i)
            ax.plot(angles, values, 'o-', linewidth=2, label=operator.get('name', f'干员{i+1}'), color=color)
            ax.fill(angles, values, alpha=0.25, color=color)
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(attributes)
        ax.set_ylim(0, 100)
        
        # 设置标题和图例
        self.set_title_with_font(ax, "干员属性雷达图")
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        return fig
    
    def create_pie_chart(self, data: Dict[str, float], title: str = "饼图") -> Figure:
        """
        创建饼图
        
        Args:
            data: 数据字典 {'标签1': 值1, '标签2': 值2, ...}
            title: 图表标题
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=(8, 8), dpi=self.dpi)
        
        labels = list(data.keys())
        sizes = list(data.values())
        colors = [self.get_color_for_index(i) for i in range(len(labels))]
        
        # 创建饼图
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                         startangle=90, explode=[0.05] * len(labels))
        
        # 美化文字
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(self.get_font_size('small'))
        
        self.set_title_with_font(ax, title)
        plt.tight_layout()
        
        return fig
    
    def create_heatmap(self, data: np.ndarray, row_labels: List[str], 
                      col_labels: List[str], title: str = "热力图") -> Figure:
        """
        创建热力图
        
        Args:
            data: 二维数据数组
            row_labels: 行标签
            col_labels: 列标签
            title: 图表标题
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # 创建热力图
        im = ax.imshow(data, cmap='RdYlBu_r', aspect='auto')
        
        # 设置标签
        ax.set_xticks(np.arange(len(col_labels)))
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_xticklabels(col_labels)
        ax.set_yticklabels(row_labels)
        
        # 旋转x轴标签
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # 添加数值标注
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                text = ax.text(j, i, f'{data[i, j]:.1f}', 
                             ha="center", va="center", color="black", fontweight='bold')
        
        self.set_title_with_font(ax, title)
        
        # 添加颜色条
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("数值", rotation=-90, va="bottom")
        
        plt.tight_layout()
        return fig
    
    def create_timeline_chart(self, timeline_data: Dict[str, List[Tuple[float, float]]], 
                            title: str = "时间轴伤害图") -> Figure:
        """
        创建时间轴伤害图
        
        Args:
            timeline_data: 时间轴数据 {'干员1': [(时间, 累计伤害), ...], ...}
            title: 图表标题
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        for i, (operator_name, data) in enumerate(timeline_data.items()):
            if data:
                times, damages = zip(*data)
                color = self.get_color_for_index(i)
                ax.plot(times, damages, label=operator_name, color=color, linewidth=2)
        
        self.set_title_with_font(ax, title)
        ax.set_xlabel("时间 (秒)", fontsize=self.get_font_size('header'))
        ax.set_ylabel("累计伤害", fontsize=self.get_font_size('header'))
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_comparison_bar_chart(self, comparison_data: Dict[str, Dict[str, float]], 
                                   title: str = "对比柱状图") -> Figure:
        """
        创建对比柱状图
        
        Args:
            comparison_data: 对比数据 {'干员1': {'DPS': 100, 'HPS': 50, ...}, ...}
            title: 图表标题
            
        Returns:
            matplotlib Figure对象
        """
        if not comparison_data:
            return self.create_empty_chart("暂无对比数据")
        
        # 准备数据
        operators = list(comparison_data.keys())
        metrics = list(next(iter(comparison_data.values())).keys())
        
        # 过滤掉值为0或极小的指标
        filtered_metrics = []
        for metric in metrics:
            max_value = max(comparison_data[op].get(metric, 0) for op in operators)
            if max_value > 0.1:  # 只保留有意义的指标
                filtered_metrics.append(metric)
        
        if not filtered_metrics:
            return self.create_empty_chart("暂无有效的对比数据")
        
        # 创建图表 - 使用更大的尺寸
        fig, ax = plt.subplots(figsize=(max(12, len(operators) * 2), 8), dpi=self.dpi)
        
        # 改进的分组柱状图布局
        x = np.arange(len(operators))
        total_width = 0.8
        bar_width = total_width / len(filtered_metrics)
        
        for i, metric in enumerate(filtered_metrics):
            metric_data = [comparison_data[op].get(metric, 0) for op in operators]
            
            # 计算条的位置，确保居中对齐
            offset = (i - len(filtered_metrics)/2 + 0.5) * bar_width
            x_pos = x + offset
            
            bars = ax.bar(x_pos, metric_data, bar_width * 0.9, 
                         label=metric, color=self.get_color_for_index(i),
                         alpha=0.8, edgecolor='white', linewidth=0.5)
            
            # 改进的数值标签 - 避免重叠
            for bar, value in zip(bars, metric_data):
                if value > 0:
                    height = bar.get_height()
                    # 根据条的高度调整标签位置
                    label_y = height + max(height * 0.01, 0.5)
                    ax.text(bar.get_x() + bar.get_width()/2., label_y,
                           f'{value:.1f}', ha='center', va='bottom', 
                           fontsize=self.get_font_size('small'), fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7))
        
        self.set_title_with_font(ax, title)
        ax.set_xlabel("干员", fontsize=self.get_font_size('header'))
        ax.set_ylabel("数值", fontsize=self.get_font_size('header'))
        ax.set_xticks(x)
        ax.set_xticklabels(operators, rotation=45, ha='right', fontsize=self.get_font_size('small'))
        
        # 改进图例显示
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=self.get_font_size('small'))
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # 自动调整Y轴范围
        all_values = [comparison_data[op].get(metric, 0) 
                     for op in operators for metric in filtered_metrics]
        if all_values:
            max_val = max(all_values)
            ax.set_ylim(0, max_val * 1.15)
        
        plt.tight_layout()
        return fig
    
    def create_empty_chart(self, message: str = "暂无数据") -> Figure:
        """
        创建空图表
        
        Args:
            message: 显示的消息
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        ax.text(0.5, 0.5, message, transform=ax.transAxes, 
                fontsize=self.get_font_size('title'), ha='center', va='center', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return fig
    
    def create_subplot_figure(self, chart_configs: List[Dict], 
                             rows: int = 2, cols: int = 2) -> Figure:
        """
        创建多子图的Figure
        
        Args:
            chart_configs: 图表配置列表
            rows: 行数
            cols: 列数
            
        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(rows, cols, figsize=(15, 10), dpi=self.dpi)
        
        if rows * cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for i, config in enumerate(chart_configs[:len(axes)]):
            ax = axes[i]
            chart_type = config.get('type', 'empty')
            
            if chart_type == 'line':
                self._create_line_subplot(ax, config)
            elif chart_type == 'bar':
                self._create_bar_subplot(ax, config)
            elif chart_type == 'pie':
                self._create_pie_subplot(ax, config)
            else:
                ax.text(0.5, 0.5, '暂无数据', transform=ax.transAxes,
                       ha='center', va='center', fontsize=self.get_font_size('small'))
                self.set_title_with_font(ax, config.get('title', '图表'), font_type='header')
        
        # 隐藏多余的子图
        for i in range(len(chart_configs), len(axes)):
            axes[i].axis('off')
        
        plt.tight_layout(pad=3.0)
        return fig
    
    def _create_line_subplot(self, ax: Axes, config: Dict):
        """在子图中创建折线图"""
        data = config.get('data', [])
        if data:
            x_vals, y_vals = zip(*data)
            ax.plot(x_vals, y_vals, color=self.get_color_for_index(0), marker='o', linewidth=2)
        
        self.set_title_with_font(ax, config.get('title', ''), font_type='header')
        self.set_labels_with_font(ax, config.get('xlabel', ''), config.get('ylabel', ''))
        ax.grid(True, alpha=0.3)
    
    def _create_bar_subplot(self, ax: Axes, config: Dict):
        """在子图中创建柱状图"""
        data = config.get('data', {})
        if data:
            labels = list(data.keys())
            values = list(data.values())
            bars = ax.bar(labels, values, color=[self.get_color_for_index(i) for i in range(len(labels))])
            
            # 添加数值标签
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}', ha='center', va='bottom', fontsize=self.get_font_size('small'))
        
        self.set_title_with_font(ax, config.get('title', ''), font_type='header')
        ax.tick_params(axis='x', rotation=45)
    
    def _create_pie_subplot(self, ax: Axes, config: Dict):
        """在子图中创建饼图"""
        data = config.get('data', {})
        if data:
            labels = list(data.keys())
            sizes = list(data.values())
            colors = [self.get_color_for_index(i) for i in range(len(labels))]
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        
        self.set_title_with_font(ax, config.get('title', ''), font_type='header')
    
    def create_timeline_damage_chart(self, timeline_data: Dict[str, List[Tuple[float, float]]], 
                                    duration: float = 60.0, title: str = "时间轴伤害分析") -> Figure:
        """
        创建时间轴伤害分析图表
        
        Args:
            timeline_data: 时间轴数据 {'干员1': [(时间, 累计伤害), ...], ...}
            duration: 分析时长（秒）
            title: 图表标题
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        if not timeline_data:
            return self.create_empty_chart("暂无时间轴数据")
        
        for i, (operator_name, data) in enumerate(timeline_data.items()):
            if data:
                times, cumulative_damages = zip(*data)
                color = self.get_color_for_index(i)
                ax.plot(times, cumulative_damages, label=operator_name, 
                       color=color, linewidth=2, marker='o', markersize=3)
        
        self.set_title_with_font(ax, title)
        ax.set_xlabel("时间 (秒)", fontsize=self.get_font_size('header'))
        ax.set_ylabel("累计伤害", fontsize=self.get_font_size('header'))
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 设置x轴范围
        ax.set_xlim(0, duration)
        
        plt.tight_layout()
        return fig
    
    def create_multi_operator_dps_bar_chart(self, dps_data: Dict[str, Dict[str, float]], 
                                          title: str = "多干员DPS对比") -> Figure:
        """
        创建多干员DPS对比柱状图
        
        Args:
            dps_data: DPS数据 {'干员1': {'DPS': 200, 'HPS': 100, ...}, ...}
            title: 图表标题
            
        Returns:
            matplotlib Figure对象
        """
        if not dps_data:
            return self.create_empty_chart("暂无DPS数据")
        
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # 准备数据
        operators = list(dps_data.keys())
        metrics = ['DPS', 'HPS', 'DPH', 'HPH']  # 主要指标
        
        # 过滤存在的指标
        available_metrics = []
        for metric in metrics:
            if any(metric in data for data in dps_data.values()):
                available_metrics.append(metric)
        
        if not available_metrics:
            return self.create_empty_chart("暂无有效的DPS数据")
        
        # 创建分组柱状图
        x = np.arange(len(operators))
        width = 0.8 / len(available_metrics)
        
        for i, metric in enumerate(available_metrics):
            metric_values = []
            for operator in operators:
                value = dps_data[operator].get(metric, 0)
                metric_values.append(value)
            
            bars = ax.bar(x + i * width - (len(available_metrics) - 1) * width / 2, 
                         metric_values, width, 
                         label=metric, color=self.get_color_for_index(i))
            
            # 添加数值标签
            for bar, value in zip(bars, metric_values):
                if value > 0:  # 只在有值时显示标签
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{value:.1f}', ha='center', va='bottom', fontsize=self.get_font_size('small'))
        
        self.set_title_with_font(ax, title)
        ax.set_xlabel("干员", fontsize=self.get_font_size('header'))
        ax.set_ylabel("数值", fontsize=self.get_font_size('header'))
        ax.set_xticks(x)
        ax.set_xticklabels(operators, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return fig

    def smart_auto_adjust_axes(self, figure, chart_type='default'):
        """
        智能调整图表坐标轴 - 针对不同图表类型的优化
        
        Args:
            figure: matplotlib Figure对象
            chart_type: 图表类型
        """
        try:
            # 导入缩放管理器
            from utils.chart_zoom_manager import ChartZoomManager
            
            zoom_manager = ChartZoomManager()
            return zoom_manager.auto_fit_chart(figure, chart_type)
            
        except Exception as e:
            print(f"智能调整坐标轴失败: {e}")
            # 回退到原有的调整方法
            for ax in figure.get_axes():
                self._legacy_auto_adjust_axes(ax)
            return False
    
    def apply_zoom_to_chart(self, figure, zoom_params):
        """
        应用缩放参数到图表
        
        Args:
            figure: matplotlib Figure对象
            zoom_params: 缩放参数字典
        """
        try:
            axes_list = figure.get_axes()
            
            for i, ax in enumerate(axes_list):
                if i < len(zoom_params.get('axes_limits', [])):
                    limits = zoom_params['axes_limits'][i]
                    
                    # 应用X轴限制
                    if 'xlim' in limits:
                        ax.set_xlim(limits['xlim'])
                    
                    # 应用Y轴限制
                    if 'ylim' in limits:
                        ax.set_ylim(limits['ylim'])
                    
                    # 应用其他样式设置
                    if 'grid' in limits:
                        ax.grid(limits['grid'], alpha=0.3)
            
            # 刷新图表
            figure.canvas.draw_idle()
            return True
            
        except Exception as e:
            print(f"应用缩放参数失败: {e}")
            return False
    
    def _legacy_auto_adjust_axes(self, ax):
        """原有的坐标轴调整方法 - 作为回退选项"""
        try:
            # 获取所有数据的范围
            x_data = []
            y_data = []
            
            for line in ax.get_lines():
                x_data.extend(line.get_xdata())
                y_data.extend(line.get_ydata())
            
            for collection in ax.collections:
                if hasattr(collection, 'get_offsets'):
                    offsets = collection.get_offsets()
                    if len(offsets) > 0:
                        x_data.extend(offsets[:, 0])
                        y_data.extend(offsets[:, 1])
            
            for patch in ax.patches:
                if hasattr(patch, 'get_x') and hasattr(patch, 'get_width'):
                    x_data.extend([patch.get_x(), patch.get_x() + patch.get_width()])
                if hasattr(patch, 'get_y') and hasattr(patch, 'get_height'):
                    y_data.extend([patch.get_y(), patch.get_y() + patch.get_height()])
            
            # 设置合适的坐标轴范围
            if x_data:
                x_min, x_max = min(x_data), max(x_data)
                x_range = x_max - x_min
                if x_range > 0:
                    x_margin = x_range * 0.05
                    ax.set_xlim(x_min - x_margin, x_max + x_margin)
            
            if y_data:
                y_min, y_max = min(y_data), max(y_data)
                y_range = y_max - y_min
                if y_range > 0:
                    y_margin = y_range * 0.05
                    ax.set_ylim(max(0, y_min - y_margin), y_max + y_margin)
                elif y_max > 0:
                    ax.set_ylim(0, y_max * 1.1)
            
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            print(f"原有坐标轴调整失败: {e}")

    def get_chart_zoom_params(self, figure):
        """
        获取当前图表的缩放参数
        
        Args:
            figure: matplotlib Figure对象
            
        Returns:
            缩放参数字典
        """
        try:
            zoom_params = {
                'axes_limits': [],
                'figure_size': figure.get_size_inches().tolist(),
                'dpi': figure.dpi
            }
            
            for ax in figure.get_axes():
                ax_params = {
                    'xlim': ax.get_xlim(),
                    'ylim': ax.get_ylim(),
                    'title': ax.get_title(),
                    'xlabel': ax.get_xlabel(),
                    'ylabel': ax.get_ylabel(),
                    'grid': ax.get_gridspec() is not None
                }
                zoom_params['axes_limits'].append(ax_params)
            
            return zoom_params
            
        except Exception as e:
            print(f"获取缩放参数失败: {e}")
            return {}
    
    def optimize_chart_for_export(self, figure, export_dpi=300):
        """
        为导出优化图表显示
        
        Args:
            figure: matplotlib Figure对象
            export_dpi: 导出DPI
        """
        try:
            # 设置高DPI
            figure.set_dpi(export_dpi)
            
            # 优化字体大小
            for ax in figure.get_axes():
                # 调整标题字体
                title = ax.get_title()
                if title:
                    ax.set_title(title, fontsize=self.get_font_size('title'), fontweight='bold')
                
                # 调整坐标轴标签字体
                ax.set_xlabel(ax.get_xlabel(), fontsize=self.get_font_size('header'))
                ax.set_ylabel(ax.get_ylabel(), fontsize=self.get_font_size('header'))
                
                # 调整刻度标签字体
                ax.tick_params(axis='both', which='major', labelsize=self.get_font_size('small'))
                
                # 调整图例字体
                legend = ax.get_legend()
                if legend:
                    legend.set_fontsize(self.get_font_size('small'))
            
            # 调整布局
            figure.tight_layout(pad=3.0)
            
        except Exception as e:
            print(f"优化图表导出失败: {e}")

# 创建全局图表工厂实例（用于测试和向后兼容）
# 注意：在实际应用中应该传入root_widget参数以获得更好的字体支持
chart_factory = ChartFactory() 