#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键数据模型
Enhanced Hotkey Data Models

基于现有项目优化的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Set, Optional, Any

@dataclass
class HotkeyInfo:
    """增强的热键信息数据类"""
    key_combination: str
    modifier_keys: Set[str] = field(default_factory=set)
    virtual_key_code: int = 0
    source_type: str = "unknown"  # 'system', 'application', 'known_software', 'user_defined'
    source_name: str = ""
    window_title: str = ""
    process_id: int = 0
    process_name: str = ""
    description: str = ""
    conflict_severity: str = "low"  # 'low', 'medium', 'high', 'critical'
    detected_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'key_combination': self.key_combination,
            'modifier_keys': list(self.modifier_keys),
            'virtual_key_code': self.virtual_key_code,
            'source_type': self.source_type,
            'source_name': self.source_name,
            'window_title': self.window_title,
            'process_id': self.process_id,
            'process_name': self.process_name,
            'description': self.description,
            'conflict_severity': self.conflict_severity,
            'detected_time': self.detected_time.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HotkeyInfo':
        """从字典创建对象"""
        detected_time = datetime.fromisoformat(data.get('detected_time', datetime.now().isoformat()))
        return cls(
            key_combination=data.get('key_combination', ''),
            modifier_keys=set(data.get('modifier_keys', [])),
            virtual_key_code=data.get('virtual_key_code', 0),
            source_type=data.get('source_type', 'unknown'),
            source_name=data.get('source_name', ''),
            window_title=data.get('window_title', ''),
            process_id=data.get('process_id', 0),
            process_name=data.get('process_name', ''),
            description=data.get('description', ''),
            conflict_severity=data.get('conflict_severity', 'low'),
            detected_time=detected_time
        )

@dataclass
class ConflictGroup:
    """冲突组数据类"""
    key_combination: str
    hotkeys: List[HotkeyInfo] = field(default_factory=list)
    severity: str = "medium"  # 'low', 'medium', 'high', 'critical'
    conflict_type: str = "standard"  # 'standard', 'cross_application', 'system_override'
    resolution_suggestions: List[str] = field(default_factory=list)
    priority_hotkey: Optional[HotkeyInfo] = None
    alternative_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'key_combination': self.key_combination,
            'severity': self.severity,
            'conflict_type': self.conflict_type,
            'resolution_suggestions': self.resolution_suggestions,
            'alternative_suggestions': self.alternative_suggestions,
            'priority_hotkey': self.priority_hotkey.to_dict() if self.priority_hotkey else None,
            'hotkeys': [h.to_dict() for h in self.hotkeys]
        }

@dataclass
class ConflictReport:
    """冲突报告数据类"""
    timestamp: datetime
    total_hotkeys: int
    total_conflicts: int
    conflict_groups: List[ConflictGroup]
    severity_breakdown: Dict[str, int]
    general_recommendations: List[str]
    hotkey_statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'summary': {
                'total_hotkeys': self.total_hotkeys,
                'total_conflicts': self.total_conflicts,
                'severity_breakdown': self.severity_breakdown
            },
            'conflict_groups': [group.to_dict() for group in self.conflict_groups],
            'general_recommendations': self.general_recommendations,
            'hotkey_statistics': self.hotkey_statistics
        }

@dataclass
class AppConfig:
    """应用配置数据类"""
    # General settings
    auto_start_monitoring: bool = True
    check_interval: int = 5
    language: str = 'zh_CN'
    theme: str = 'light'

    # Detection settings
    scan_system_hotkeys: bool = True
    scan_application_hotkeys: bool = True
    scan_known_software: bool = True
    include_user_defined: bool = True

    # Alert settings
    show_critical_alerts: bool = True
    show_high_alerts: bool = True
    show_medium_alerts: bool = False
    show_low_alerts: bool = False

    # Export settings
    default_export_format: str = 'json'
    include_timestamps: bool = True
    include_suggestions: bool = True
    auto_cleanup_reports: bool = True
    max_report_count: int = 20

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'general': {
                'auto_start_monitoring': self.auto_start_monitoring,
                'check_interval': self.check_interval,
                'language': self.language,
                'theme': self.theme
            },
            'detection': {
                'scan_system_hotkeys': self.scan_system_hotkeys,
                'scan_application_hotkeys': self.scan_application_hotkeys,
                'scan_known_software': self.scan_known_software,
                'include_user_defined': self.include_user_defined
            },
            'alerts': {
                'show_critical_alerts': self.show_critical_alerts,
                'show_high_alerts': self.show_high_alerts,
                'show_medium_alerts': self.show_medium_alerts,
                'show_low_alerts': self.show_low_alerts
            },
            'export': {
                'default_export_format': self.default_export_format,
                'include_timestamps': self.include_timestamps,
                'include_suggestions': self.include_suggestions,
                'auto_cleanup_reports': self.auto_cleanup_reports,
                'max_report_count': self.max_report_count
            }
        }