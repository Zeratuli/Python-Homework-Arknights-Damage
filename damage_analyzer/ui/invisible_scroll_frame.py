"""
隐形滚动框架 - 支持鼠标滚轮的无可见滚动条组件
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import platform

class InvisibleScrollFrame:
    """隐形滚动框架，通过鼠标滚轮控制，无可见滚动条"""
    
    def __init__(self, parent, scroll_speed=5, **kwargs):
        """
        初始化隐形滚动框架
        
        Args:
            parent: 父容器
            scroll_speed: 滚动速度倍数 (默认5，更快的滚动体验)
            **kwargs: 传递给Canvas的其他参数
        """
        self.parent = parent
        self.scroll_speed = scroll_speed
        
        # 先初始化所有属性，避免在绑定事件时出现AttributeError
        self._bound_widgets = set()
        self.can_scroll_flag = False
        
        # 创建主容器
        self.main_frame = ttk.Frame(parent)
        
        # 创建Canvas (无高亮边框，隐形设计)
        canvas_kwargs = {
            'highlightthickness': 0,
            'borderwidth': 0,
            'relief': 'flat'
        }
        canvas_kwargs.update(kwargs)
        
        self.canvas = ttk.Canvas(self.main_frame, **canvas_kwargs)
        self.canvas.pack(fill=BOTH, expand=True)
        
        # 创建滚动内容框架
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 绑定事件（所有属性初始化完成后）
        self.bind_events()
        
    def pack(self, **kwargs):
        """包装pack方法"""
        self.main_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.main_frame.grid(**kwargs)
    
    def place(self, **kwargs):
        """包装place方法"""
        self.main_frame.place(**kwargs)
    
    def bind_events(self):
        """绑定必要的事件"""
        # 绑定内容框架的配置变化事件
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        
        # 绑定Canvas的配置变化事件
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 绑定Canvas的鼠标滚轮事件
        self.bind_mousewheel_to_widget(self.canvas)
        
        # 绑定鼠标进入/离开事件，用于焦点管理
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
    
    def on_frame_configure(self, event):
        """内容框架尺寸变化时的处理"""
        # 更新滚动区域
        self.update_scroll_region()
    
    def on_canvas_configure(self, event):
        """Canvas尺寸变化时的处理"""
        # 调整内容框架宽度以匹配Canvas
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
        
        # 更新滚动状态
        self.update_scroll_region()
    
    def update_scroll_region(self):
        """更新滚动区域并检查是否需要滚动"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # 检查是否需要滚动
        bbox = self.canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = self.canvas.winfo_height()
            self.can_scroll_flag = content_height > canvas_height
        else:
            self.can_scroll_flag = False
    
    def can_scroll(self):
        """检查当前是否可以滚动"""
        # 确保can_scroll_flag存在
        if not hasattr(self, 'can_scroll_flag'):
            self.can_scroll_flag = False
        return self.can_scroll_flag
    
    def bind_mousewheel_to_widget(self, widget):
        """为单个控件绑定鼠标滚轮事件"""
        # 确保_bound_widgets存在
        if not hasattr(self, '_bound_widgets'):
            self._bound_widgets = set()
            
        if widget in self._bound_widgets:
            return
        
        try:
            # 检测操作系统并绑定相应的滚轮事件
            system = platform.system()
            
            if system == "Windows":
                widget.bind("<MouseWheel>", self.on_mousewheel)
            elif system == "Darwin":  # macOS
                widget.bind("<MouseWheel>", self.on_mousewheel)
            else:  # Linux
                widget.bind("<Button-4>", self.on_mousewheel)
                widget.bind("<Button-5>", self.on_mousewheel)
            
            self._bound_widgets.add(widget)
        except Exception as e:
            # 如果绑定失败，记录错误但不中断程序
            print(f"滚轮事件绑定失败: {e}")
    
    def bind_mousewheel_recursive(self, widget):
        """递归为所有子控件绑定鼠标滚轮事件"""
        self.bind_mousewheel_to_widget(widget)
        
        # 递归处理所有子控件
        try:
            for child in widget.winfo_children():
                self.bind_mousewheel_recursive(child)
        except tk.TclError:
            # 控件可能已被销毁
            pass
    
    def on_enter(self, event):
        """鼠标进入Canvas区域"""
        # 为滚动框架内的所有控件绑定滚轮事件
        self.bind_mousewheel_recursive(self.scrollable_frame)
    
    def on_leave(self, event):
        """鼠标离开Canvas区域"""
        # 可以在这里添加一些清理逻辑
        pass
    
    def on_mousewheel(self, event):
        """鼠标滚轮事件处理 - 优化版：更快的滚动体验"""
        if not self.can_scroll():
            return
        
        # 获取滚动方向和数量
        delta = self.get_scroll_delta(event)
        if delta == 0:
            return
        
        # 应用滚动速度 - 增加基础滚动量
        base_scroll_unit = 20  # 基础滚动单位（像素）
        scroll_amount = delta * self.scroll_speed * base_scroll_unit
        
        # 获取当前滚动位置和内容信息
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        
        content_height = bbox[3] - bbox[1]
        canvas_height = self.canvas.winfo_height()
        
        if content_height <= canvas_height:
            return
        
        # 计算新的滚动位置
        current_top = self.canvas.canvasy(0)
        new_top = current_top + scroll_amount
        
        # 边界检测
        max_scroll = content_height - canvas_height
        new_top = max(0, min(new_top, max_scroll))
        
        # 执行滚动
        scroll_fraction = new_top / content_height if content_height > 0 else 0
        self.canvas.yview_moveto(scroll_fraction)
    
    def get_scroll_delta(self, event):
        """获取滚动增量"""
        system = platform.system()
        
        if system == "Windows":
            # Windows系统，event.delta通常是120的倍数
            return int(-1 * (event.delta / 120))
        elif system == "Darwin":  # macOS
            # macOS系统
            return int(-1 * event.delta)
        else:  # Linux
            if event.num == 4:
                return -1  # 向上滚动
            elif event.num == 5:
                return 1   # 向下滚动
        
        return 0
    
    def scroll_to_top(self):
        """滚动到顶部"""
        self.canvas.yview_moveto(0)
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        self.canvas.yview_moveto(1)
    
    def scroll_to_widget(self, widget):
        """滚动到指定控件位置"""
        try:
            # 获取控件在Canvas中的位置
            x1, y1, x2, y2 = self.canvas.bbox(widget)
            canvas_height = self.canvas.winfo_height()
            
            # 计算滚动位置使控件居中
            widget_center = (y1 + y2) / 2
            target_position = widget_center - canvas_height / 2
            
            bbox = self.canvas.bbox("all")
            if bbox:
                content_height = bbox[3] - bbox[1]
                scroll_fraction = target_position / content_height
                scroll_fraction = max(0, min(1, scroll_fraction))
                
                self.canvas.yview_moveto(scroll_fraction)
        except (tk.TclError, TypeError):
            # 控件可能不存在或不可见
            pass
    
    def add_widget_to_scroll_area(self, widget_func, *args, **kwargs):
        """在滚动区域中添加控件的便捷方法"""
        widget = widget_func(self.scrollable_frame, *args, **kwargs)
        # 立即为新控件绑定滚轮事件
        self.bind_mousewheel_recursive(widget)
        return widget
    
    def refresh_bindings(self):
        """刷新所有滚轮事件绑定"""
        # 确保_bound_widgets存在
        if not hasattr(self, '_bound_widgets'):
            self._bound_widgets = set()
        
        self._bound_widgets.clear()
        
        # 确保scrollable_frame存在
        if hasattr(self, 'scrollable_frame'):
            self.bind_mousewheel_recursive(self.scrollable_frame)
    
    def destroy(self):
        """清理资源"""
        self._bound_widgets.clear()
        self.main_frame.destroy() 