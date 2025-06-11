# analyzer_main.py - 伤害计算分析器主入口

import ttkbootstrap as ttk
from ttkbootstrap.constants import PRIMARY, SECONDARY, SUCCESS, INFO, WARNING, DANGER, BOTH, X, Y, LEFT, RIGHT, TOP, BOTTOM, W, E, N, S, NW, NE, SW, SE, CENTER, HORIZONTAL, VERTICAL
from tkinter import StringVar, IntVar, DoubleVar
import sys
import os
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('damage_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from ui.main_window import DamageAnalyzerMainWindow
from data.database_manager import DatabaseManager

def main():
    """主程序入口"""
    try:
        # 确保数据库文件在正确的路径
        db_path = os.path.join(os.path.dirname(__file__), 'damage_analyzer.db')
        logger.info(f"使用数据库路径: {db_path}")
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(db_path)
        
        # 创建主窗口（使用新的ttk.Window方式）
        main_window = DamageAnalyzerMainWindow(db_manager)
        
        # 设置窗口图标（如果存在）
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                main_window.iconbitmap(icon_path)
        except (FileNotFoundError, OSError, AttributeError) as e:
            logger.debug(f"设置图标失败: {e}")
        
        # 运行主循环
        main_window.mainloop()
        
    except ImportError as e:
        error_msg = f"模块导入失败: {e}"
        logger.error(error_msg)
        
        # 显示错误对话框
        try:
            import tkinter.messagebox as mb
            mb.showerror("导入错误", f"程序启动失败：\n{str(e)}\n\n请检查依赖包是否正确安装")
        except ImportError:
            pass
    except Exception as e:
        error_msg = f"程序启动失败: {e}"
        logger.error(error_msg)
        
        # 显示错误对话框
        try:
            import tkinter.messagebox as mb
            mb.showerror("启动错误", f"程序启动失败：\n{str(e)}")
        except ImportError:
            pass

if __name__ == "__main__":
    main() 