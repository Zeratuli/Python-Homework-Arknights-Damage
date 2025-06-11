# 🎯Python期末大作业-明日方舟伤害计算分析器



[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![ttkbootstrap](https://img.shields.io/badge/GUI-ttkbootstrap-green.svg)](https://ttkbootstrap.readthedocs.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue.svg)](https://www.sqlite.org/)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](CHANGELOG.md)



**📊 项目统计信息**
![File Count](https://img.shields.io/badge/Files-80+-blue)
![Language](https://img.shields.io/badge/Language-Python-yellow)



---

## 📖 项目简介

这是我个人为Python期末大作业做的一个Python程序，README拿AI写的，目前只支持基础伤害计算，不打算更新与维护，仅供学习交流使用。



### 技术栈详情
| 分层 | 技术选型 | 版本要求 | 用途说明 |
|------|----------|----------|----------|
| **前端界面** | ttkbootstrap | ≥1.10.1 | 现代化GUI框架 |
| **数据可视化** | matplotlib | ≥3.6.0 | 图表绘制 |
| **数据处理** | pandas + numpy | ≥1.5.0 | 数据分析和处理 |
| **数据存储** | SQLite | 内置 | 轻量级数据库 |
| **文档生成** | reportlab | 可选 | PDF报告生成 |
| **配置管理** | JSON | 内置 | 配置文件格式 |

---



## 💻 系统要求

### 最低配置要求
| 项目 | 要求 | 推荐 |
|------|------|------|
| **操作系统** | Windows 10+ | Windows 11 |
| **Python版本** | Python 3.8+ | Python 3.10+ |
| **内存** | 4GB RAM | 8GB RAM |
| **存储空间** | 500MB 可用空间 | 1GB 可用空间 |
| **显示器** | 1280×720 分辨率 | 1920×1080 分辨率 |

### 兼容性说明
- ✅ **Windows**: 完全支持，推荐Windows 10/11

---



## 🚀 安装指南

### 方法一：快速安装（推荐）

#### 1. 克隆项目
```bash
git clone https://github.com/zeratuli/damage_analyzer.git
cd damage_analyzer
```

#### 2. 创建虚拟环境
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 启动程序
```bash
python analyzer_main.py
```



### 方法二：手动安装

#### 1. 安装Python
- 访问 [Python官网](https://www.python.org/) 下载Python 3.8+
- 安装时勾选"Add Python to PATH"

#### 2. 安装依赖包
```bash
pip install ttkbootstrap>=1.10.1
pip install matplotlib>=3.6.0
pip install pandas>=1.5.0
pip install numpy>=1.21.0
pip install openpyxl>=3.0.0
pip install seaborn>=0.11.0
```

#### 3. 下载项目文件
- 下载项目ZIP文件并解压
- 或使用git克隆项目

#### 4. 运行程序
```bash
cd damage_analyzer
python analyzer_main.py
```



---

## ⚡ 快速开始

### 5分钟上手指南

#### 第一步：启动程序
```bash
cd damage_analyzer
python analyzer_main.py
```

#### 第二步：添加干员数据
1. 点击 **"干员管理"** 标签页
2. 点击 **"添加新干员"** 按钮
3. 填写干员基本信息
4. 点击 **"保存"** 完成添加

当然可以自己导入，这里要键值对匹配



## 

### 项目结构

```
damage_analyzer/
├── 📁 core/                    # 核心计算引擎
│   ├── damage_calculator.py    # 伤害计算算法
│   └── __init__.py
├── 📁 ui/                      # 用户界面模块
│   ├── main_window.py          # 主窗口
│   ├── calculation_panel.py    # 计算面板
│   ├── comparison_panel.py     # 对比面板
│   ├── chart_panel.py          # 图表面板
│   ├── operator_editor.py      # 干员编辑器
│   ├── settings_dialog.py      # 设置对话框
│   ├── theme_manager.py        # 主题管理器
│   ├── font_manager.py         # 字体管理器
│   └── components/             # UI组件
│       └── sortable_treeview.py
├── 📁 data/                    # 数据管理模块
│   ├── database_manager.py     # 数据库管理
│   ├── import_export_manager.py # 导入导出管理
│   ├── excel_handler.py        # Excel处理
│   ├── csv_handler.py          # CSV处理
│   └── json_handler.py         # JSON处理
├── 📁 visualization/           # 数据可视化模块
│   ├── chart_factory.py        # 图表工厂
│   └── enhanced_chart_factory.py
├── 📁 utils/                   # 工具模块
│   ├── report_generator.py     # 报告生成器
│   ├── event_manager.py        # 事件管理
│   └── __init__.py
├── 📁 config/                  # 配置管理
│   ├── config_manager.py       # 配置管理器
│   └── app_config.json         # 应用配置文件
├── 📄 analyzer_main.py         # 程序入口文件
├── 📄 requirements.txt         # 依赖包列表
├── 📄 damage_analyzer.db       # SQLite数据库
├── 📄 damage_analyzer.log      # 日志文件
└── 📄 README.md               # 项目说明文档
```





如果这个项目对你有帮助，别忘了点击star支持一下！
