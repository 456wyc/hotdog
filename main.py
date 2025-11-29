#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键冲突检测器主程序入口
Windows桌面应用程序，用于检测和分析热键冲突
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """检查依赖项"""
    missing_deps = []

    try:
        import win32api
        import win32con
        import win32gui
        import win32process
        import winreg
    except ImportError:
        missing_deps.append("pywin32")

    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")

    return missing_deps

def show_dependency_error(missing_deps):
    """显示依赖错误对话框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    message = "缺少必要的依赖项:\\n\\n"
    for dep in missing_deps:
        message += f"• {dep}\\n"

    message += "\\n请运行以下命令安装依赖:\\n"
    message += "pip install pywin32 psutil\\n\\n"
    message += "是否继续运行程序？（某些功能可能无法使用）"

    result = messagebox.askyesno("依赖检查", message)
    root.destroy()

    return result

def main():
    """主程序入口"""
    try:
        print("热键冲突检测器启动中...")
        print("检查系统兼容性...")

        # 检查操作系统
        if sys.platform != 'win32':
            print("错误: 此程序仅支持Windows系统")
            return

        # 检查Python版本
        if sys.version_info < (3, 6):
            print("错误: 需要Python 3.6或更高版本")
            return

        print("检查依赖项...")
        missing_deps = check_dependencies()

        if missing_deps:
            print(f"警告: 缺少依赖项 {missing_deps}")
            if not show_dependency_error(missing_deps):
                print("用户取消启动")
                return

        print("启动GUI界面...")

        # 导入并启动增强版GUI
        from enhanced_gui import EnhancedHotkeyGUI

        app = EnhancedHotkeyGUI()
        print("增强版GUI界面已创建，开始运行...")
        app.run()

    except ImportError as e:
        error_msg = f"导入模块失败: {e}\\n\\n请确保所有依赖项已正确安装"
        print(f"错误: {error_msg}")

        # 尝试显示错误对话框
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("导入错误", error_msg)
            root.destroy()
        except:
            pass

    except Exception as e:
        error_msg = f"程序启动失败: {e}\\n\\n{traceback.format_exc()}"
        print(f"错误: {error_msg}")

        # 尝试显示错误对话框
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动错误", error_msg)
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()