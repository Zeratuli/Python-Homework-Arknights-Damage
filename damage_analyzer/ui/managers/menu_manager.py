# menu_manager.py - 简化的菜单管理器

import tkinter as tk
from typing import Callable, Dict

class MenuManager:
    """简化的菜单管理器"""
    
    def __init__(self, window, callbacks: Dict[str, Callable]):
        """
        初始化菜单管理器
        
        Args:
            window: 主窗口
            callbacks: 回调函数字典
        """
        self.window = window
        self.callbacks = callbacks
        self.menubar = None
    
    def create_menu(self) -> tk.Menu:
        """创建简化菜单栏"""
        self.menubar = tk.Menu(self.window)
        self.window.config(menu=self.menubar)
        
        # 创建文件菜单
        self.create_file_menu()
        
        # 创建帮助菜单
        self.create_help_menu()
        
        return self.menubar
    
    def create_file_menu(self):
        """创建文件菜单"""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="文件", menu=file_menu)
        
        # 设置选项
        file_menu.add_command(
            label="设置",
            command=self.callbacks.get('show_settings', lambda: None),
            accelerator="Ctrl+,"
        )
        
        file_menu.add_separator()
        
        file_menu.add_command(
            label="退出",
            command=self.callbacks.get('exit_app', lambda: None),
            accelerator="Ctrl+Q"
        )
    
    def create_help_menu(self):
        """创建帮助菜单"""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="帮助", menu=help_menu)
        
        help_menu.add_command(
            label="ℹ️ 关于",
            command=self.callbacks.get('show_about', lambda: None)
        ) 