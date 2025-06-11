# chart_preview.py - 图表预览组件

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, Optional, Any, List
import logging

logger = logging.getLogger(__name__)

class ChartPreview(ttk.Frame):
    """图表预览组件"""
    
    def __init__(self, parent, chart_factory=None, **kwargs):
        """
        初始化图表预览组件
        
        Args:
            parent: 父容器
            chart_factory: 图表工厂实例
        """
        super().__init__(parent, **kwargs)
        
        self.chart_factory = chart_factory
        self.current_chart_type = "damage_curve"
        self.preview_figure = None
        self.preview_canvas = None
        
        # 示例数据
        self.sample_data = self.generate_sample_data()
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建标题
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(title_frame, text="📋 图表预览", 
                 font=("微软雅黑", 10, "bold")).pack(anchor=W)
        
        # 创建预览区域
        self.create_preview_area()
        
        # 显示初始预览
        self.update_preview(self.current_chart_type)
    
    def create_preview_area(self):
        """创建预览区域"""
        # 预览容器
        preview_container = ttk.Frame(self)
        preview_container.pack(fill=BOTH, expand=True)
        
        # 创建matplotlib图形
        self.preview_figure = Figure(figsize=(3, 2.5), dpi=80, facecolor='white')
        self.preview_figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
        
        # 创建画布
        self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, preview_container)
        self.preview_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        
        # 状态标签
        self.status_label = ttk.Label(preview_container, text="预览已就绪", 
                                     font=("微软雅黑", 8), bootstyle="secondary")
        self.status_label.pack(pady=2)
    
    def generate_sample_data(self) -> Dict[str, Any]:
        """生成示例数据"""
        # 模拟干员数据
        operators = [
            {"name": "示例干员A", "atk": 800, "hp": 3000, "def": 200, "class_type": "近卫"},
            {"name": "示例干员B", "atk": 600, "hp": 4000, "def": 400, "class_type": "重装"},
            {"name": "示例干员C", "atk": 1000, "hp": 2500, "def": 150, "class_type": "狙击"}
        ]
        
        # 模拟时间序列数据
        time_points = np.linspace(0, 60, 61)
        timeline_data = {}
        for i, op in enumerate(operators):
            # 生成模拟的DPS曲线
            base_dps = op["atk"] * 0.8
            variation = np.sin(time_points * 0.1) * base_dps * 0.2
            dps_values = base_dps + variation + np.random.normal(0, base_dps*0.05, len(time_points))
            timeline_data[op["name"]] = list(zip(time_points, np.maximum(0, dps_values)))
        
        # 模拟防御曲线数据
        defense_range = np.arange(0, 1001, 50)
        damage_curves = {}
        for op in operators:
            atk = op["atk"]
            # 模拟物理伤害计算
            damage_values = [max(atk - def_val, atk * 0.05) for def_val in defense_range]
            damage_curves[op["name"]] = list(zip(defense_range, damage_values))
        
        return {
            "operators": operators,
            "timeline_data": timeline_data,
            "damage_curves": damage_curves,
            "defense_range": defense_range
        }
    
    def update_preview(self, chart_type: str):
        """
        更新预览图表
        
        Args:
            chart_type: 图表类型
        """
        if not self.preview_figure:
            return
        
        try:
            self.current_chart_type = chart_type
            self.status_label.configure(text="正在生成预览...")
            
            # 清除现有图表
            self.preview_figure.clear()
            
            # 根据图表类型生成预览
            if chart_type == "damage_curve":
                self.create_damage_curve_preview()
            elif chart_type == "radar_chart":
                self.create_radar_chart_preview()
            elif chart_type == "bar_chart":
                self.create_bar_chart_preview()
            elif chart_type == "pie_chart":
                self.create_pie_chart_preview()
            elif chart_type == "heatmap":
                self.create_heatmap_preview()
            elif chart_type == "timeline":
                self.create_timeline_preview()
            elif chart_type == "area_chart":
                self.create_area_chart_preview()
            elif chart_type == "stacked_bar":
                self.create_stacked_bar_preview()
            elif chart_type == "box_plot":
                self.create_box_plot_preview()
            elif chart_type == "scatter_plot":
                self.create_scatter_plot_preview()
            elif chart_type == "3d_bar":
                self.create_3d_bar_preview()
            elif chart_type == "3d_scatter":
                self.create_3d_scatter_preview()
            else:
                self.create_default_preview()
            
            # 刷新画布
            self.preview_canvas.draw()
            self.status_label.configure(text="预览已更新")
            
        except Exception as e:
            logger.error(f"更新图表预览失败: {e}")
            self.create_error_preview(str(e))
            self.status_label.configure(text="预览失败")
    
    def create_damage_curve_preview(self):
        """创建伤害曲线预览"""
        ax = self.preview_figure.add_subplot(111)
        
        # 使用示例数据
        for i, (name, curve_data) in enumerate(self.sample_data["damage_curves"].items()):
            if i >= 2:  # 只显示前两个
                break
            x_vals, y_vals = zip(*curve_data[:15])  # 取前15个点
            ax.plot(x_vals, y_vals, label=name[:6], linewidth=1.5)
        
        ax.set_title("伤害-防御曲线", fontsize=9)
        ax.set_xlabel("防御", fontsize=8)
        ax.set_ylabel("伤害", fontsize=8)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)
    
    def create_radar_chart_preview(self):
        """创建雷达图预览"""
        ax = self.preview_figure.add_subplot(111, projection='polar')
        
        # 示例属性
        attributes = ['攻击', '生命', '防御', 'DPS']
        angles = np.linspace(0, 2 * np.pi, len(attributes), endpoint=False).tolist()
        angles += angles[:1]
        
        # 示例数据
        for i, op in enumerate(self.sample_data["operators"][:2]):
            values = [
                op["atk"] / 1000 * 100,
                op["hp"] / 4000 * 100,
                op["def"] / 400 * 100,
                80 + i * 20
            ]
            values += values[:1]
            
            ax.plot(angles, values, 'o-', linewidth=1, label=op["name"][:6], markersize=3)
            ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(attributes, fontsize=7)
        ax.set_title("雷达图对比", fontsize=9, pad=15)
        ax.legend(fontsize=6, loc='upper right', bbox_to_anchor=(1.2, 1.0))
        ax.tick_params(labelsize=6)
    
    def create_bar_chart_preview(self):
        """创建柱状图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        names = [op["name"][:4] for op in self.sample_data["operators"]]
        values = [op["atk"] for op in self.sample_data["operators"]]
        
        bars = ax.bar(names, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax.set_title("攻击力对比", fontsize=9)
        ax.set_ylabel("攻击力", fontsize=8)
        ax.tick_params(labelsize=7)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 10,
                   f'{value}', ha='center', va='bottom', fontsize=6)
    
    def create_pie_chart_preview(self):
        """创建饼图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        classes = ['近卫', '重装', '狙击']
        sizes = [40, 35, 25]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        ax.pie(sizes, labels=classes, colors=colors, autopct='%1.1f%%', 
               startangle=90, textprops={'fontsize': 7})
        ax.set_title("职业分布", fontsize=9)
    
    def create_heatmap_preview(self):
        """创建热力图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        # 生成示例热力图数据
        data = np.random.rand(5, 4) * 100
        
        im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
        ax.set_title("属性热力图", fontsize=9)
        ax.set_xticks(range(4))
        ax.set_xticklabels(['攻击', '生命', '防御', 'DPS'], fontsize=7)
        ax.set_yticks(range(5))
        ax.set_yticklabels([f'干员{i+1}' for i in range(5)], fontsize=7)
        
        # 添加颜色条
        cbar = self.preview_figure.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.tick_params(labelsize=6)
    
    def create_timeline_preview(self):
        """创建时间轴预览"""
        ax = self.preview_figure.add_subplot(111)
        
        # 使用示例时间轴数据
        for i, (name, timeline) in enumerate(self.sample_data["timeline_data"].items()):
            if i >= 2:  # 只显示前两个
                break
            x_vals, y_vals = zip(*timeline[::5])  # 每5个点取一个
            ax.plot(x_vals, y_vals, label=name[:6], linewidth=1.5)
        
        ax.set_title("时间轴伤害", fontsize=9)
        ax.set_xlabel("时间(s)", fontsize=8)
        ax.set_ylabel("DPS", fontsize=8)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)
    
    def create_area_chart_preview(self):
        """创建面积图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        x = np.linspace(0, 10, 50)
        y1 = np.sin(x) * 50 + 100
        y2 = np.cos(x) * 30 + 80
        
        ax.fill_between(x, y1, alpha=0.6, label='数据A')
        ax.fill_between(x, y2, alpha=0.6, label='数据B')
        
        ax.set_title("面积图", fontsize=9)
        ax.legend(fontsize=7)
        ax.tick_params(labelsize=7)
    
    def create_stacked_bar_preview(self):
        """创建堆叠柱状图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        categories = ['A', 'B', 'C']
        values1 = [20, 35, 30]
        values2 = [25, 15, 30]
        
        ax.bar(categories, values1, label='系列1', color='#FF6B6B')
        ax.bar(categories, values2, bottom=values1, label='系列2', color='#4ECDC4')
        
        ax.set_title("堆叠柱状图", fontsize=9)
        ax.legend(fontsize=7)
        ax.tick_params(labelsize=7)
    
    def create_box_plot_preview(self):
        """创建箱线图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        data = [np.random.normal(0, std, 100) for std in [1, 2, 1.5]]
        
        ax.boxplot(data, labels=['A', 'B', 'C'])
        ax.set_title("箱线图", fontsize=9)
        ax.tick_params(labelsize=7)
    
    def create_scatter_plot_preview(self):
        """创建散点图预览"""
        ax = self.preview_figure.add_subplot(111)
        
        x = np.random.randn(50)
        y = x + np.random.randn(50) * 0.5
        
        ax.scatter(x, y, alpha=0.6, color='#FF6B6B', s=30)
        ax.set_title("散点图", fontsize=9)
        ax.set_xlabel("X轴", fontsize=8)
        ax.set_ylabel("Y轴", fontsize=8)
        ax.tick_params(labelsize=7)
    
    def create_3d_bar_preview(self):
        """创建3D柱状图预览"""
        try:
            ax = self.preview_figure.add_subplot(111, projection='3d')
            
            x = [1, 2, 3]
            y = [1, 2, 3]
            z = [0, 0, 0]
            dx = dy = [0.8] * 3
            dz = [30, 50, 40]
            
            ax.bar3d(x, y, z, dx, dy, dz, alpha=0.8)
            ax.set_title("3D柱状图", fontsize=9)
            ax.tick_params(labelsize=6)
        except:
            self.create_default_preview()
    
    def create_3d_scatter_preview(self):
        """创建3D散点图预览"""
        try:
            ax = self.preview_figure.add_subplot(111, projection='3d')
            
            x = np.random.randn(30)
            y = np.random.randn(30)
            z = np.random.randn(30)
            
            ax.scatter(x, y, z, alpha=0.6, s=20)
            ax.set_title("3D散点图", fontsize=9)
            ax.tick_params(labelsize=6)
        except:
            self.create_default_preview()
    
    def create_default_preview(self):
        """创建默认预览"""
        ax = self.preview_figure.add_subplot(111)
        ax.text(0.5, 0.5, "图表预览\n敬请期待", ha='center', va='center', 
                transform=ax.transAxes, fontsize=10)
        ax.set_title("预览", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    
    def create_error_preview(self, error_msg: str):
        """创建错误预览"""
        self.preview_figure.clear()
        ax = self.preview_figure.add_subplot(111)
        ax.text(0.5, 0.5, f"预览失败\n{error_msg[:30]}...", ha='center', va='center',
                transform=ax.transAxes, fontsize=8, color='red')
        ax.set_title("错误", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        self.preview_canvas.draw()
    
    def clear_preview(self):
        """清除预览"""
        if self.preview_figure:
            self.preview_figure.clear()
            self.preview_canvas.draw()
            self.status_label.configure(text="预览已清除")
    
    def get_current_chart_type(self) -> str:
        """获取当前图表类型"""
        return self.current_chart_type 