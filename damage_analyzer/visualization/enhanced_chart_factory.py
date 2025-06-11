# enhanced_chart_factory.py - 增强的图表工厂类

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd
from datetime import datetime
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

# 继承原有的图表工厂
from .chart_factory import ChartFactory

class EnhancedChartFactory(ChartFactory):
    """增强的图表工厂类"""
    
    def __init__(self, root_widget=None):
        super().__init__(root_widget)
        
        # 现代化配色方案
        self.modern_color_schemes = {
            'gradient_blues': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3'],
            'gradient_greens': ['#E8F5E8', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50'],
            'gradient_oranges': ['#FFF3E0', '#FFE0B2', '#FFCC80', '#FFB74D', '#FFA726', '#FF9800'],
            'vibrant_mix': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'],
            'professional': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
            'pastel': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFDFBA', '#E0BBE4']
        }
        
        # 图表模板配置
        self.chart_templates = {
            'modern': {
                'figure_style': {'facecolor': 'white', 'edgecolor': 'none'},
                'grid_style': {'alpha': 0.3, 'linestyle': '-', 'linewidth': 0.8},
                'title_style': {'fontsize': 14, 'fontweight': 'bold', 'pad': 20},
                'label_style': {'fontsize': 12},
                'tick_style': {'labelsize': 10}
            },
            'minimal': {
                'figure_style': {'facecolor': '#FAFAFA', 'edgecolor': 'none'},
                'grid_style': {'alpha': 0.2, 'linestyle': '--', 'linewidth': 0.5},
                'title_style': {'fontsize': 13, 'fontweight': 'normal', 'pad': 15},
                'label_style': {'fontsize': 11},
                'tick_style': {'labelsize': 9}
            },
            'dark': {
                'figure_style': {'facecolor': '#2E2E2E', 'edgecolor': 'none'},
                'grid_style': {'alpha': 0.4, 'linestyle': '-', 'linewidth': 0.8, 'color': 'white'},
                'title_style': {'fontsize': 14, 'fontweight': 'bold', 'pad': 20, 'color': 'white'},
                'label_style': {'fontsize': 12, 'color': 'white'},
                'tick_style': {'labelsize': 10, 'colors': 'white'}
            }
        }
        
        # 设置默认模板
        self.current_template = 'modern'
    
    def set_template(self, template_name: str):
        """设置图表模板"""
        if template_name in self.chart_templates:
            self.current_template = template_name
    
    def get_color_scheme(self, scheme_name: str = 'vibrant_mix') -> List[str]:
        """获取配色方案"""
        return self.modern_color_schemes.get(scheme_name, self.color_palette)
    
    def apply_template_style(self, fig: Figure, ax: Axes, title: str = ""):
        """应用模板样式"""
        template = self.chart_templates[self.current_template]
        
        # 应用图形样式
        for key, value in template['figure_style'].items():
            setattr(fig, key, value)
        
        # 应用标题样式
        if title:
            ax.set_title(title, **template['title_style'])
        
        # 应用网格样式
        ax.grid(True, **template['grid_style'])
        
        # 应用刻度样式
        ax.tick_params(**template['tick_style'])
    
    def create_area_chart(self, data: List[Tuple], title: str = "面积图", 
                         xlabel: str = "X轴", ylabel: str = "Y轴",
                         multiple_series: Optional[Dict[str, List[Tuple]]] = None,
                         stacked: bool = False) -> Figure:
        """
        创建面积图
        
        Args:
            data: 单条线的数据 [(x1, y1), (x2, y2), ...]
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            multiple_series: 多条线数据
            stacked: 是否堆叠
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        colors = self.get_color_scheme('gradient_blues')
        
        if multiple_series:
            previous_y = None
            for i, (series_name, series_data) in enumerate(multiple_series.items()):
                if series_data:
                    x_vals, y_vals = zip(*series_data)
                    color = colors[i % len(colors)]
                    
                    if stacked and previous_y is not None:
                        # 堆叠显示
                        combined_y = [y + py for y, py in zip(y_vals, previous_y)]
                        ax.fill_between(x_vals, previous_y, combined_y, 
                                      label=series_name, color=color, alpha=0.7)
                        previous_y = combined_y
                    else:
                        # 独立显示
                        ax.fill_between(x_vals, 0, y_vals, 
                                      label=series_name, color=color, alpha=0.7)
                        if previous_y is None:
                            previous_y = y_vals
            
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
        else:
            if data:
                x_vals, y_vals = zip(*data)
                ax.fill_between(x_vals, 0, y_vals, color=colors[0], alpha=0.7)
        
        self.apply_template_style(fig, ax, title)
        ax.set_xlabel(xlabel, **self.chart_templates[self.current_template]['label_style'])
        ax.set_ylabel(ylabel, **self.chart_templates[self.current_template]['label_style'])
        
        return fig
    
    def create_stacked_bar_chart(self, data: Dict[str, Dict[str, float]], 
                                title: str = "堆叠柱状图") -> Figure:
        """
        创建堆叠柱状图
        
        Args:
            data: 数据格式 {'category1': {'series1': value1, 'series2': value2}, ...}
            title: 图表标题
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        colors = self.get_color_scheme('professional')
        
        # 转换数据格式
        df = pd.DataFrame(data).T
        df.plot(kind='bar', stacked=True, ax=ax, color=colors[:len(df.columns)])
        
        self.apply_template_style(fig, ax, title)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return fig
    
    def create_box_plot(self, data: Dict[str, List[float]], title: str = "箱线图") -> Figure:
        """
        创建箱线图
        
        Args:
            data: 数据格式 {'category1': [values], 'category2': [values], ...}
            title: 图表标题
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        labels = list(data.keys())
        values = list(data.values())
        
        # 创建箱线图
        box_plot = ax.boxplot(values, labels=labels, patch_artist=True)
        
        # 设置颜色
        colors = self.get_color_scheme('pastel')
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.8)
        
        self.apply_template_style(fig, ax, title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return fig
    
    def create_scatter_plot(self, data: List[Tuple[float, float]], title: str = "散点图",
                           xlabel: str = "X轴", ylabel: str = "Y轴",
                           categories: Optional[List[str]] = None) -> Figure:
        """
        创建散点图
        
        Args:
            data: 散点数据 [(x1, y1), (x2, y2), ...]
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            categories: 分类标签列表
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        if data:
            x_vals, y_vals = zip(*data)
            
            if categories:
                # 分类散点图
                unique_categories = list(set(categories))
                colors = self.get_color_scheme('vibrant_mix')
                
                for i, category in enumerate(unique_categories):
                    cat_indices = [j for j, cat in enumerate(categories) if cat == category]
                    cat_x = [x_vals[j] for j in cat_indices]
                    cat_y = [y_vals[j] for j in cat_indices]
                    ax.scatter(cat_x, cat_y, label=category, 
                             color=colors[i % len(colors)], alpha=0.7, s=60)
                
                ax.legend()
            else:
                # 单一散点图
                ax.scatter(x_vals, y_vals, color=self.get_color_scheme()[0], 
                         alpha=0.7, s=60)
        
        self.apply_template_style(fig, ax, title)
        ax.set_xlabel(xlabel, **self.chart_templates[self.current_template]['label_style'])
        ax.set_ylabel(ylabel, **self.chart_templates[self.current_template]['label_style'])
        
        return fig
    
    def create_3d_bar_chart(self, data: Dict[str, Dict[str, float]], 
                           title: str = "3D柱状图") -> Figure:
        """
        创建3D柱状图
        
        Args:
            data: 数据格式 {'category1': {'metric1': value1, 'metric2': value2}, ...}
            title: 图表标题
        """
        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='3d')
        
        # 准备数据
        categories = list(data.keys())
        metrics = list(next(iter(data.values())).keys())
        
        x_pos = np.arange(len(categories))
        y_pos = np.arange(len(metrics))
        x_pos, y_pos = np.meshgrid(x_pos, y_pos)
        x_pos = x_pos.flatten()
        y_pos = y_pos.flatten()
        z_pos = np.zeros_like(x_pos)
        
        # 计算高度
        heights = []
        for category in categories:
            for metric in metrics:
                heights.append(data[category].get(metric, 0))
        
        colors = self.get_color_scheme('gradient_blues')
        dx = dy = 0.8
        
        ax.bar3d(x_pos, y_pos, z_pos, dx, dy, heights,
                color=[colors[i % len(colors)] for i in range(len(heights))],
                alpha=0.8)
        
        ax.set_xlabel('类别')
        ax.set_ylabel('指标')
        ax.set_zlabel('数值')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # 设置刻度标签
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories)
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels(metrics)
        
        return fig
    
    def create_3d_scatter_plot(self, data: List[Tuple[float, float, float]], 
                              title: str = "3D散点图",
                              categories: Optional[List[str]] = None) -> Figure:
        """
        创建3D散点图
        
        Args:
            data: 3D散点数据 [(x1, y1, z1), (x2, y2, z2), ...]
            title: 图表标题
            categories: 分类标签列表
        """
        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='3d')
        
        if data:
            x_vals, y_vals, z_vals = zip(*data)
            
            if categories:
                # 分类3D散点图
                unique_categories = list(set(categories))
                colors = self.get_color_scheme('vibrant_mix')
                
                for i, category in enumerate(unique_categories):
                    cat_indices = [j for j, cat in enumerate(categories) if cat == category]
                    cat_x = [x_vals[j] for j in cat_indices]
                    cat_y = [y_vals[j] for j in cat_indices]
                    cat_z = [z_vals[j] for j in cat_indices]
                    ax.scatter(cat_x, cat_y, cat_z, label=category,
                             color=colors[i % len(colors)], alpha=0.7, s=60)
                
                ax.legend()
            else:
                # 单一3D散点图
                ax.scatter(x_vals, y_vals, z_vals, 
                         color=self.get_color_scheme()[0], alpha=0.7, s=60)
        
        ax.set_xlabel('X轴')
        ax.set_ylabel('Y轴')
        ax.set_zlabel('Z轴')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        return fig
    
    def create_density_plot(self, data: List[float], title: str = "密度图",
                           xlabel: str = "数值", ylabel: str = "密度") -> Figure:
        """
        创建密度图
        
        Args:
            data: 数据列表
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        if data:
            # 使用seaborn创建密度图
            sns.histplot(data, kde=True, ax=ax, color=self.get_color_scheme()[0], alpha=0.7)
        
        self.apply_template_style(fig, ax, title)
        ax.set_xlabel(xlabel, **self.chart_templates[self.current_template]['label_style'])
        ax.set_ylabel(ylabel, **self.chart_templates[self.current_template]['label_style'])
        
        return fig
    
    def create_multi_axis_chart(self, primary_data: List[Tuple], secondary_data: List[Tuple],
                               title: str = "多轴图", primary_label: str = "主轴", 
                               secondary_label: str = "次轴") -> Figure:
        """
        创建多轴图表
        
        Args:
            primary_data: 主轴数据
            secondary_data: 次轴数据
            title: 图表标题
            primary_label: 主轴标签
            secondary_label: 次轴标签
        """
        fig, ax1 = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        colors = self.get_color_scheme('professional')
        
        # 绘制主轴数据
        if primary_data:
            x1_vals, y1_vals = zip(*primary_data)
            ax1.plot(x1_vals, y1_vals, color=colors[0], linewidth=2, label=primary_label)
            ax1.set_ylabel(primary_label, color=colors[0])
            ax1.tick_params(axis='y', labelcolor=colors[0])
        
        # 创建次轴
        ax2 = ax1.twinx()
        
        # 绘制次轴数据
        if secondary_data:
            x2_vals, y2_vals = zip(*secondary_data)
            ax2.plot(x2_vals, y2_vals, color=colors[1], linewidth=2, label=secondary_label)
            ax2.set_ylabel(secondary_label, color=colors[1])
            ax2.tick_params(axis='y', labelcolor=colors[1])
        
        # 应用样式
        ax1.set_title(title, **self.chart_templates[self.current_template]['title_style'])
        ax1.grid(True, **self.chart_templates[self.current_template]['grid_style'])
        
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        return fig
    
    def create_enhanced_heatmap(self, data: np.ndarray, row_labels: List[str], 
                               col_labels: List[str], title: str = "增强热力图") -> Figure:
        """
        创建增强的热力图
        
        Args:
            data: 二维数据数组
            row_labels: 行标签
            col_labels: 列标签
            title: 图表标题
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # 使用seaborn创建热力图
        sns.heatmap(data, annot=True, fmt='.1f', cmap='YlOrRd',
                   xticklabels=col_labels, yticklabels=row_labels,
                   ax=ax, cbar_kws={'shrink': 0.8})
        
        ax.set_title(title, **self.chart_templates[self.current_template]['title_style'])
        plt.tight_layout()
        
        return fig
    
    def create_waterfall_chart(self, categories: List[str], values: List[float],
                              title: str = "瀑布图") -> Figure:
        """
        创建瀑布图
        
        Args:
            categories: 类别标签
            values: 数值列表（正值为增加，负值为减少）
            title: 图表标题
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # 计算累积值
        cumulative = [0]
        for value in values:
            cumulative.append(cumulative[-1] + value)
        
        colors = ['green' if v >= 0 else 'red' for v in values]
        colors.append('blue')  # 最终值用蓝色
        
        # 绘制瀑布图
        for i, (cat, val) in enumerate(zip(categories + ['总计'], values + [cumulative[-1]])):
            if i < len(values):
                # 中间步骤
                ax.bar(cat, abs(val), bottom=min(cumulative[i], cumulative[i+1]),
                      color=colors[i], alpha=0.7)
                # 连接线
                if i < len(values) - 1:
                    ax.plot([i+0.4, i+1.6], [cumulative[i+1], cumulative[i+1]], 
                           'k--', alpha=0.5)
            else:
                # 最终总计
                ax.bar(cat, cumulative[-1], color=colors[i], alpha=0.7)
        
        self.apply_template_style(fig, ax, title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return fig 