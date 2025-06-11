# chart_type_selector.py - 现代化图表类型选择器

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from typing import Dict, Optional, Callable, Any
import logging

# 相对导入隐形滚动框架
from ..invisible_scroll_frame import InvisibleScrollFrame

logger = logging.getLogger(__name__)

class ChartTypeSelector(ttk.Frame):
    """现代化图表类型选择器"""
    
    def __init__(self, parent, callback: Optional[Callable] = None, **kwargs):
        """
        初始化图表类型选择器
        
        Args:
            parent: 父容器
            callback: 选择变化时的回调函数
        """
        super().__init__(parent, **kwargs)
        
        self.callback = callback
        self.selected_type = tk.StringVar(value="damage_curve")
        self.chart_cards = {}
        
        # 图表类型定义
        self.chart_types = {
            "damage_curve": {
                "name": "伤害-防御曲线", 
                "icon": "📈",
                "description": "分析干员在不同防御下的伤害表现",
                "category": "基础图表"
            },
            "radar_chart": {
                "name": "雷达图对比", 
                "icon": "🕸️",
                "description": "多维度对比干员属性",
                "category": "高级图表"
            },
            "bar_chart": {
                "name": "性能柱状图", 
                "icon": "📊",
                "description": "直观对比干员性能指标",
                "category": "基础图表"
            },
            "pie_chart": {
                "name": "属性饼图", 
                "icon": "🥧",
                "description": "显示属性分布比例",
                "category": "基础图表"
            },
            "heatmap": {
                "name": "热力图分析", 
                "icon": "🔥",
                "description": "可视化多维数据关系",
                "category": "高级图表"
            },
            "timeline": {
                "name": "时间轴伤害", 
                "icon": "⏱️",
                "description": "分析时间序列伤害输出",
                "category": "专业图表"
            },
            "area_chart": {
                "name": "面积图", 
                "icon": "📉",
                "description": "显示数据变化趋势",
                "category": "基础图表"
            },
            "stacked_bar": {
                "name": "堆叠柱状图", 
                "icon": "📊",
                "description": "分层对比多个指标",
                "category": "高级图表"
            },
            "box_plot": {
                "name": "箱线图", 
                "icon": "📦",
                "description": "显示数据分布和异常值",
                "category": "专业图表"
            },
            "scatter_plot": {
                "name": "散点图", 
                "icon": "🔗",
                "description": "分析两个变量的关系",
                "category": "专业图表"
            },
            "3d_bar": {
                "name": "3D柱状图", 
                "icon": "🧊",
                "description": "立体展示数据对比",
                "category": "3D图表"
            },
            "3d_scatter": {
                "name": "3D散点图", 
                "icon": "🌐",
                "description": "三维空间数据分析",
                "category": "3D图表"
            }
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建标题
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(title_frame, text="📊 图表类型选择", 
                 font=("微软雅黑", 12, "bold")).pack(anchor=W)
        
        # 创建可滚动容器
        self.create_scrollable_container()
        
        # 创建图表卡片
        self.create_chart_cards()
        
        # 绑定选择变化事件
        self.selected_type.trace('w', self.on_selection_changed)
    
    def create_scrollable_container(self):
        """创建可滚动容器 - 使用隐形滚动框架"""
        # 使用隐形滚动框架替代Canvas+Scrollbar
        self.scroll_frame = InvisibleScrollFrame(self, scroll_speed=3, height=400)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        
        # 获取滚动容器中的frame
        self.scrollable_frame = self.scroll_frame.scrollable_frame
    
    def create_chart_cards(self):
        """创建图表类型卡片"""
        # 按类别分组
        categories = {}
        for chart_type, info in self.chart_types.items():
            category = info["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((chart_type, info))
        
        row = 0
        for category, charts in categories.items():
            # 创建分类标题
            category_frame = ttk.LabelFrame(self.scrollable_frame, text=category, padding=5)
            category_frame.grid(row=row, column=0, sticky="ew", pady=5, padx=5)
            row += 1
            
            # 创建该分类下的图表卡片
            for i, (chart_type, info) in enumerate(charts):
                self.create_chart_card(category_frame, chart_type, info, i)
            
            # 配置网格权重
            self.scrollable_frame.grid_rowconfigure(row-1, weight=0)
        
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
    
    def create_chart_card(self, parent, chart_type: str, info: Dict[str, str], index: int):
        """创建单个图表卡片"""
        # 创建卡片框架
        card_frame = ttk.Frame(parent)
        card_frame.grid(row=index//2, column=index%2, sticky="ew", padx=2, pady=2)
        
        # 创建单选按钮（隐藏选择器，使用自定义样式）
        radio_button = ttk.Radiobutton(
            card_frame,
            text="",
            variable=self.selected_type,
            value=chart_type
        )
        radio_button.pack_forget()  # 隐藏默认样式
        
        # 创建自定义卡片内容
        content_frame = ttk.Frame(card_frame, style="Card.TFrame", padding=8)
        content_frame.pack(fill=BOTH, expand=True)
        
        # 图标和名称
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill=X)
        
        icon_label = ttk.Label(header_frame, text=info["icon"], font=("微软雅黑", 16))
        icon_label.pack(side=LEFT)
        
        name_label = ttk.Label(header_frame, text=info["name"], 
                              font=("微软雅黑", 10, "bold"))
        name_label.pack(side=LEFT, padx=(5, 0))
        
        # 描述
        desc_label = ttk.Label(content_frame, text=info["description"], 
                              font=("微软雅黑", 8), wraplength=150)
        desc_label.pack(anchor=W, pady=(2, 0))
        
        # 绑定点击事件
        def on_card_click(event=None):
            self.selected_type.set(chart_type)
            self.update_card_selection()
        
        # 为所有组件绑定点击事件
        for widget in [content_frame, header_frame, icon_label, name_label, desc_label]:
            widget.bind("<Button-1>", on_card_click)
            widget.bind("<Enter>", lambda e, w=widget: self.on_card_hover(w, True))
            widget.bind("<Leave>", lambda e, w=widget: self.on_card_hover(w, False))
        
        # 存储卡片引用
        self.chart_cards[chart_type] = {
            "frame": content_frame,
            "widgets": [content_frame, header_frame, icon_label, name_label, desc_label]
        }
        
        # 配置网格权重
        parent.grid_columnconfigure(index%2, weight=1)
    
    def on_card_hover(self, widget, enter: bool):
        """处理卡片悬停效果"""
        if enter:
            widget.configure(cursor="hand2")
        else:
            widget.configure(cursor="")
    
    def update_card_selection(self):
        """更新卡片选中状态"""
        selected_type = self.selected_type.get()
        
        for chart_type, card_info in self.chart_cards.items():
            frame = card_info["frame"]
            if chart_type == selected_type:
                # 选中状态 - 蓝色边框
                frame.configure(style="Selected.TFrame")
                try:
                    frame.configure(relief="solid", borderwidth=2)
                except:
                    pass
            else:
                # 未选中状态 - 默认样式
                frame.configure(style="Card.TFrame")
                try:
                    frame.configure(relief="flat", borderwidth=1)
                except:
                    pass
    
    def on_selection_changed(self, *args):
        """处理选择变化"""
        self.update_card_selection()
        
        if self.callback:
            try:
                self.callback(self.selected_type.get())
            except Exception as e:
                logger.error(f"图表选择回调执行失败: {e}")
    
    def get_selected_type(self) -> str:
        """获取选中的图表类型"""
        return self.selected_type.get()
    
    def set_selected_type(self, chart_type: str):
        """设置选中的图表类型"""
        if chart_type in self.chart_types:
            self.selected_type.set(chart_type)
    
    def get_chart_info(self, chart_type: str) -> Optional[Dict[str, str]]:
        """获取图表类型信息"""
        return self.chart_types.get(chart_type)
    
    def get_all_chart_types(self) -> Dict[str, Dict[str, str]]:
        """获取所有图表类型信息"""
        return self.chart_types.copy() 