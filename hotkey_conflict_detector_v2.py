#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键冲突检测器 v2.0 主程序
Hotkey Conflict Detector v2.0 Main Program

整合所有新功能的主控制器
"""

import logging
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from hotkey_data_models import HotkeyInfo, ConflictReport, AppConfig
from enhanced_hotkey_detector import EnhancedHotkeyDetector
from smart_conflict_analyzer import SmartConflictAnalyzer
from config_manager import ConfigManager
from report_exporter import ReportExporter
from user_hotkey_manager import UserHotkeyManager

class HotkeyConflictDetectorV2:
    """热键冲突检测器 v2.0 主控制器"""

    def __init__(self, base_path: Optional[str] = None):
        # 设置基础路径
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent

        # 初始化日志系统
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

        # 初始化各个模块
        self.config_manager = ConfigManager(str(self.base_path))
        self.detector = EnhancedHotkeyDetector()
        self.analyzer = SmartConflictAnalyzer()
        self.report_exporter = ReportExporter(str(self.base_path))
        self.user_hotkey_manager = UserHotkeyManager(str(self.base_path))

        # 获取应用配置
        self.app_config = self.config_manager.get_app_config()

        # 当前检测到的热键
        self.detected_hotkeys: List[HotkeyInfo] = []
        self.last_scan_time: Optional[datetime] = None
        self.last_report: Optional[ConflictReport] = None

        self.logger.info("热键冲突检测器 v2.0 初始化完成")

    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = self.base_path / 'logs'
        log_dir.mkdir(exist_ok=True)

        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # 配置根日志器
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(
                    log_dir / f'hotkey_detector_{datetime.now().strftime("%Y%m%d")}.log',
                    encoding='utf-8'
                ),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def scan_hotkeys(self, progress_callback=None) -> List[HotkeyInfo]:
        """扫描热键

        Args:
            progress_callback: 进度回调函数，接收(当前步骤, 总步骤, 描述)参数

        Returns:
            List[HotkeyInfo]: 检测到的热键列表
        """
        self.logger.info("开始扫描热键...")

        if progress_callback:
            progress_callback(0, 5, "初始化扫描...")

        all_hotkeys = []

        # 扫描系统热键
        if self.app_config.scan_system_hotkeys:
            if progress_callback:
                progress_callback(1, 5, "扫描系统热键...")

            system_hotkeys = self.detector.detect_system_hotkeys()
            all_hotkeys.extend(system_hotkeys)
            self.logger.info(f"扫描到 {len(system_hotkeys)} 个系统热键")

        # 扫描应用程序热键
        if self.app_config.scan_application_hotkeys:
            if progress_callback:
                progress_callback(2, 5, "扫描应用程序热键...")

            app_hotkeys = self.detector.detect_application_hotkeys()
            all_hotkeys.extend(app_hotkeys)
            self.logger.info(f"扫描到 {len(app_hotkeys)} 个应用程序热键")

        # 扫描注册表热键
        if progress_callback:
            progress_callback(3, 5, "扫描注册表热键...")

        registry_hotkeys = self.detector.detect_registry_hotkeys()
        all_hotkeys.extend(registry_hotkeys)
        self.logger.info(f"扫描到 {len(registry_hotkeys)} 个注册表热键")

        # 包含用户自定义热键
        if self.app_config.include_user_defined:
            if progress_callback:
                progress_callback(4, 5, "加载用户自定义热键...")

            user_hotkeys = self.user_hotkey_manager.get_user_hotkeys()
            all_hotkeys.extend(user_hotkeys)
            self.logger.info(f"加载了 {len(user_hotkeys)} 个用户自定义热键")

        if progress_callback:
            progress_callback(5, 5, "扫描完成")

        # 更新检测结果
        self.detected_hotkeys = all_hotkeys
        self.last_scan_time = datetime.now()

        self.logger.info(f"热键扫描完成，共检测到 {len(all_hotkeys)} 个热键")
        return all_hotkeys

    def analyze_conflicts(self, hotkeys: Optional[List[HotkeyInfo]] = None) -> ConflictReport:
        """分析热键冲突

        Args:
            hotkeys: 要分析的热键列表，如果为None则使用最新扫描结果

        Returns:
            ConflictReport: 冲突分析报告
        """
        if hotkeys is None:
            hotkeys = self.detected_hotkeys

        if not hotkeys:
            self.logger.warning("没有热键数据可供分析")
            # 返回空报告
            return ConflictReport(
                timestamp=datetime.now(),
                total_hotkeys=0,
                total_conflicts=0,
                conflict_groups=[],
                severity_breakdown={},
                general_recommendations=["没有检测到热键，请先运行热键扫描"],
                hotkey_statistics={}
            )

        self.logger.info(f"开始分析 {len(hotkeys)} 个热键的冲突...")

        # 使用智能分析器分析冲突
        report = self.analyzer.analyze_conflicts(hotkeys)
        self.last_report = report

        self.logger.info(f"冲突分析完成，发现 {report.total_conflicts} 个冲突")
        return report

    def export_report(self, report: Optional[ConflictReport] = None,
                     formats: List[str] = None,
                     custom_filename: Optional[str] = None) -> Dict[str, str]:
        """导出冲突报告

        Args:
            report: 要导出的报告，如果为None则使用最新分析结果
            formats: 导出格式列表，如果为None则使用配置中的默认格式
            custom_filename: 自定义文件名

        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        if report is None:
            report = self.last_report

        if report is None:
            self.logger.error("没有可导出的报告")
            return {}

        if formats is None:
            formats = [self.app_config.default_export_format]

        self.logger.info(f"开始导出报告，格式: {formats}")

        # 导出报告
        results = self.report_exporter.export_multiple_formats(report, formats, custom_filename)

        # 自动清理旧报告
        if self.app_config.auto_cleanup_reports:
            self.report_exporter.cleanup_old_reports(self.app_config.max_report_count)

        successful_exports = [fmt for fmt, path in results.items() if path is not None]
        self.logger.info(f"报告导出完成，成功导出格式: {successful_exports}")

        return results

    def get_hotkey_statistics(self, hotkeys: Optional[List[HotkeyInfo]] = None) -> Dict[str, Any]:
        """获取热键统计信息

        Args:
            hotkeys: 要统计的热键列表，如果为None则使用最新扫描结果

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        if hotkeys is None:
            hotkeys = self.detected_hotkeys

        if not hotkeys:
            return {}

        return self.analyzer._generate_statistics(hotkeys)

    def get_user_hotkeys(self) -> List[HotkeyInfo]:
        """获取用户自定义热键"""
        return self.user_hotkey_manager.get_user_hotkeys()

    def add_user_hotkey(self, hotkey: HotkeyInfo) -> tuple:
        """添加用户自定义热键"""
        return self.user_hotkey_manager.add_user_hotkey(hotkey)

    def remove_user_hotkey(self, key_combination: str) -> tuple:
        """删除用户自定义热键"""
        return self.user_hotkey_manager.remove_user_hotkey(key_combination)

    def search_hotkeys(self, keyword: str, search_type: str = "all") -> List[HotkeyInfo]:
        """搜索热键

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型 ("all", "detected", "user")

        Returns:
            List[HotkeyInfo]: 匹配的热键列表
        """
        results = []

        if search_type in ["all", "detected"]:
            # 在检测到的热键中搜索
            keyword_lower = keyword.lower()
            for hotkey in self.detected_hotkeys:
                if (keyword_lower in hotkey.key_combination.lower() or
                    keyword_lower in hotkey.source_name.lower() or
                    keyword_lower in hotkey.description.lower()):
                    results.append(hotkey)

        if search_type in ["all", "user"]:
            # 在用户热键中搜索
            user_results = self.user_hotkey_manager.search_hotkeys(keyword)
            results.extend(user_results)

        return results

    def get_app_config(self) -> AppConfig:
        """获取应用配置"""
        return self.app_config

    def update_config(self, config: AppConfig):
        """更新应用配置"""
        self.app_config = config
        self.config_manager.update_app_config(config)

    def get_config_value(self, section: str, key: str, default: str = ""):
        """获取配置值"""
        return self.config_manager.get_config(section, key, default)

    def set_config_value(self, section: str, key: str, value):
        """设置配置值"""
        self.config_manager.set_config(section, key, value)

    def save_config(self):
        """保存配置"""
        self.config_manager.save_config()

    def get_report_list(self) -> List[Dict[str, Any]]:
        """获取报告文件列表"""
        return self.report_exporter.get_report_list()

    def delete_report(self, filename: str) -> bool:
        """删除报告文件"""
        return self.report_exporter.delete_report(filename)

    def get_recent_scan_info(self) -> Dict[str, Any]:
        """获取最近扫描信息"""
        return {
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'total_hotkeys': len(self.detected_hotkeys),
            'has_report': self.last_report is not None,
            'total_conflicts': self.last_report.total_conflicts if self.last_report else 0
        }

    def validate_hotkey_combination(self, combination: str) -> tuple:
        """验证热键组合格式"""
        from hotkey_data_models import HotkeyInfo

        # 创建临时热键对象进行验证
        temp_hotkey = HotkeyInfo(
            key_combination=combination,
            source_name="Validation Test"
        )

        return self.user_hotkey_manager.validate_hotkey(temp_hotkey)

    def get_application_summary(self) -> Dict[str, Any]:
        """获取应用程序摘要信息"""
        try:
            hotkey_stats = self.get_hotkey_statistics()
            user_stats = self.user_hotkey_manager.get_statistics()
            report_summary = self.report_exporter.get_report_summary()

            return {
                'version': '2.0',
                'initialized_at': datetime.now().isoformat(),
                'modules': {
                    'detector': 'EnhancedHotkeyDetector',
                    'analyzer': 'SmartConflictAnalyzer',
                    'config_manager': 'ConfigManager',
                    'report_exporter': 'ReportExporter',
                    'user_hotkey_manager': 'UserHotkeyManager'
                },
                'statistics': {
                    'detected_hotkeys': hotkey_stats,
                    'user_hotkeys': user_stats,
                    'reports': report_summary
                },
                'recent_scan': self.get_recent_scan_info()
            }

        except Exception as e:
            self.logger.error(f"获取应用程序摘要失败: {e}")
            return {
                'version': '2.0',
                'error': str(e)
            }

    def close(self):
        """关闭应用程序，清理资源"""
        try:
            self.config_manager.close()
            self.logger.info("应用程序已关闭")
        except Exception as e:
            self.logger.error(f"关闭应用程序时出错: {e}")

# 命令行接口
def main():
    """命令行主程序"""
    print("热键冲突检测器 v2.0")
    print("=" * 50)

    try:
        # 创建应用实例
        app = HotkeyConflictDetectorV2()

        # 显示应用信息
        print(f"初始化完成")
        print(f"基础路径: {app.base_path}")

        # 扫描热键
        print("\n开始扫描热键...")
        hotkeys = app.scan_hotkeys()
        print(f"检测到 {len(hotkeys)} 个热键")

        # 分析冲突
        print("\n分析冲突...")
        report = app.analyze_conflicts()
        print(f"发现 {report.total_conflicts} 个冲突")

        # 显示严重程度分布
        if report.severity_breakdown:
            print("\n冲突严重程度分布:")
            for severity, count in report.severity_breakdown.items():
                print(f"  {severity}: {count} 个")

        # 导出报告
        if report.total_conflicts > 0:
            print("\n导出报告...")
            results = app.export_report(formats=['json', 'txt'])

            for format_type, filepath in results.items():
                if filepath:
                    print(f"  {format_type.upper()}: {filepath}")

        # 显示总体建议
        if report.general_recommendations:
            print("\n总体建议:")
            for i, rec in enumerate(report.general_recommendations, 1):
                print(f"  {i}. {rec}")

        print(f"\n检测完成！")

    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n运行过程中出错: {e}")
    finally:
        try:
            app.close()
        except:
            pass

if __name__ == "__main__":
    main()