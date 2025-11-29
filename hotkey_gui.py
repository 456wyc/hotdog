#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键冲突检测器GUI界面
提供详细的热键信息显示和冲突分析界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import logging

from hotkey_conflict_detector import (
    SystemHotkeyDetector, RegistryHotkeyDetector,
    ApplicationHotkeyDetector, ActiveWindowHotkeyDetector,
    ConflictAnalyzer, HAS_WIN32
)

class HotkeyConflictGUI:
    """热键冲突检测器主界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("热键冲突检测器 v1.0")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # 设置图标（如果需要）
        # self.root.iconbitmap('icon.ico')

        # 数据存储
        self.all_hotkeys = []
        self.conflicts = []
        self.is_scanning = False

        # 初始化检测器
        self.system_detector = SystemHotkeyDetector()
        self.registry_detector = RegistryHotkeyDetector()
        self.app_detector = ApplicationHotkeyDetector()
        self.window_detector = ActiveWindowHotkeyDetector()
        self.analyzer = ConflictAnalyzer()

        # 创建界面
        self.create_widgets()
        self.create_menu()

        # 设置日志
        self.setup_logging()

        # 检查依赖
        if not HAS_WIN32:
            messagebox.showwarning(
                "依赖缺失",
                "检测到缺少win32api模块，某些功能可能无法使用。\\n"
                "请运行: pip install pywin32 psutil"
            )

    def create_widgets(self):
        """创建主界面组件"""

        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部控制栏
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 扫描按钮
        self.scan_button = ttk.Button(
            control_frame,
            text="开始扫描",
            command=self.start_scan
        )
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))

        # 刷新按钮
        self.refresh_button = ttk.Button(
            control_frame,
            text="刷新",
            command=self.refresh_data
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))

        # 导出按钮
        self.export_button = ttk.Button(
            control_frame,
            text="导出报告",
            command=self.export_report
        )
        self.export_button.pack(side=tk.LEFT, padx=(0, 10))

        # 状态标签
        self.status_label = ttk.Label(control_frame, text="就绪")
        self.status_label.pack(side=tk.RIGHT)

        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(0, 10))

        # 主内容区域 - 使用Notebook组织
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建各个标签页
        self.create_overview_tab()
        self.create_conflicts_tab()
        self.create_system_tab()
        self.create_applications_tab()
        self.create_registry_tab()
        self.create_window_tab()
        self.create_log_tab()

    def create_overview_tab(self):
        """创建概览标签页"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="概览")

        # 统计信息框架
        stats_frame = ttk.LabelFrame(overview_frame, text="统计信息", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # 统计标签
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        # 第一行
        ttk.Label(stats_grid, text="总热键数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.total_hotkeys_label = ttk.Label(stats_grid, text="0", foreground="blue")
        self.total_hotkeys_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(stats_grid, text="冲突数:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.conflicts_label = ttk.Label(stats_grid, text="0", foreground="red")
        self.conflicts_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        # 第二行
        ttk.Label(stats_grid, text="系统热键:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.system_hotkeys_label = ttk.Label(stats_grid, text="0")
        self.system_hotkeys_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(stats_grid, text="应用程序热键:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        self.app_hotkeys_label = ttk.Label(stats_grid, text="0")
        self.app_hotkeys_label.grid(row=1, column=3, sticky=tk.W, padx=(0, 20))

        # 冲突概览
        conflicts_frame = ttk.LabelFrame(overview_frame, text="冲突概览", padding=10)
        conflicts_frame.pack(fill=tk.BOTH, expand=True)

        # 冲突列表
        columns = ('热键', '冲突应用', '类型', '严重程度')
        self.conflicts_tree = ttk.Treeview(conflicts_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.conflicts_tree.heading(col, text=col)
            self.conflicts_tree.column(col, width=150)

        # 滚动条
        conflicts_scroll = ttk.Scrollbar(conflicts_frame, orient=tk.VERTICAL, command=self.conflicts_tree.yview)
        self.conflicts_tree.configure(yscrollcommand=conflicts_scroll.set)

        self.conflicts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conflicts_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_conflicts_tab(self):
        """创建冲突详情标签页"""
        conflicts_frame = ttk.Frame(self.notebook)
        self.notebook.add(conflicts_frame, text="冲突详情")

        # 冲突详细列表
        columns = ('热键组合', '应用程序', '类型', '描述', '进程ID', '检测时间')
        self.detailed_conflicts_tree = ttk.Treeview(conflicts_frame, columns=columns, show='headings')

        for col in columns:
            self.detailed_conflicts_tree.heading(col, text=col)
            self.detailed_conflicts_tree.column(col, width=120)

        # 滚动条
        detailed_scroll_y = ttk.Scrollbar(conflicts_frame, orient=tk.VERTICAL, command=self.detailed_conflicts_tree.yview)
        detailed_scroll_x = ttk.Scrollbar(conflicts_frame, orient=tk.HORIZONTAL, command=self.detailed_conflicts_tree.xview)
        self.detailed_conflicts_tree.configure(yscrollcommand=detailed_scroll_y.set, xscrollcommand=detailed_scroll_x.set)

        self.detailed_conflicts_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        detailed_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        detailed_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def create_system_tab(self):
        """创建系统热键标签页"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="系统热键")

        self.system_tree = self._create_hotkey_tree(system_frame)

    def create_applications_tab(self):
        """创建应用程序热键标签页"""
        app_frame = ttk.Frame(self.notebook)
        self.notebook.add(app_frame, text="应用程序")

        self.app_tree = self._create_hotkey_tree(app_frame)

    def create_registry_tab(self):
        """创建注册表热键标签页"""
        registry_frame = ttk.Frame(self.notebook)
        self.notebook.add(registry_frame, text="注册表")

        self.registry_tree = self._create_hotkey_tree(registry_frame)

    def create_window_tab(self):
        """创建活动窗口热键标签页"""
        window_frame = ttk.Frame(self.notebook)
        self.notebook.add(window_frame, text="活动窗口")

        self.window_tree = self._create_hotkey_tree(window_frame)

    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="日志")

        # 日志文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_hotkey_tree(self, parent):
        """创建热键树形视图的通用方法"""
        columns = ('热键组合', '应用程序', '描述', '进程ID', '检测时间')
        tree = ttk.Treeview(parent, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        # 滚动条
        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        return tree

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出报告", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 扫描菜单
        scan_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="扫描", menu=scan_menu)
        scan_menu.add_command(label="开始扫描", command=self.start_scan)
        scan_menu.add_command(label="停止扫描", command=self.stop_scan)
        scan_menu.add_command(label="刷新", command=self.refresh_data)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def setup_logging(self):
        """设置日志"""
        # 创建日志处理器
        self.log_handler = LogHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)

        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)

    def start_scan(self):
        """开始扫描热键"""
        if self.is_scanning:
            return

        self.is_scanning = True
        self.scan_button.config(state='disabled', text="扫描中...")
        self.progress.start()
        self.status_label.config(text="正在扫描...")

        # 在后台线程中执行扫描
        scan_thread = threading.Thread(target=self._scan_hotkeys)
        scan_thread.daemon = True
        scan_thread.start()

    def _scan_hotkeys(self):
        """在后台线程中扫描热键"""
        try:
            self._log("开始扫描热键...")
            all_hotkeys = []

            # 扫描系统热键
            self._log("扫描系统热键...")
            system_hotkeys = self.system_detector.detect_system_hotkeys()
            all_hotkeys.extend(system_hotkeys)

            # 扫描应用程序热键
            self._log("扫描应用程序热键...")
            app_hotkeys = self.app_detector.detect_application_hotkeys()
            all_hotkeys.extend(app_hotkeys)

            # 扫描注册表热键
            self._log("扫描注册表热键...")
            registry_hotkeys = self.registry_detector.detect_registry_hotkeys()
            all_hotkeys.extend(registry_hotkeys)

            # 扫描活动窗口热键
            self._log("扫描活动窗口热键...")
            window_hotkeys = self.window_detector.detect_active_window_hotkeys()
            all_hotkeys.extend(window_hotkeys)

            # 分析冲突
            self._log("分析冲突...")
            conflicts = self.analyzer.analyze_conflicts(all_hotkeys)

            # 更新UI（在主线程中）
            self.root.after(0, self._update_ui, all_hotkeys, conflicts)

        except Exception as e:
            self._log(f"扫描过程中出错: {e}")
            self.root.after(0, self._scan_completed)

    def _update_ui(self, all_hotkeys, conflicts):
        """更新界面数据"""
        self.all_hotkeys = all_hotkeys
        self.conflicts = conflicts

        # 更新统计信息
        self.update_statistics()

        # 更新各个树视图
        self.populate_overview_conflicts()
        self.populate_detailed_conflicts()
        self.populate_system_hotkeys()
        self.populate_app_hotkeys()
        self.populate_registry_hotkeys()
        self.populate_window_hotkeys()

        self._log(f"扫描完成 - 发现 {len(all_hotkeys)} 个热键，{len(conflicts)} 个冲突")
        self._scan_completed()

    def _scan_completed(self):
        """扫描完成后的UI更新"""
        self.is_scanning = False
        self.scan_button.config(state='normal', text="开始扫描")
        self.progress.stop()
        self.status_label.config(text="扫描完成")

    def stop_scan(self):
        """停止扫描"""
        self.is_scanning = False
        self._scan_completed()

    def refresh_data(self):
        """刷新数据"""
        if not self.is_scanning:
            self.start_scan()

    def update_statistics(self):
        """更新统计信息"""
        system_count = sum(1 for h in self.all_hotkeys if h.hotkey_type == 'system')
        app_count = sum(1 for h in self.all_hotkeys if h.hotkey_type == 'application')

        self.total_hotkeys_label.config(text=str(len(self.all_hotkeys)))
        self.conflicts_label.config(text=str(len(self.conflicts)))
        self.system_hotkeys_label.config(text=str(system_count))
        self.app_hotkeys_label.config(text=str(app_count))

    def populate_overview_conflicts(self):
        """填充概览冲突列表"""
        # 清空现有项目
        for item in self.conflicts_tree.get_children():
            self.conflicts_tree.delete(item)

        # 添加冲突项目
        for conflict in self.conflicts:
            apps = ', '.join(set(h.application for h in conflict['hotkeys']))
            self.conflicts_tree.insert('', 'end', values=(
                conflict['key_combination'],
                apps,
                conflict['conflict_type'],
                conflict['severity']
            ))

    def populate_detailed_conflicts(self):
        """填充详细冲突列表"""
        # 清空现有项目
        for item in self.detailed_conflicts_tree.get_children():
            self.detailed_conflicts_tree.delete(item)

        # 添加冲突的详细信息
        for conflict in self.conflicts:
            for hotkey in conflict['hotkeys']:
                self.detailed_conflicts_tree.insert('', 'end', values=(
                    hotkey.key_combination,
                    hotkey.application,
                    hotkey.hotkey_type,
                    hotkey.description,
                    hotkey.process_id or "",
                    hotkey.detected_time.strftime("%Y-%m-%d %H:%M:%S")
                ))

    def populate_system_hotkeys(self):
        """填充系统热键列表"""
        self._populate_hotkey_tree(self.system_tree, 'system')

    def populate_app_hotkeys(self):
        """填充应用程序热键列表"""
        self._populate_hotkey_tree(self.app_tree, 'application')

    def populate_registry_hotkeys(self):
        """填充注册表热键列表"""
        self._populate_hotkey_tree(self.registry_tree, 'registry')

    def populate_window_hotkeys(self):
        """填充活动窗口热键列表"""
        self._populate_hotkey_tree(self.window_tree, 'window')

    def _populate_hotkey_tree(self, tree, hotkey_type):
        """填充指定类型的热键树"""
        # 清空现有项目
        for item in tree.get_children():
            tree.delete(item)

        # 添加指定类型的热键
        for hotkey in self.all_hotkeys:
            if hotkey.hotkey_type == hotkey_type:
                tree.insert('', 'end', values=(
                    hotkey.key_combination,
                    hotkey.application,
                    hotkey.description,
                    hotkey.process_id or "",
                    hotkey.detected_time.strftime("%Y-%m-%d %H:%M:%S")
                ))

    def export_report(self):
        """导出报告"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )

            if filename:
                self._export_to_file(filename)
                messagebox.showinfo("导出成功", f"报告已保存到: {filename}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出报告时出错: {e}")

    def _export_to_file(self, filename):
        """将报告导出到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("热键冲突检测报告\\n")
            f.write("=" * 50 + "\\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")

            # 统计信息
            f.write("统计信息:\\n")
            f.write(f"总热键数: {len(self.all_hotkeys)}\\n")
            f.write(f"冲突数: {len(self.conflicts)}\\n\\n")

            # 冲突详情
            if self.conflicts:
                f.write("冲突详情:\\n")
                f.write("-" * 30 + "\\n")
                for i, conflict in enumerate(self.conflicts, 1):
                    f.write(f"{i}. 热键: {conflict['key_combination']}\\n")
                    f.write(f"   冲突类型: {conflict['conflict_type']}\\n")
                    f.write(f"   严重程度: {conflict['severity']}\\n")
                    f.write("   涉及应用:\\n")
                    for hotkey in conflict['hotkeys']:
                        f.write(f"     - {hotkey.application} ({hotkey.hotkey_type})\\n")
                    f.write("\\n")

            # 所有热键
            f.write("所有热键:\\n")
            f.write("-" * 30 + "\\n")
            for hotkey in self.all_hotkeys:
                f.write(f"{hotkey.key_combination} | {hotkey.application} | {hotkey.hotkey_type} | {hotkey.description}\\n")

    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于",
            "热键冲突检测器 v1.0\\n\\n"
            "功能特点:\\n"
            "• 检测系统级热键\\n"
            "• 检测应用程序热键\\n"
            "• 检测注册表热键\\n"
            "• 检测活动窗口热键\\n"
            "• 分析热键冲突\\n"
            "• 导出详细报告\\n\\n"
            "开发环境: Python + tkinter"
        )

    def _log(self, message):
        """添加日志消息"""
        logging.info(message)

    def run(self):
        """运行应用程序"""
        self.root.mainloop()

class LogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到tkinter Text组件"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.text_widget.insert(tk.END, msg + '\\n')
            self.text_widget.see(tk.END)
        except:
            self.handleError(record)

if __name__ == "__main__":
    app = HotkeyConflictGUI()
    app.run()