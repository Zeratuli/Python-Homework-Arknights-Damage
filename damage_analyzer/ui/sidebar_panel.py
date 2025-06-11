# sidebar_panel.py - 增强的侧边栏面板

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from typing import Dict, Callable
import logging
from tkinter import messagebox
from ui.invisible_scroll_frame import InvisibleScrollFrame

logger = logging.getLogger(__name__)

class SidebarPanel:
    """增强的侧边栏面板 - 基本导航、数据统计和导出功能"""
    
    def __init__(self, parent, db_manager, callbacks: Dict[str, Callable] = None):
        """
        初始化侧边栏面板
        
        Args:
            parent: 父容器
            db_manager: 数据库管理器
            callbacks: 回调函数字典
        """
        self.parent = parent
        self.db_manager = db_manager
        self.callbacks = callbacks or {}
        
        # 状态变量
        self.current_section = "概览"
        self.stats_data = {
            'operator_count': 0,
            'import_count': 0,
            'calculation_count': 0,
            'today_calculations': 0
        }
        
        # 组件初始化标志
        self.ui_initialized = False
        
        # 先创建UI
        self.setup_ui()
        
        # UI创建完成后，延迟执行数据刷新
        self.parent.after(100, self._delayed_refresh_data)
    
    def setup_ui(self):
        """设置侧边栏UI - 集成隐形滚动功能"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建隐形滚动容器
        self.scroll_frame = InvisibleScrollFrame(self.main_frame, scroll_speed=3)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        
        # 在滚动容器中创建内容
        content_frame = self.scroll_frame.scrollable_frame
        
        # 标题
        title_label = ttk.Label(content_frame, text="系统状态", 
                               font=("微软雅黑", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 系统概览
        self.create_overview_section(content_frame)
        
        # 导出功能区域
        self.create_export_section(content_frame)
        
        # 基本导航
        self.create_basic_navigation_section(content_frame)
        
        # 快捷操作
        self.create_quick_actions_section(content_frame)
        
        # 标记UI初始化完成
        self.ui_initialized = True
    
    def _delayed_refresh_data(self):
        """延迟刷新数据，确保UI完全初始化"""
        try:
            if self.ui_initialized:
                self.refresh_data()
            else:
                # 如果UI还没初始化，再延迟一点
                self.parent.after(50, self._delayed_refresh_data)
        except Exception as e:
            logger.error(f"延迟刷新数据失败: {e}")
    
    def create_overview_section(self, parent=None):
        """创建增强的概览区域"""
        if parent is None:
            parent = self.main_frame
            
        overview_frame = ttk.LabelFrame(parent, text="📊 数据统计", padding=10)
        overview_frame.pack(fill=X, pady=(0, 10))
        
        # 干员数量
        self.operator_count_label = ttk.Label(overview_frame, text="👥 干员数量: 0", 
                                             font=("微软雅黑", 9))
        self.operator_count_label.pack(anchor=W, pady=2)
        
        # 导入记录数量
        self.import_count_label = ttk.Label(overview_frame, text="📁 导入记录: 0", 
                                           font=("微软雅黑", 9))
        self.import_count_label.pack(anchor=W, pady=2)
        
        # 计算记录数量
        self.calculation_count_label = ttk.Label(overview_frame, text="📈 计算记录: 0", 
                                                font=("微软雅黑", 9))
        self.calculation_count_label.pack(anchor=W, pady=2)
        
        # 今日计算次数
        self.today_calc_label = ttk.Label(overview_frame, text="🔢 今日计算: 0", 
                                         font=("微软雅黑", 9))
        self.today_calc_label.pack(anchor=W, pady=2)
        
        # 分隔线
        ttk.Separator(overview_frame, orient=HORIZONTAL).pack(fill=X, pady=(8, 8))
        
        # 刷新按钮
        ttk.Button(overview_frame, text="🔄 刷新数据", bootstyle=INFO, width=15,
                  command=self.refresh_data_with_feedback).pack(pady=5)
    
    def create_export_section(self, parent=None):
        """创建导出功能区域"""
        if parent is None:
            parent = self.main_frame
            
        export_frame = ttk.LabelFrame(parent, text="📤 数据导出", padding=10)
        export_frame.pack(fill=X, pady=(0, 10))
        
        # 导出按钮组
        export_buttons = [
            ("📊 导出Excel", "export_excel", SUCCESS, "导出完整Excel数据表"),
            ("📄 导出PDF", "export_pdf", PRIMARY, "生成PDF分析报告"),
            ("🌐 导出HTML", "export_html", INFO, "生成网页版报告"),
            ("💾 导出JSON", "export_json", SECONDARY, "导出原始JSON数据")
        ]
        
        for text, callback_name, style, tooltip in export_buttons:
            btn = ttk.Button(export_frame, text=text, bootstyle=style, width=15,
                           command=self._callback(callback_name))
            btn.pack(fill=X, pady=2)
            self.create_tooltip(btn, tooltip)
    
    def create_basic_navigation_section(self, parent=None):
        """创建基本导航区域"""
        if parent is None:
            parent = self.main_frame
            
        nav_frame = ttk.LabelFrame(parent, text="📋 页面导航", padding=10)
        nav_frame.pack(fill=X, pady=(0, 10))
        
        # 导航按钮
        nav_buttons = [
            ("📊 数据概览", "switch_to_overview", "查看系统数据概览"),
            ("📈 数据分析", "switch_to_analysis", "进行伤害计算分析"),
            ("📊 图表对比", "switch_to_comparison", "多干员图表对比"),
            ("👥 干员管理", "switch_to_import", "管理干员数据")
        ]
        
        for text, callback_name, tooltip in nav_buttons:
            btn = ttk.Button(nav_frame, text=text, bootstyle=SECONDARY, width=15,
                           command=self._callback(callback_name))
            btn.pack(fill=X, pady=2)
            self.create_tooltip(btn, tooltip)
    
    def create_quick_actions_section(self, parent=None):
        """创建快捷操作区域"""
        if parent is None:
            parent = self.main_frame
            
        actions_frame = ttk.LabelFrame(parent, text="⚡ 快捷操作", padding=10)
        actions_frame.pack(fill=X, pady=(0, 10))
        
        # 快捷操作按钮
        quick_buttons = [
            ("📥 导入数据", "quick_import", WARNING, "快速导入干员数据"),
            ("🧹 清理缓存", "clear_cache", DANGER, "清理系统缓存数据")
        ]
        
        for text, callback_name, style, tooltip in quick_buttons:
            btn = ttk.Button(actions_frame, text=text, bootstyle=style, width=15,
                           command=self._callback(callback_name))
            btn.pack(fill=X, pady=2)
            self.create_tooltip(btn, tooltip)
    
    def create_tooltip(self, widget, text):
        """创建工具提示"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="lightyellow", 
                            relief="solid", borderwidth=1, font=("微软雅黑", 8))
            label.pack(padx=5, pady=2)
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def refresh_data_with_feedback(self):
        """带用户反馈的刷新数据"""
        try:
            # 显示刷新进度
            original_text = "🔄 刷新数据"
            refresh_btn = None
            
            # 安全查找刷新按钮
            for child in self.main_frame.winfo_children():
                if hasattr(child, 'winfo_children'):
                    for btn in child.winfo_children():
                        # 安全检查组件是否支持text选项
                        if hasattr(btn, 'cget') and hasattr(btn, 'winfo_class'):
                            try:
                                # 检查组件类型，确保是Button类型
                                widget_class = btn.winfo_class()
                                if widget_class in ['Button', 'TButton']:
                                    btn_text = btn.cget('text')
                                    if "刷新" in str(btn_text):
                                        refresh_btn = btn
                                        break
                            except Exception as e:
                                # 如果获取text失败，跳过这个组件
                                logger.debug(f"查找刷新按钮时跳过组件: {e}")
                                continue
            
            if refresh_btn:
                refresh_btn.configure(text="⏳ 刷新中...", state="disabled")
            
            # 强制更新UI
            self.main_frame.update_idletasks()
            
            # 执行刷新
            self.refresh_data()
            
            # 恢复按钮状态
            if refresh_btn:
                refresh_btn.configure(text="✅ 完成", state="normal")
                self.main_frame.after(2000, lambda: refresh_btn.configure(text=original_text))
            
            # messagebox.showinfo("刷新成功", "数据统计已成功刷新！")
            
        except Exception as e:
            logger.error(f"刷新数据失败: {e}")
            if refresh_btn:
                refresh_btn.configure(text="❌ 失败", state="normal")
                self.main_frame.after(3000, lambda: refresh_btn.configure(text=original_text))
            messagebox.showerror("刷新失败", f"刷新数据时出现错误：\n{str(e)}")
    
    def refresh_data(self):
        """刷新数据统计"""
        try:
            logger.info("开始刷新sidebar数据...")
            
            # 检查UI是否已经初始化
            if not getattr(self, 'ui_initialized', False):
                logger.debug("UI未初始化，跳过数据刷新")
                return
            
            logger.info("UI已初始化，继续刷新...")
            
            if self.db_manager:
                logger.info("开始获取统计摘要...")
                # 获取统计摘要
                stats = self.db_manager.get_statistics_summary()
                logger.info(f"获取统计摘要成功: {stats}")
                
                # 更新内部数据
                self.stats_data.update({
                    'operator_count': stats.get('total_operators', 0),
                    'import_count': stats.get('total_imports', 0),
                    'calculation_count': stats.get('total_calculations', 0),
                    'today_calculations': stats.get('today_calculations', 0)
                })
                logger.info("内部数据更新完成")
                
                # 简化的UI更新逻辑 - 直接更新标签
                logger.info("开始更新UI标签...")
                
                try:
                    # 直接更新标签，移除复杂的安全检查
                    if hasattr(self, 'operator_count_label') and self.operator_count_label:
                        self.operator_count_label.configure(text=f"👥 干员数量: {self.stats_data['operator_count']}")
                        logger.info("干员数量标签更新成功")
                    
                    if hasattr(self, 'import_count_label') and self.import_count_label:
                        self.import_count_label.configure(text=f"📁 导入记录: {self.stats_data['import_count']}")
                        logger.info("导入记录标签更新成功")
                    
                    if hasattr(self, 'calculation_count_label') and self.calculation_count_label:
                        self.calculation_count_label.configure(text=f"📈 计算记录: {self.stats_data['calculation_count']}")
                        logger.info("计算记录标签更新成功")
                    
                    if hasattr(self, 'today_calc_label') and self.today_calc_label:
                        self.today_calc_label.configure(text=f"🔢 今日计算: {self.stats_data['today_calculations']}")
                        logger.info("今日计算标签更新成功")
                        
                except Exception as e:
                    logger.error(f"更新UI标签失败: {e}")
                
                logger.info(f"侧边栏数据刷新完成: {self.stats_data}")
                
        except Exception as e:
            logger.error(f"刷新侧边栏数据失败: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 安全显示错误状态
            if getattr(self, 'ui_initialized', False):
                try:
                    if hasattr(self, 'operator_count_label') and self.operator_count_label:
                        self.operator_count_label.configure(text="👥 干员数量: 错误")
                    if hasattr(self, 'import_count_label') and self.import_count_label:
                        self.import_count_label.configure(text="📁 导入记录: 错误")
                    if hasattr(self, 'calculation_count_label') and self.calculation_count_label:
                        self.calculation_count_label.configure(text="📈 计算记录: 错误")
                    if hasattr(self, 'today_calc_label') and self.today_calc_label:
                        self.today_calc_label.configure(text="🔢 今日计算: 错误")
                except:
                    pass
    
    def refresh_stats(self):
        """刷新统计数据的别名方法，兼容旧版本调用"""
        self.refresh_data()
    
    def _callback(self, name: str) -> Callable:
        """获取回调函数"""
        def default_callback():
            messagebox.showinfo("功能提示", f"{name} 功能正在开发中...")
        
        return self.callbacks.get(name, default_callback) 