#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows热键冲突检测器
功能：
- 检测系统级热键
- 检测应用程序热键
- 检测当前活动窗口热键
- 检测注册表中的热键
- 分析和显示冲突
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
from datetime import datetime
import logging
import sys
import os

# 尝试导入Windows相关模块
try:
    import win32api
    import win32con
    import win32gui
    import win32process
    import winreg
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("警告: win32api模块未安装，某些功能可能无法使用")
    print("请运行: pip install pywin32 psutil")

class HotkeyInfo:
    """热键信息类"""
    def __init__(self, key_combination, application, hotkey_type, description="", process_id=None):
        self.key_combination = key_combination
        self.application = application
        self.hotkey_type = hotkey_type  # 'system', 'application', 'registry', 'window'
        self.description = description
        self.process_id = process_id
        self.detected_time = datetime.now()

    def to_dict(self):
        return {
            'key_combination': self.key_combination,
            'application': self.application,
            'hotkey_type': self.hotkey_type,
            'description': self.description,
            'process_id': self.process_id,
            'detected_time': self.detected_time.isoformat()
        }

class SystemHotkeyDetector:
    """系统级热键检测器"""

    def __init__(self):
        self.system_hotkeys = []

    def detect_system_hotkeys(self):
        """检测Windows系统热键"""
        system_hotkeys = [
            HotkeyInfo("Win+R", "Windows", "system", "运行对话框"),
            HotkeyInfo("Win+E", "Windows", "system", "文件资源管理器"),
            HotkeyInfo("Win+L", "Windows", "system", "锁定计算机"),
            HotkeyInfo("Win+D", "Windows", "system", "显示桌面"),
            HotkeyInfo("Alt+Tab", "Windows", "system", "切换窗口"),
            HotkeyInfo("Ctrl+Shift+Esc", "Windows", "system", "任务管理器"),
            HotkeyInfo("Win+Tab", "Windows", "system", "任务视图"),
            HotkeyInfo("Win+I", "Windows", "system", "设置"),
            HotkeyInfo("Win+X", "Windows", "system", "快速链接菜单"),
            HotkeyInfo("Win+Pause", "Windows", "system", "系统属性"),
        ]

        self.system_hotkeys = system_hotkeys
        return system_hotkeys

class RegistryHotkeyDetector:
    """注册表热键检测器"""

    def __init__(self):
        self.registry_hotkeys = []

    def detect_registry_hotkeys(self):
        """从注册表检测热键"""
        if not HAS_WIN32:
            return []

        hotkeys = []

        # 检查常见的注册表位置
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"),
        ]

        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, reg_type = winreg.EnumValue(key, i)
                            if 'hotkey' in name.lower() or 'shortcut' in name.lower():
                                hotkey_info = HotkeyInfo(
                                    key_combination=f"{name}={value}",
                                    application="Registry",
                                    hotkey_type="registry",
                                    description=f"注册表热键: {path}"
                                )
                                hotkeys.append(hotkey_info)
                            i += 1
                        except WindowsError:
                            break
            except FileNotFoundError:
                continue
            except PermissionError:
                continue

        self.registry_hotkeys = hotkeys
        return hotkeys

class ApplicationHotkeyDetector:
    """应用程序热键检测器"""

    def __init__(self):
        self.app_hotkeys = []

    def detect_application_hotkeys(self):
        """检测应用程序热键"""
        if not HAS_WIN32:
            return []

        hotkeys = []

        try:
            # 获取所有运行中的进程
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['exe'] and os.path.exists(proc_info['exe']):
                        # 检查是否有已知的热键注册
                        app_name = proc_info['name']

                        # 检查一些常见应用的热键
                        known_hotkeys = self._get_known_app_hotkeys(app_name)
                        for hotkey in known_hotkeys:
                            hotkey_info = HotkeyInfo(
                                key_combination=hotkey['key'],
                                application=app_name,
                                hotkey_type="application",
                                description=hotkey['desc'],
                                process_id=proc_info['pid']
                            )
                            hotkeys.append(hotkey_info)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            logging.error(f"检测应用程序热键时出错: {e}")

        self.app_hotkeys = hotkeys
        return hotkeys

    def _get_known_app_hotkeys(self, app_name):
        """获取已知应用程序的热键"""
        known_hotkeys = {
            'chrome.exe': [
                {'key': 'Ctrl+T', 'desc': '新标签页'},
                {'key': 'Ctrl+W', 'desc': '关闭标签页'},
                {'key': 'Ctrl+Shift+T', 'desc': '重新打开关闭的标签页'},
                {'key': 'F12', 'desc': '开发者工具'},
            ],
            'notepad.exe': [
                {'key': 'Ctrl+N', 'desc': '新建文件'},
                {'key': 'Ctrl+S', 'desc': '保存文件'},
                {'key': 'Ctrl+F', 'desc': '查找'},
            ],
            'explorer.exe': [
                {'key': 'Ctrl+N', 'desc': '新建文件夹'},
                {'key': 'F2', 'desc': '重命名'},
                {'key': 'Delete', 'desc': '删除'},
            ],
            'cmd.exe': [
                {'key': 'Ctrl+C', 'desc': '中断命令'},
                {'key': 'Tab', 'desc': '自动完成'},
            ],
        }

        return known_hotkeys.get(app_name.lower(), [])

class ActiveWindowHotkeyDetector:
    """当前活动窗口热键检测器"""

    def __init__(self):
        self.window_hotkeys = []

    def detect_active_window_hotkeys(self):
        """检测当前活动窗口的热键"""
        if not HAS_WIN32:
            return []

        hotkeys = []

        try:
            # 获取当前活动窗口
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                window_text = win32gui.GetWindowText(hwnd)
                thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)

                try:
                    process = psutil.Process(process_id)
                    app_name = process.name()

                    # 获取当前应用的快捷键
                    app_hotkeys = self._get_window_specific_hotkeys(app_name, window_text)

                    for hotkey in app_hotkeys:
                        hotkey_info = HotkeyInfo(
                            key_combination=hotkey['key'],
                            application=f"{app_name} ({window_text})",
                            hotkey_type="window",
                            description=hotkey['desc'],
                            process_id=process_id
                        )
                        hotkeys.append(hotkey_info)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except Exception as e:
            logging.error(f"检测活动窗口热键时出错: {e}")

        self.window_hotkeys = hotkeys
        return hotkeys

    def _get_window_specific_hotkeys(self, app_name, window_title):
        """获取特定窗口的热键"""
        # 根据应用名称和窗口标题返回可能的热键
        hotkeys = []

        if 'notepad' in app_name.lower():
            hotkeys.extend([
                {'key': 'Ctrl+Z', 'desc': '撤销'},
                {'key': 'Ctrl+Y', 'desc': '重做'},
                {'key': 'Ctrl+A', 'desc': '全选'},
            ])
        elif 'chrome' in app_name.lower() or 'firefox' in app_name.lower():
            hotkeys.extend([
                {'key': 'Ctrl+L', 'desc': '地址栏'},
                {'key': 'Ctrl+R', 'desc': '刷新'},
                {'key': 'F5', 'desc': '刷新'},
            ])

        return hotkeys

class ConflictAnalyzer:
    """冲突分析器"""

    def __init__(self):
        self.conflicts = []

    def analyze_conflicts(self, all_hotkeys):
        """分析热键冲突"""
        conflicts = []

        # 按键组合分组
        hotkey_groups = {}
        for hotkey in all_hotkeys:
            key = hotkey.key_combination.lower()
            if key not in hotkey_groups:
                hotkey_groups[key] = []
            hotkey_groups[key].append(hotkey)

        # 查找冲突
        for key_combo, hotkeys in hotkey_groups.items():
            if len(hotkeys) > 1:
                # 检查是否是真正的冲突
                if self._is_real_conflict(hotkeys):
                    conflicts.append({
                        'key_combination': key_combo,
                        'hotkeys': hotkeys,
                        'conflict_type': self._get_conflict_type(hotkeys),
                        'severity': self._get_conflict_severity(hotkeys)
                    })

        self.conflicts = conflicts
        return conflicts

    def _is_real_conflict(self, hotkeys):
        """判断是否是真正的冲突"""
        # 如果所有热键都来自同一个应用，通常不是冲突
        apps = set(h.application for h in hotkeys)
        if len(apps) == 1:
            return False

        # 如果包含系统级热键，可能是冲突
        types = set(h.hotkey_type for h in hotkeys)
        if 'system' in types and len(types) > 1:
            return True

        # 如果有多个不同的应用程序热键，可能是冲突
        if 'application' in types and len(apps) > 1:
            return True

        return len(apps) > 1

    def _get_conflict_type(self, hotkeys):
        """获取冲突类型"""
        types = set(h.hotkey_type for h in hotkeys)

        if 'system' in types:
            return 'system_conflict'
        elif len(types) > 1:
            return 'mixed_conflict'
        else:
            return 'application_conflict'

    def _get_conflict_severity(self, hotkeys):
        """获取冲突严重程度"""
        types = set(h.hotkey_type for h in hotkeys)

        if 'system' in types:
            return 'high'
        elif len(types) > 1:
            return 'medium'
        else:
            return 'low'

if __name__ == "__main__":
    # 基础测试
    print("热键冲突检测器 - 初始化完成")
    print(f"Windows API支持: {'是' if HAS_WIN32 else '否'}")

    if HAS_WIN32:
        # 测试各个检测器
        system_detector = SystemHotkeyDetector()
        system_hotkeys = system_detector.detect_system_hotkeys()
        print(f"检测到 {len(system_hotkeys)} 个系统热键")

        app_detector = ApplicationHotkeyDetector()
        app_hotkeys = app_detector.detect_application_hotkeys()
        print(f"检测到 {len(app_hotkeys)} 个应用程序热键")

        registry_detector = RegistryHotkeyDetector()
        registry_hotkeys = registry_detector.detect_registry_hotkeys()
        print(f"检测到 {len(registry_hotkeys)} 个注册表热键")

        window_detector = ActiveWindowHotkeyDetector()
        window_hotkeys = window_detector.detect_active_window_hotkeys()
        print(f"检测到 {len(window_hotkeys)} 个活动窗口热键")

        # 冲突分析
        all_hotkeys = system_hotkeys + app_hotkeys + registry_hotkeys + window_hotkeys
        analyzer = ConflictAnalyzer()
        conflicts = analyzer.analyze_conflicts(all_hotkeys)
        print(f"检测到 {len(conflicts)} 个潜在冲突")