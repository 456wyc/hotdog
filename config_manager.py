#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理系统
Configuration Manager

基于现有项目优化的配置管理功能
"""

import os
import logging
import configparser
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from hotkey_data_models import AppConfig

class ConfigManager:
    """应用配置管理器"""

    def __init__(self, base_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # 设置基础路径
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))

        # 创建配置目录
        self.config_dir = self.base_path / 'config'
        self.config_dir.mkdir(exist_ok=True)

        # 配置文件路径
        self.config_file = self.config_dir / 'settings.ini'

        # 初始化配置解析器
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # 保持键的大小写

        # 当前配置对象
        self.app_config = AppConfig()

        # 加载配置
        self._init_config()

        self.logger.info(f"配置管理器初始化完成，配置文件：{self.config_file}")

    def _init_config(self):
        """初始化配置文件"""
        # 默认配置结构
        default_sections = {
            'General': {
                'auto_start_monitoring': 'true',
                'check_interval': '5',
                'language': 'zh_CN',
                'theme': 'light',
                'window_geometry': '1000x700',
                'window_position': 'center',
                'minimize_to_tray': 'false',
                'start_minimized': 'false'
            },
            'Detection': {
                'scan_system_hotkeys': 'true',
                'scan_application_hotkeys': 'true',
                'scan_known_software': 'true',
                'include_user_defined': 'true',
                'scan_registry_hotkeys': 'false',
                'scan_active_window': 'true',
                'deep_scan_mode': 'false',
                'exclude_processes': ''
            },
            'Alerts': {
                'show_critical_alerts': 'true',
                'show_high_alerts': 'true',
                'show_medium_alerts': 'false',
                'show_low_alerts': 'false',
                'alert_sound': 'true',
                'popup_notifications': 'true',
                'log_alerts': 'true'
            },
            'Export': {
                'default_format': 'json',
                'include_timestamps': 'true',
                'include_suggestions': 'true',
                'include_statistics': 'true',
                'auto_cleanup_reports': 'true',
                'max_report_count': '20',
                'report_path': 'reports'
            },
            'Advanced': {
                'logging_level': 'INFO',
                'max_log_files': '10',
                'scan_timeout': '30',
                'process_scan_limit': '1000',
                'enable_hotkey_monitoring': 'false',
                'monitoring_interval': '10'
            }
        }

        # 如果配置文件不存在，创建默认配置
        if not self.config_file.exists():
            self._create_default_config(default_sections)
        else:
            self.config.read(self.config_file, encoding='utf-8')
            # 检查并补充缺失的配置项
            self._validate_and_update_config(default_sections)

        # 加载配置到对象
        self._load_config_to_object()

    def _create_default_config(self, sections: Dict[str, Dict[str, str]]):
        """创建默认配置文件"""
        try:
            for section_name, options in sections.items():
                self.config.add_section(section_name)
                for key, value in options.items():
                    self.config.set(section_name, key, value)

            self.save_config()
            self.logger.info("创建了默认配置文件")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")

    def _validate_and_update_config(self, default_sections: Dict[str, Dict[str, str]]):
        """验证并更新配置文件"""
        updated = False

        for section_name, default_options in default_sections.items():
            # 添加缺失的节
            if not self.config.has_section(section_name):
                self.config.add_section(section_name)
                updated = True

            # 添加缺失的选项
            for key, default_value in default_options.items():
                if not self.config.has_option(section_name, key):
                    self.config.set(section_name, key, default_value)
                    updated = True

        if updated:
            self.save_config()
            self.logger.info("更新了配置文件中的缺失项")

    def _load_config_to_object(self):
        """将INI配置加载到AppConfig对象"""
        try:
            self.app_config = AppConfig(
                # General settings
                auto_start_monitoring=self._get_bool('General', 'auto_start_monitoring', True),
                check_interval=self._get_int('General', 'check_interval', 5),
                language=self.get_config('General', 'language', 'zh_CN'),
                theme=self.get_config('General', 'theme', 'light'),

                # Detection settings
                scan_system_hotkeys=self._get_bool('Detection', 'scan_system_hotkeys', True),
                scan_application_hotkeys=self._get_bool('Detection', 'scan_application_hotkeys', True),
                scan_known_software=self._get_bool('Detection', 'scan_known_software', True),
                include_user_defined=self._get_bool('Detection', 'include_user_defined', True),

                # Alert settings
                show_critical_alerts=self._get_bool('Alerts', 'show_critical_alerts', True),
                show_high_alerts=self._get_bool('Alerts', 'show_high_alerts', True),
                show_medium_alerts=self._get_bool('Alerts', 'show_medium_alerts', False),
                show_low_alerts=self._get_bool('Alerts', 'show_low_alerts', False),

                # Export settings
                default_export_format=self.get_config('Export', 'default_format', 'json'),
                include_timestamps=self._get_bool('Export', 'include_timestamps', True),
                include_suggestions=self._get_bool('Export', 'include_suggestions', True),
                auto_cleanup_reports=self._get_bool('Export', 'auto_cleanup_reports', True),
                max_report_count=self._get_int('Export', 'max_report_count', 20)
            )
            self.logger.debug("配置已加载到应用对象")
        except Exception as e:
            self.logger.error(f"加载配置到对象失败: {e}")
            self.app_config = AppConfig()  # 使用默认配置

    def get_config(self, section: str, key: str, default: str = "") -> str:
        """获取配置值"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.logger.warning(f"配置项不存在: [{section}] {key}，使用默认值: {default}")
            return default

    def _get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """获取布尔类型配置值"""
        value = self.get_config(section, key, str(default).lower())
        return value.lower() in ('true', '1', 'yes', 'on')

    def _get_int(self, section: str, key: str, default: int = 0) -> int:
        """获取整数类型配置值"""
        try:
            value = self.get_config(section, key, str(default))
            return int(value)
        except (ValueError, TypeError):
            self.logger.warning(f"配置值类型转换失败: [{section}] {key}，使用默认值: {default}")
            return default

    def _get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """获取浮点数类型配置值"""
        try:
            value = self.get_config(section, key, str(default))
            return float(value)
        except (ValueError, TypeError):
            self.logger.warning(f"配置值类型转换失败: [{section}] {key}，使用默认值: {default}")
            return default

    def set_config(self, section: str, key: str, value: Union[str, bool, int, float]):
        """设置配置值"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)

            # 转换值为字符串
            if isinstance(value, bool):
                str_value = 'true' if value else 'false'
            else:
                str_value = str(value)

            self.config.set(section, key, str_value)
            self.logger.debug(f"设置配置: [{section}] {key} = {str_value}")

            # 更新应用配置对象
            self._update_app_config(section, key, value)

        except Exception as e:
            self.logger.error(f"设置配置失败: [{section}] {key} = {value}, 错误: {e}")

    def _update_app_config(self, section: str, key: str, value: Any):
        """更新应用配置对象中的对应属性"""
        try:
            # 映射配置到AppConfig属性
            config_mapping = {
                ('General', 'auto_start_monitoring'): 'auto_start_monitoring',
                ('General', 'check_interval'): 'check_interval',
                ('General', 'language'): 'language',
                ('General', 'theme'): 'theme',
                ('Detection', 'scan_system_hotkeys'): 'scan_system_hotkeys',
                ('Detection', 'scan_application_hotkeys'): 'scan_application_hotkeys',
                ('Detection', 'scan_known_software'): 'scan_known_software',
                ('Detection', 'include_user_defined'): 'include_user_defined',
                ('Alerts', 'show_critical_alerts'): 'show_critical_alerts',
                ('Alerts', 'show_high_alerts'): 'show_high_alerts',
                ('Alerts', 'show_medium_alerts'): 'show_medium_alerts',
                ('Alerts', 'show_low_alerts'): 'show_low_alerts',
                ('Export', 'default_format'): 'default_export_format',
                ('Export', 'include_timestamps'): 'include_timestamps',
                ('Export', 'include_suggestions'): 'include_suggestions',
                ('Export', 'auto_cleanup_reports'): 'auto_cleanup_reports',
                ('Export', 'max_report_count'): 'max_report_count'
            }

            attr_name = config_mapping.get((section, key))
            if attr_name and hasattr(self.app_config, attr_name):
                setattr(self.app_config, attr_name, value)

        except Exception as e:
            self.logger.error(f"更新应用配置对象失败: {e}")

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.logger.debug("配置文件保存成功")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")

    def reload_config(self):
        """重新加载配置文件"""
        try:
            self.config.clear()
            self._init_config()
            self.logger.info("配置文件重新加载成功")
        except Exception as e:
            self.logger.error(f"重新加载配置文件失败: {e}")

    def reset_to_defaults(self):
        """重置为默认配置"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()

            self.config.clear()
            self._init_config()
            self.logger.info("配置已重置为默认值")

        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")

    def export_config(self, export_path: str) -> bool:
        """导出配置文件"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, 'w', encoding='utf-8') as f:
                self.config.write(f)

            self.logger.info(f"配置已导出到: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """导入配置文件"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                raise FileNotFoundError(f"配置文件不存在: {import_path}")

            # 备份当前配置
            backup_file = self.config_file.with_suffix('.bak')
            if self.config_file.exists():
                self.config_file.rename(backup_file)

            # 导入新配置
            temp_config = configparser.ConfigParser()
            temp_config.read(import_file, encoding='utf-8')

            # 验证配置有效性
            self.config.clear()
            for section_name in temp_config.sections():
                self.config.add_section(section_name)
                for key, value in temp_config.items(section_name):
                    self.config.set(section_name, key, value)

            self.save_config()
            self._load_config_to_object()

            # 删除备份
            if backup_file.exists():
                backup_file.unlink()

            self.logger.info(f"配置已从 {import_path} 导入")
            return True

        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")

            # 恢复备份
            backup_file = self.config_file.with_suffix('.bak')
            if backup_file.exists():
                backup_file.rename(self.config_file)
                self.reload_config()

            return False

    def get_app_config(self) -> AppConfig:
        """获取应用配置对象"""
        return self.app_config

    def update_app_config(self, config: AppConfig):
        """更新整个应用配置对象"""
        try:
            self.app_config = config

            # 同步到INI文件
            config_dict = config.to_dict()

            for section_name, section_data in config_dict.items():
                section_title = section_name.title()
                if not self.config.has_section(section_title):
                    self.config.add_section(section_title)

                for key, value in section_data.items():
                    if isinstance(value, bool):
                        str_value = 'true' if value else 'false'
                    else:
                        str_value = str(value)
                    self.config.set(section_title, key, str_value)

            self.save_config()
            self.logger.info("应用配置对象已更新并保存")

        except Exception as e:
            self.logger.error(f"更新应用配置对象失败: {e}")

    def get_all_sections(self) -> Dict[str, Dict[str, str]]:
        """获取所有配置节和选项"""
        result = {}
        for section in self.config.sections():
            result[section] = dict(self.config.items(section))
        return result

    def validate_config(self) -> List[str]:
        """验证配置文件的有效性"""
        errors = []

        try:
            # 验证必需的节是否存在
            required_sections = ['General', 'Detection', 'Alerts', 'Export']
            for section in required_sections:
                if not self.config.has_section(section):
                    errors.append(f"缺少必需的配置节: {section}")

            # 验证数值范围
            check_interval = self._get_int('General', 'check_interval', 5)
            if check_interval < 1 or check_interval > 60:
                errors.append("检查间隔必须在1-60秒之间")

            max_reports = self._get_int('Export', 'max_report_count', 20)
            if max_reports < 1 or max_reports > 1000:
                errors.append("最大报告数量必须在1-1000之间")

            # 验证格式选项
            export_format = self.get_config('Export', 'default_format', 'json')
            if export_format not in ['json', 'csv', 'txt']:
                errors.append("导出格式必须是json、csv或txt之一")

        except Exception as e:
            errors.append(f"配置验证过程中出错: {e}")

        return errors

    def close(self):
        """关闭配置管理器"""
        self.save_config()
        self.logger.info("配置管理器已关闭")