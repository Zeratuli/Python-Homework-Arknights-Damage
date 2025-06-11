"""
中央事件管理器
统一管理所有UI事件绑定，防止重复绑定和性能问题
"""

import tkinter as tk
from typing import Optional, Callable

class EventManager:
    """简化的事件管理器"""
    
    def __init__(self):
        pass
    
    def bind_mousewheel(self, widget: tk.Widget, callback: Optional[Callable] = None) -> bool:
        """
        绑定鼠标滚轮事件
        
        Args:
            widget: 要绑定的控件
            callback: 自定义回调函数
            
        Returns:
            是否成功绑定
        """
        def default_handler(event):
            try:
                widget.yview_scroll(int(-1*(event.delta/120)), "units")
            except (tk.TclError, AttributeError):
                pass
        
        handler = callback if callback else default_handler
        
        try:
            widget.bind("<MouseWheel>", handler)
            return True
        except Exception:
            return False
    
    def cleanup(self):
        """清理资源"""
        pass

# 全局事件管理器实例
_event_manager = None

def get_event_manager() -> EventManager:
    """获取事件管理器实例"""
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager 