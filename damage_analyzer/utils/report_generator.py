# report_generator.py - 报告生成器

import os
import logging
from typing import Dict, List, Any, Optional
from tkinter import messagebox, filedialog
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportGenerator:
    """统一的报告生成器"""
    
    def __init__(self, db_manager):
        """
        初始化报告生成器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def generate_complete_analysis_report(self, format_type: str, filename: str = None, data: Dict[str, Any] = None) -> bool:
        """
        生成完整分析报告
        
        Args:
            format_type: 报告格式 ('pdf', 'html', 'txt')
            filename: 输出文件路径
            data: 报告数据
            
        Returns:
            是否生成成功
        """
        try:
            if filename is None:
                if format_type == 'pdf':
                    filename = filedialog.asksaveasfilename(
                        title="导出分析报告",
                        defaultextension=".pdf",
                        filetypes=[("PDF 文件", "*.pdf")]
                    )
                elif format_type == 'html':
                    filename = filedialog.asksaveasfilename(
                        title="导出分析报告",
                        defaultextension=".html",
                        filetypes=[("HTML 文件", "*.html")]
                    )
                elif format_type == 'txt':
                    filename = filedialog.asksaveasfilename(
                        title="导出分析报告",
                        defaultextension=".txt",
                        filetypes=[("文本文件", "*.txt")]
                    )
                
            if not filename:
                return False
            
            # 获取报告数据
            if data is None:
                data = self._collect_report_data()
            
            current_time = datetime.now()
            
            if format_type == 'pdf':
                return self.generate_pdf_report(filename, data['stats'], data['operators'], data['calc_records'], data['recent_calculations'], current_time)
            elif format_type == 'html':
                return self.generate_html_report(filename, data['stats'], data['operators'], data['calc_records'], data['recent_calculations'], current_time)
            elif format_type == 'txt':
                return self.generate_text_report(filename, data['stats'], data['operators'], data['calc_records'], data['recent_calculations'], current_time)
            else:
                messagebox.showerror("错误", f"不支持的报告格式: {format_type}")
                return False
                
        except Exception as e:
            logger.error(f"生成{format_type}报告失败: {e}")
            messagebox.showerror("生成失败", f"生成{format_type}报告失败：\n{str(e)}")
            return False
    
    def _collect_report_data(self) -> Dict[str, Any]:
        """收集报告数据"""
        try:
            # 获取统计数据
            stats = self.db_manager.get_statistics_summary()
            
            # 获取干员数据
            operators = self.db_manager.get_all_operators()
            
            # 获取前4次计算记录（最新的4次）
            recent_calculations = self.db_manager.get_calculation_history(limit=4)
            
            # 获取计算记录（用于历史记录展示）
            calc_records = self.db_manager.get_calculation_history(limit=100)
            
            return {
                'stats': stats,
                'operators': operators,
                'calc_records': calc_records,
                'recent_calculations': recent_calculations  # 新增：前4次计算结果
            }
        except Exception as e:
            logger.error(f"收集报告数据失败: {e}")
            return {
                'stats': {},
                'operators': [],
                'calc_records': [],
                'recent_calculations': []
            }
    
    def generate_pdf_report(self, filename: str, stats: Dict, operators: List, calc_records: List, recent_calculations: List, current_time: datetime) -> bool:
        """生成PDF报告"""
        try:
            # 尝试导入reportlab
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
            except ImportError:
                messagebox.showerror("错误", "需要安装reportlab库才能生成PDF报告\n请运行: pip install reportlab")
                return False
            
            # 注册中文字体
            try:
                # 尝试注册系统中文字体
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    "/System/Library/Fonts/PingFang.ttc",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Linux
                ]
                
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                            font_registered = True
                            break
                        except:
                            continue
                
                if not font_registered:
                    # 使用默认字体
                    chinese_font = 'Helvetica'
                else:
                    chinese_font = 'ChineseFont'
                    
            except Exception as e:
                logger.warning(f"注册中文字体失败: {e}")
                chinese_font = 'Helvetica'
            
            # 创建PDF文档
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            
            # 获取样式
            styles = getSampleStyleSheet()
            
            # 创建中文样式
            title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Title'],
                fontName=chinese_font,
                fontSize=18,
                spaceAfter=30,
                alignment=1  # 居中
            )
            
            heading_style = ParagraphStyle(
                'ChineseHeading',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=14,
                spaceAfter=12
            )
            
            normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10,
                spaceAfter=6
            )
            
            # 标题
            story.append(Paragraph("塔防游戏伤害分析器 - 完整分析报告", title_style))
            story.append(Spacer(1, 12))
            
            # 生成时间
            story.append(Paragraph(f"报告生成时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 20))
            
            # 统计摘要
            story.append(Paragraph("统计摘要", heading_style))
            
            stats_data = [
                ['统计项目', '数值'],
                ['干员总数', str(stats.get('total_operators', 0))],
                ['导入记录总数', str(stats.get('total_imports', 0))],
                ['计算记录总数', str(stats.get('total_calculations', 0))],
                ['今日计算次数', str(stats.get('today_calculations', 0))]
            ]
            
            # 添加职业分布
            class_dist = stats.get('class_distribution', {})
            for class_type, count in class_dist.items():
                stats_data.append([f'{class_type}职业干员', str(count)])
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # 干员数据表（前20个）
            if operators:
                story.append(Paragraph("干员数据 (前20个)", heading_style))
                
                operator_data = [['名称', '职业', '攻击力', '生命值', '攻击类型']]
                for i, op in enumerate(operators[:20]):
                    operator_data.append([
                        str(op.get('name', '')),
                        str(op.get('class_type', '')),
                        str(op.get('atk', 0)),
                        str(op.get('hp', 0)),
                        str(op.get('atk_type', ''))
                    ])
                
                operator_table = Table(operator_data)
                operator_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(operator_table)
                story.append(Spacer(1, 20))
            
            # 添加前4次计算结果详情
            if recent_calculations:
                story.append(Paragraph("前4次计算结果详情", heading_style))
                story.append(Paragraph("按时间顺序展示的最新计算分析结果", normal_style))
                story.append(Spacer(1, 10))
                
                for i, calc in enumerate(recent_calculations, 1):
                    try:
                        # 计算基本信息
                        operator_name = calc.get('operator_name', '未知干员')
                        calc_type = calc.get('calculation_type', '未知计算')
                        created_at = str(calc.get('created_at', ''))[:19]
                        
                        # 解析参数和结果
                        parameters = calc.get('parameters', {})
                        results = calc.get('results', {})
                        
                        # 检查是否是多干员对比计算
                        if '多干员对比' in calc_type and 'detailed_table' in results:
                            # 显示多干员对比的详细表格
                            detailed_table = results['detailed_table']
                            if detailed_table:
                                html_content = f"""
                        <tr>
                            <td colspan="4">
                                <h4>计算 {i}: {calc_type} - {len(detailed_table)}个干员对比</h4>
                                <p><strong>计算时间:</strong> {created_at}</p>
                                <p><strong>计算参数:</strong> 敌防{parameters.get('enemy_def', 0)}, 敌法抗{parameters.get('enemy_mdef', 0)}, {parameters.get('calc_mode_display', '未知模式')}</p>
                                
                                <table style="width: 100%; margin: 10px 0; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background-color: #007bff; color: white;">
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">干员名称</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">职业类型</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击类型</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击力</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击速度</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">生命值</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">部署费用</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">DPS</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">DPH</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">破甲线</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">性价比</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                """
                                
                                for row in detailed_table:
                                    html_content += f"""
                                        <tr style="background-color: #f8f9fa;">
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('干员名称', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('职业类型', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('攻击类型', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('攻击力', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('攻击速度', 0)):.1f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('生命值', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('部署费用', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('DPS', 0)):.2f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('DPH', 0)):.2f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('破甲线', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('性价比', 0)):.2f}</td>
                                        </tr>
                                    """
                                
                                html_content += f"""
                                    </tbody>
                                </table>
                                
                                <p style="margin: 10px 0; font-style: italic; color: #666;">
                                    <strong>对比汇总:</strong> 最大DPS {results.get('max_dps', 0):.2f}, 平均DPS {results.get('avg_dps', 0):.2f}, 最大性价比 {results.get('max_efficiency', 0):.2f}
                                </p>
                            </td>
                        </tr>
                        """
                        else:
                            # 单干员计算的简化显示
                            # 构建参数字符串
                            param_details = []
                            if 'enemy_def' in parameters:
                                param_details.append(f"敌人防御: {parameters['enemy_def']}")
                            if 'enemy_mdef' in parameters:
                                param_details.append(f"敌人法抗: {parameters['enemy_mdef']}")
                            if 'attack_type' in parameters:
                                param_details.append(f"攻击类型: {parameters['attack_type']}")
                            
                            # 构建结果字符串
                            result_details = []
                            if 'dps' in results:
                                result_details.append(f"DPS: {results['dps']:.2f}")
                            if 'dph' in results:
                                result_details.append(f"单发伤害: {results['dph']:.2f}")
                            if 'total_damage' in results:
                                result_details.append(f"总伤害: {results['total_damage']:.0f}")
                            if 'hps' in results:
                                result_details.append(f"HPS: {results['hps']:.2f}")
                            
                            html_content = f"""
                        <tr>
                            <td>{i}</td>
                            <td>{operator_name}</td>
                            <td>{calc_type}</td>
                            <td>{created_at}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td colspan="4" style="font-style: italic; color: #666;">
                                <strong>计算参数:</strong> {' | '.join(param_details) if param_details else '无参数信息'}<br>
                                <strong>计算结果:</strong> {' | '.join(result_details) if result_details else '无结果信息'}
                            </td>
                        </tr>
                        """
                        
                    except Exception as e:
                        logger.warning(f"处理计算记录 {i} 失败: {e}")
                        html_content = f"""
                        <tr>
                            <td>{i}</td>
                            <td>数据解析失败</td>
                            <td>数据解析失败</td>
                            <td>数据解析失败</td>
                        </tr>
                        """
                
                story.append(PageBreak())
            else:
                # 如果没有计算记录
                story.append(Paragraph("计算结果", heading_style))
                story.append(Paragraph("当前没有计算记录。请在应用中进行一些计算分析。", normal_style))
                story.append(Spacer(1, 20))
            
            # 最近计算记录（前10个）
            if calc_records:
                story.append(Paragraph("最近计算记录 (前10个)", heading_style))
                
                calc_data = [['干员名称', '计算类型', '创建时间']]
                for i, record in enumerate(calc_records[:10]):
                    calc_data.append([
                        str(record.get('operator_name', '未知')),
                        str(record.get('calculation_type', '')),
                        str(record.get('created_at', ''))[:19]  # 只显示日期时间部分
                    ])
                
                calc_table = Table(calc_data)
                calc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(calc_table)
            
            # 生成PDF
            doc.build(story)
            
            messagebox.showinfo("导出成功", f"PDF报告已导出到: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"生成PDF报告失败: {e}")
            messagebox.showerror("导出失败", f"生成PDF报告失败：\n{str(e)}")
            return False
    
    def generate_html_report(self, filename: str, stats: Dict, operators: List, calc_records: List, recent_calculations: List, current_time: datetime) -> bool:
        """生成HTML报告"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>塔防游戏伤害分析器 - 完整分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .meta-info {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background-color: #3498db;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>塔防游戏伤害分析器 - 完整分析报告</h1>
        
        <div class="meta-info">
            <strong>报告生成时间:</strong> {current_time.strftime('%Y年%m月%d日 %H:%M:%S')}
        </div>
        
        <h2>📊 统计摘要</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_operators', 0)}</div>
                <div class="stat-label">干员总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_imports', 0)}</div>
                <div class="stat-label">导入记录总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_calculations', 0)}</div>
                <div class="stat-label">计算记录总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('today_calculations', 0)}</div>
                <div class="stat-label">今日计算次数</div>
            </div>
        </div>
        
        <h2>👥 职业分布</h2>
        <table>
            <thead>
                <tr>
                    <th>职业类型</th>
                    <th>干员数量</th>
                    <th>占比</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 添加职业分布数据
            class_dist = stats.get('class_distribution', {})
            total_ops = stats.get('total_operators', 1)
            for class_type, count in class_dist.items():
                percentage = (count / total_ops * 100) if total_ops > 0 else 0
                html_content += f"""
                <tr>
                    <td>{class_type}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <h2>🎯 干员数据 (前20个)</h2>
        <table>
            <thead>
                <tr>
                    <th>名称</th>
                    <th>职业</th>
                    <th>攻击力</th>
                    <th>生命值</th>
                    <th>攻击类型</th>
                    <th>部署费用</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 添加干员数据
            for op in operators[:20]:
                html_content += f"""
                <tr>
                    <td>{op.get('name', '')}</td>
                    <td>{op.get('class_type', '')}</td>
                    <td>{op.get('atk', 0)}</td>
                    <td>{op.get('hp', 0)}</td>
                    <td>{op.get('atk_type', '')}</td>
                    <td>{op.get('cost', 0)}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <h2>📈 前4次计算结果详情</h2>
        <table>
            <thead>
                <tr>
                    <th>计算编号</th>
                    <th>干员名称</th>
                    <th>计算类型</th>
                    <th>计算时间</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 添加前4次计算结果详情
            if recent_calculations:
                for i, calc in enumerate(recent_calculations, 1):
                    try:
                        # 计算基本信息
                        operator_name = calc.get('operator_name', '未知干员')
                        calc_type = calc.get('calculation_type', '未知计算')
                        created_at = str(calc.get('created_at', ''))[:19]
                        
                        # 解析参数和结果
                        parameters = calc.get('parameters', {})
                        results = calc.get('results', {})
                        
                        # 检查是否是多干员对比计算
                        if '多干员对比' in calc_type and 'detailed_table' in results:
                            # 显示多干员对比的详细表格
                            detailed_table = results['detailed_table']
                            if detailed_table:
                                html_final = f"""
                        <tr>
                            <td colspan="4">
                                <h4>计算 {i}: {calc_type} - {len(detailed_table)}个干员对比</h4>
                                <p><strong>计算时间:</strong> {created_at}</p>
                                <p><strong>计算参数:</strong> 敌防{parameters.get('enemy_def', 0)}, 敌法抗{parameters.get('enemy_mdef', 0)}, {parameters.get('calc_mode_display', '未知模式')}</p>
                                
                                <table style="width: 100%; margin: 10px 0; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background-color: #007bff; color: white;">
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">干员名称</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">职业类型</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击类型</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击力</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击速度</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">生命值</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">部署费用</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">DPS</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">DPH</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">破甲线</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">性价比</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                """
                                
                                for row in detailed_table:
                                    html_final += f"""
                                        <tr style="background-color: #f8f9fa;">
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('干员名称', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('职业类型', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('攻击类型', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('攻击力', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('攻击速度', 0)):.1f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('生命值', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('部署费用', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('DPS', 0)):.2f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('DPH', 0)):.2f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('破甲线', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('性价比', 0)):.2f}</td>
                                        </tr>
                                    """
                                
                                html_final += f"""
                                    </tbody>
                                </table>
                                
                                <p style="margin: 10px 0; font-style: italic; color: #666;">
                                    <strong>对比汇总:</strong> 最大DPS {results.get('max_dps', 0):.2f}, 平均DPS {results.get('avg_dps', 0):.2f}, 最大性价比 {results.get('max_efficiency', 0):.2f}
                                </p>
                            </td>
                        </tr>
                        """
                        else:
                            # 单干员计算的简化显示
                            # 构建参数字符串
                            param_details = []
                            if 'enemy_def' in parameters:
                                param_details.append(f"敌人防御: {parameters['enemy_def']}")
                            if 'enemy_mdef' in parameters:
                                param_details.append(f"敌人法抗: {parameters['enemy_mdef']}")
                            if 'attack_type' in parameters:
                                param_details.append(f"攻击类型: {parameters['attack_type']}")
                            
                            # 构建结果字符串
                            result_details = []
                            if 'dps' in results:
                                result_details.append(f"DPS: {results['dps']:.2f}")
                            if 'dph' in results:
                                result_details.append(f"单发伤害: {results['dph']:.2f}")
                            if 'total_damage' in results:
                                result_details.append(f"总伤害: {results['total_damage']:.0f}")
                            if 'hps' in results:
                                result_details.append(f"HPS: {results['hps']:.2f}")
                            
                            html_final = f"""
                        <tr>
                            <td>{i}</td>
                            <td>{operator_name}</td>
                            <td>{calc_type}</td>
                            <td>{created_at}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td colspan="4" style="font-style: italic; color: #666;">
                                <strong>计算参数:</strong> {' | '.join(param_details) if param_details else '无参数信息'}<br>
                                <strong>计算结果:</strong> {' | '.join(result_details) if result_details else '无结果信息'}
                            </td>
                        </tr>
                        """
                        
                    except Exception as e:
                        logger.warning(f"处理计算记录 {i} 失败: {e}")
                        html_final = f"""
                        <tr>
                            <td>{i}</td>
                            <td>数据解析失败</td>
                            <td>数据解析失败</td>
                            <td>数据解析失败</td>
                        </tr>
                        """
                
                html_final += """
            </tbody>
        </table>
        
        <h2>📈 最近计算记录 (前10个)</h2>
        <table>
            <thead>
                <tr>
                    <th>干员名称</th>
                    <th>计算类型</th>
                    <th>创建时间</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 添加计算记录
            for record in calc_records[:10]:
                html_final += f"""
                <tr>
                    <td>{record.get('operator_name', '未知')}</td>
                    <td>{record.get('calculation_type', '')}</td>
                    <td>{str(record.get('created_at', ''))[:19]}</td>
                </tr>
"""
            
            html_final += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p>报告由塔防游戏伤害分析器自动生成 | 生成时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
            
            # 写入HTML文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_final)
            
            messagebox.showinfo("导出成功", f"HTML报告已导出到: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            messagebox.showerror("生成失败", f"生成HTML报告失败：\n{str(e)}")
            return False
    
    def generate_text_report(self, filename: str, stats: Dict, operators: List, calc_records: List, recent_calculations: List, current_time: datetime) -> bool:
        """生成文本报告"""
        try:
            report_content = f"""
塔防游戏伤害分析器 - 完整分析报告
{'='*50}

报告生成时间: {current_time.strftime('%Y年%m月%d日 %H:%M:%S')}

统计摘要
{'-'*20}
干员总数: {stats.get('total_operators', 0)}
导入记录总数: {stats.get('total_imports', 0)}
计算记录总数: {stats.get('total_calculations', 0)}
今日计算次数: {stats.get('today_calculations', 0)}

职业分布
{'-'*20}
"""
            
            # 添加职业分布
            class_dist = stats.get('class_distribution', {})
            for class_type, count in class_dist.items():
                report_content += f"{class_type}: {count} 个\n"
            
            # 添加干员数据
            report_content += f"\n干员数据 (前20个)\n{'-'*20}\n"
            for i, op in enumerate(operators[:20], 1):
                report_content += f"{i:2d}. {op.get('name', ''):12s} | {op.get('class_type', ''):8s} | 攻击:{op.get('atk', 0):4d} | 生命:{op.get('hp', 0):4d} | {op.get('atk_type', '')}\n"
            
            # 添加前4次计算结果详情
            report_content += f"\n前4次计算结果详情\n{'-'*20}\n"
            for i, calc in enumerate(recent_calculations, 1):
                try:
                    # 计算基本信息
                    operator_name = calc.get('operator_name', '未知干员')
                    calc_type = calc.get('calculation_type', '未知计算')
                    created_at = str(calc.get('created_at', ''))[:19]
                    
                    # 解析参数和结果
                    parameters = calc.get('parameters', {})
                    results = calc.get('results', {})
                    
                    # 构建详细信息字符串
                    details = []
                    if parameters:
                        if 'enemy_def' in parameters:
                            details.append(f"敌人防御: {parameters['enemy_def']}")
                        if 'enemy_mdef' in parameters:
                            details.append(f"敌人法抗: {parameters['enemy_mdef']}")
                        if 'attack_type' in parameters:
                            details.append(f"攻击类型: {parameters['attack_type']}")
                    
                    if results:
                        if 'dps' in results:
                            details.append(f"DPS: {results['dps']:.2f}")
                        if 'dph' in results:
                            details.append(f"单发: {results['dph']:.2f}")
                        if 'total_damage' in results:
                            details.append(f"总伤害: {results['total_damage']:.0f}")
                        if 'hps' in results:
                            details.append(f"HPS: {results['hps']:.2f}")
                    
                    detail_str = " | ".join(details) if details else "无详细数据"
                    report_content += f"计算 {i}: {operator_name} - {calc_type}\n"
                    report_content += f"时间: {created_at}\n"
                    report_content += f"详情: {detail_str}\n\n"
                    
                except Exception as e:
                    logger.warning(f"处理计算记录 {i} 失败: {e}")
                    report_content += f"计算 {i}: 数据解析失败\n\n"
            
            # 添加计算记录
            report_content += f"\n最近计算记录 (前10个)\n{'-'*20}\n"
            for i, record in enumerate(calc_records[:10], 1):
                report_content += f"{i:2d}. {record.get('operator_name', '未知'):12s} | {record.get('calculation_type', ''):15s} | {str(record.get('created_at', ''))[:19]}\n"
            
            report_content += f"\n\n报告结束\n生成时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 写入文本文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            messagebox.showinfo("导出成功", f"文本报告已导出到: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"生成文本报告失败: {e}")
            messagebox.showerror("导出失败", f"生成文本报告失败：\n{str(e)}")
            return False
    
    def generate_complete_analysis_report_with_charts(self, format_type: str, filename: str = None, current_charts: List = None) -> bool:
        """
        生成包含当前图表的完整分析报告
        
        Args:
            format_type: 报告格式 ('pdf', 'html')
            filename: 输出文件路径
            current_charts: 当前显示的图表列表
            
        Returns:
            是否生成成功
        """
        try:
            if filename is None:
                if format_type == 'pdf':
                    filename = filedialog.asksaveasfilename(
                        title="导出PDF分析报告(包含图表)",
                        defaultextension=".pdf",
                        filetypes=[("PDF 文件", "*.pdf")]
                    )
                elif format_type == 'html':
                    filename = filedialog.asksaveasfilename(
                        title="导出HTML分析报告(包含图表)",
                        defaultextension=".html",
                        filetypes=[("HTML 文件", "*.html")]
                    )
                
            if not filename:
                return False
            
            # 获取报告数据
            data = self._collect_report_data()
            current_time = datetime.now()
            
            # 保存当前图表
            chart_paths = []
            if current_charts:
                base_filename = filename.rsplit('.', 1)[0]
                chart_paths = self._save_current_charts_as_images(current_charts, base_filename)
            
            if format_type == 'pdf':
                return self.generate_pdf_report_with_charts(filename, data['stats'], data['operators'], data['calc_records'], data['recent_calculations'], current_time, chart_paths)
            elif format_type == 'html':
                return self.generate_html_report_with_charts(filename, data['stats'], data['operators'], data['calc_records'], data['recent_calculations'], current_time, chart_paths)
            else:
                messagebox.showerror("错误", f"不支持的报告格式: {format_type}")
                return False
                
        except Exception as e:
            logger.error(f"生成{format_type}报告失败: {e}")
            messagebox.showerror("生成失败", f"生成{format_type}报告失败：\n{str(e)}")
            return False
    
    def _save_current_charts_as_images(self, current_charts: List, base_filename: str) -> List[str]:
        """将当前图表保存为图片文件"""
        chart_paths = []
        
        try:
            for i, chart_info in enumerate(current_charts):
                try:
                    figure = chart_info.get('figure')
                    title = chart_info.get('title', f'图表_{i+1}')
                    
                    if figure:
                        # 清理文件名中的非法字符
                        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        chart_path = f"{base_filename}_{safe_title}.png"
                        
                        # 保存图表
                        figure.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
                        chart_paths.append(chart_path)
                        
                        logger.info(f"已保存图表: {chart_path}")
                        
                except Exception as e:
                    logger.warning(f"保存图表 {i} 失败: {e}")
                    
        except Exception as e:
            logger.error(f"保存当前图表失败: {e}")
        
        return chart_paths
    
    def generate_pdf_report_with_charts(self, filename: str, stats: Dict, operators: List, calc_records: List, recent_calculations: List, timestamp: datetime, chart_paths: List[str] = None) -> bool:
        """生成包含图表的PDF报告"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 注册中文字体 - 修复版本
            chinese_font = 'Helvetica'  # 默认字体
            try:
                # 尝试注册系统中文字体
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
                    "C:/Windows/Fonts/simsun.ttc",    # 宋体
                    "C:/Windows/Fonts/simhei.ttf",    # 黑体
                    "/System/Library/Fonts/PingFang.ttc",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Linux
                ]
                
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            # 对于TTC字体文件，需要指定子字体
                            if font_path.endswith('.ttc'):
                                # 微软雅黑和宋体是TTC文件，需要特殊处理
                                if 'msyh' in font_path:
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                                elif 'simsun' in font_path:
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                                else:
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                            else:
                                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                            
                            chinese_font = 'ChineseFont'
                            font_registered = True
                            logger.info(f"成功注册中文字体: {font_path}")
                            break
                        except Exception as font_error:
                            logger.debug(f"注册字体 {font_path} 失败: {font_error}")
                            continue
                
                if not font_registered:
                    logger.warning("无法注册中文字体，将使用默认字体")
                    
            except Exception as e:
                logger.warning(f"注册中文字体过程失败: {e}")
            
            # 创建PDF文档
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # 创建支持中文的样式
            title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Title'],
                fontName=chinese_font,
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # 居中
                fontFamily=chinese_font
            )
            
            heading_style = ParagraphStyle(
                'ChineseHeading',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=14,
                spaceAfter=12,
                fontFamily=chinese_font
            )
            
            normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10,
                spaceAfter=6,
                fontFamily=chinese_font
            )
            
            # 标题
            story.append(Paragraph("塔防游戏伤害分析报告", title_style))
            story.append(Spacer(1, 12))
            
            # 生成时间
            story.append(Paragraph(f"生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 20))
            
            # 统计摘要
            story.append(Paragraph("统计摘要", heading_style))
            stats_data = [
                ['项目', '数值'],
                ['干员总数', str(stats.get('total_operators', 0))],
                ['导入记录', str(stats.get('total_imports', 0))],
                ['计算记录', str(stats.get('total_calculations', 0))],
                ['今日计算', str(stats.get('today_calculations', 0))]
            ]
            
            # 添加职业分布统计
            class_dist = stats.get('class_distribution', {})
            for class_type, count in class_dist.items():
                stats_data.append([f'{class_type}职业', str(count)])
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # 添加用户生成的图表
            if chart_paths:
                story.append(Paragraph("用户生成的分析图表", heading_style))
                story.append(Paragraph("以下图表来自用户在图表对比面板中实际生成的分析结果", normal_style))
                story.append(Spacer(1, 10))
                
                for i, chart_path in enumerate(chart_paths):
                    if os.path.exists(chart_path):
                        try:
                            chart_name = os.path.basename(chart_path).replace('.png', '')
                            story.append(Paragraph(f"图表 {i+1}: {chart_name}", heading_style))
                            
                            # 调整图片大小适合页面，保持宽高比
                            try:
                                # 读取图片尺寸
                                from PIL import Image as PILImage
                                with PILImage.open(chart_path) as pil_img:
                                    img_width, img_height = pil_img.size
                                    
                                # 计算合适的显示尺寸（最大宽度6英寸）
                                max_width = 6 * inch
                                max_height = 4 * inch
                                
                                # 保持宽高比
                                scale = min(max_width / img_width, max_height / img_height)
                                display_width = img_width * scale
                                display_height = img_height * scale
                                
                            except ImportError:
                                # 如果没有PIL，使用默认尺寸
                                display_width = 6 * inch
                                display_height = 4 * inch
                            except Exception as e:
                                logger.warning(f"读取图片尺寸失败: {e}")
                                display_width = 6 * inch
                                display_height = 4 * inch
                            
                            # 插入图片
                            img = Image(chart_path, width=display_width, height=display_height)
                            story.append(img)
                            story.append(Spacer(1, 15))
                            
                            # 如果还有更多图表，添加分页
                            if i < len(chart_paths) - 1:
                                story.append(PageBreak())
                        
                        except Exception as e:
                            logger.warning(f"添加图表 {chart_path} 失败: {e}")
                            # 添加错误提示
                            error_text = f"图表显示失败: {os.path.basename(chart_path)}"
                            story.append(Paragraph(error_text, normal_style))
                            story.append(Spacer(1, 10))
                
                # 图表部分结束后添加分页
                story.append(PageBreak())
            else:
                # 如果没有用户生成的图表，添加说明
                story.append(Paragraph("图表分析", heading_style))
                story.append(Paragraph("当前没有用户生成的图表。请在图表对比面板中选择干员并生成图表。", normal_style))
                story.append(Spacer(1, 20))
            
            # 添加计算结果部分 - 这是修复的关键部分
            if recent_calculations:
                story.append(Paragraph("用户计算结果详情", heading_style))
                story.append(Paragraph(f"包含 {len(recent_calculations)} 条用户实际的计算记录", normal_style))
                story.append(Spacer(1, 10))
                
                for i, calc in enumerate(recent_calculations, 1):
                    try:
                        # 获取计算信息
                        operator_name = calc.get('operator_name', '未知干员')
                        calc_type = calc.get('calculation_type', '未知计算')
                        created_at = str(calc.get('created_at', ''))[:19]
                        parameters = calc.get('parameters', {})
                        results = calc.get('results', {})
                        
                        # 计算标题
                        story.append(Paragraph(f"计算 {i}: {operator_name} - {calc_type}", heading_style))
                        
                        # 计算时间
                        story.append(Paragraph(f"计算时间: {created_at}", normal_style))
                        
                        # 计算参数
                        param_info = []
                        if 'enemy_def' in parameters:
                            param_info.append(f"敌人防御: {parameters['enemy_def']}")
                        if 'enemy_mdef' in parameters:
                            param_info.append(f"敌人法抗: {parameters['enemy_mdef']}")
                        if 'calc_mode_display' in parameters:
                            param_info.append(f"计算模式: {parameters['calc_mode_display']}")
                        if 'attack_type' in parameters:
                            param_info.append(f"攻击类型: {parameters['attack_type']}")
                        
                        if param_info:
                            story.append(Paragraph(f"计算参数: {' | '.join(param_info)}", normal_style))
                        
                        # 计算结果 - 检查是否是多干员对比
                        if '多干员对比' in calc_type and 'detailed_table' in results:
                            # 多干员对比结果
                            detailed_table = results['detailed_table']
                            if detailed_table:
                                # 对比汇总
                                summary_info = []
                                if 'max_dps' in results:
                                    summary_info.append(f"最大DPS: {results['max_dps']:.2f}")
                                if 'avg_dps' in results:
                                    summary_info.append(f"平均DPS: {results['avg_dps']:.2f}")
                                if 'max_efficiency' in results:
                                    summary_info.append(f"最大性价比: {results['max_efficiency']:.2f}")
                                
                                if summary_info:
                                    story.append(Paragraph(f"对比汇总: {' | '.join(summary_info)}", normal_style))
                                
                                # 详细数据表格
                                table_data = [['干员名称', '职业类型', 'DPS', 'DPH', '性价比']]
                                for row in detailed_table[:10]:  # 限制显示前10个干员
                                    table_data.append([
                                        str(row.get('干员名称', '')),
                                        str(row.get('职业类型', '')),
                                        f"{float(row.get('DPS', 0)):.2f}",
                                        f"{float(row.get('DPH', 0)):.2f}",
                                        f"{float(row.get('性价比', 0)):.2f}"
                                    ])
                                
                                if len(detailed_table) > 10:
                                    table_data.append(['...', '...', '...', '...', '...'])
                                    table_data.append(['', f"共 {len(detailed_table)} 个干员", '', '', ''])
                                
                                calc_table = Table(table_data)
                                calc_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                story.append(calc_table)
                        else:
                            # 单干员计算结果
                            result_info = []
                            if 'dps' in results:
                                result_info.append(f"DPS: {results['dps']:.2f}")
                            if 'dph' in results:
                                result_info.append(f"单发伤害: {results['dph']:.2f}")
                            if 'total_damage' in results:
                                result_info.append(f"总伤害: {results['total_damage']:.0f}")
                            if 'armor_break' in results:
                                result_info.append(f"破甲线: {results['armor_break']}")
                            if 'hps' in results:
                                result_info.append(f"治疗量: {results['hps']:.2f}")
                            
                            if result_info:
                                story.append(Paragraph(f"计算结果: {' | '.join(result_info)}", normal_style))
                        
                        story.append(Spacer(1, 15))
                        
                        # 如果还有更多计算记录，且当前不是最后一条，添加分隔线
                        if i < len(recent_calculations):
                            story.append(Paragraph("─" * 50, normal_style))
                            story.append(Spacer(1, 10))
                    
                    except Exception as e:
                        logger.warning(f"处理计算记录 {i} 失败: {e}")
                        story.append(Paragraph(f"计算 {i}: 数据解析失败", normal_style))
                        story.append(Spacer(1, 10))
                
                # 计算结果部分结束
                story.append(PageBreak())
            else:
                # 如果没有计算记录，添加说明
                story.append(Paragraph("计算结果", heading_style))
                story.append(Paragraph("当前没有计算记录。请在应用中进行一些计算分析。", normal_style))
                story.append(Spacer(1, 20))
            
            # 干员数据表格 - 限制显示前20个干员以避免PDF过长
            if operators:
                story.append(Paragraph("干员数据", heading_style))
                
                # 构建表格数据
                table_data = [['干员名称', '职业类型', '攻击力', '生命值', '攻击类型']]
                display_operators = operators[:20]  # 只显示前20个干员
                
                for op in display_operators:
                    table_data.append([
                        str(op.get('name', '')),
                        str(op.get('class_type', '')),
                        str(op.get('atk', '')),
                        str(op.get('hp', '')),
                        str(op.get('atk_type', ''))
                    ])
                
                if len(operators) > 20:
                    table_data.append(['...', '...', '...', '...', '...'])
                    table_data.append(['', f"共 {len(operators)} 个干员", '', '', ''])
                
                operators_table = Table(table_data)
                operators_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(operators_table)
                story.append(Spacer(1, 20))
            
            # 生成PDF
            doc.build(story)
            
            calc_info = f"包含 {len(recent_calculations)} 条计算结果" if recent_calculations else "未包含计算结果"
            chart_info = f"包含 {len(chart_paths)} 个用户生成的图表" if chart_paths else "未包含图表（用户未生成图表）"
            messagebox.showinfo("导出成功", f"PDF报告已导出到: {filename}\n{calc_info} | {chart_info}")
            return True
            
        except Exception as e:
            logger.error(f"生成PDF报告失败: {e}")
            messagebox.showerror("导出失败", f"生成PDF报告失败：\n{str(e)}")
            return False
    
    def generate_html_report_with_charts(self, filename: str, stats: Dict, operators: List, calc_records: List, recent_calculations: List, timestamp: datetime, chart_paths: List[str] = None) -> bool:
        """生成包含图表的HTML报告"""
        try:
            import base64
            
            html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>塔防游戏伤害分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .chart-section {{ margin: 30px 0; text-align: center; }}
        .chart-image {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; }}
        .chart-description {{ margin: 10px 0; font-style: italic; color: #666; }}
        .no-charts {{ background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 塔防游戏伤害分析报告</h1>
        
        <div class="summary">
            <h2>📊 数据概览</h2>
            <p><strong>报告生成时间:</strong> {timestamp}</p>
            <p><strong>干员总数:</strong> {total_operators} 个</p>
            <p><strong>导入记录:</strong> {total_imports} 条</p>
            <p><strong>计算记录:</strong> {total_calculations} 条</p>
            <p><strong>今日计算:</strong> {today_calculations} 次</p>
        </div>
        
        {charts_section}
        
        <h2>📋 干员数据概览</h2>
        <table>
            <thead>
                <tr>
                    <th>名称</th>
                    <th>职业</th>
                    <th>攻击力</th>
                    <th>生命值</th>
                    <th>防御力</th>
                    <th>费用</th>
                </tr>
            </thead>
            <tbody>
                {operator_rows}
            </tbody>
        </table>
        
        <h2>📈 前4次计算结果详情</h2>
        <table>
            <thead>
                <tr>
                    <th>计算编号</th>
                    <th>干员名称</th>
                    <th>计算类型</th>
                    <th>计算时间</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 生成图表部分
            charts_section = ""
            if chart_paths:
                charts_section = f"<h2>📈 用户生成的分析图表 (共{len(chart_paths)}个)</h2>"
                charts_section += "<p class='chart-description'>以下图表来自用户在图表对比面板中实际生成的分析结果</p>"
                
                for i, chart_path in enumerate(chart_paths, 1):
                    if os.path.exists(chart_path):
                        try:
                            # 将图片转换为base64编码内嵌到HTML中
                            with open(chart_path, 'rb') as img_file:
                                img_data = base64.b64encode(img_file.read()).decode()
                                chart_name = os.path.basename(chart_path).replace('.png', '')
                                charts_section += f"""
                                <div class="chart-section">
                                    <h3>图表 {i}: {chart_name}</h3>
                                    <img src="data:image/png;base64,{img_data}" class="chart-image" alt="{chart_name}">
                                    <p class="chart-description">用户在图表对比面板中生成的分析图表</p>
                                </div>
                                """
                        except Exception as e:
                            logger.warning(f"处理图表 {chart_path} 失败: {e}")
                            charts_section += f"""
                            <div class="chart-section">
                                <h3>图表 {i}: 加载失败</h3>
                                <p>图表文件 {os.path.basename(chart_path)} 无法加载</p>
                            </div>
                            """
            else:
                # 如果没有用户生成的图表，显示提示
                charts_section = """
                <h2>📈 图表分析</h2>
                <div class="no-charts">
                    <p><strong>当前没有用户生成的图表</strong></p>
                    <p>要在报告中包含图表，请按以下步骤操作：</p>
                    <ol>
                        <li>前往"图表对比"标签页</li>
                        <li>选择要分析的干员</li>
                        <li>选择图表类型（折线图、柱状图、饼图等）</li>
                        <li>点击"生成图表"按钮</li>
                        <li>重新导出报告</li>
                    </ol>
                </div>
                """
            
            # 生成干员数据行
            operator_rows = ""
            for op in operators[:20]:  # 限制显示前20个
                operator_rows += f"""
                <tr>
                    <td>{op.get('name', '')}</td>
                    <td>{op.get('class_type', '')}</td>
                    <td>{op.get('atk', 0)}</td>
                    <td>{op.get('hp', 0)}</td>
                    <td>{op.get('def', 0)}</td>
                    <td>{op.get('cost', 0)}</td>
                </tr>
                """
            
            # 填充模板
            html_final = html_content.format(
                timestamp=timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                total_operators=stats.get('total_operators', 0),
                total_imports=stats.get('total_imports', 0),
                total_calculations=stats.get('total_calculations', 0),
                today_calculations=stats.get('today_calculations', 0),
                charts_section=charts_section,
                operator_rows=operator_rows
            )
            
            # 添加前4次计算结果详情
            if recent_calculations:
                for i, calc in enumerate(recent_calculations, 1):
                    try:
                        # 计算基本信息
                        operator_name = calc.get('operator_name', '未知干员')
                        calc_type = calc.get('calculation_type', '未知计算')
                        created_at = str(calc.get('created_at', ''))[:19]
                        
                        # 解析参数和结果
                        parameters = calc.get('parameters', {})
                        results = calc.get('results', {})
                        
                        # 检查是否是多干员对比计算
                        if '多干员对比' in calc_type and 'detailed_table' in results:
                            # 显示多干员对比的详细表格
                            detailed_table = results['detailed_table']
                            if detailed_table:
                                html_final += f"""
                        <tr>
                            <td colspan="4">
                                <h4>计算 {i}: {calc_type} - {len(detailed_table)}个干员对比</h4>
                                <p><strong>计算时间:</strong> {created_at}</p>
                                <p><strong>计算参数:</strong> 敌防{parameters.get('enemy_def', 0)}, 敌法抗{parameters.get('enemy_mdef', 0)}, {parameters.get('calc_mode_display', '未知模式')}</p>
                                
                                <table style="width: 100%; margin: 10px 0; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background-color: #007bff; color: white;">
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">干员名称</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">职业类型</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击类型</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击力</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">攻击速度</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">生命值</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">部署费用</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">DPS</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">DPH</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">破甲线</th>
                                            <th style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">性价比</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                """
                                
                                for row in detailed_table:
                                    html_final += f"""
                                        <tr style="background-color: #f8f9fa;">
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('干员名称', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('职业类型', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('攻击类型', '')}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('攻击力', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('攻击速度', 0)):.1f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('生命值', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('部署费用', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('DPS', 0)):.2f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('DPH', 0)):.2f}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{row.get('破甲线', 0)}</td>
                                            <td style="border: 1px solid #ddd; padding: 6px; font-size: 11px;">{float(row.get('性价比', 0)):.2f}</td>
                                        </tr>
                                    """
                                
                                html_final += f"""
                                    </tbody>
                                </table>
                                
                                <p style="margin: 10px 0; font-style: italic; color: #666;">
                                    <strong>对比汇总:</strong> 最大DPS {results.get('max_dps', 0):.2f}, 平均DPS {results.get('avg_dps', 0):.2f}, 最大性价比 {results.get('max_efficiency', 0):.2f}
                                </p>
                            </td>
                        </tr>
                        """
                        else:
                            # 单干员计算的简化显示
                            # 构建参数字符串
                            param_details = []
                            if 'enemy_def' in parameters:
                                param_details.append(f"敌人防御: {parameters['enemy_def']}")
                            if 'enemy_mdef' in parameters:
                                param_details.append(f"敌人法抗: {parameters['enemy_mdef']}")
                            if 'attack_type' in parameters:
                                param_details.append(f"攻击类型: {parameters['attack_type']}")
                            
                            # 构建结果字符串
                            result_details = []
                            if 'dps' in results:
                                result_details.append(f"DPS: {results['dps']:.2f}")
                            if 'dph' in results:
                                result_details.append(f"单发伤害: {results['dph']:.2f}")
                            if 'total_damage' in results:
                                result_details.append(f"总伤害: {results['total_damage']:.0f}")
                            if 'hps' in results:
                                result_details.append(f"HPS: {results['hps']:.2f}")
                            
                            html_final += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{operator_name}</td>
                            <td>{calc_type}</td>
                            <td>{created_at}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td colspan="4" style="font-style: italic; color: #666;">
                                <strong>计算参数:</strong> {' | '.join(param_details) if param_details else '无参数信息'}<br>
                                <strong>计算结果:</strong> {' | '.join(result_details) if result_details else '无结果信息'}
                            </td>
                        </tr>
                        """
                        
                    except Exception as e:
                        logger.warning(f"处理计算记录 {i} 失败: {e}")
                        html_final += f"""
                        <tr>
                            <td>{i}</td>
                            <td>数据解析失败</td>
                            <td>数据解析失败</td>
                            <td>数据解析失败</td>
                        </tr>
                        """
            
            html_final += """
            </tbody>
        </table>
        
        <h2>📈 最近计算记录 (前10个)</h2>
        <table>
            <thead>
                <tr>
                    <th>干员名称</th>
                    <th>计算类型</th>
                    <th>创建时间</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 添加计算记录
            for record in calc_records[:10]:
                html_final += f"""
                <tr>
                    <td>{record.get('operator_name', '未知')}</td>
                    <td>{record.get('calculation_type', '')}</td>
                    <td>{str(record.get('created_at', ''))[:19]}</td>
                </tr>
"""
            
            html_final += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p>报告由塔防游戏伤害分析器自动生成 | 生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
            
            # 写入HTML文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_final)
            
            chart_info = f"包含 {len(chart_paths)} 个用户生成的图表" if chart_paths else "未包含图表（用户未生成图表）"
            messagebox.showinfo("导出成功", f"HTML报告已导出到: {filename}\n{chart_info}")
            return True
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            messagebox.showerror("生成失败", f"生成HTML报告失败：\n{str(e)}")
            return False 
    
    def generate_complete_analysis_report_with_charts_and_calculations(self, format_type: str, filename: str = None, current_charts: List = None, current_calculations: List = None) -> bool:
        """
        生成包含当前图表和用户计算结果的完整分析报告
        
        Args:
            format_type: 报告格式 ('pdf', 'html')
            filename: 输出文件路径
            current_charts: 当前显示的图表列表
            current_calculations: 用户当前的计算结果列表
            
        Returns:
            是否生成成功
        """
        try:
            if filename is None:
                if format_type == 'pdf':
                    filename = filedialog.asksaveasfilename(
                        title="导出PDF分析报告(包含图表和计算结果)",
                        defaultextension=".pdf",
                        filetypes=[("PDF 文件", "*.pdf")]
                    )
                elif format_type == 'html':
                    filename = filedialog.asksaveasfilename(
                        title="导出HTML分析报告(包含图表和计算结果)",
                        defaultextension=".html",
                        filetypes=[("HTML 文件", "*.html")]
                    )
                
            if not filename:
                return False
            
            # 获取报告数据
            data = self._collect_report_data()
            
            # 使用传入的用户计算结果替换数据库中的历史记录
            if current_calculations is not None:
                data['recent_calculations'] = current_calculations
                logger.info(f"使用用户当前的 {len(current_calculations)} 条计算结果")
            else:
                logger.info(f"使用数据库中的 {len(data.get('recent_calculations', []))} 条历史计算记录")
            
            current_time = datetime.now()
            
            # 保存当前图表
            chart_paths = []
            if current_charts:
                base_filename = filename.rsplit('.', 1)[0]
                chart_paths = self._save_current_charts_as_images(current_charts, base_filename)
                logger.info(f"保存了 {len(chart_paths)} 个用户生成的图表")
            
            success = False
            if format_type == 'pdf':
                success = self.generate_pdf_report_with_charts(
                    filename,
                    data['stats'],
                    data['operators'],
                    data['calc_records'],
                    data['recent_calculations'],  # 使用更新后的计算结果
                    current_time,
                    chart_paths
                )
            elif format_type == 'html':
                success = self.generate_html_report_with_charts(
                    filename,
                    data['stats'],
                    data['operators'],
                    data['calc_records'],
                    data['recent_calculations'],  # 使用更新后的计算结果
                    current_time,
                    chart_paths
                )
            else:
                messagebox.showerror("错误", f"不支持的报告格式: {format_type}")
                return False
            
            # 显示成功消息
            if success:
                chart_info = f"\n包含 {len(chart_paths)} 个用户生成的图表" if chart_paths else "\n未包含图表（用户未生成图表）"
                calc_info = f"\n包含 {len(data['recent_calculations'])} 条计算结果" if data['recent_calculations'] else "\n未包含计算结果"
                total_operators = len(data['operators'])
                
                messagebox.showinfo(
                    "导出成功", 
                    f"{format_type.upper()}报告已导出到: {filename}\n"
                    f"共导出 {total_operators} 个干员数据{chart_info}{calc_info}"
                )
                logger.info(f"{format_type}报告导出成功: {filename}")
            
            return success
                
        except Exception as e:
            logger.error(f"生成{format_type}报告失败: {e}")
            messagebox.showerror("生成失败", f"生成{format_type}报告失败：\n{str(e)}")
            return False