#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明日方舟伤害计算分析器 - EXE打包脚本
使用PyInstaller将Python项目打包为Windows可执行文件

作者: 项目团队
创建时间: 2024年
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent

def create_spec_file():
    """创建PyInstaller配置文件"""
    project_root = get_project_root()
    main_script = project_root / "damage_analyzer" / "analyzer_main.py"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 项目路径
project_root = Path(r"{project_root}")
damage_analyzer_path = project_root / "damage_analyzer"

block_cipher = None

# 分析主脚本
a = Analysis(
    [str(damage_analyzer_path / "analyzer_main.py")],
    pathex=[str(project_root), str(damage_analyzer_path)],
    binaries=[],
    datas=[
        # 配置文件
        (str(damage_analyzer_path / "config" / "app_config.json"), "config"),
        # 模板文件（如果存在）
        (str(project_root / "干员数据模板_基础模板.xlsx"), "."),
        (str(project_root / "干员数据模板_高级模板.xlsx"), "."),
        # 示例数据（如果存在）
        (str(project_root / "tower_1_kroos.json"), "."),
    ],
    hiddenimports=[
        # 核心模块
        'ttkbootstrap',
        'ttkbootstrap.constants',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.cm',
        'numpy',
        'pandas',
        'pandas.io',
        'pandas.io.excel',
        'openpyxl',
        'seaborn',
        'PIL',
        'PIL.Image',
        'reportlab',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        # 数据库模块
        'sqlite3',
        # 数学和科学计算
        'math',
        'statistics',
        # 系统模块
        'psutil',
        # 字体支持
        'fonttools',
        # UI相关隐藏导入
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.colorchooser',
        'tkinter.simpledialog',
        # matplotlib相关
        'matplotlib.figure',
        'matplotlib.axes',
        'matplotlib.patches',
        'matplotlib.font_manager',
        'mpl_toolkits.mplot3d',
        # 日期时间
        'datetime',
        # 文件处理
        'csv',
        'json',
        'xml',
        'xml.etree',
        'xml.etree.ElementTree',
        # 网络和并发
        'threading',
        'multiprocessing',
        'queue',
        # 数据类型
        'typing',
        'typing_extensions',
        'collections',
        'collections.abc',
        # 其他可能需要的模块
        'logging',
        'logging.handlers',
        'platform',
        'locale',
        'encodings',
        'encodings.utf_8',
        'encodings.cp1252',
        'encodings.gbk',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'IPython',
        'jupyter',
        'notebook',
        'tornado',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'tkinter.test',
        'test',
        'tests',
        'unittest',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 收集所有文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 单文件执行程序
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='明日方舟伤害计算分析器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(damage_analyzer_path / "assets" / "icon.ico"),  # 如果有图标文件，在这里指定
    version=None,
)

# 如果需要目录分发版本，取消注释以下代码
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='DamageAnalyzer'
# )
'''
    
    spec_file = project_root / "damage_analyzer.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    return spec_file

def install_dependencies():
    """安装打包所需的依赖"""
    print("🔧 正在检查和安装依赖...")
    
    try:
        # 检查是否已安装PyInstaller
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("📦 正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=5.0.0"], check=True)
    
    # 安装项目依赖
    requirements_file = get_project_root() / "damage_analyzer" / "requirements.txt"
    if requirements_file.exists():
        print("📦 正在安装项目依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
    
    print("✅ 依赖安装完成")

def clean_build_dirs():
    """清理之前的构建目录"""
    print("🧹 清理构建目录...")
    
    project_root = get_project_root()
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   删除: {{dir_name}}")
    
    # 清理.spec文件
    spec_files = list(project_root.glob("*.spec"))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"   删除: {{spec_file.name}}")

def build_exe():
    """构建EXE文件"""
    print("🚀 开始构建EXE文件...")
    
    project_root = get_project_root()
    
    try:
        # 创建spec文件
        spec_file = create_spec_file()
        print(f"✅ 已创建配置文件: {{spec_file.name}}")
        
        # 执行PyInstaller构建
        build_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",  # 清理临时文件
            "--noconfirm",  # 不询问覆盖
            str(spec_file)
        ]
        
        print("⚡ 正在执行打包命令...")
        print(f"   命令: {{' '.join(build_cmd)}}")
        
        result = subprocess.run(build_cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 构建成功！")
            
            # 检查输出文件
            dist_dir = project_root / "dist"
            exe_file = dist_dir / "明日方舟伤害计算分析器.exe"
            
            if exe_file.exists():
                file_size = exe_file.stat().st_size / (1024 * 1024)  # MB
                print(f"📁 输出文件: {{exe_file}}")
                print(f"📏 文件大小: {{file_size:.1f}} MB")
                
                # 复制示例文件到dist目录
                copy_example_files(dist_dir)
                
                print("🎉 打包完成！")
                print(f"💡 执行文件位置: {{exe_file}}")
            else:
                print("❌ 构建完成但未找到exe文件")
        else:
            print("❌ 构建失败")
            print("错误输出:", result.stderr)
            print("标准输出:", result.stdout)
            
    except Exception as e:
        print(f"❌ 构建过程中发生错误: {{e}}")
        raise

def copy_example_files(dist_dir):
    """复制示例文件到输出目录"""
    print("📋 复制示例文件...")
    
    project_root = get_project_root()
    
    # 要复制的文件列表
    files_to_copy = [
        "干员数据模板_基础模板.xlsx",
        "干员数据模板_高级模板.xlsx", 
        "tower_1_kroos.json"
    ]
    
    for file_name in files_to_copy:
        source_file = project_root / file_name
        if source_file.exists():
            dest_file = dist_dir / file_name
            shutil.copy2(source_file, dest_file)
            print(f"   复制: {{file_name}}")

def create_installer_script():
    """创建安装程序脚本"""
    project_root = get_project_root()
    
    installer_content = '''@echo off
chcp 65001 >nul
echo 明日方舟伤害计算分析器 - 安装程序
echo =======================================
echo.

echo 正在创建程序快捷方式...

set "exe_path=%~dp0明日方舟伤害计算分析器.exe"
set "desktop=%USERPROFILE%\\Desktop"
set "start_menu=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"

if exist "%exe_path%" (
    echo 在桌面创建快捷方式...
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%desktop%\\明日方舟伤害计算分析器.lnk'); $Shortcut.TargetPath = '%exe_path%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"
    
    echo 在开始菜单创建快捷方式...
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%start_menu%\\明日方舟伤害计算分析器.lnk'); $Shortcut.TargetPath = '%exe_path%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"
    
    echo.
    echo ✅ 安装完成！
    echo 📁 程序位置: %~dp0
    echo 🖥️  桌面快捷方式已创建
    echo 📋 开始菜单快捷方式已创建
    echo.
    echo 按任意键启动程序...
    pause >nul
    "%exe_path%"
) else (
    echo ❌ 未找到程序文件！
    echo 请确保此脚本与程序文件在同一目录下
    pause
)
'''
    
    installer_file = project_root / "dist" / "安装.bat"
    installer_file.parent.mkdir(exist_ok=True)
    
    with open(installer_file, 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print(f"✅ 已创建安装脚本: {{installer_file}}")

def create_readme():
    """创建README文件"""
    project_root = get_project_root()
    
    readme_content = '''# 明日方舟伤害计算分析器

## 📖 简介
这是一款专为明日方舟玩家设计的伤害计算分析工具，支持精确的伤害计算、性能分析和数据可视化。

## 🚀 快速开始
1. 双击 `明日方舟伤害计算分析器.exe` 启动程序
2. 或者运行 `安装.bat` 创建桌面快捷方式后启动

## 📁 文件说明
- `明日方舟伤害计算分析器.exe` - 主程序文件
- `干员数据模板_基础模板.xlsx` - Excel导入模板（基础版）
- `干员数据模板_高级模板.xlsx` - Excel导入模板（高级版）
- `tower_1_kroos.json` - JSON格式示例数据
- `安装.bat` - 快捷方式安装脚本

## ✨ 主要功能
- 🧮 精确伤害计算（基于官方公式）
- 📊 数据可视化分析
- 📥 多格式数据导入（Excel/JSON/CSV）
- 📤 多格式数据导出
- 📈 性能对比分析
- 📄 专业报告生成

## 💡 使用提示
1. 首次使用建议导入示例数据熟悉功能
2. 支持拖拽文件到程序窗口进行导入
3. 所有数据本地存储，保护隐私安全
4. 支持明暗主题切换和字体调节

## 🔧 系统要求
- Windows 10 或更高版本
- 至少 4GB 内存
- 100MB 可用磁盘空间

## 📞 技术支持
如遇问题请查看程序内帮助文档或联系技术支持。

---
构建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''
    
    readme_file = project_root / "dist" / "README.txt"
    readme_file.parent.mkdir(exist_ok=True)
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 已创建使用说明: {{readme_file}}")

def main():
    """主函数"""
    print("🎯 明日方舟伤害计算分析器 - EXE构建工具")
    print("=" * 50)
    
    try:
        # 步骤1: 安装依赖
        install_dependencies()
        
        # 步骤2: 清理构建目录
        clean_build_dirs()
        
        # 步骤3: 构建EXE
        build_exe()
        
        # 步骤4: 创建辅助文件
        create_installer_script()
        create_readme()
        
        print("=" * 50)
        print("🎉 构建完成！")
        print("📁 输出目录: dist/")
        print("🚀 运行程序: dist/明日方舟伤害计算分析器.exe")
        print("📦 快速安装: dist/安装.bat")
        
    except Exception as e:
        print(f"❌ 构建失败: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main() 