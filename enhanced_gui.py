#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版热键冲突检测器GUI界面
Enhanced Hotkey Conflict Detector GUI

提供现代化的用户界面，集成所有v2.0新功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from hotkey_conflict_detector_v2 import HotkeyConflictDetectorV2
from hotkey_data_models import HotkeyInfo, ConflictReport, AppConfig, ConflictGroup
from config_manager import ConfigManager
from user_hotkey_manager import UserHotkeyManager
from report_exporter import ReportExporter

class EnhancedHotkeyGUI:
    """增强版热键冲突检测器主界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("热键冲突检测器 v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # 设置现代化主题
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用现代化主题

        # 初始化核心组件
        self.detector = HotkeyConflictDetectorV2()
        self.config_manager = self.detector.config_manager
        self.user_manager = self.detector.user_hotkey_manager
        self.report_exporter = self.detector.report_exporter

        # 应用配置
        self.app_config = self.detector.get_app_config()

        # 数据存储
        self.detected_hotkeys: List[HotkeyInfo] = []
        self.conflict_report: Optional[ConflictReport] = None
        self.is_scanning = False

        # 创建界面
        self.create_widgets()
        self.create_menu()
        self.setup_logging()

        # 初始状态
        self.update_status("就绪")
        self.load_initial_data()

        logging.info("增强版GUI界面初始化完成")

    def create_widgets(self):
        """创建主界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部工具栏
        self.create_toolbar(main_frame)

        # 主内容区域 - 使用PanedWindow实现可调整分割
        self.main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # 左侧面板 - 统计和快速操作
        left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(left_panel, weight=1)

        # 右侧面板 - 主内容
        right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(right_panel, weight=3)

        # 构建左侧面板
        self.create_left_panel(left_panel)

        # 构建右侧面板
        self.create_right_panel(right_panel)

    def create_toolbar(self, parent):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # 主要操作按钮
        self.scan_button = ttk.Button(
            toolbar,
            text="开始扫描",
            command=self.start_scan,
            width=12
        )
        self.scan_button.pack(side=tk.LEFT, padx=(0, 5))

        self.analyze_button = ttk.Button(
            toolbar,
            text="分析冲突",
            command=self.analyze_conflicts,
            width=12,
            state='disabled'
        )
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 5))

        self.export_button = ttk.Button(
            toolbar,
            text="导出报告",
            command=self.export_report,
            width=12,
            state='disabled'
        )
        self.export_button.pack(side=tk.LEFT, padx=(0, 5))

        # 分隔符
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # 用户热键管理按钮
        self.user_hotkeys_button = ttk.Button(
            toolbar,
            text="用户热键管理",
            command=self.show_user_hotkeys_dialog,
            width=12
        )
        self.user_hotkeys_button.pack(side=tk.LEFT, padx=(0, 5))

        self.settings_button = ttk.Button(
            toolbar,
            text="设置",
            command=self.show_settings_dialog,
            width=8
        )
        self.settings_button.pack(side=tk.LEFT, padx=(0, 5))

        # 状态指示器
        status_frame = ttk.Frame(toolbar)
        status_frame.pack(side=tk.RIGHT)

        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=(0, 10))

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=100)
        self.progress.pack(side=tk.LEFT)

    def create_left_panel(self, parent):
        """创建左侧面板"""
        # 统计信息框架
        stats_frame = ttk.LabelFrame(parent, text="统计概览", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # 统计网格布局
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        # 热键统计
        ttk.Label(stats_grid, text="总热键数:", font=('', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.total_hotkeys_label = ttk.Label(stats_grid, text="0", foreground="blue")
        self.total_hotkeys_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 15), pady=2)

        ttk.Label(stats_grid, text="冲突数:", font=('', 9, 'bold')).grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5), pady=2)
        self.conflicts_label = ttk.Label(stats_grid, text="0", foreground="red")
        self.conflicts_label.grid(row=0, column=3, sticky=tk.W, pady=2)

        # 类型统计
        ttk.Label(stats_grid, text="系统热键:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.system_hotkeys_label = ttk.Label(stats_grid, text="0")
        self.system_hotkeys_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 15), pady=2)

        ttk.Label(stats_grid, text="应用热键:").grid(
            row=1, column=2, sticky=tk.W, padx=(0, 5), pady=2)
        self.app_hotkeys_label = ttk.Label(stats_grid, text="0")
        self.app_hotkeys_label.grid(row=1, column=3, sticky=tk.W, pady=2)

        # 严重程度统计
        severity_frame = ttk.LabelFrame(parent, text="冲突严重程度", padding=10)
        severity_frame.pack(fill=tk.X, pady=(0, 10))

        self.severity_labels = {}
        severities = [('critical', '严重'), ('high', '高'), ('medium', '中'), ('low', '低')]
        
        for i, (severity_key, severity_name) in enumerate(severities):
            ttk.Label(severity_frame, text=f"{severity_name}:").grid(
                row=i, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            label = ttk.Label(severity_frame, text="0")
            label.grid(row=i, column=1, sticky=tk.W, pady=2)
            self.severity_labels[severity_key] = label

        # 快速操作框架
        quick_actions_frame = ttk.LabelFrame(parent, text="快速操作", padding=10)
        quick_actions_frame.pack(fill=tk.X)

        ttk.Button(
            quick_actions_frame,
            text="查看最近报告",
            command=self.show_recent_reports,
            width=15
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            quick_actions_frame,
            text="添加用户热键",
            command=self.add_user_hotkey,
            width=15
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            quick_actions_frame,
            text="清理旧报告",
            command=self.cleanup_old_reports,
            width=15
        ).pack(fill=tk.X, pady=2)

    def create_right_panel(self, parent):
        """创建右侧主内容面板"""
        # 使用Notebook组织内容
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建各个标签页
        self.create_overview_tab()
        self.create_conflicts_tab()
        self.create_hotkeys_tab()
        self.create_reports_tab()
        self.create_log_tab()

    def create_overview_tab(self):
        """创建概览标签页"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="概览")

        # 冲突概览列表
        conflicts_frame = ttk.LabelFrame(overview_frame, text="冲突概览", padding=10)
        conflicts_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 冲突列表
        columns = ('热键组合', '冲突应用', '类型', '严重程度', '建议')
        self.overview_tree = ttk.Treeview(
            conflicts_frame, 
            columns=columns, 
            show='headings',
            height=15
        )

        # 设置列宽
        column_widths = {'热键组合': 120, '冲突应用': 200, '类型': 100, '严重程度': 80, '建议': 150}
        for col in columns:
            self.overview_tree.heading(col, text=col)
            self.overview_tree.column(col, width=column_widths.get(col, 100))

        # 滚动条
        scroll_y = ttk.Scrollbar(conflicts_frame, orient=tk.VERTICAL, command=self.overview_tree.yview)
        scroll_x = ttk.Scrollbar(conflicts_frame, orient=tk.HORIZONTAL, command=self.overview_tree.xview)
        self.overview_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.overview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 双击查看详情
        self.overview_tree.bind('<Double-1>', self.on_conflict_double_click)

    def create_conflicts_tab(self):
        """创建冲突详情标签页"""
        conflicts_frame = ttk.Frame(self.notebook)
        self.notebook.add(conflicts_frame, text="冲突详情")

        # 冲突详细列表
        columns = ('热键组合', '应用程序', '类型', '描述', '进程ID', '检测时间')
        self.detailed_conflicts_tree = ttk.Treeview(
            conflicts_frame, 
            columns=columns, 
            show='headings'
        )

        for col in columns:
            self.detailed_conflicts_tree.heading(col, text=col)
            self.detailed_conflicts_tree.column(col, width=120)

        # 滚动条
        scroll_y = ttk.Scrollbar(conflicts_frame, orient=tk.VERTICAL, command=self.detailed_conflicts_tree.yview)
        scroll_x = ttk.Scrollbar(conflicts_frame, orient=tk.HORIZONTAL, command=self.detailed_conflicts_tree.xview)
        self.detailed_conflicts_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.detailed_conflicts_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def create_hotkeys_tab(self):
        """创建热键列表标签页"""
        hotkeys_frame = ttk.Frame(self.notebook)
        self.notebook.add(hotkeys_frame, text="所有热键")

        # 搜索和过滤框架
        search_frame = ttk.Frame(hotkeys_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)

        ttk.Button(search_frame, text="搜索", command=self.search_hotkeys).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="清除", command=self.clear_search).pack(side=tk.LEFT)

        # 热键列表
        columns = ('热键组合', '应用程序', '类型', '描述', '进程ID', '检测时间')
        self.hotkeys_tree = ttk.Treeview(
            hotkeys_frame, 
            columns=columns, 
            show='headings'
        )

        for col in columns:
            self.hotkeys_tree.heading(col, text=col)
            self.hotkeys_tree.column(col, width=120)

        # 滚动条
        scroll_y = ttk.Scrollbar(hotkeys_frame, orient=tk.VERTICAL, command=self.hotkeys_tree.yview)
        scroll_x = ttk.Scrollbar(hotkeys_frame, orient=tk.HORIZONTAL, command=self.hotkeys_tree.xview)
        self.hotkeys_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.hotkeys_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def create_reports_tab(self):
        """创建报告标签页"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="报告")

        # 报告操作框架
        report_controls = ttk.Frame(reports_frame)
        report_controls.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(report_controls, text="生成报告", command=self.generate_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(report_controls, text="刷新列表", command=self.refresh_report_list).pack(side=tk.LEFT, padx=(0, 5))

        # 报告格式选择
        format_frame = ttk.Frame(report_controls)
        format_frame.pack(side=tk.RIGHT)

        ttk.Label(format_frame, text="格式:").pack(side=tk.LEFT, padx=(0, 5))
        self.report_format = tk.StringVar(value='json')
        format_combo = ttk.Combobox(format_frame, textvariable=self.report_format, 
                                   values=['json', 'csv', 'txt'], state='readonly', width=8)
        format_combo.pack(side=tk.LEFT)

        # 报告列表
        columns = ('文件名', '大小', '生成时间', '格式')
        self.reports_tree = ttk.Treeview(
            reports_frame, 
            columns=columns, 
            show='headings',
            height=10
        )

        for col in columns:
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=100)

        # 滚动条
        scroll_y = ttk.Scrollbar(reports_frame, orient=tk.VERTICAL, command=self.reports_tree.yview)
        self.reports_tree.configure(yscrollcommand=scroll_y.set)

        self.reports_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 报告操作按钮
        report_buttons = ttk.Frame(reports_frame)
        report_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        ttk.Button(report_buttons, text="查看", command=self.view_report, width=10).pack(fill=tk.X, pady=2)
        ttk.Button(report_buttons, text="导出", command=self.export_selected_report, width=10).pack(fill=tk.X, pady=2)
        ttk.Button(report_buttons, text="删除", command=self.delete_report, width=10).pack(fill=tk.X, pady=2)

    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="日志")

        # 日志文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 9))
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 日志控制按钮
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        ttk.Button(log_controls, text="清空", command=self.clear_log, width=8).pack(fill=tk.X, pady=2)
        ttk.Button(log_controls, text="保存", command=self.save_log, width=8).pack(fill=tk.X, pady=2)

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出报告...", command=self.export_report)
        file_menu.add_command(label="导入配置...", command=self.import_config)
        file_menu.add_command(label="导出配置...", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 扫描菜单
        scan_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="扫描", menu=scan_menu)
        scan_menu.add_command(label="开始扫描", command=self.start_scan)
        scan_menu.add_command(label="停止扫描", command=self.stop_scan)
        scan_menu.add_separator()
        scan_menu.add_command(label="分析冲突", command=self.analyze_conflicts)
        scan_menu.add_command(label="刷新数据", command=self.refresh_data)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="用户热键管理", command=self.show_user_hotkeys_dialog)
        tools_menu.add_command(label="配置设置", command=self.show_settings_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="清理旧报告", command=self.cleanup_old_reports)
        tools_menu.add_command(label="查看统计", command=self.show_statistics)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="使用说明", command=self.show_help)

    def setup_logging(self):
        """设置日志系统"""
        # 创建自定义日志处理器
        self.log_handler = LogHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)

        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)

    def load_initial_data(self):
        """加载初始数据"""
        self.refresh_report_list()
        self._log("应用程序已启动")

    # 主要功能方法
    def start_scan(self):
        """开始扫描热键"""
        if self.is_scanning:
            return

        self.is_scanning = True
        self.scan_button.config(state='disabled', text="扫描中...")
        self.analyze_button.config(state='disabled')
        self.export_button.config(state='disabled')
        self.progress.start()
        self.update_status("正在扫描热键...")

        # 在后台线程中执行扫描
        scan_thread = threading.Thread(target=self._scan_hotkeys)
        scan_thread.daemon = True
        scan_thread.start()

    def _scan_hotkeys(self):
        """在后台线程中扫描热键"""
        try:
            self._log("开始扫描热键...")

            def progress_callback(current, total, description):
                self.root.after(0, self._update_progress, current, total, description)

            # 执行扫描
            hotkeys = self.detector.scan_hotkeys(progress_callback)
            
            # 更新UI（在主线程中）
            self.root.after(0, self._scan_completed, hotkeys)

        except Exception as e:
            self._log(f"扫描过程中出错: {e}")
            self.root.after(0, self._scan_failed, str(e))

    def _scan_completed(self, hotkeys):
        """扫描完成后的处理"""
        self.detected_hotkeys = hotkeys
        self.is_scanning = False
        
        self.scan_button.config(state='normal', text="开始扫描")
        self.analyze_button.config(state='normal')
        self.progress.stop()
        self.update_status("扫描完成")

        # 更新统计信息
        self.update_statistics()
        
        self._log(f"热键扫描完成，共检测到 {len(hotkeys)} 个热键")

    def _scan_failed(self, error_msg):
        """扫描失败后的处理"""
        self.is_scanning = False
        self.scan_button.config(state='normal', text="开始扫描")
        self.progress.stop()
        self.update_status("扫描失败")
        
        messagebox.showerror("扫描错误", f"热键扫描失败: {error_msg}")

    def _update_progress(self, current, total, description):
        """更新进度显示"""
        self.update_status(f"{description} ({current}/{total})")

    def analyze_conflicts(self):
        """分析冲突"""
        if not self.detected_hotkeys:
            messagebox.showwarning("警告", "请先扫描热键")
            return

        self.update_status("正在分析冲突...")
        self.progress.start()

        # 在后台线程中分析冲突
        analyze_thread = threading.Thread(target=self._analyze_conflicts_thread)
        analyze_thread.daemon = True
        analyze_thread.start()

    def _analyze_conflicts_thread(self):
        """在后台线程中分析冲突"""
        try:
            report = self.detector.analyze_conflicts()
            
            # 更新UI（在主线程中）
            self.root.after(0, self._analysis_completed, report)

        except Exception as e:
            self.root.after(0, self._analysis_failed, str(e))

    def _analysis_completed(self, report):
        """分析完成后的处理"""
        self.conflict_report = report
        self.progress.stop()
        self.update_status("分析完成")
        self.export_button.config(state='normal')

        # 更新界面数据
        self.update_conflict_display()
        
        self._log(f"冲突分析完成，发现 {report.total_conflicts} 个冲突")

    def _analysis_failed(self, error_msg):
        """分析失败后的处理"""
        self.progress.stop()
        self.update_status("分析失败")
        
        messagebox.showerror("分析错误", f"冲突分析失败: {error_msg}")

    def export_report(self):
        """导出报告"""
        if not self.conflict_report:
            messagebox.showwarning("警告", "请先分析冲突")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[
                    ("JSON文件", "*.json"),
                    ("CSV文件", "*.csv"), 
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ],
                title="导出冲突报告"
            )

            if filename:
                # 根据文件扩展名确定格式
                file_ext = Path(filename).suffix.lower()[1:]
                if file_ext not in ['json', 'csv', 'txt']:
                    file_ext = 'json'  # 默认格式

                # 导出报告
                results = self.detector.export_report(
                    report=self.conflict_report,
                    formats=[file_ext],
                    custom_filename=Path(filename).stem
                )

                if results and results.get(file_ext):
                    messagebox.showinfo("导出成功", f"报告已保存到: {results[file_ext]}")
                    self._log(f"报告已导出: {results[file_ext]}")
                else:
                    messagebox.showerror("导出失败", "报告导出失败")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出报告时出错: {e}")

    # 界面更新方法
    def update_statistics(self):
        """更新统计信息"""
        total_count = len(self.detected_hotkeys)
        system_count = sum(1 for h in self.detected_hotkeys if h.source_type == 'system')
        app_count = sum(1 for h in self.detected_hotkeys if h.source_type in ['application', 'known_software'])

        self.total_hotkeys_label.config(text=str(total_count))
        self.system_hotkeys_label.config(text=str(system_count))
        self.app_hotkeys_label.config(text=str(app_count))

        # 更新冲突统计
        if self.conflict_report:
            self.conflicts_label.config(text=str(self.conflict_report.total_conflicts))
            
            # 更新严重程度统计
            for severity_key, label in self.severity_labels.items():
                count = self.conflict_report.severity_breakdown.get(severity_key, 0)
                label.config(text=str(count))
        else:
            self.conflicts_label.config(text="0")
            for label in self.severity_labels.values():
                label.config(text="0")

    def update_conflict_display(self):
        """更新冲突显示"""
        if not self.conflict_report:
            return

        # 清空现有数据
        for tree in [self.overview_tree, self.detailed_conflicts_tree]:
            for item in tree.get_children():
                tree.delete(item)

        # 填充概览冲突列表
        for conflict_group in self.conflict_report.conflict_groups:
            apps = ', '.join(set(h.source_name for h in conflict_group.hotkeys))
            suggestions = conflict_group.resolution_suggestions[0] if conflict_group.resolution_suggestions else ""

            self.overview_tree.insert('', 'end', values=(
                conflict_group.key_combination,
                apps,
                conflict_group.conflict_type,
                conflict_group.severity,
                suggestions
            ))

        # 填充详细冲突列表
        for conflict_group in self.conflict_report.conflict_groups:
            for hotkey in conflict_group.hotkeys:
                self.detailed_conflicts_tree.insert('', 'end', values=(
                    hotkey.key_combination,
                    hotkey.source_name,
                    hotkey.source_type,
                    hotkey.description,
                    hotkey.process_id or "",
                    hotkey.detected_time.strftime("%Y-%m-%d %H:%M:%S")
                ))

        # 填充热键列表
        self.populate_hotkeys_tree()

    def populate_hotkeys_tree(self):
        """填充热键列表"""
        # 清空现有项目
        for item in self.hotkeys_tree.get_children():
            self.hotkeys_tree.delete(item)

        # 添加所有热键
        for hotkey in self.detected_hotkeys:
            self.hotkeys_tree.insert('', 'end', values=(
                hotkey.key_combination,
                hotkey.source_name,
                hotkey.source_type,
                hotkey.description,
                hotkey.process_id or "",
                hotkey.detected_time.strftime("%Y-%m-%d %H:%M:%S")
            ))

    # 其他功能方法
    def show_user_hotkeys_dialog(self):
        """显示用户热键管理对话框"""
        dialog = UserHotkeysDialog(self.root, self.user_manager)
        self.root.wait_window(dialog.dialog)
        self._log("用户热键管理对话框已关闭")

    def show_settings_dialog(self):
        """显示配置设置对话框"""
        dialog = SettingsDialog(self.root, self.config_manager, self.app_config)
        if dialog.result:
            self.app_config = dialog.result
            self.detector.update_config(self.app_config)
            self._log("配置已更新")

    def refresh_report_list(self):
        """刷新报告列表"""
        try:
            # 清空现有项目
            for item in self.reports_tree.get_children():
                self.reports_tree.delete(item)

            # 获取报告列表
            report_list = self.detector.get_report_list()
            
            for report in report_list:
                self.reports_tree.insert('', 'end', values=(
                    report['filename'],
                    report['size'],
                    report['created_time'],
                    report['format']
                ))

        except Exception as e:
            self._log(f"刷新报告列表失败: {e}")

    def search_hotkeys(self):
        """搜索热键"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            return

        try:
            results = self.detector.search_hotkeys(keyword, "all")
            
            # 清空现有项目
            for item in self.hotkeys_tree.get_children():
                self.hotkeys_tree.delete(item)

            # 显示搜索结果
            for hotkey in results:
                self.hotkeys_tree.insert('', 'end', values=(
                    hotkey.key_combination,
                    hotkey.source_name,
                    hotkey.source_type,
                    hotkey.description,
                    hotkey.process_id or "",
                    hotkey.detected_time.strftime("%Y-%m-%d %H:%M:%S")
                ))

            self._log(f"搜索 '{keyword}' 找到 {len(results)} 个结果")

        except Exception as e:
            self._log(f"搜索热键失败: {e}")

    def clear_search(self):
        """清除搜索"""
        self.search_entry.delete(0, tk.END)
        self.populate_hotkeys_tree()

    def on_search_changed(self, event):
        """搜索内容改变时的处理"""
        # 可以在这里实现实时搜索
        pass

    def on_conflict_double_click(self, event):
        """冲突项双击事件"""
        selection = self.overview_tree.selection()
        if selection:
            item = selection[0]
            values = self.overview_tree.item(item, 'values')
            if values:
                messagebox.showinfo(
                    "冲突详情", 
                    f"热键: {values[0]}\n"
                    f"冲突应用: {values[1]}\n"
                    f"类型: {values[2]}\n"
                    f"严重程度: {values[3]}\n"
                    f"建议: {values[4]}"
                )

    def generate_report(self):
        """生成报告"""
        if not self.conflict_report:
            messagebox.showwarning("警告", "请先分析冲突")
            return

        try:
            format_type = self.report_format.get()
            results = self.detector.export_report(formats=[format_type])
            
            if results and results.get(format_type):
                self._log(f"报告已生成: {results[format_type]}")
                self.refresh_report_list()
                messagebox.showinfo("成功", "报告生成完成")
            else:
                messagebox.showerror("失败", "报告生成失败")

        except Exception as e:
            messagebox.showerror("错误", f"生成报告失败: {e}")

    def view_report(self):
        """查看选中的报告"""
        selection = self.reports_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个报告")
            return

        item = selection[0]
        filename = self.reports_tree.item(item, 'values')[0]
        
        try:
            # 这里可以打开报告文件查看内容
            report_path = self.reports_dir / filename
            if report_path.exists():
                # 简单的文本查看
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 显示报告内容
                self.show_text_dialog(f"报告内容 - {filename}", content)
            else:
                messagebox.showerror("错误", "报告文件不存在")

        except Exception as e:
            messagebox.showerror("错误", f"查看报告失败: {e}")

    def export_selected_report(self):
        """导出选中的报告"""
        selection = self.reports_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个报告")
            return

        item = selection[0]
        filename = self.reports_tree.item(item, 'values')[0]
        
        try:
            source_path = self.reports_dir / filename
            if not source_path.exists():
                messagebox.showerror("错误", "报告文件不存在")
                return

            dest_path = filedialog.asksaveasfilename(
                initialfile=filename,
                title="导出报告文件"
            )

            if dest_path:
                import shutil
                shutil.copy2(source_path, dest_path)
                messagebox.showinfo("成功", f"报告已导出到: {dest_path}")
                self._log(f"报告已导出: {dest_path}")

        except Exception as e:
            messagebox.showerror("错误", f"导出报告失败: {e}")

    def delete_report(self):
        """删除选中的报告"""
        selection = self.reports_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个报告")
            return

        item = selection[0]
        filename = self.reports_tree.item(item, 'values')[0]
        
        if messagebox.askyesno("确认删除", f"确定要删除报告 '{filename}' 吗？"):
            try:
                if self.detector.delete_report(filename):
                    self.refresh_report_list()
                    self._log(f"报告已删除: {filename}")
                else:
                    messagebox.showerror("错误", "删除报告失败")

            except Exception as e:
                messagebox.showerror("错误", f"删除报告失败: {e}")

    def cleanup_old_reports(self):
        """清理旧报告"""
        try:
            count = self.report_exporter.cleanup_old_reports(self.app_config.max_report_count)
            self.refresh_report_list()
            messagebox.showinfo("成功", f"已清理 {count} 个旧报告")
            self._log(f"已清理 {count} 个旧报告")

        except Exception as e:
            messagebox.showerror("错误", f"清理报告失败: {e}")

    def show_recent_reports(self):
        """显示最近报告"""
        self.notebook.select(3)  # 切换到报告标签页

    def add_user_hotkey(self):
        """添加用户热键"""
        dialog = AddHotkeyDialog(self.root, self.user_manager)
        if dialog.result:
            self._log("用户热键已添加")

    def refresh_data(self):
        """刷新数据"""
        if not self.is_scanning:
            self.start_scan()

    def stop_scan(self):
        """停止扫描"""
        self.is_scanning = False
        self._scan_completed(self.detected_hotkeys)

    def import_config(self):
        """导入配置"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("INI文件", "*.ini"), ("所有文件", "*.*")],
                title="选择配置文件"
            )

            if filename:
                # 这里可以实现配置导入逻辑
                messagebox.showinfo("提示", "配置导入功能待实现")

        except Exception as e:
            messagebox.showerror("错误", f"导入配置失败: {e}")

    def export_config(self):
        """导出配置"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".ini",
                filetypes=[("INI文件", "*.ini"), ("所有文件", "*.*")],
                title="导出配置文件"
            )

            if filename:
                # 这里可以实现配置导出逻辑
                messagebox.showinfo("提示", "配置导出功能待实现")

        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败: {e}")

    def show_statistics(self):
        """显示统计信息"""
        if not self.conflict_report:
            messagebox.showwarning("警告", "请先分析冲突")
            return

        stats = self.conflict_report.hotkey_statistics
        stats_text = f"热键统计信息:\n\n"
        stats_text += f"总热键数: {stats.get('total_count', 0)}\n"
        stats_text += f"热键密度: {stats.get('hotkey_density', 0):.2%}\n\n"

        stats_text += "按类型分布:\n"
        for type_name, count in stats.get('by_source_type', {}).items():
            stats_text += f"  {type_name}: {count}\n"

        stats_text += "\n按严重程度分布:\n"
        for severity, count in stats.get('by_severity', {}).items():
            stats_text += f"  {severity}: {count}\n"

        self.show_text_dialog("统计信息", stats_text)

    def show_text_dialog(self, title, content):
        """显示文本对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # 文本区域
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.insert('1.0', content)
        text_widget.config(state='disabled')

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 关闭按钮
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', tk.END)

    def save_log(self):
        """保存日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存日志"
            )

            if filename:
                content = self.log_text.get('1.0', tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已保存到: {filename}")

        except Exception as e:
            messagebox.showerror("错误", f"保存日志失败: {e}")

    def show_about(self):
        """显示关于对话框"""
        about_text = """热键冲突检测器 v2.0

功能特点:
• 智能热键冲突分析
• 多维度评分系统
• 用户热键管理
• 多格式报告导出
• 现代化配置管理

技术栈:
• Python + tkinter
• Windows API
• 模块化架构

开发团队: Claude Code Assistant
版本: 2.0.0
发布日期: 2024年11月"""

        messagebox.showinfo("关于", about_text)

    def show_help(self):
        """显示帮助信息"""
        help_text = """使用说明:

1. 扫描热键
   - 点击"开始扫描"按钮扫描系统中的热键
   - 扫描过程可能需要几分钟时间

2. 分析冲突
   - 扫描完成后点击"分析冲突"按钮
   - 系统会自动识别并分类热键冲突

3. 查看结果
   - 在"概览"标签页查看冲突概览
   - 在"冲突详情"标签页查看详细信息
   - 在"所有热键"标签页查看所有检测到的热键

4. 管理用户热键
   - 点击"用户热键管理"添加自定义热键
   - 用户热键会参与冲突分析

5. 导出报告
   - 支持JSON、CSV、TXT三种格式
   - 可选择导出单个报告或批量导出

6. 配置设置
   - 点击"设置"按钮调整应用程序行为
   - 可配置扫描选项、警报设置等"""

        self.show_text_dialog("使用说明", help_text)

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)

    def _log(self, message):
        """添加日志消息"""
        logging.info(message)

    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        finally:
            self.detector.close()


class LogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到tkinter Text组件"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
        except:
            self.handleError(record)


class UserHotkeysDialog:
    """用户热键管理对话框"""

    def __init__(self, parent, user_manager):
        self.user_manager = user_manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("用户热键管理")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.load_user_hotkeys()

    def create_widgets(self):
        """创建对话框组件"""
        # 工具栏
        toolbar = ttk.Frame(self.dialog)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(toolbar, text="添加", command=self.add_hotkey).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="编辑", command=self.edit_hotkey).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="删除", command=self.delete_hotkey).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="刷新", command=self.load_user_hotkeys).pack(side=tk.LEFT)

        # 热键列表
        list_frame = ttk.Frame(self.dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ('热键组合', '应用程序', '描述')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 关闭按钮
        ttk.Button(self.dialog, text="关闭", command=self.dialog.destroy).pack(pady=10)

    def load_user_hotkeys(self):
        """加载用户热键"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 加载用户热键
        hotkeys = self.user_manager.get_user_hotkeys()
        for hotkey in hotkeys:
            self.tree.insert('', 'end', values=(
                hotkey.key_combination,
                hotkey.source_name,
                hotkey.description
            ))

    def add_hotkey(self):
        """添加热键"""
        dialog = AddHotkeyDialog(self.dialog, self.user_manager)
        if dialog.result:
            self.load_user_hotkeys()

    def edit_hotkey(self):
        """编辑热键"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个热键")
            return

        # 这里可以实现编辑功能
        messagebox.showinfo("提示", "编辑功能待实现")

    def delete_hotkey(self):
        """删除热键"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个热键")
            return

        item = selection[0]
        values = self.tree.item(item, 'values')
        key_combination = values[0]

        if messagebox.askyesno("确认删除", f"确定要删除热键 '{key_combination}' 吗？"):
            success, message = self.user_manager.remove_user_hotkey(key_combination)
            if success:
                self.load_user_hotkeys()
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)


class AddHotkeyDialog:
    """添加用户热键对话框"""

    def __init__(self, parent, user_manager):
        self.user_manager = user_manager
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("添加用户热键")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()

    def create_widgets(self):
        """创建对话框组件"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 热键组合
        ttk.Label(main_frame, text="热键组合:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.combo_entry = ttk.Entry(main_frame, width=30)
        self.combo_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5, 0))

        # 应用程序名称
        ttk.Label(main_frame, text="应用程序:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.app_entry = ttk.Entry(main_frame, width=30)
        self.app_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(5, 0))

        # 描述
        ttk.Label(main_frame, text="描述:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(main_frame, width=30)
        self.desc_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=(5, 0))

        # 示例文本
        example_frame = ttk.LabelFrame(main_frame, text="示例", padding=10)
        example_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        example_text = """常用热键格式:
• Ctrl+C
• Alt+Tab  
• Win+L
• Ctrl+Shift+Esc
• F1
• Ctrl+Alt+Delete"""

        example_label = ttk.Label(example_frame, text=example_text, justify=tk.LEFT)
        example_label.pack(anchor=tk.W)

        # 验证信息
        self.validation_label = ttk.Label(main_frame, text="", foreground="red")
        self.validation_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="添加", command=self.add_hotkey).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 绑定事件
        self.combo_entry.bind('<KeyRelease>', self.validate_hotkey)

    def validate_hotkey(self, event=None):
        """验证热键格式"""
        combination = self.combo_entry.get().strip()
        if not combination:
            self.validation_label.config(text="")
            return

        try:
            # 使用主检测器验证热键格式
            success, message = self.user_manager.validate_hotkey_combination(combination)
            if success:
                self.validation_label.config(text="✓ 热键格式正确", foreground="green")
            else:
                self.validation_label.config(text=f"✗ {message}", foreground="red")
        except Exception as e:
            self.validation_label.config(text=f"验证错误: {e}", foreground="red")

    def add_hotkey(self):
        """添加热键"""
        combination = self.combo_entry.get().strip()
        app_name = self.app_entry.get().strip()
        description = self.desc_entry.get().strip()

        if not combination:
            messagebox.showwarning("警告", "请输入热键组合")
            return

        if not app_name:
            app_name = "用户定义"

        # 创建热键对象
        hotkey = HotkeyInfo(
            key_combination=combination,
            source_type='user_defined',
            source_name=app_name,
            description=description
        )

        # 添加热键
        success, message = self.user_manager.add_user_hotkey(hotkey)
        if success:
            self.result = hotkey
            messagebox.showinfo("成功", message)
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", message)


class SettingsDialog:
    """配置设置对话框"""

    def __init__(self, parent, config_manager, app_config):
        self.config_manager = config_manager
        self.app_config = app_config
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("配置设置")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.load_current_settings()

    def create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 使用Notebook组织设置分类
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建各个设置标签页
        self.create_general_tab()
        self.create_detection_tab()
        self.create_alerts_tab()
        self.create_export_tab()
        self.create_advanced_tab()

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="保存", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="恢复默认", command=self.reset_defaults).pack(side=tk.RIGHT)

    def create_general_tab(self):
        """创建常规设置标签页"""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="常规")

        # 自动启动监控
        self.auto_start_var = tk.BooleanVar()
        auto_start_check = ttk.Checkbutton(
            general_frame, 
            text="自动启动热键监控",
            variable=self.auto_start_var
        )
        auto_start_check.grid(row=0, column=0, sticky=tk.W, pady=5)

        # 检查间隔
        ttk.Label(general_frame, text="检查间隔 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.interval_var = tk.StringVar()
        interval_spin = ttk.Spinbox(
            general_frame, 
            from_=1, to=60, 
            textvariable=self.interval_var,
            width=10
        )
        interval_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 语言设置
        ttk.Label(general_frame, text="语言:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.language_var = tk.StringVar()
        language_combo = ttk.Combobox(
            general_frame,
            textvariable=self.language_var,
            values=['zh_CN', 'en_US'],
            state='readonly',
            width=10
        )
        language_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 主题设置
        ttk.Label(general_frame, text="主题:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(
            general_frame,
            textvariable=self.theme_var,
            values=['light', 'dark', 'system'],
            state='readonly',
            width=10
        )
        theme_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 窗口设置
        ttk.Label(general_frame, text="窗口设置:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.minimize_to_tray_var = tk.BooleanVar()
        minimize_check = ttk.Checkbutton(
            general_frame,
            text="最小化到系统托盘",
            variable=self.minimize_to_tray_var
        )
        minimize_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.start_minimized_var = tk.BooleanVar()
        start_minimized_check = ttk.Checkbutton(
            general_frame,
            text="启动时最小化",
            variable=self.start_minimized_var
        )
        start_minimized_check.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=2)

    def create_detection_tab(self):
        """创建检测设置标签页"""
        detection_frame = ttk.Frame(self.notebook)
        self.notebook.add(detection_frame, text="检测")

        # 扫描选项
        ttk.Label(detection_frame, text="扫描选项:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.scan_system_var = tk.BooleanVar()
        system_check = ttk.Checkbutton(
            detection_frame,
            text="扫描系统热键",
            variable=self.scan_system_var
        )
        system_check.grid(row=1, column=0, sticky=tk.W, pady=2)

        self.scan_app_var = tk.BooleanVar()
        app_check = ttk.Checkbutton(
            detection_frame,
            text="扫描应用程序热键",
            variable=self.scan_app_var
        )
        app_check.grid(row=2, column=0, sticky=tk.W, pady=2)

        self.scan_known_var = tk.BooleanVar()
        known_check = ttk.Checkbutton(
            detection_frame,
            text="扫描已知软件热键",
            variable=self.scan_known_var
        )
        known_check.grid(row=3, column=0, sticky=tk.W, pady=2)

        self.include_user_var = tk.BooleanVar()
        user_check = ttk.Checkbutton(
            detection_frame,
            text="包含用户自定义热键",
            variable=self.include_user_var
        )
        user_check.grid(row=4, column=0, sticky=tk.W, pady=2)

        self.scan_registry_var = tk.BooleanVar()
        registry_check = ttk.Checkbutton(
            detection_frame,
            text="扫描注册表热键",
            variable=self.scan_registry_var
        )
        registry_check.grid(row=5, column=0, sticky=tk.W, pady=2)

        self.scan_window_var = tk.BooleanVar()
        window_check = ttk.Checkbutton(
            detection_frame,
            text="扫描活动窗口热键",
            variable=self.scan_window_var
        )
        window_check.grid(row=6, column=0, sticky=tk.W, pady=2)

        # 高级扫描选项
        ttk.Label(detection_frame, text="高级选项:").grid(row=7, column=0, sticky=tk.W, pady=(10, 5))

        self.deep_scan_var = tk.BooleanVar()
        deep_scan_check = ttk.Checkbutton(
            detection_frame,
            text="深度扫描模式",
            variable=self.deep_scan_var
        )
        deep_scan_check.grid(row=8, column=0, sticky=tk.W, pady=2)

        # 排除进程
        ttk.Label(detection_frame, text="排除进程 (逗号分隔):").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.exclude_processes_var = tk.StringVar()
        exclude_entry = ttk.Entry(
            detection_frame,
            textvariable=self.exclude_processes_var,
            width=30
        )
        exclude_entry.grid(row=10, column=0, sticky=tk.W+tk.E, pady=2)

    def create_alerts_tab(self):
        """创建警报设置标签页"""
        alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(alerts_frame, text="警报")

        # 警报级别
        ttk.Label(alerts_frame, text="显示警报级别:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.show_critical_var = tk.BooleanVar()
        critical_check = ttk.Checkbutton(
            alerts_frame,
            text="严重",
            variable=self.show_critical_var
        )
        critical_check.grid(row=1, column=0, sticky=tk.W, pady=2)

        self.show_high_var = tk.BooleanVar()
        high_check = ttk.Checkbutton(
            alerts_frame,
            text="高",
            variable=self.show_high_var
        )
        high_check.grid(row=2, column=0, sticky=tk.W, pady=2)

        self.show_medium_var = tk.BooleanVar()
        medium_check = ttk.Checkbutton(
            alerts_frame,
            text="中",
            variable=self.show_medium_var
        )
        medium_check.grid(row=3, column=0, sticky=tk.W, pady=2)

        self.show_low_var = tk.BooleanVar()
        low_check = ttk.Checkbutton(
            alerts_frame,
            text="低",
            variable=self.show_low_var
        )
        low_check.grid(row=4, column=0, sticky=tk.W, pady=2)

        # 警报方式
        ttk.Label(alerts_frame, text="警报方式:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))

        self.alert_sound_var = tk.BooleanVar()
        sound_check = ttk.Checkbutton(
            alerts_frame,
            text="播放声音",
            variable=self.alert_sound_var
        )
        sound_check.grid(row=6, column=0, sticky=tk.W, pady=2)

        self.popup_notifications_var = tk.BooleanVar()
        popup_check = ttk.Checkbutton(
            alerts_frame,
            text="弹出通知",
            variable=self.popup_notifications_var
        )
        popup_check.grid(row=7, column=0, sticky=tk.W, pady=2)

        self.log_alerts_var = tk.BooleanVar()
        log_check = ttk.Checkbutton(
            alerts_frame,
            text="记录到日志",
            variable=self.log_alerts_var
        )
        log_check.grid(row=8, column=0, sticky=tk.W, pady=2)

    def create_export_tab(self):
        """创建导出设置标签页"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="导出")

        # 默认格式
        ttk.Label(export_frame, text="默认导出格式:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.default_format_var = tk.StringVar()
        format_combo = ttk.Combobox(
            export_frame,
            textvariable=self.default_format_var,
            values=['json', 'csv', 'txt'],
            state='readonly',
            width=10
        )
        format_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 报告内容
        ttk.Label(export_frame, text="报告内容:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.include_timestamps_var = tk.BooleanVar()
        timestamps_check = ttk.Checkbutton(
            export_frame,
            text="包含时间戳",
            variable=self.include_timestamps_var
        )
        timestamps_check.grid(row=2, column=0, sticky=tk.W, pady=2)

        self.include_suggestions_var = tk.BooleanVar()
        suggestions_check = ttk.Checkbutton(
            export_frame,
            text="包含解决建议",
            variable=self.include_suggestions_var
        )
        suggestions_check.grid(row=3, column=0, sticky=tk.W, pady=2)

        self.include_statistics_var = tk.BooleanVar()
        statistics_check = ttk.Checkbutton(
            export_frame,
            text="包含统计信息",
            variable=self.include_statistics_var
        )
        statistics_check.grid(row=4, column=0, sticky=tk.W, pady=2)

        # 报告管理
        ttk.Label(export_frame, text="报告管理:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))

        self.auto_cleanup_var = tk.BooleanVar()
        cleanup_check = ttk.Checkbutton(
            export_frame,
            text="自动清理旧报告",
            variable=self.auto_cleanup_var
        )
        cleanup_check.grid(row=6, column=0, sticky=tk.W, pady=2)

        ttk.Label(export_frame, text="最大报告数量:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.max_reports_var = tk.StringVar()
        max_reports_spin = ttk.Spinbox(
            export_frame,
            from_=1, to=100,
            textvariable=self.max_reports_var,
            width=10
        )
        max_reports_spin.grid(row=7, column=1, sticky=tk.W, pady=5, padx=(5, 0))

    def create_advanced_tab(self):
        """创建高级设置标签页"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="高级")

        # 日志设置
        ttk.Label(advanced_frame, text="日志级别:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.log_level_var = tk.StringVar()
        log_level_combo = ttk.Combobox(
            advanced_frame,
            textvariable=self.log_level_var,
            values=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            state='readonly',
            width=10
        )
        log_level_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        ttk.Label(advanced_frame, text="最大日志文件数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_log_files_var = tk.StringVar()
        max_log_spin = ttk.Spinbox(
            advanced_frame,
            from_=1, to=50,
            textvariable=self.max_log_files_var,
            width=10
        )
        max_log_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 扫描设置
        ttk.Label(advanced_frame, text="扫描超时 (秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.scan_timeout_var = tk.StringVar()
        timeout_spin = ttk.Spinbox(
            advanced_frame,
            from_=10, to=300,
            textvariable=self.scan_timeout_var,
            width=10
        )
        timeout_spin.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        ttk.Label(advanced_frame, text="进程扫描限制:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.process_limit_var = tk.StringVar()
        process_spin = ttk.Spinbox(
            advanced_frame,
            from_=10, to=5000,
            textvariable=self.process_limit_var,
            width=10
        )
        process_spin.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 实时监控
        ttk.Label(advanced_frame, text="实时监控:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))

        self.enable_monitoring_var = tk.BooleanVar()
        monitoring_check = ttk.Checkbutton(
            advanced_frame,
            text="启用热键实时监控",
            variable=self.enable_monitoring_var
        )
        monitoring_check.grid(row=5, column=0, sticky=tk.W, pady=2)

        ttk.Label(advanced_frame, text="监控间隔 (秒):").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.monitoring_interval_var = tk.StringVar()
        monitoring_spin = ttk.Spinbox(
            advanced_frame,
            from_=1, to=60,
            textvariable=self.monitoring_interval_var,
            width=10
        )
        monitoring_spin.grid(row=6, column=1, sticky=tk.W, pady=5, padx=(5, 0))

    def load_current_settings(self):
        """加载当前设置"""
        # 常规设置
        self.auto_start_var.set(self.app_config.auto_start_monitoring)
        self.interval_var.set(str(self.app_config.check_interval))
        self.language_var.set(self.app_config.language)
        self.theme_var.set(self.app_config.theme)

        # 检测设置
        self.scan_system_var.set(self.app_config.scan_system_hotkeys)
        self.scan_app_var.set(self.app_config.scan_application_hotkeys)
        self.scan_known_var.set(self.app_config.scan_known_software)
        self.include_user_var.set(self.app_config.include_user_defined)

        # 警报设置
        self.show_critical_var.set(self.app_config.show_critical_alerts)
        self.show_high_var.set(self.app_config.show_high_alerts)
        self.show_medium_var.set(self.app_config.show_medium_alerts)
        self.show_low_var.set(self.app_config.show_low_alerts)

        # 导出设置
        self.default_format_var.set(self.app_config.default_export_format)
        self.include_timestamps_var.set(self.app_config.include_timestamps)
        self.include_suggestions_var.set(self.app_config.include_suggestions)
        self.auto_cleanup_var.set(self.app_config.auto_cleanup_reports)
        self.max_reports_var.set(str(self.app_config.max_report_count))

        # 高级设置从配置管理器获取
        self.log_level_var.set(self.config_manager.get_config('Advanced', 'logging_level', 'INFO'))
        self.max_log_files_var.set(self.config_manager.get_config('Advanced', 'max_log_files', '10'))
        self.scan_timeout_var.set(self.config_manager.get_config('Advanced', 'scan_timeout', '30'))
        self.process_limit_var.set(self.config_manager.get_config('Advanced', 'process_scan_limit', '1000'))
        self.enable_monitoring_var.set(self.config_manager.get_config('Advanced', 'enable_hotkey_monitoring', 'false').lower() == 'true')
        self.monitoring_interval_var.set(self.config_manager.get_config('Advanced', 'monitoring_interval', '10'))

        # 其他设置
        self.minimize_to_tray_var.set(self.config_manager.get_config('General', 'minimize_to_tray', 'false').lower() == 'true')
        self.start_minimized_var.set(self.config_manager.get_config('General', 'start_minimized', 'false').lower() == 'true')
        self.scan_registry_var.set(self.config_manager.get_config('Detection', 'scan_registry_hotkeys', 'false').lower() == 'true')
        self.scan_window_var.set(self.config_manager.get_config('Detection', 'scan_active_window', 'true').lower() == 'true')
        self.deep_scan_var.set(self.config_manager.get_config('Detection', 'deep_scan_mode', 'false').lower() == 'true')
        self.exclude_processes_var.set(self.config_manager.get_config('Detection', 'exclude_processes', ''))
        self.alert_sound_var.set(self.config_manager.get_config('Alerts', 'alert_sound', 'true').lower() == 'true')
        self.popup_notifications_var.set(self.config_manager.get_config('Alerts', 'popup_notifications', 'true').lower() == 'true')
        self.log_alerts_var.set(self.config_manager.get_config('Alerts', 'log_alerts', 'true').lower() == 'true')
        self.include_statistics_var.set(self.config_manager.get_config('Export', 'include_statistics', 'true').lower() == 'true')

    def save_settings(self):
        """保存设置"""
        try:
            # 更新应用配置对象
            self.app_config.auto_start_monitoring = self.auto_start_var.get()
            self.app_config.check_interval = int(self.interval_var.get())
            self.app_config.language = self.language_var.get()
            self.app_config.theme = self.theme_var.get()

            self.app_config.scan_system_hotkeys = self.scan_system_var.get()
            self.app_config.scan_application_hotkeys = self.scan_app_var.get()
            self.app_config.scan_known_software = self.scan_known_var.get()
            self.app_config.include_user_defined = self.include_user_var.get()

            self.app_config.show_critical_alerts = self.show_critical_var.get()
            self.app_config.show_high_alerts = self.show_high_var.get()
            self.app_config.show_medium_alerts = self.show_medium_var.get()
            self.app_config.show_low_alerts = self.show_low_var.get()

            self.app_config.default_export_format = self.default_format_var.get()
            self.app_config.include_timestamps = self.include_timestamps_var.get()
            self.app_config.include_suggestions = self.include_suggestions_var.get()
            self.app_config.auto_cleanup_reports = self.auto_cleanup_var.get()
            self.app_config.max_report_count = int(self.max_reports_var.get())

            # 保存到配置管理器
            self.config_manager.set_config('General', 'minimize_to_tray', str(self.minimize_to_tray_var.get()).lower())
            self.config_manager.set_config('General', 'start_minimized', str(self.start_minimized_var.get()).lower())
            
            self.config_manager.set_config('Detection', 'scan_registry_hotkeys', str(self.scan_registry_var.get()).lower())
            self.config_manager.set_config('Detection', 'scan_active_window', str(self.scan_window_var.get()).lower())
            self.config_manager.set_config('Detection', 'deep_scan_mode', str(self.deep_scan_var.get()).lower())
            self.config_manager.set_config('Detection', 'exclude_processes', self.exclude_processes_var.get())
            
            self.config_manager.set_config('Alerts', 'alert_sound', str(self.alert_sound_var.get()).lower())
            self.config_manager.set_config('Alerts', 'popup_notifications', str(self.popup_notifications_var.get()).lower())
            self.config_manager.set_config('Alerts', 'log_alerts', str(self.log_alerts_var.get()).lower())
            
            self.config_manager.set_config('Export', 'include_statistics', str(self.include_statistics_var.get()).lower())
            
            self.config_manager.set_config('Advanced', 'logging_level', self.log_level_var.get())
            self.config_manager.set_config('Advanced', 'max_log_files', self.max_log_files_var.get())
            self.config_manager.set_config('Advanced', 'scan_timeout', self.scan_timeout_var.get())
            self.config_manager.set_config('Advanced', 'process_scan_limit', self.process_limit_var.get())
            self.config_manager.set_config('Advanced', 'enable_hotkey_monitoring', str(self.enable_monitoring_var.get()).lower())
            self.config_manager.set_config('Advanced', 'monitoring_interval', self.monitoring_interval_var.get())

            # 保存配置
            self.config_manager.save_config()
            self.result = self.app_config

            messagebox.showinfo("成功", "设置已保存")
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")

    def reset_defaults(self):
        """恢复默认设置"""
        if messagebox.askyesno("确认", "确定要恢复默认设置吗？"):
            try:
                # 创建默认配置
                default_config = AppConfig()
                
                # 更新界面
                self.app_config = default_config
                self.load_current_settings()
                
                messagebox.showinfo("成功", "已恢复默认设置")

            except Exception as e:
                messagebox.showerror("错误", f"恢复默认设置失败: {e}")


if __name__ == "__main__":
    # 测试GUI界面
    app = EnhancedHotkeyGUI()
    app.run()
