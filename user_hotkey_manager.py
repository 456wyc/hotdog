#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户热键管理器
User Hotkey Manager

管理用户自定义热键的增删改查功能
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from hotkey_data_models import HotkeyInfo

class UserHotkeyManager:
    """用户热键管理器"""

    def __init__(self, base_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # 设置基础路径
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))

        # 创建数据目录
        self.data_dir = self.base_path / 'data'
        self.data_dir.mkdir(exist_ok=True)

        # 文件路径
        self.user_hotkeys_file = self.data_dir / 'user_hotkeys.json'
        self.history_file = self.data_dir / 'hotkey_history.json'

        # 用户热键列表
        self.user_hotkeys: List[HotkeyInfo] = []

        # 加载用户热键
        self.load_user_hotkeys()

        self.logger.info(f"用户热键管理器初始化完成，数据目录：{self.data_dir}")

    def load_user_hotkeys(self) -> List[HotkeyInfo]:
        """加载用户自定义热键"""
        self.user_hotkeys = []

        try:
            if self.user_hotkeys_file.exists():
                with open(self.user_hotkeys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 验证文件格式
                if not isinstance(data, dict) or 'hotkeys' not in data:
                    self.logger.warning("用户热键文件格式不正确，重新创建")
                    self._create_empty_hotkeys_file()
                    return self.user_hotkeys

                # 加载热键
                for item in data.get('hotkeys', []):
                    try:
                        hotkey = HotkeyInfo.from_dict(item)
                        # 确保是用户定义类型
                        hotkey.source_type = 'user_defined'
                        self.user_hotkeys.append(hotkey)
                    except Exception as e:
                        self.logger.warning(f"跳过无效的热键数据: {e}")
                        continue

                self.logger.info(f"加载了 {len(self.user_hotkeys)} 个用户自定义热键")

            else:
                self._create_empty_hotkeys_file()

        except Exception as e:
            self.logger.error(f"加载用户热键失败: {e}")
            self._create_empty_hotkeys_file()

        return self.user_hotkeys

    def _create_empty_hotkeys_file(self):
        """创建空的热键文件"""
        try:
            data = {
                'version': '2.0',
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'hotkeys': []
            }

            with open(self.user_hotkeys_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info("创建了空的用户热键文件")

        except Exception as e:
            self.logger.error(f"创建空热键文件失败: {e}")

    def save_user_hotkeys(self) -> bool:
        """保存用户自定义热键"""
        try:
            data = {
                'version': '2.0',
                'created_at': self._get_file_created_time(),
                'last_modified': datetime.now().isoformat(),
                'total_count': len(self.user_hotkeys),
                'hotkeys': [hotkey.to_dict() for hotkey in self.user_hotkeys]
            }

            with open(self.user_hotkeys_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"保存了 {len(self.user_hotkeys)} 个用户自定义热键")
            return True

        except Exception as e:
            self.logger.error(f"保存用户热键失败: {e}")
            return False

    def _get_file_created_time(self) -> str:
        """获取文件创建时间"""
        try:
            if self.user_hotkeys_file.exists():
                with open(self.user_hotkeys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('created_at', datetime.now().isoformat())
        except:
            pass
        return datetime.now().isoformat()

    def add_user_hotkey(self, hotkey: HotkeyInfo) -> Tuple[bool, str]:
        """添加用户自定义热键

        Args:
            hotkey: 热键信息对象

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证热键有效性
            validation_result = self.validate_hotkey(hotkey)
            if not validation_result[0]:
                return False, validation_result[1]

            # 检查是否已存在相同的热键
            for existing in self.user_hotkeys:
                if existing.key_combination.lower() == hotkey.key_combination.lower():
                    return False, f"热键 {hotkey.key_combination} 已存在"

            # 设置为用户定义类型
            hotkey.source_type = 'user_defined'
            hotkey.source_name = hotkey.source_name or 'User Defined'
            hotkey.detected_time = datetime.now()

            # 添加到列表
            self.user_hotkeys.append(hotkey)

            # 保存到文件
            if self.save_user_hotkeys():
                self._record_hotkey_operation('add', hotkey.key_combination)
                self.logger.info(f"添加用户热键成功: {hotkey.key_combination}")
                return True, f"成功添加热键: {hotkey.key_combination}"
            else:
                # 如果保存失败，从列表中移除
                self.user_hotkeys.remove(hotkey)
                return False, "保存失败"

        except Exception as e:
            self.logger.error(f"添加用户热键失败: {e}")
            return False, f"添加失败: {str(e)}"

    def update_user_hotkey(self, old_combination: str, updated_hotkey: HotkeyInfo) -> Tuple[bool, str]:
        """更新用户自定义热键

        Args:
            old_combination: 原热键组合
            updated_hotkey: 更新后的热键信息

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 查找要更新的热键
            target_index = -1
            for i, hotkey in enumerate(self.user_hotkeys):
                if hotkey.key_combination.lower() == old_combination.lower():
                    target_index = i
                    break

            if target_index == -1:
                return False, f"未找到热键: {old_combination}"

            # 如果热键组合发生了变化，检查新组合是否冲突
            if updated_hotkey.key_combination.lower() != old_combination.lower():
                for i, existing in enumerate(self.user_hotkeys):
                    if i != target_index and existing.key_combination.lower() == updated_hotkey.key_combination.lower():
                        return False, f"热键 {updated_hotkey.key_combination} 已存在"

            # 验证新热键有效性
            validation_result = self.validate_hotkey(updated_hotkey)
            if not validation_result[0]:
                return False, validation_result[1]

            # 确保是用户定义类型
            updated_hotkey.source_type = 'user_defined'
            updated_hotkey.source_name = updated_hotkey.source_name or 'User Defined'

            # 更新热键
            old_hotkey = self.user_hotkeys[target_index]
            self.user_hotkeys[target_index] = updated_hotkey

            # 保存到文件
            if self.save_user_hotkeys():
                self._record_hotkey_operation('update', f"{old_combination} -> {updated_hotkey.key_combination}")
                self.logger.info(f"更新用户热键成功: {old_combination} -> {updated_hotkey.key_combination}")
                return True, f"成功更新热键: {old_combination} -> {updated_hotkey.key_combination}"
            else:
                # 如果保存失败，恢复原热键
                self.user_hotkeys[target_index] = old_hotkey
                return False, "保存失败"

        except Exception as e:
            self.logger.error(f"更新用户热键失败: {e}")
            return False, f"更新失败: {str(e)}"

    def remove_user_hotkey(self, key_combination: str) -> Tuple[bool, str]:
        """移除用户自定义热键

        Args:
            key_combination: 要移除的热键组合

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 查找要删除的热键
            target_hotkey = None
            for hotkey in self.user_hotkeys:
                if hotkey.key_combination.lower() == key_combination.lower():
                    target_hotkey = hotkey
                    break

            if not target_hotkey:
                return False, f"未找到热键: {key_combination}"

            # 从列表中移除
            self.user_hotkeys.remove(target_hotkey)

            # 保存到文件
            if self.save_user_hotkeys():
                self._record_hotkey_operation('remove', key_combination)
                self.logger.info(f"移除用户热键成功: {key_combination}")
                return True, f"成功移除热键: {key_combination}"
            else:
                # 如果保存失败，重新添加
                self.user_hotkeys.append(target_hotkey)
                return False, "保存失败"

        except Exception as e:
            self.logger.error(f"移除用户热键失败: {e}")
            return False, f"移除失败: {str(e)}"

    def validate_hotkey(self, hotkey: HotkeyInfo) -> Tuple[bool, str]:
        """验证热键有效性

        Args:
            hotkey: 热键信息对象

        Returns:
            Tuple[bool, str]: (是否有效, 验证消息)
        """
        try:
            # 检查必需字段
            if not hotkey.key_combination or not hotkey.key_combination.strip():
                return False, "热键组合不能为空"

            # 标准化热键组合
            combo = hotkey.key_combination.strip()

            # 检查格式
            if '+' in combo:
                parts = [part.strip() for part in combo.split('+')]
                if len(parts) < 2:
                    return False, "热键组合格式不正确"

                # 检查修饰键
                modifiers = parts[:-1]
                base_key = parts[-1]

                valid_modifiers = {'Ctrl', 'Alt', 'Shift', 'Win', 'Control', 'Windows'}
                for modifier in modifiers:
                    if modifier not in valid_modifiers:
                        return False, f"无效的修饰键: {modifier}"

                # 检查基础键
                if not base_key:
                    return False, "缺少基础键"

                # 不允许只有修饰键
                if base_key in valid_modifiers:
                    return False, "基础键不能是修饰键"

            # 检查应用名称
            if not hotkey.source_name or not hotkey.source_name.strip():
                hotkey.source_name = 'User Defined'

            # 检查描述长度
            if len(hotkey.description) > 200:
                return False, "描述长度不能超过200个字符"

            return True, "热键验证通过"

        except Exception as e:
            return False, f"验证过程中出错: {str(e)}"

    def get_user_hotkeys(self) -> List[HotkeyInfo]:
        """获取所有用户自定义热键"""
        return self.user_hotkeys.copy()

    def get_hotkey_by_combination(self, key_combination: str) -> Optional[HotkeyInfo]:
        """根据热键组合查找热键

        Args:
            key_combination: 热键组合

        Returns:
            Optional[HotkeyInfo]: 找到的热键，不存在则返回None
        """
        for hotkey in self.user_hotkeys:
            if hotkey.key_combination.lower() == key_combination.lower():
                return hotkey
        return None

    def search_hotkeys(self, keyword: str) -> List[HotkeyInfo]:
        """搜索热键

        Args:
            keyword: 搜索关键词

        Returns:
            List[HotkeyInfo]: 匹配的热键列表
        """
        if not keyword:
            return self.user_hotkeys.copy()

        keyword_lower = keyword.lower()
        results = []

        for hotkey in self.user_hotkeys:
            # 搜索热键组合、应用名称、描述
            if (keyword_lower in hotkey.key_combination.lower() or
                keyword_lower in hotkey.source_name.lower() or
                keyword_lower in hotkey.description.lower()):
                results.append(hotkey)

        return results

    def get_hotkeys_by_application(self, app_name: str) -> List[HotkeyInfo]:
        """获取特定应用程序的热键

        Args:
            app_name: 应用程序名称

        Returns:
            List[HotkeyInfo]: 该应用的热键列表
        """
        results = []
        app_name_lower = app_name.lower()

        for hotkey in self.user_hotkeys:
            if app_name_lower in hotkey.source_name.lower():
                results.append(hotkey)

        return results

    def export_user_hotkeys(self, export_path: str) -> bool:
        """导出用户热键到指定文件

        Args:
            export_path: 导出文件路径

        Returns:
            bool: 是否导出成功
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            export_data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'exporter': '热键冲突检测器 v2.0',
                    'total_count': len(self.user_hotkeys)
                },
                'hotkeys': [hotkey.to_dict() for hotkey in self.user_hotkeys]
            }

            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"用户热键导出成功: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"导出用户热键失败: {e}")
            return False

    def import_user_hotkeys(self, import_path: str, overwrite: bool = False) -> Tuple[bool, str, int]:
        """从文件导入用户热键

        Args:
            import_path: 导入文件路径
            overwrite: 是否覆盖现有热键

        Returns:
            Tuple[bool, str, int]: (是否成功, 消息, 导入数量)
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                return False, f"导入文件不存在: {import_path}", 0

            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查文件格式
            if 'hotkeys' not in data:
                return False, "导入文件格式不正确", 0

            imported_count = 0
            skipped_count = 0
            backup_hotkeys = self.user_hotkeys.copy()

            try:
                for item in data['hotkeys']:
                    hotkey = HotkeyInfo.from_dict(item)
                    hotkey.source_type = 'user_defined'

                    # 检查是否已存在
                    existing = self.get_hotkey_by_combination(hotkey.key_combination)
                    if existing:
                        if overwrite:
                            # 更新现有热键
                            result = self.update_user_hotkey(hotkey.key_combination, hotkey)
                            if result[0]:
                                imported_count += 1
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                    else:
                        # 添加新热键
                        result = self.add_user_hotkey(hotkey)
                        if result[0]:
                            imported_count += 1
                        else:
                            skipped_count += 1

                message = f"导入完成：成功 {imported_count} 个，跳过 {skipped_count} 个"
                self.logger.info(message)
                return True, message, imported_count

            except Exception as e:
                # 导入失败，恢复备份
                self.user_hotkeys = backup_hotkeys
                self.save_user_hotkeys()
                return False, f"导入过程中出错，已恢复: {str(e)}", 0

        except Exception as e:
            self.logger.error(f"导入用户热键失败: {e}")
            return False, f"导入失败: {str(e)}", 0

    def _record_hotkey_operation(self, operation: str, details: str):
        """记录热键操作历史

        Args:
            operation: 操作类型 (add, update, remove)
            details: 操作详情
        """
        try:
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'details': details
            }

            # 加载现有历史
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

            # 添加新记录
            history.append(history_entry)

            # 保持最近100条记录
            if len(history) > 100:
                history = history[-100:]

            # 保存历史
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.warning(f"记录操作历史失败: {e}")

    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取操作历史

        Args:
            limit: 返回的记录数量限制

        Returns:
            List[Dict]: 操作历史列表
        """
        try:
            if not self.history_file.exists():
                return []

            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # 返回最近的记录
            return history[-limit:] if len(history) > limit else history

        except Exception as e:
            self.logger.error(f"获取操作历史失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取用户热键统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            stats = {
                'total_count': len(self.user_hotkeys),
                'by_application': {},
                'by_severity': {},
                'most_common_modifiers': {},
                'most_common_keys': {},
                'creation_dates': []
            }

            for hotkey in self.user_hotkeys:
                # 按应用程序统计
                app = hotkey.source_name or 'Unknown'
                stats['by_application'][app] = stats['by_application'].get(app, 0) + 1

                # 按严重程度统计
                severity = hotkey.conflict_severity or 'unknown'
                stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1

                # 修饰键统计
                for modifier in hotkey.modifier_keys:
                    stats['most_common_modifiers'][modifier] = stats['most_common_modifiers'].get(modifier, 0) + 1

                # 基础键统计
                if '+' in hotkey.key_combination:
                    base_key = hotkey.key_combination.split('+')[-1]
                else:
                    base_key = hotkey.key_combination
                stats['most_common_keys'][base_key] = stats['most_common_keys'].get(base_key, 0) + 1

                # 创建时间
                stats['creation_dates'].append(hotkey.detected_time.isoformat())

            return stats

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}

    def clear_all_hotkeys(self) -> bool:
        """清除所有用户热键

        Returns:
            bool: 是否清除成功
        """
        try:
            self.user_hotkeys.clear()
            if self.save_user_hotkeys():
                self._record_hotkey_operation('clear_all', f"清除所有用户热键")
                self.logger.info("清除所有用户热键成功")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"清除所有用户热键失败: {e}")
            return False