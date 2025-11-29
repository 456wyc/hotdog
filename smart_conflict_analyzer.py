#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能冲突分析器
Smart Conflict Analyzer

基于现有项目优化的冲突分析系统
"""

import logging
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime
from hotkey_data_models import HotkeyInfo, ConflictGroup, ConflictReport

class SmartConflictAnalyzer:
    """智能热键冲突分析器"""

    # 不同源类型的优先级（数字越大优先级越高）
    SOURCE_PRIORITY = {
        'system': 100,
        'known_software': 80,
        'application': 60,
        'user_defined': 40,
        'unknown': 20
    }

    # 应用程序重要性评分
    APP_IMPORTANCE = {
        'explorer.exe': 95,
        'dwm.exe': 90,
        'winlogon.exe': 90,
        'csrss.exe': 90,
        'taskmgr.exe': 85,
        'chrome.exe': 75,
        'firefox.exe': 75,
        'msedge.exe': 75,
        'code.exe': 80,
        'devenv.exe': 80,
        'pycharm64.exe': 75,
        'notepad.exe': 50,
        'calc.exe': 45,
        'mspaint.exe': 45,
        'wordpad.exe': 50,
        'winword.exe': 70,
        'excel.exe': 70,
        'powerpnt.exe': 70,
        'outlook.exe': 70,
        'discord.exe': 60,
        'slack.exe': 60,
        'teams.exe': 65,
        'zoom.exe': 65,
        'obs64.exe': 70,
        'vlc.exe': 60,
        'steam.exe': 55
    }

    # 系统级热键数据库
    SYSTEM_HOTKEYS = [
        ('Win+L', {'Win'}, 'Lock screen', 'critical'),
        ('Win+D', {'Win'}, 'Show desktop', 'high'),
        ('Win+E', {'Win'}, 'Open explorer', 'high'),
        ('Win+R', {'Win'}, 'Run dialog', 'high'),
        ('Win+Tab', {'Win'}, 'Task view', 'medium'),
        ('Alt+Tab', {'Alt'}, 'Switch windows', 'critical'),
        ('Ctrl+Alt+Del', {'Ctrl', 'Alt'}, 'Security options', 'critical'),
        ('Ctrl+Shift+Esc', {'Ctrl', 'Shift'}, 'Task manager', 'high'),
        ('Win+I', {'Win'}, 'Settings', 'medium'),
        ('Win+X', {'Win'}, 'Quick Link menu', 'medium'),
        ('Win+A', {'Win'}, 'Action Center', 'medium'),
        ('Win+S', {'Win'}, 'Search', 'medium'),
        ('Win+V', {'Win'}, 'Clipboard History', 'medium'),
        ('Alt+F4', {'Alt'}, 'Close window', 'high'),
        ('F11', set(), 'Full screen', 'medium'),
        ('Print Screen', set(), 'Screenshot', 'medium'),
        ('Alt+Print Screen', {'Alt'}, 'Window screenshot', 'medium'),
        ('Win+Print Screen', {'Win'}, 'Screenshot to Pictures', 'medium'),
    ]

    # 通用应用热键数据库
    COMMON_APP_HOTKEYS = [
        ('Ctrl+C', {'Ctrl'}, 'Copy', 'critical'),
        ('Ctrl+V', {'Ctrl'}, 'Paste', 'critical'),
        ('Ctrl+X', {'Ctrl'}, 'Cut', 'critical'),
        ('Ctrl+Z', {'Ctrl'}, 'Undo', 'high'),
        ('Ctrl+Y', {'Ctrl'}, 'Redo', 'high'),
        ('Ctrl+S', {'Ctrl'}, 'Save', 'critical'),
        ('Ctrl+O', {'Ctrl'}, 'Open', 'high'),
        ('Ctrl+N', {'Ctrl'}, 'New', 'high'),
        ('Ctrl+A', {'Ctrl'}, 'Select All', 'high'),
        ('Ctrl+F', {'Ctrl'}, 'Find', 'high'),
        ('Ctrl+H', {'Ctrl'}, 'Replace', 'medium'),
        ('Ctrl+P', {'Ctrl'}, 'Print', 'medium'),
        ('F1', set(), 'Help', 'low'),
        ('F5', set(), 'Refresh', 'medium'),
        ('Ctrl+W', {'Ctrl'}, 'Close tab/window', 'high'),
        ('Ctrl+T', {'Ctrl'}, 'New tab', 'medium'),
        ('Ctrl+Shift+T', {'Ctrl', 'Shift'}, 'Reopen closed tab', 'medium'),
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.known_hotkeys = self._build_known_hotkeys_database()

    def _build_known_hotkeys_database(self) -> List[HotkeyInfo]:
        """构建已知热键数据库"""
        known_hotkeys = []

        # 添加系统热键
        for combo, modifiers, desc, severity in self.SYSTEM_HOTKEYS:
            hotkey = HotkeyInfo(
                key_combination=combo,
                modifier_keys=modifiers,
                virtual_key_code=self._get_vk_code_from_combo(combo),
                source_type='system',
                source_name='Windows System',
                description=desc,
                conflict_severity=severity
            )
            known_hotkeys.append(hotkey)

        # 添加通用应用热键
        for combo, modifiers, desc, severity in self.COMMON_APP_HOTKEYS:
            hotkey = HotkeyInfo(
                key_combination=combo,
                modifier_keys=modifiers,
                virtual_key_code=self._get_vk_code_from_combo(combo),
                source_type='known_software',
                source_name='Common Applications',
                description=desc,
                conflict_severity=severity
            )
            known_hotkeys.append(hotkey)

        self.logger.info(f"构建了 {len(known_hotkeys)} 个已知热键的数据库")
        return known_hotkeys

    def _get_vk_code_from_combo(self, combo: str) -> int:
        """从热键组合字符串获取虚拟键码"""
        # Windows虚拟键码映射
        vk_codes = {
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
            'PAGE_UP': 0x21, 'PAGE_DOWN': 0x22,
            'PRINT SCREEN': 0x2C, 'PAUSE': 0x13
        }

        key = combo.split('+')[-1].upper()
        return vk_codes.get(key, ord(key) if len(key) == 1 else 0)

    def analyze_conflicts(self, detected_hotkeys: List[HotkeyInfo]) -> ConflictReport:
        """分析热键冲突"""
        self.logger.info(f"开始分析 {len(detected_hotkeys)} 个检测到的热键")

        # 合并已知热键和检测到的热键
        all_hotkeys = detected_hotkeys + self.known_hotkeys

        # 按键组合分组
        key_groups = self._group_by_key_combination(all_hotkeys)

        # 识别冲突
        conflict_groups = []
        for key_combo, hotkey_list in key_groups.items():
            if len(hotkey_list) > 1:
                conflict_group = self._create_conflict_group(key_combo, hotkey_list)
                conflict_groups.append(conflict_group)

        # 生成统计信息
        hotkey_statistics = self._generate_statistics(all_hotkeys)

        # 生成报告
        report = self._generate_report(all_hotkeys, conflict_groups, hotkey_statistics)

        self.logger.info(f"分析完成 - 发现 {len(conflict_groups)} 个冲突组")
        return report

    def _group_by_key_combination(self, hotkeys: List[HotkeyInfo]) -> Dict[str, List[HotkeyInfo]]:
        """按键组合分组热键"""
        groups = defaultdict(list)
        for hotkey in hotkeys:
            normalized_combo = self._normalize_key_combination(hotkey.key_combination)
            groups[normalized_combo].append(hotkey)
        return dict(groups)

    def _normalize_key_combination(self, combo: str) -> str:
        """标准化键组合格式"""
        if not combo:
            return ""

        parts = combo.replace(' ', '').split('+')
        if len(parts) <= 1:
            return combo.upper()

        # 标准化修饰键顺序
        modifier_order = ['Ctrl', 'Alt', 'Shift', 'Win']
        modifiers = []
        base_key = parts[-1].upper()

        for part in parts[:-1]:
            normalized_mod = part.strip().title()
            if normalized_mod == 'Control':
                normalized_mod = 'Ctrl'
            elif normalized_mod == 'Windows':
                normalized_mod = 'Win'
            modifiers.append(normalized_mod)

        # 按标准顺序排序修饰键
        sorted_modifiers = []
        for mod in modifier_order:
            if mod in modifiers:
                sorted_modifiers.append(mod)

        # 添加其他修饰键
        for mod in modifiers:
            if mod not in sorted_modifiers:
                sorted_modifiers.append(mod)

        return '+'.join(sorted_modifiers + [base_key])

    def _create_conflict_group(self, key_combo: str, hotkeys: List[HotkeyInfo]) -> ConflictGroup:
        """创建冲突组"""
        # 确定冲突类型
        conflict_type = self._determine_conflict_type(hotkeys)

        # 计算严重程度
        severity = self._calculate_conflict_severity(hotkeys)

        # 选择优先级最高的热键
        priority_hotkey = self._select_priority_hotkey(hotkeys)

        # 生成解决建议
        resolution_suggestions = self._generate_resolution_suggestions(hotkeys, conflict_type)

        # 生成替代方案
        alternative_suggestions = self._suggest_alternative_hotkeys(key_combo, hotkeys)

        return ConflictGroup(
            key_combination=key_combo,
            hotkeys=hotkeys,
            severity=severity,
            conflict_type=conflict_type,
            resolution_suggestions=resolution_suggestions,
            priority_hotkey=priority_hotkey,
            alternative_suggestions=alternative_suggestions
        )

    def _determine_conflict_type(self, hotkeys: List[HotkeyInfo]) -> str:
        """确定冲突类型"""
        source_types = set(h.source_type for h in hotkeys)
        source_names = set(h.source_name for h in hotkeys if h.source_name)

        if 'system' in source_types:
            return 'system_override'
        elif len(source_names) > 1:
            return 'cross_application'
        else:
            return 'standard'

    def _calculate_conflict_severity(self, hotkeys: List[HotkeyInfo]) -> str:
        """计算冲突严重程度"""
        # 获取最高源类型优先级
        max_source_priority = max(
            self.SOURCE_PRIORITY.get(h.source_type, 0) for h in hotkeys
        )

        # 检查是否涉及系统热键
        system_involved = any(h.source_type == 'system' for h in hotkeys)

        # 统计应用程序数量
        app_count = len(set(h.source_name for h in hotkeys if h.source_name))

        # 检查是否包含关键热键
        critical_hotkeys = any(
            h.conflict_severity == 'critical' for h in hotkeys
        )

        # 计算严重程度
        if system_involved and critical_hotkeys:
            return 'critical'
        elif system_involved or max_source_priority >= 90 or critical_hotkeys:
            return 'high'
        elif max_source_priority >= 70 or app_count >= 3:
            return 'medium'
        else:
            return 'low'

    def _select_priority_hotkey(self, hotkeys: List[HotkeyInfo]) -> HotkeyInfo:
        """选择优先级最高的热键"""
        def get_priority_score(hotkey: HotkeyInfo) -> int:
            base_score = self.SOURCE_PRIORITY.get(hotkey.source_type, 0)
            app_bonus = self.APP_IMPORTANCE.get(
                hotkey.process_name.lower() if hotkey.process_name else '', 0
            )
            severity_bonus = {
                'critical': 50, 'high': 30, 'medium': 10, 'low': 0
            }.get(hotkey.conflict_severity, 0)

            return base_score + app_bonus + severity_bonus

        return max(hotkeys, key=get_priority_score)

    def _generate_resolution_suggestions(self, hotkeys: List[HotkeyInfo], conflict_type: str) -> List[str]:
        """生成解决建议"""
        suggestions = []

        if conflict_type == 'system_override':
            suggestions.extend([
                "系统级热键具有最高优先级，建议修改应用程序热键设置",
                "避免使用与系统冲突的热键组合",
                "考虑使用应用程序专用的热键前缀（如Ctrl+Alt+）"
            ])

        elif conflict_type == 'cross_application':
            suggestions.extend([
                "多个应用程序使用相同热键，可能导致功能冲突",
                "检查各应用程序的热键自定义选项",
                "考虑关闭某些应用程序的全局热键功能",
                "为不同应用程序设置不同的热键前缀"
            ])

        elif conflict_type == 'standard':
            suggestions.extend([
                "同类热键冲突，建议检查相关程序的配置",
                "可能需要手动调整热键设置以避免冲突"
            ])

        # 通用建议
        suggestions.extend([
            "使用不常用的功能键（F13-F24）可以减少冲突",
            "考虑使用三键组合（Ctrl+Alt+X）来避免冲突",
            "定期检查和清理不再使用的全局热键"
        ])

        return suggestions

    def _suggest_alternative_hotkeys(self, conflicted_combo: str, hotkeys: List[HotkeyInfo]) -> List[str]:
        """建议替代热键组合"""
        suggestions = []
        all_existing = set(h.key_combination for h in self.known_hotkeys)

        try:
            parts = conflicted_combo.split('+')
            base_key = parts[-1]
            current_modifiers = set(parts[:-1]) if len(parts) > 1 else set()

            # 生成替代组合
            alternative_modifiers = [
                current_modifiers | {'Shift'},
                current_modifiers | {'Alt'},
                current_modifiers | {'Ctrl', 'Alt'},
                current_modifiers | {'Ctrl', 'Shift'},
                current_modifiers | {'Alt', 'Shift'},
                {'Ctrl', 'Alt', 'Shift'}
            ]

            for mod_set in alternative_modifiers:
                if mod_set != current_modifiers:
                    new_combo = '+'.join(sorted(mod_set)) + '+' + base_key
                    if new_combo not in all_existing:
                        suggestions.append(new_combo)

            # 建议使用功能键
            for i in range(1, 13):
                func_combo = '+'.join(sorted(current_modifiers)) + f'+F{i}' if current_modifiers else f'F{i}'
                if func_combo not in all_existing:
                    suggestions.append(func_combo)

        except Exception as e:
            self.logger.warning(f"生成替代热键建议时出错: {e}")

        return suggestions[:5]  # 返回前5个建议

    def _generate_statistics(self, hotkeys: List[HotkeyInfo]) -> Dict[str, any]:
        """生成热键统计信息"""
        stats = {
            'total_count': len(hotkeys),
            'by_source_type': dict(Counter(h.source_type for h in hotkeys)),
            'by_application': dict(Counter(h.source_name for h in hotkeys if h.source_name)),
            'by_severity': dict(Counter(h.conflict_severity for h in hotkeys)),
            'most_common_modifiers': dict(Counter()),
            'most_common_keys': dict(Counter()),
            'hotkey_density': len(hotkeys) / 1000  # 假设1000个可能的热键组合
        }

        # 统计修饰键使用频率
        for hotkey in hotkeys:
            for modifier in hotkey.modifier_keys:
                stats['most_common_modifiers'][modifier] = stats['most_common_modifiers'].get(modifier, 0) + 1

        # 统计基础键使用频率
        for hotkey in hotkeys:
            if '+' in hotkey.key_combination:
                base_key = hotkey.key_combination.split('+')[-1]
            else:
                base_key = hotkey.key_combination
            stats['most_common_keys'][base_key] = stats['most_common_keys'].get(base_key, 0) + 1

        return stats

    def _generate_report(self, all_hotkeys: List[HotkeyInfo], conflict_groups: List[ConflictGroup],
                        statistics: Dict[str, any]) -> ConflictReport:
        """生成冲突报告"""
        # 统计严重程度分布
        severity_count = Counter(group.severity for group in conflict_groups)

        # 生成总体建议
        general_recommendations = self._generate_general_recommendations(all_hotkeys, conflict_groups)

        return ConflictReport(
            timestamp=datetime.now(),
            total_hotkeys=len(all_hotkeys),
            total_conflicts=len(conflict_groups),
            conflict_groups=conflict_groups,
            severity_breakdown=dict(severity_count),
            general_recommendations=general_recommendations,
            hotkey_statistics=statistics
        )

    def _generate_general_recommendations(self, all_hotkeys: List[HotkeyInfo],
                                        conflict_groups: List[ConflictGroup]) -> List[str]:
        """生成总体建议"""
        recommendations = []

        # 统计各严重程度的冲突数量
        critical_count = sum(1 for g in conflict_groups if g.severity == 'critical')
        high_count = sum(1 for g in conflict_groups if g.severity == 'high')
        medium_count = sum(1 for g in conflict_groups if g.severity == 'medium')

        if critical_count > 0:
            recommendations.append(f"发现 {critical_count} 个严重冲突，强烈建议立即处理")

        if high_count > 0:
            recommendations.append(f"发现 {high_count} 个高优先级冲突，建议尽快处理")

        if medium_count > 3:
            recommendations.append(f"发现 {medium_count} 个中等冲突，建议定期检查")

        # 热键密度分析
        hotkey_density = len(all_hotkeys) / 1000
        if hotkey_density > 0.15:
            recommendations.append("热键密度较高（>15%），建议定期清理不需要的热键")

        # 检查常见问题
        critical_hotkeys = ['Ctrl+C', 'Ctrl+V', 'Ctrl+S', 'Alt+Tab']
        for hotkey in critical_hotkeys:
            if any(hotkey in g.key_combination for g in conflict_groups):
                recommendations.append(f"检测到 {hotkey} 冲突，这可能严重影响日常使用")

        # 系统级冲突警告
        system_conflicts = sum(1 for g in conflict_groups if g.conflict_type == 'system_override')
        if system_conflicts > 0:
            recommendations.append(f"发现 {system_conflicts} 个系统级冲突，可能影响系统稳定性")

        if not recommendations:
            recommendations.append("未发现严重冲突，热键配置良好")

        return recommendations