#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的热键检测器
Enhanced Hotkey Detector

基于原有检测器升级，使用新的数据结构
"""

import logging
import time
from datetime import datetime
from typing import List, Set
from hotkey_data_models import HotkeyInfo

try:
    import win32api
    import win32gui
    import win32con
    import win32process
    import winreg
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class EnhancedHotkeyDetector:
    """增强的热键检测器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 虚拟键码映射
        self.vk_codes = {
            'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46,
            'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C,
            'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52,
            'S': 0x53, 'T': 0x54, 'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58,
            'Y': 0x59, 'Z': 0x5A,
            'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74,
            'F6': 0x75, 'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79,
            'F11': 0x7A, 'F12': 0x7B,
            'ESC': 0x1B, 'SPACE': 0x20, 'ENTER': 0x0D, 'TAB': 0x09,
            'DELETE': 0x2E, 'INSERT': 0x2D, 'HOME': 0x24, 'END': 0x23,
            'PAGE_UP': 0x21, 'PAGE_DOWN': 0x22, 'PRINT_SCREEN': 0x2C
        }

    def _get_vk_code(self, key: str) -> int:
        """获取虚拟键码"""
        key_upper = key.upper()
        return self.vk_codes.get(key_upper, ord(key_upper) if len(key_upper) == 1 else 0)

    def _parse_key_combination(self, combo: str) -> tuple:
        """解析热键组合，返回(修饰键集合, 虚拟键码)"""
        if not combo:
            return set(), 0

        parts = combo.replace(' ', '').split('+')
        if len(parts) <= 1:
            return set(), self._get_vk_code(combo)

        modifiers = set()
        base_key = parts[-1]

        for modifier in parts[:-1]:
            mod_normalized = modifier.title()
            if mod_normalized in ['Control', 'Ctrl']:
                modifiers.add('Ctrl')
            elif mod_normalized in ['Windows', 'Win']:
                modifiers.add('Win')
            elif mod_normalized == 'Alt':
                modifiers.add('Alt')
            elif mod_normalized == 'Shift':
                modifiers.add('Shift')

        return modifiers, self._get_vk_code(base_key)

    def detect_system_hotkeys(self) -> List[HotkeyInfo]:
        """检测系统级热键"""
        self.logger.info("开始检测系统级热键...")

        system_hotkeys = [
            ('Win+L', 'Lock screen', 'critical'),
            ('Win+D', 'Show desktop', 'high'),
            ('Win+E', 'Open explorer', 'high'),
            ('Win+R', 'Run dialog', 'high'),
            ('Win+Tab', 'Task view', 'medium'),
            ('Alt+Tab', 'Switch windows', 'critical'),
            ('Ctrl+Alt+Del', 'Security options', 'critical'),
            ('Ctrl+Shift+Esc', 'Task manager', 'high'),
            ('Win+I', 'Settings', 'medium'),
            ('Win+X', 'Quick Link menu', 'medium'),
            ('Win+A', 'Action Center', 'medium'),
            ('Win+S', 'Search', 'medium'),
            ('Win+V', 'Clipboard History', 'medium'),
            ('Alt+F4', 'Close window', 'high'),
            ('F11', 'Full screen', 'medium'),
            ('Print Screen', 'Screenshot', 'medium'),
        ]

        detected = []
        for combo, desc, severity in system_hotkeys:
            modifiers, vk_code = self._parse_key_combination(combo)

            hotkey = HotkeyInfo(
                key_combination=combo,
                modifier_keys=modifiers,
                virtual_key_code=vk_code,
                source_type='system',
                source_name='Windows System',
                description=desc,
                conflict_severity=severity,
                detected_time=datetime.now()
            )
            detected.append(hotkey)

        self.logger.info(f"检测到 {len(detected)} 个系统级热键")
        return detected

    def detect_application_hotkeys(self) -> List[HotkeyInfo]:
        """检测应用程序热键"""
        self.logger.info("开始检测应用程序热键...")

        if not HAS_WIN32:
            self.logger.warning("缺少win32api，跳过应用程序热键检测")
            return []

        detected = []

        try:
            # 获取运行中的进程
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if not proc_info['exe']:
                        continue

                    app_name = proc_info['name']
                    process_id = proc_info['pid']

                    # 获取已知应用程序的热键
                    app_hotkeys = self._get_known_app_hotkeys(app_name)

                    for combo, desc, severity in app_hotkeys:
                        modifiers, vk_code = self._parse_key_combination(combo)

                        hotkey = HotkeyInfo(
                            key_combination=combo,
                            modifier_keys=modifiers,
                            virtual_key_code=vk_code,
                            source_type='application',
                            source_name=app_name,
                            process_id=process_id,
                            process_name=app_name,
                            description=desc,
                            conflict_severity=severity,
                            detected_time=datetime.now()
                        )
                        detected.append(hotkey)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            self.logger.error(f"检测应用程序热键时出错: {e}")

        self.logger.info(f"检测到 {len(detected)} 个应用程序热键")
        return detected

    def _get_known_app_hotkeys(self, app_name: str) -> List[tuple]:
        """获取已知应用程序的热键"""
        known_hotkeys = {
            'chrome.exe': [
                ('Ctrl+T', 'New tab', 'medium'),
                ('Ctrl+W', 'Close tab', 'medium'),
                ('Ctrl+Shift+T', 'Reopen closed tab', 'medium'),
                ('F12', 'Developer tools', 'low'),
                ('Ctrl+R', 'Refresh page', 'medium'),
                ('Ctrl+L', 'Address bar', 'medium'),
            ],
            'firefox.exe': [
                ('Ctrl+T', 'New tab', 'medium'),
                ('Ctrl+W', 'Close tab', 'medium'),
                ('Ctrl+Shift+T', 'Reopen closed tab', 'medium'),
                ('F12', 'Developer tools', 'low'),
                ('Ctrl+R', 'Refresh page', 'medium'),
            ],
            'notepad.exe': [
                ('Ctrl+N', 'New file', 'medium'),
                ('Ctrl+O', 'Open file', 'medium'),
                ('Ctrl+S', 'Save file', 'high'),
                ('Ctrl+F', 'Find', 'medium'),
                ('Ctrl+H', 'Replace', 'medium'),
            ],
            'explorer.exe': [
                ('Ctrl+N', 'New window', 'medium'),
                ('F2', 'Rename', 'medium'),
                ('Delete', 'Delete', 'medium'),
                ('Ctrl+C', 'Copy', 'critical'),
                ('Ctrl+V', 'Paste', 'critical'),
            ],
            'code.exe': [
                ('Ctrl+Shift+P', 'Command palette', 'high'),
                ('Ctrl+`', 'Toggle terminal', 'medium'),
                ('Ctrl+B', 'Toggle sidebar', 'medium'),
                ('F5', 'Debug/Run', 'high'),
                ('Ctrl+F', 'Find', 'high'),
            ],
            'devenv.exe': [
                ('F5', 'Start debugging', 'high'),
                ('Ctrl+Shift+B', 'Build solution', 'high'),
                ('F9', 'Toggle breakpoint', 'medium'),
                ('Ctrl+K+C', 'Comment', 'medium'),
            ]
        }

        return known_hotkeys.get(app_name.lower(), [])

    def detect_registry_hotkeys(self) -> List[HotkeyInfo]:
        """检测注册表热键"""
        self.logger.info("开始检测注册表热键...")

        if not HAS_WIN32:
            self.logger.warning("缺少win32api，跳过注册表热键检测")
            return []

        detected = []

        # 常见的注册表热键位置
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"),
            (winreg.HKEY_CURRENT_USER, r"Software\Classes\Applications"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        ]

        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, reg_type = winreg.EnumValue(key, i)
                            if any(keyword in name.lower() for keyword in ['hotkey', 'shortcut', 'key']):
                                hotkey = HotkeyInfo(
                                    key_combination=f"{name}={value}",
                                    modifier_keys=set(),
                                    virtual_key_code=0,
                                    source_type='registry',
                                    source_name='Registry',
                                    description=f"注册表热键: {path}\\{name}",
                                    conflict_severity='low',
                                    detected_time=datetime.now()
                                )
                                detected.append(hotkey)
                            i += 1
                        except WindowsError:
                            break
            except (FileNotFoundError, PermissionError, OSError):
                continue

        self.logger.info(f"检测到 {len(detected)} 个注册表热键")
        return detected

    def detect_active_window_hotkeys(self) -> List[HotkeyInfo]:
        """检测当前活动窗口的热键"""
        self.logger.info("开始检测活动窗口热键...")

        if not HAS_WIN32:
            self.logger.warning("缺少win32api，跳过活动窗口热键检测")
            return []

        detected = []

        try:
            # 获取当前活动窗口
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                window_title = win32gui.GetWindowText(hwnd)
                thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)

                try:
                    process = psutil.Process(process_id)
                    app_name = process.name()

                    # 获取窗口特定的热键
                    window_hotkeys = self._get_window_specific_hotkeys(app_name, window_title)

                    for combo, desc, severity in window_hotkeys:
                        modifiers, vk_code = self._parse_key_combination(combo)

                        hotkey = HotkeyInfo(
                            key_combination=combo,
                            modifier_keys=modifiers,
                            virtual_key_code=vk_code,
                            source_type='application',
                            source_name=f"{app_name} (Active Window)",
                            window_title=window_title,
                            process_id=process_id,
                            process_name=app_name,
                            description=desc,
                            conflict_severity=severity,
                            detected_time=datetime.now()
                        )
                        detected.append(hotkey)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except Exception as e:
            self.logger.error(f"检测活动窗口热键时出错: {e}")

        self.logger.info(f"检测到 {len(detected)} 个活动窗口热键")
        return detected

    def _get_window_specific_hotkeys(self, app_name: str, window_title: str) -> List[tuple]:
        """获取特定窗口的热键"""
        hotkeys = []

        # 基于应用程序的通用热键
        common_hotkeys = [
            ('Ctrl+C', 'Copy', 'critical'),
            ('Ctrl+V', 'Paste', 'critical'),
            ('Ctrl+X', 'Cut', 'critical'),
            ('Ctrl+Z', 'Undo', 'high'),
            ('Ctrl+Y', 'Redo', 'high'),
            ('Ctrl+A', 'Select all', 'high'),
            ('Ctrl+S', 'Save', 'critical'),
        ]

        # 添加通用热键
        hotkeys.extend(common_hotkeys)

        # 基于应用程序类型的特定热键
        if any(browser in app_name.lower() for browser in ['chrome', 'firefox', 'edge', 'browser']):
            hotkeys.extend([
                ('F5', 'Refresh', 'medium'),
                ('Ctrl+R', 'Refresh', 'medium'),
                ('Ctrl+D', 'Bookmark', 'medium'),
                ('Ctrl+Shift+Delete', 'Clear browsing data', 'medium'),
            ])

        elif any(editor in app_name.lower() for editor in ['notepad', 'code', 'edit']):
            hotkeys.extend([
                ('Ctrl+F', 'Find', 'high'),
                ('Ctrl+H', 'Replace', 'medium'),
                ('Ctrl+G', 'Go to line', 'medium'),
            ])

        return hotkeys

    def detect_all_hotkeys(self, include_system=True, include_application=True,
                          include_registry=True, include_active_window=True) -> List[HotkeyInfo]:
        """检测所有类型的热键

        Args:
            include_system: 是否包含系统热键
            include_application: 是否包含应用程序热键
            include_registry: 是否包含注册表热键
            include_active_window: 是否包含活动窗口热键

        Returns:
            List[HotkeyInfo]: 检测到的所有热键
        """
        self.logger.info("开始全面检测热键...")
        all_hotkeys = []

        if include_system:
            all_hotkeys.extend(self.detect_system_hotkeys())

        if include_application:
            all_hotkeys.extend(self.detect_application_hotkeys())

        if include_registry:
            all_hotkeys.extend(self.detect_registry_hotkeys())

        if include_active_window:
            all_hotkeys.extend(self.detect_active_window_hotkeys())

        self.logger.info(f"全面检测完成，共发现 {len(all_hotkeys)} 个热键")
        return all_hotkeys