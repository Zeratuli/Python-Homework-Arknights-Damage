"""
Utils工具模块初始化
包含事件管理、错误处理等工具
"""

# 导入保留的工具模块
# from .error_handler import ErrorHandler
from .event_manager import EventManager, get_event_manager

# 公开的工具类
__all__ = [
    'EventManager',
    'get_event_manager'
]

# 尝试导入其他可选组件
try:
    from .async_handler import AsyncHandler
    __all__.append('AsyncHandler')
except ImportError:
    pass

# except ImportError as e:
#     # 提供备用导入
#     import logging
#     logger = logging.getLogger(__name__)
#     logger.warning(f"Utils模块导入警告: {e}")
    
#     __all__ = [] 