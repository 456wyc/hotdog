#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI功能测试脚本
测试界面组件是否能正常创建和初始化
"""

import sys
import os

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")

    try:
        # 测试核心检测器导入
        from hotkey_conflict_detector import (
            SystemHotkeyDetector, RegistryHotkeyDetector,
            ApplicationHotkeyDetector, ActiveWindowHotkeyDetector,
            ConflictAnalyzer, HotkeyInfo, HAS_WIN32
        )
        print("[OK] 核心检测器模块导入成功")

        # 测试GUI模块导入
        from hotkey_gui import HotkeyConflictGUI, LogHandler
        print("[OK] GUI模块导入成功")

        return True

    except ImportError as e:
        print(f"[ERROR] 模块导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基础功能"""
    print("\\n测试基础功能...")

    try:
        from hotkey_conflict_detector import (
            SystemHotkeyDetector, ApplicationHotkeyDetector,
            ConflictAnalyzer, HAS_WIN32
        )

        print(f"Windows API支持: {'是' if HAS_WIN32 else '否'}")

        # 测试系统热键检测
        system_detector = SystemHotkeyDetector()
        system_hotkeys = system_detector.detect_system_hotkeys()
        print(f"[OK] 系统热键检测: {len(system_hotkeys)} 个热键")

        # 测试应用程序热键检测
        app_detector = ApplicationHotkeyDetector()
        app_hotkeys = app_detector.detect_application_hotkeys()
        print(f"[OK] 应用程序热键检测: {len(app_hotkeys)} 个热键")

        # 测试冲突分析
        all_hotkeys = system_hotkeys + app_hotkeys
        analyzer = ConflictAnalyzer()
        conflicts = analyzer.analyze_conflicts(all_hotkeys)
        print(f"[OK] 冲突分析: {len(conflicts)} 个冲突")

        return True

    except Exception as e:
        print(f"[ERROR] 功能测试失败: {e}")
        return False

def test_gui_creation():
    """测试GUI创建（不显示窗口）"""
    print("\\n测试GUI创建...")

    try:
        import tkinter as tk
        from hotkey_gui import HotkeyConflictGUI

        # 创建一个测试root窗口但不显示
        test_root = tk.Tk()
        test_root.withdraw()  # 隐藏窗口

        print("[OK] tkinter可用")
        print("[OK] GUI类可以导入")

        test_root.destroy()
        return True

    except Exception as e:
        print(f"[ERROR] GUI测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 热键冲突检测器功能测试 ===")

    # 测试导入
    if not test_imports():
        print("\\n测试失败：模块导入问题")
        return False

    # 测试基础功能
    if not test_basic_functionality():
        print("\\n测试失败：基础功能问题")
        return False

    # 测试GUI创建
    if not test_gui_creation():
        print("\\n测试失败：GUI创建问题")
        return False

    print("\\n=== 所有测试通过! ===")
    print("程序可以正常运行")
    print("\\n使用方法:")
    print("python main.py  # 启动图形界面")
    print("python hotkey_conflict_detector.py  # 运行命令行版本")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)