# overview_panel.py - 概览面板

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import sys
import os
from typing import Dict, Optional, Callable, Any, List
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

class OverviewPanel:
    """概览面板 - 显示数据库统计和快速入口"""
    
    def __init__(self, parent, db_manager, status_callback: Optional[Callable] = None):
        """
        初始化概览面板
        
        Args:
            parent: 父容器
            db_manager: 数据库管理器
            status_callback: 状态回调函数
        """
        self.parent = parent
        self.db_manager = db_manager
        self.status_callback = status_callback
        self.main_window = None  # 主窗口引用，用于标签页切换
        
        # 统计数据
        self.stats_data = {
            'total_operators': 0,
            'total_skills': 0,
            'class_distribution': {},
            'recent_activity': []
        }
        
        self.setup_ui()
        # 初始化后自动刷新数据
        self.parent.after(100, self.refresh_data)  # 延迟100ms执行
        # 设置定时刷新（每30秒）
        self.setup_auto_refresh()
    
    def setup_auto_refresh(self):
        """设置自动刷新机制"""
        def auto_refresh():
            try:
                self.refresh_data()
            except Exception as e:
                logger.error(f"自动刷新失败: {e}")
            finally:
                # 30秒后再次刷新
                self.parent.after(30000, auto_refresh)
        
        # 30秒后开始第一次自动刷新
        self.parent.after(30000, auto_refresh)
    
    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
    
    def setup_ui(self):
        """设置概览面板UI"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 创建上下布局
        self.create_header_section(main_frame)
        self.create_stats_section(main_frame)
        self.create_charts_section(main_frame)
    
    def create_header_section(self, parent):
        """创建头部区域"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 20))
        
        # 欢迎标题
        title_label = ttk.Label(header_frame, text="塔防游戏伤害分析器", 
                               font=("微软雅黑", 18, "bold"))
        title_label.pack(anchor=W)
        
        subtitle_label = ttk.Label(header_frame, text="数据概览与快速导航", 
                                  font=("微软雅黑", 11), bootstyle="secondary")
        subtitle_label.pack(anchor=W, pady=(2, 0))
        
        # 系统状态
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(fill=X, pady=(10, 0))
        
        self.system_status_label = ttk.Label(status_frame, text="系统正常运行", 
                                            font=("微软雅黑", 9), bootstyle="success")
        self.system_status_label.pack(side=LEFT)
        
        self.last_update_label = ttk.Label(status_frame, text="最后更新: 未知", 
                                          font=("微软雅黑", 9), bootstyle="secondary")
        self.last_update_label.pack(side=RIGHT)
    
    def create_stats_section(self, parent):
        """创建统计区域"""
        stats_frame = ttk.LabelFrame(parent, text="📊 数据统计", padding=15)
        stats_frame.pack(fill=X, pady=(0, 20))
        
        # 创建统计卡片网格
        cards_frame = ttk.Frame(stats_frame)
        cards_frame.pack(fill=X)
        
        # 简化为3个核心统计卡片 - 单行布局
        self.create_stat_card(cards_frame, "干员总数", "0", "👥", 0, 0)
        self.create_stat_card(cards_frame, "导入记录", "0", "📁", 0, 1)
        self.create_stat_card(cards_frame, "今日计算", "0", "📈", 0, 2)
        
        # 添加刷新数据按钮
        refresh_frame = ttk.Frame(stats_frame)
        refresh_frame.pack(fill=X, pady=(10, 0))
        
        refresh_btn = ttk.Button(refresh_frame, text="🔄 刷新数据", bootstyle=INFO, width=15,
                  command=self.refresh_data_with_feedback)
        refresh_btn.pack(anchor=CENTER)
        
        # 保存刷新按钮引用
        self.refresh_btn = refresh_btn
    
    def create_stat_card(self, parent, title, value, icon, row, col):
        """创建统计卡片"""
        card_frame = ttk.Frame(parent, bootstyle="light")
        card_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        
        # 配置网格权重
        parent.grid_columnconfigure(col, weight=1)
        
        # 图标和数值
        top_frame = ttk.Frame(card_frame)
        top_frame.pack(fill=X, pady=(10, 5))
        
        icon_label = ttk.Label(top_frame, text=icon, font=("微软雅黑", 16))
        icon_label.pack(side=LEFT)
        
        value_label = ttk.Label(top_frame, text=value, font=("微软雅黑", 18, "bold"),
                               bootstyle="primary")
        value_label.pack(side=RIGHT)
        
        # 标题
        title_label = ttk.Label(card_frame, text=title, font=("微软雅黑", 10))
        title_label.pack(anchor=W, pady=(0, 10))
        
        # 标题到英文属性名的映射
        title_mapping = {
            "干员总数": "operators_count",
            "导入记录": "imports_count", 
            "今日计算": "today_calcs_count"
        }
        
        # 使用英文属性名存储引用以便更新
        attr_name = f"{title_mapping.get(title, title)}_value_label"
        setattr(self, attr_name, value_label)
        
        # 调试信息
        logger.info(f"创建统计卡片: {title} -> {attr_name}")
    
    def create_charts_section(self, parent):
        """创建图表区域"""
        charts_frame = ttk.LabelFrame(parent, text="📈 数据可视化", padding=15)
        charts_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # 创建左右分栏
        chart_paned = ttk.PanedWindow(charts_frame, orient=HORIZONTAL)
        chart_paned.pack(fill=BOTH, expand=True)
        
        # 左侧：职业分布饼图
        left_frame = ttk.Frame(chart_paned)
        chart_paned.add(left_frame, weight=1)
        
        self.create_class_distribution_chart(left_frame)
        
        # 右侧：活动时间线
        right_frame = ttk.Frame(chart_paned)
        chart_paned.add(right_frame, weight=1)
        
        self.create_activity_timeline(right_frame)
    
    def create_class_distribution_chart(self, parent):
        """创建职业分布饼图"""
        chart_frame = ttk.Frame(parent)
        chart_frame.pack(fill=BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(chart_frame, text="干员职业分布", font=("微软雅黑", 10, "bold")).pack(pady=(0, 5))
        
        # 创建matplotlib图表
        self.class_fig = Figure(figsize=(4, 3), dpi=80)
        self.class_ax = self.class_fig.add_subplot(111)
        
        self.class_canvas = FigureCanvasTkAgg(self.class_fig, chart_frame)
        self.class_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        
        # 初始化空图表
        self.update_class_distribution_chart()
    
    def create_activity_timeline(self, parent):
        """创建活动时间线"""
        timeline_frame = ttk.Frame(parent)
        timeline_frame.pack(fill=BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(timeline_frame, text="最近活动", font=("微软雅黑", 10, "bold")).pack(pady=(0, 5))
        
        # 活动列表
        self.activity_listbox = tk.Listbox(timeline_frame, height=8, font=("微软雅黑", 9))
        activity_scrollbar = ttk.Scrollbar(timeline_frame, orient=VERTICAL, 
                                          command=self.activity_listbox.yview)
        self.activity_listbox.configure(yscrollcommand=activity_scrollbar.set)
        
        self.activity_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        activity_scrollbar.pack(side=RIGHT, fill=Y)
    
    def refresh_data_with_feedback(self):
        """带用户反馈的刷新数据方法 - 优化版"""
        try:
            logger.info("用户点击刷新按钮，开始刷新数据...")
            
            # 显示刷新状态
            original_text = self.refresh_btn.cget('text')
            self.refresh_btn.configure(text="⏳ 刷新中...", state="disabled")
            self.update_status("正在刷新数据...")
            
            # 强制更新UI以显示刷新状态
            self.parent.update_idletasks()
            
            # 记录刷新前的数据状态
            old_stats = self.stats_data.copy()
            logger.info(f"刷新前数据状态: {old_stats}")
            
            # 执行刷新
            self.refresh_data()
            
            # 记录刷新后的数据状态
            logger.info(f"刷新后数据状态: {self.stats_data}")
            
            # 检查数据是否有变化
            changes = []
            for key in ['total_operators', 'total_imports', 'today_calculations']:
                old_val = old_stats.get(key, 0)
                new_val = self.stats_data.get(key, 0)
                if old_val != new_val:
                    changes.append(f"{key}: {old_val} -> {new_val}")
            
            # 显示成功状态
            self.refresh_btn.configure(text="✅ 刷新完成", state="normal")
            self.parent.after(2000, lambda: self.refresh_btn.configure(text=original_text))
            
            # 构建成功消息
            if changes:
                change_msg = "\n".join(changes)
                success_msg = f"数据已成功刷新！\n\n数据变化:\n{change_msg}"
            else:
                success_msg = "数据已成功刷新！\n\n没有检测到数据变化。"
            
            messagebox.showinfo("刷新成功", success_msg)
            logger.info(f"刷新成功，数据变化: {changes}")
            
        except Exception as e:
            logger.error(f"刷新数据失败: {e}", exc_info=True)
            
            # 恢复按钮状态
            try:
                self.refresh_btn.configure(text="❌ 刷新失败", state="normal")
                self.parent.after(3000, lambda: self.refresh_btn.configure(text="🔄 刷新数据"))
            except:
                pass
            
            # 显示详细错误信息
            error_msg = f"刷新数据时出现错误：\n\n{str(e)}\n\n请检查日志文件获取更多详细信息。"
            messagebox.showerror("刷新失败", error_msg)
    
    def refresh_data(self):
        """刷新数据统计 - 修复版本"""
        try:
            logger.info("开始刷新概览数据...")
            
            # 不要调用close()，因为SQLite的DatabaseManager不需要显式关闭单个连接
            # 每次get_connection()都会创建新的连接
            
            # 测试数据库连接
            if not self.db_manager.test_connection():
                raise Exception("数据库连接失败")
            
            # 强制清除可能的缓存，重新获取统计数据
            logger.info("正在获取最新统计数据...")
            stats_summary = self.db_manager.get_statistics_summary()
            logger.info(f"获取到统计数据: {stats_summary}")
            
            # 更新内部数据
            old_data = self.stats_data.copy()
            self.stats_data.update({
                'total_operators': stats_summary.get('total_operators', 0),
                'total_imports': stats_summary.get('total_imports', 0),
                'today_calculations': stats_summary.get('today_calculations', 0),
                'class_distribution': stats_summary.get('class_distribution', {})
            })
            
            # 记录所有数据变化
            for key in ['total_operators', 'total_imports', 'today_calculations']:
                old_val = old_data.get(key, 0)
                new_val = self.stats_data[key]
                if old_val != new_val:
                    logger.info(f"{key}数量变化: {old_val} -> {new_val}")
            
            # 强制更新UI显示
            logger.info("开始更新UI组件...")
            self.update_stat_cards()
            logger.info("统计卡片更新完成")
            
            self.update_class_distribution_chart()
            logger.info("职业分布图表更新完成")
            
            self.update_activity_timeline()
            logger.info("活动时间线更新完成")
            
            # 检查是否有临时活动记录需要处理
            self._check_and_process_temp_activity()
            
            # 强制UI重绘
            self.parent.update_idletasks()
            
            # 更新状态显示
            self.update_status("数据刷新完成")
            
            logger.info(f"概览数据刷新完成: 干员数量={self.stats_data['total_operators']}, 导入记录={self.stats_data['total_imports']}, 今日计算={self.stats_data['today_calculations']}")
            
        except Exception as e:
            error_msg = f"刷新概览数据失败: {e}"
            logger.error(error_msg)
            self.update_status("数据刷新失败", "error")
            raise e  # 重新抛出异常，让调用方处理
    
    def _check_and_process_temp_activity(self):
        """检查并处理临时活动记录"""
        try:
            activity_file = "temp_activity.txt"
            if os.path.exists(activity_file):
                with open(activity_file, "r", encoding="utf-8") as f:
                    activity_description = f.read().strip()
                
                if activity_description:
                    logger.info(f"处理临时活动记录: {activity_description}")
                    self.push_real_time_activity(activity_description)
                
                # 删除临时文件
                os.remove(activity_file)
                logger.info("临时活动记录文件已删除")
                
        except Exception as e:
            logger.error(f"处理临时活动记录失败: {e}")
    
    def update_stat_cards(self):
        """更新统计卡片 - 修复版本"""
        try:
            logger.info("开始更新统计卡片...")
            logger.info(f"当前统计数据: {self.stats_data}")
            
            # 检查所有应该存在的属性
            expected_attrs = ['operators_count_value_label', 'imports_count_value_label', 'today_calcs_count_value_label']
            missing_attrs = []
            for attr in expected_attrs:
                if not hasattr(self, attr):
                    missing_attrs.append(attr)
            
            if missing_attrs:
                logger.error(f"缺少属性: {missing_attrs}")
                logger.info("尝试重新创建统计区域...")
                return
            
            # 更新干员总数
            if hasattr(self, 'operators_count_value_label'):
                try:
                    old_value = self.operators_count_value_label.cget('text')
                    new_value = str(self.stats_data['total_operators'])
                    self.operators_count_value_label.configure(text=new_value)
                    logger.info(f"干员总数更新: {old_value} -> {new_value}")
                except Exception as e:
                    logger.error(f"更新干员总数失败: {e}")
            else:
                logger.warning("operators_count_value_label 属性不存在")
            
            # 更新导入记录统计
            if hasattr(self, 'imports_count_value_label'):
                try:
                    old_value = self.imports_count_value_label.cget('text')
                    new_value = str(self.stats_data['total_imports'])
                    self.imports_count_value_label.configure(text=new_value)
                    logger.info(f"导入记录更新: {old_value} -> {new_value}")
                except Exception as e:
                    logger.error(f"更新导入记录失败: {e}")
            else:
                logger.warning("imports_count_value_label 属性不存在")
            
            # 更新今日计算统计
            if hasattr(self, 'today_calcs_count_value_label'):
                try:
                    old_value = self.today_calcs_count_value_label.cget('text')
                    new_value = str(self.stats_data['today_calculations'])
                    self.today_calcs_count_value_label.configure(text=new_value)
                    logger.info(f"今日计算更新: {old_value} -> {new_value}")
                except Exception as e:
                    logger.error(f"更新今日计算失败: {e}")
            else:
                logger.warning("today_calcs_count_value_label 属性不存在")
            
            # 强制更新UI显示
            try:
                self.parent.update_idletasks()
                
                # 强制刷新每个label
                for attr_name in expected_attrs:
                    if hasattr(self, attr_name):
                        widget = getattr(self, attr_name)
                        widget.update_idletasks()
                        
                logger.info("UI强制更新完成")
            except Exception as e:
                logger.error(f"强制UI更新失败: {e}")
            
            logger.info("统计卡片更新完成")
                    
        except Exception as e:
            logger.error(f"更新统计卡片失败: {e}")
            # 显示错误状态
            try:
                if hasattr(self, 'operators_count_value_label'):
                    self.operators_count_value_label.configure(text="错误")
                if hasattr(self, 'imports_count_value_label'):
                    self.imports_count_value_label.configure(text="错误")
                if hasattr(self, 'today_calcs_count_value_label'):
                    self.today_calcs_count_value_label.configure(text="错误")
            except Exception as inner_e:
                logger.error(f"设置错误状态失败: {inner_e}")
    
    def get_import_records_count(self) -> int:
        """获取导入记录数量"""
        try:
            # 使用数据库管理器的新方法获取导入记录
            if hasattr(self.db_manager, 'get_import_records'):
                records = self.db_manager.get_import_records()
                return len(records)
            else:
                # 兼容性处理：如果方法不存在，返回干员总数
                return self.stats_data['total_operators']
        except Exception as e:
            logger.error(f"获取导入记录数量失败: {e}")
            return 0
    
    def get_today_calculations_count(self) -> int:
        """获取今日计算次数"""
        try:
            # 使用数据库管理器的新方法获取今日计算记录
            if hasattr(self.db_manager, 'get_today_calculations'):
                return self.db_manager.get_today_calculations()
            else:
                # 兼容性处理：使用日志文件统计
                return self.count_today_calculations_from_log()
        except Exception as e:
            logger.error(f"获取今日计算次数失败: {e}")
            return 0
    
    def count_today_calculations_from_log(self) -> int:
        """从日志文件统计今日计算次数"""
        try:
            today = datetime.date.today()
            log_file = "damage_analyzer.log"
            
            if not os.path.exists(log_file):
                return 0
            
            calculation_count = 0
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 查找包含计算相关的日志条目
                    if any(keyword in line for keyword in ['计算', 'calculate', 'DPS', '伤害分析']):
                        # 检查是否是今天的日志
                        if today.strftime('%Y-%m-%d') in line:
                            calculation_count += 1
            
            return calculation_count
            
        except Exception as e:
            logger.error(f"从日志统计今日计算次数失败: {e}")
            return 0
    
    def update_class_distribution_chart(self):
        """更新职业分布图表"""
        try:
            self.class_ax.clear()
            
            distribution = self.stats_data['class_distribution']
            if distribution:
                labels = list(distribution.keys())
                sizes = list(distribution.values())
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
                
                self.class_ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                 colors=colors[:len(labels)], startangle=90)
                self.class_ax.set_title('干员职业分布', fontsize=10, fontweight='bold')
            else:
                self.class_ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                                  transform=self.class_ax.transAxes)
                self.class_ax.set_title('干员职业分布', fontsize=10, fontweight='bold')
            
            self.class_fig.tight_layout()
            self.class_canvas.draw()
            
        except Exception as e:
            logger.error(f"更新职业分布图表失败: {e}")
    
    def update_activity_timeline(self):
        """更新活动时间线 - 修复版本"""
        try:
            self.activity_listbox.delete(0, tk.END)
            
            # 获取混合活动记录并按时间排序
            import_records = self.db_manager.get_import_records(limit=5)
            calc_records = self.db_manager.get_calculation_history(limit=5)
            
            # 合并并排序活动
            all_activities = []
            
            # 添加导入记录
            for record in import_records:
                all_activities.append({
                    'time': record.get('created_at', ''),
                    'text': f"导入了{record.get('record_count', 0)}条数据",
                    'type': 'import'
                })
            
            # 添加计算记录
            for record in calc_records:
                all_activities.append({
                    'time': record.get('created_at', ''),
                    'text': f"计算了{record.get('operator_name', '未知干员')}的伤害",
                    'type': 'calculation'
                })
            
            # 按时间倒序排序（最新的在前）
            all_activities.sort(key=lambda x: x['time'], reverse=True)
            
            # 显示最近6条活动
            if all_activities:
                for activity in all_activities[:6]:
                    time_str = self._format_time_for_display(activity['time'])
                    self.activity_listbox.insert(tk.END, f"• {time_str} {activity['text']}")
            else:
                # 如果没有活动记录，显示提示信息
                current_time = datetime.datetime.now().strftime("%H:%M")
                self.activity_listbox.insert(tk.END, f"• {current_time} 系统初始化完成")
                self.activity_listbox.insert(tk.END, "• 请导入数据或进行计算")
                self.activity_listbox.insert(tk.END, "• 数据将在此处显示")
                
        except Exception as e:
            logger.error(f"更新活动时间线失败: {e}")
            # 显示错误信息
            self.activity_listbox.delete(0, tk.END)
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.activity_listbox.insert(tk.END, f"• {current_time} 活动记录更新失败")
            self.activity_listbox.insert(tk.END, f"• 错误: {str(e)[:50]}...")
    
    def push_real_time_activity(self, activity_description: str):
        """推送实时活动记录 - 修复版本"""
        try:
            # 使用当前本地时间
            current_time = datetime.datetime.now().strftime("%H:%M")
            
            # 在活动列表顶部插入新活动
            self.activity_listbox.insert(0, f"• {current_time} {activity_description}")
            
            # 保持列表长度不超过6条，删除最旧的记录
            while self.activity_listbox.size() > 6:
                self.activity_listbox.delete(tk.END)
            
            # 强制刷新显示
            self.activity_listbox.update_idletasks()
            
            logger.info(f"推送实时活动: {activity_description}")
            
        except Exception as e:
            logger.error(f"推送实时活动失败: {e}")
    
    def update_status(self, message: str, status_type: str = "info"):
        """更新状态显示 - 修复版本"""
        try:
            color = "success" if status_type == "info" else "danger"
            self.system_status_label.configure(text=message, bootstyle=color)
            
            # 使用与时间格式化一致的时间源
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.last_update_label.configure(text=f"最后更新: {current_time}")
            
            if self.status_callback:
                self.status_callback(message)
                
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计数据"""
        return self.stats_data.copy()
    
    def _format_time_for_display(self, time_str: str) -> str:
        """统一的时间格式化方法 - 修复版本
        
        解决时间不一致问题，统一使用本地时间源
        """
        try:
            if not time_str:
                return "未知时间"
            
            # 尝试解析不同的时间格式
            time_formats = [
                "%Y-%m-%d %H:%M:%S",     # 数据库标准格式
                "%Y-%m-%d %H:%M",        # 推送时使用的格式
                "%Y-%m-%d %H:%M:%S.%f"   # 带微秒的格式
            ]
            
            parsed_time = None
            for fmt in time_formats:
                try:
                    parsed_time = datetime.datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_time is None:
                # 如果都解析不了，截取前16个字符
                logger.warning(f"无法解析时间格式: {time_str}")
                return time_str[:16] if len(time_str) >= 16 else time_str
            
            # 修复：检查数据库时间是否是UTC时间，如果是，转换为本地时间
            # 如果时间差距太大（比如8小时），可能是UTC时间，需要转换
            current_local_time = datetime.datetime.now()
            time_diff = abs((current_local_time - parsed_time).total_seconds())
            
            # 如果时间差超过6小时但小于10小时，可能是UTC时间需要转换
            if 21600 <= time_diff <= 36000:  # 6-10小时之间
                # 转换为本地时间（+8小时）
                parsed_time = parsed_time + datetime.timedelta(hours=8)
                logger.debug(f"检测到UTC时间，已转换为本地时间: {time_str} -> {parsed_time}")
            
            # 检查是否是今天的时间
            today = datetime.date.today()
            if parsed_time.date() == today:
                # 今天的时间只显示时分
                return parsed_time.strftime("%H:%M")
            else:
                # 非今天的时间显示月日时分
                return parsed_time.strftime("%m-%d %H:%M")
            
        except Exception as e:
            logger.error(f"时间格式化失败: {e}, time_str: {time_str}")
            return "时间错误"
    
    def _get_current_time_for_activity(self) -> str:
        """获取当前时间用于活动记录 - 修复版本
        
        使用与右上角时间显示一致的时间源
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 