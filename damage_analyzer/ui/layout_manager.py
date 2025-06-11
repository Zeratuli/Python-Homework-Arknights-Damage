# layout_manager.py - 简化的布局管理器

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Optional, Tuple

class LayoutManager:
    """简化的布局管理器"""
    
    def __init__(self, root_widget: tk.Widget):
        self.root_widget = root_widget
        self.sidebar_visible = True
        self.sidebar_width = 300
        
        # 存储布局组件
        self.sidebar_frame = None
        self.main_frame = None
        self.paned_window = None
    
    def create_sidebar_layout(self, sidebar_width: Optional[int] = None, 
                             min_sidebar_width: Optional[int] = None) -> Tuple[tk.Widget, tk.Widget]:
        """创建侧边栏布局"""
        if sidebar_width:
            self.sidebar_width = sidebar_width
        
        # 创建PanedWindow
        self.paned_window = ttk.PanedWindow(self.root_widget, orient=HORIZONTAL)
        self.paned_window.pack(fill=BOTH, expand=True)
        
        # 创建侧边栏框架
        self.sidebar_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.sidebar_frame, weight=1)
        
        # 创建主工作区框架
        self.main_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.main_frame, weight=4)
        
        return self.sidebar_frame, self.main_frame
    
    def toggle_sidebar(self, animated: bool = False):
        """切换侧边栏显示/隐藏"""
        if self.sidebar_frame and self.paned_window:
            if self.sidebar_visible:
                # 隐藏侧边栏
                self.paned_window.forget(self.sidebar_frame)
                self.sidebar_visible = False
            else:
                # 显示侧边栏
                self.paned_window.insert(0, self.sidebar_frame)
                self.sidebar_visible = True
    
    def is_sidebar_visible(self) -> bool:
        """检查侧边栏是否可见"""
        return self.sidebar_visible
    
    def cleanup(self):
        """清理资源"""
        pass 