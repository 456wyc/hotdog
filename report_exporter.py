#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告导出器
Report Exporter

支持多种格式的冲突报告导出功能
"""

import os
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from hotkey_data_models import ConflictReport, ConflictGroup, HotkeyInfo

class ReportExporter:
    """多格式报告导出器"""

    def __init__(self, base_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # 设置基础路径
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))

        # 创建报告目录
        self.reports_dir = self.base_path / 'reports'
        self.reports_dir.mkdir(exist_ok=True)

        self.logger.info(f"报告导出器初始化完成，报告目录：{self.reports_dir}")

    def export_report(self, report: ConflictReport, format_type: str = 'json',
                     custom_filename: Optional[str] = None) -> str:
        """导出冲突报告

        Args:
            report: 冲突报告对象
            format_type: 导出格式 ('json', 'csv', 'txt')
            custom_filename: 自定义文件名（不包含扩展名）

        Returns:
            str: 导出文件的完整路径
        """
        try:
            # 生成文件名
            if custom_filename:
                filename_base = custom_filename
            else:
                timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
                filename_base = f"hotkey_conflict_report_{timestamp}"

            # 根据格式调用相应的导出方法
            format_type = format_type.lower()
            if format_type == 'json':
                filepath = self._export_json(report, filename_base)
            elif format_type == 'csv':
                filepath = self._export_csv(report, filename_base)
            elif format_type == 'txt':
                filepath = self._export_txt(report, filename_base)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")

            self.logger.info(f"报告导出成功: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            raise

    def _export_json(self, report: ConflictReport, filename_base: str) -> Path:
        """导出JSON格式报告"""
        filepath = self.reports_dir / f"{filename_base}.json"

        # 构建JSON数据结构
        json_data = {
            'metadata': {
                'generated_at': report.timestamp.isoformat(),
                'generator': '热键冲突检测器 v2.0',
                'format_version': '2.0'
            },
            'summary': {
                'total_hotkeys': report.total_hotkeys,
                'total_conflicts': report.total_conflicts,
                'severity_breakdown': report.severity_breakdown
            },
            'statistics': report.hotkey_statistics,
            'conflict_groups': [self._conflict_group_to_dict(group) for group in report.conflict_groups],
            'general_recommendations': report.general_recommendations
        }

        # 写入JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        return filepath

    def _conflict_group_to_dict(self, group: ConflictGroup) -> Dict[str, Any]:
        """将冲突组转换为字典"""
        return {
            'key_combination': group.key_combination,
            'severity': group.severity,
            'conflict_type': group.conflict_type,
            'hotkeys': [self._hotkey_to_dict(hotkey) for hotkey in group.hotkeys],
            'priority_hotkey': self._hotkey_to_dict(group.priority_hotkey) if group.priority_hotkey else None,
            'resolution_suggestions': group.resolution_suggestions,
            'alternative_suggestions': group.alternative_suggestions
        }

    def _hotkey_to_dict(self, hotkey: HotkeyInfo) -> Dict[str, Any]:
        """将热键信息转换为字典"""
        return {
            'key_combination': hotkey.key_combination,
            'modifier_keys': list(hotkey.modifier_keys),
            'virtual_key_code': hotkey.virtual_key_code,
            'source_type': hotkey.source_type,
            'source_name': hotkey.source_name,
            'window_title': hotkey.window_title,
            'process_id': hotkey.process_id,
            'process_name': hotkey.process_name,
            'description': hotkey.description,
            'conflict_severity': hotkey.conflict_severity,
            'detected_time': hotkey.detected_time.isoformat()
        }

    def _export_csv(self, report: ConflictReport, filename_base: str) -> Path:
        """导出CSV格式报告"""
        filepath = self.reports_dir / f"{filename_base}.csv"

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 写入标题行
            headers = [
                '热键组合', '冲突严重程度', '冲突类型', '来源类型', '来源应用',
                '窗口标题', '进程名', '进程ID', '描述', '检测时间',
                '是否优先级热键', '解决建议', '替代方案'
            ]
            writer.writerow(headers)

            # 写入冲突数据
            for group in report.conflict_groups:
                # 合并解决建议和替代方案
                suggestions = '; '.join(group.resolution_suggestions) if group.resolution_suggestions else ''
                alternatives = '; '.join(group.alternative_suggestions) if group.alternative_suggestions else ''

                for hotkey in group.hotkeys:
                    is_priority = '是' if group.priority_hotkey and hotkey == group.priority_hotkey else '否'

                    writer.writerow([
                        group.key_combination,
                        group.severity,
                        group.conflict_type,
                        hotkey.source_type,
                        hotkey.source_name,
                        hotkey.window_title,
                        hotkey.process_name,
                        hotkey.process_id,
                        hotkey.description,
                        hotkey.detected_time.strftime('%Y-%m-%d %H:%M:%S'),
                        is_priority,
                        suggestions,
                        alternatives
                    ])

        return filepath

    def _export_txt(self, report: ConflictReport, filename_base: str) -> Path:
        """导出TXT格式报告"""
        filepath = self.reports_dir / f"{filename_base}.txt"

        with open(filepath, 'w', encoding='utf-8') as f:
            # 报告标题
            f.write("═" * 60 + "\n")
            f.write("           热键冲突检测报告\n")
            f.write("═" * 60 + "\n\n")

            # 基本信息
            f.write(f"生成时间: {report.timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write(f"生成工具: 热键冲突检测器 v2.0\n\n")

            # 摘要信息
            f.write("【摘要信息】\n")
            f.write("-" * 30 + "\n")
            f.write(f"检测热键总数: {report.total_hotkeys}\n")
            f.write(f"发现冲突总数: {report.total_conflicts}\n\n")

            # 严重程度分布
            if report.severity_breakdown:
                f.write("严重程度分布:\n")
                severity_names = {
                    'critical': '严重', 'high': '高', 'medium': '中', 'low': '低'
                }
                for severity, count in report.severity_breakdown.items():
                    severity_name = severity_names.get(severity, severity)
                    f.write(f"  {severity_name}: {count} 个\n")
                f.write("\n")

            # 统计信息
            if report.hotkey_statistics:
                f.write("【统计信息】\n")
                f.write("-" * 30 + "\n")
                stats = report.hotkey_statistics

                if 'by_source_type' in stats:
                    f.write("按来源类型统计:\n")
                    type_names = {
                        'system': '系统级', 'application': '应用程序',
                        'known_software': '通用软件', 'user_defined': '用户定义'
                    }
                    for source_type, count in stats['by_source_type'].items():
                        type_name = type_names.get(source_type, source_type)
                        f.write(f"  {type_name}: {count} 个\n")
                    f.write("\n")

                if 'most_common_keys' in stats:
                    f.write("最常用的基础键:\n")
                    common_keys = sorted(stats['most_common_keys'].items(),
                                       key=lambda x: x[1], reverse=True)[:10]
                    for key, count in common_keys:
                        f.write(f"  {key}: {count} 次\n")
                    f.write("\n")

                if 'hotkey_density' in stats:
                    density = stats['hotkey_density'] * 100
                    f.write(f"热键密度: {density:.1f}%\n\n")

            # 详细冲突信息
            if report.conflict_groups:
                f.write("【详细冲突信息】\n")
                f.write("=" * 40 + "\n\n")

                for i, group in enumerate(report.conflict_groups, 1):
                    f.write(f"{i}. 热键组合: {group.key_combination}\n")
                    f.write(f"   严重程度: {group.severity}\n")
                    f.write(f"   冲突类型: {self._get_conflict_type_name(group.conflict_type)}\n")
                    f.write(f"   涉及应用: {len(group.hotkeys)} 个\n\n")

                    # 列出所有冲突的热键
                    for j, hotkey in enumerate(group.hotkeys, 1):
                        priority_mark = " ★" if group.priority_hotkey and hotkey == group.priority_hotkey else ""
                        f.write(f"   {j}) {hotkey.source_name}{priority_mark}\n")
                        f.write(f"      类型: {self._get_source_type_name(hotkey.source_type)}\n")
                        if hotkey.process_name:
                            f.write(f"      进程: {hotkey.process_name} (PID: {hotkey.process_id})\n")
                        if hotkey.window_title:
                            f.write(f"      窗口: {hotkey.window_title}\n")
                        if hotkey.description:
                            f.write(f"      描述: {hotkey.description}\n")
                        f.write(f"      检测时间: {hotkey.detected_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("\n")

                    # 解决建议
                    if group.resolution_suggestions:
                        f.write("   解决建议:\n")
                        for suggestion in group.resolution_suggestions:
                            f.write(f"   • {suggestion}\n")
                        f.write("\n")

                    # 替代方案
                    if group.alternative_suggestions:
                        f.write("   推荐的替代热键:\n")
                        for alt in group.alternative_suggestions:
                            f.write(f"   → {alt}\n")
                        f.write("\n")

                    f.write("-" * 50 + "\n\n")

            # 总体建议
            if report.general_recommendations:
                f.write("【总体建议】\n")
                f.write("=" * 40 + "\n")
                for i, rec in enumerate(report.general_recommendations, 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")

            # 结尾
            f.write("=" * 60 + "\n")
            f.write("报告结束\n")

        return filepath

    def _get_conflict_type_name(self, conflict_type: str) -> str:
        """获取冲突类型的中文名称"""
        type_names = {
            'system_override': '系统级覆盖',
            'cross_application': '跨应用程序',
            'standard': '标准冲突'
        }
        return type_names.get(conflict_type, conflict_type)

    def _get_source_type_name(self, source_type: str) -> str:
        """获取来源类型的中文名称"""
        type_names = {
            'system': '系统级',
            'application': '应用程序',
            'known_software': '通用软件',
            'user_defined': '用户定义',
            'unknown': '未知'
        }
        return type_names.get(source_type, source_type)

    def export_multiple_formats(self, report: ConflictReport, formats: List[str],
                               custom_filename: Optional[str] = None) -> Dict[str, str]:
        """同时导出多种格式的报告

        Args:
            report: 冲突报告对象
            formats: 要导出的格式列表
            custom_filename: 自定义文件名前缀

        Returns:
            Dict[str, str]: 格式名到文件路径的映射
        """
        results = {}
        for format_type in formats:
            try:
                filepath = self.export_report(report, format_type, custom_filename)
                results[format_type] = filepath
            except Exception as e:
                self.logger.error(f"导出 {format_type} 格式失败: {e}")
                results[format_type] = None

        return results

    def get_report_list(self, format_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取报告文件列表

        Args:
            format_filter: 格式过滤器 ('json', 'csv', 'txt')

        Returns:
            List[Dict]: 报告文件信息列表
        """
        reports = []

        try:
            # 支持的格式
            extensions = ['.json', '.csv', '.txt']
            if format_filter:
                extensions = [f'.{format_filter.lower()}']

            for ext in extensions:
                for file_path in self.reports_dir.glob(f"*{ext}"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        reports.append({
                            'filename': file_path.name,
                            'filepath': str(file_path),
                            'format': ext[1:],  # 去掉点号
                            'size': stat.st_size,
                            'size_human': self._format_file_size(stat.st_size),
                            'created_time': datetime.fromtimestamp(stat.st_ctime),
                            'modified_time': datetime.fromtimestamp(stat.st_mtime)
                        })

            # 按修改时间降序排序
            reports.sort(key=lambda x: x['modified_time'], reverse=True)

        except Exception as e:
            self.logger.error(f"获取报告列表失败: {e}")

        return reports

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小为人类可读格式"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def cleanup_old_reports(self, keep_count: int = 20, format_filter: Optional[str] = None) -> int:
        """清理旧的报告文件

        Args:
            keep_count: 保留的报告数量
            format_filter: 格式过滤器

        Returns:
            int: 删除的文件数量
        """
        deleted_count = 0

        try:
            reports = self.get_report_list(format_filter)

            if len(reports) > keep_count:
                # 删除最旧的报告
                for report in reports[keep_count:]:
                    try:
                        os.remove(report['filepath'])
                        deleted_count += 1
                        self.logger.info(f"删除旧报告: {report['filename']}")
                    except Exception as e:
                        self.logger.error(f"删除报告文件失败 {report['filename']}: {e}")

            self.logger.info(f"清理完成，删除了 {deleted_count} 个旧报告")

        except Exception as e:
            self.logger.error(f"清理旧报告失败: {e}")

        return deleted_count

    def delete_report(self, filename: str) -> bool:
        """删除指定的报告文件

        Args:
            filename: 要删除的文件名

        Returns:
            bool: 是否删除成功
        """
        try:
            filepath = self.reports_dir / filename
            if filepath.exists() and filepath.is_file():
                filepath.unlink()
                self.logger.info(f"删除报告文件: {filename}")
                return True
            else:
                self.logger.warning(f"报告文件不存在: {filename}")
                return False

        except Exception as e:
            self.logger.error(f"删除报告文件失败 {filename}: {e}")
            return False

    def get_report_summary(self) -> Dict[str, Any]:
        """获取报告目录摘要信息

        Returns:
            Dict: 包含报告统计信息的字典
        """
        try:
            reports = self.get_report_list()

            total_size = sum(report['size'] for report in reports)
            format_count = {}
            for report in reports:
                format_count[report['format']] = format_count.get(report['format'], 0) + 1

            return {
                'total_reports': len(reports),
                'total_size': total_size,
                'total_size_human': self._format_file_size(total_size),
                'format_distribution': format_count,
                'oldest_report': reports[-1] if reports else None,
                'newest_report': reports[0] if reports else None,
                'reports_directory': str(self.reports_dir)
            }

        except Exception as e:
            self.logger.error(f"获取报告摘要失败: {e}")
            return {}