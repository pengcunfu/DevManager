#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pip 配置页面 GUI
提供图形化的 Pip 镜像源配置功能
"""

import sys
import time
import threading
from typing import Dict, Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QGroupBox, QMessageBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

from app.pip_config import PipConfigurator


class MirrorTestThread(QThread):
    """镜像源测试线程"""
    progress_signal = Signal(str)  # 测试进度信号
    result_signal = Signal(list)  # 测试结果信号

    def __init__(self, configurator: PipConfigurator, timeout: int = 5):
        super().__init__()
        self.configurator = configurator
        self.timeout = timeout
        self.is_running = False

    def run(self):
        """执行测试"""
        self.is_running = True
        results = []

        for key, mirror in self.configurator.MIRRORS.items():
            if not self.is_running:
                break

            self.progress_signal.emit(f"正在测试 {mirror['name']}...")

            speed = self.configurator.test_mirror_speed(key, mirror, self.timeout)

            if speed is not None:
                results.append((key, mirror['name'], speed))
            else:
                results.append((key, mirror['name'], None))

        # 排序
        results.sort(key=lambda x: (x[2] is None, x[2] if x[2] is not None else float('inf')))

        self.result_signal.emit(results)

    def stop(self):
        """停止测试"""
        self.is_running = False


class PipConfigPage(QWidget):
    """Pip 配置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configurator = PipConfigurator()
        self.test_thread = None
        self.init_ui()
        self.load_current_config()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧配置面板
        left_panel = self.create_config_panel()
        splitter.addWidget(left_panel)

        # 右侧测试面板
        right_panel = self.create_test_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([400, 500])

    def create_config_panel(self) -> QWidget:
        """创建配置面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("🔧 Pip 镜像源配置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 当前配置信息组
        current_group = QGroupBox("📍 当前配置")
        current_layout = QVBoxLayout(current_group)

        self.current_mirror_label = QLabel("当前镜像源: 加载中...")
        self.current_url_label = QLabel("镜像地址: 加载中...")
        self.config_file_label = QLabel("配置文件: 加载中...")

        current_layout.addWidget(self.current_mirror_label)
        current_layout.addWidget(self.current_url_label)
        current_layout.addWidget(self.config_file_label)

        layout.addWidget(current_group)

        # 镜像源选择组
        select_group = QGroupBox("🎯 选择镜像源")
        select_layout = QVBoxLayout(select_group)

        # 镜像源下拉框
        self.mirror_combo = QComboBox()
        self.populate_mirror_combo()
        select_layout.addWidget(self.mirror_combo)

        # 配置按钮
        config_btn = QPushButton("✅ 应用配置")
        config_btn.clicked.connect(self.configure_mirror)
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        select_layout.addWidget(config_btn)

        # 恢复官方源按钮
        official_btn = QPushButton("🔄 恢复官方源")
        official_btn.clicked.connect(lambda: self.configure_mirror('official'))
        select_layout.addWidget(official_btn)

        layout.addWidget(select_group)

        # 操作按钮组
        button_group = QGroupBox("⚡ 快捷操作")
        button_layout = QGridLayout(button_group)

        # 刷新配置按钮
        refresh_btn = QPushButton("🔄 刷新配置")
        refresh_btn.clicked.connect(self.load_current_config)
        button_layout.addWidget(refresh_btn, 0, 0)

        # 打开配置文件按钮
        open_file_btn = QPushButton("📂 打开配置文件")
        open_file_btn.clicked.connect(self.open_config_file)
        button_layout.addWidget(open_file_btn, 0, 1)

        layout.addWidget(button_group)

        # 使用说明
        help_group = QGroupBox("📖 使用说明")
        help_layout = QVBoxLayout(help_group)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(120)
        help_text.setPlainText("1. 选择镜像源：从下拉框中选择合适的镜像源\n"
                             "2. 应用配置：点击\"应用配置\"按钮\n"
                             "3. 测试速度：在右侧面板测试各镜像源速度\n"
                             "4. 恢复默认：点击\"恢复官方源\"使用默认源\n\n"
                             "建议：选择响应速度最快的镜像源以获得最佳下载体验。")
        help_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        help_layout.addWidget(help_text)

        layout.addWidget(help_group)

        layout.addStretch()

        return panel

    def create_test_panel(self) -> QWidget:
        """创建测试面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("⚡ 镜像源速度测试")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 测试控制组
        control_group = QGroupBox("🎮 测试控制")
        control_layout = QHBoxLayout(control_group)

        # 开始测试按钮
        self.test_btn = QPushButton("🚀 开始测试")
        self.test_btn.clicked.connect(self.start_test)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.test_btn)

        # 停止测试按钮
        self.stop_btn = QPushButton("⏹ 停止测试")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.stop_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)

        layout.addWidget(control_group)

        # 测试结果表格
        result_group = QGroupBox("📊 测试结果")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.setup_result_table()
        result_layout.addWidget(self.result_table)

        layout.addWidget(result_group)

        # 测试状态
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        return panel

    def populate_mirror_combo(self):
        """填充镜像源下拉框"""
        self.mirror_combo.clear()

        # 按推荐顺序排序
        recommended_order = ['tsinghua', 'aliyun', 'tencent', 'huawei', 'ustc', 'douban', 'official']

        for key in recommended_order:
            if key in self.configurator.MIRRORS:
                mirror = self.configurator.MIRRORS[key]
                display_name = f"{mirror['name']} ({key})"
                self.mirror_combo.addItem(display_name, key)

    def setup_result_table(self):
        """设置结果表格"""
        headers = ["排名", "镜像源", "地址", "响应时间", "状态"]
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)

        # 设置列宽
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 排名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 镜像源
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 地址
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 响应时间
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 状态

        # 设置表格样式
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 初始化表格行
        self.result_table.setRowCount(len(self.configurator.MIRRORS))
        row = 0
        for key, mirror in self.configurator.MIRRORS.items():
            self.result_table.setItem(row, 0, QTableWidgetItem("-"))
            self.result_table.setItem(row, 1, QTableWidgetItem(mirror['name']))
            self.result_table.setItem(row, 2, QTableWidgetItem(mirror['url']))
            self.result_table.setItem(row, 3, QTableWidgetItem("-"))
            self.result_table.setItem(row, 4, QTableWidgetItem("未测试"))
            row += 1

    def load_current_config(self):
        """加载当前配置"""
        try:
            current = self.configurator.get_current_config()

            if current:
                self.current_mirror_label.setText(f"当前镜像源: {current['name']}")
                self.current_url_label.setText(f"镜像地址: {current['url']}")

                # 更新下拉框选择
                for i in range(self.mirror_combo.count()):
                    if self.mirror_combo.itemData(i) == current['key']:
                        self.mirror_combo.setCurrentIndex(i)
                        break
            else:
                self.current_mirror_label.setText("当前镜像源: 官方源（默认）")
                self.current_url_label.setText("镜像地址: https://pypi.org/simple")
                self.mirror_combo.setCurrentIndex(self.mirror_combo.count() - 1)  # 选择官方源

            config_file = self.configurator.pip_config_file
            if config_file.exists():
                self.config_file_label.setText(f"配置文件: {config_file} ✓")
            else:
                self.config_file_label.setText(f"配置文件: {config_file} ✗")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")

    def configure_mirror(self, mirror_key=None):
        """配置镜像源"""
        if mirror_key is None:
            mirror_key = self.mirror_combo.currentData()

        if not mirror_key:
            QMessageBox.warning(self, "错误", "请选择镜像源")
            return

        try:
            mirror = self.configurator.MIRRORS[mirror_key]

            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "确认配置",
                f"确定要配置 {mirror['name']} 镜像源吗？\n\n地址: {mirror['url']}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

            # 执行配置
            success = self.configurator.configure_mirror(mirror_key)

            if success:
                QMessageBox.information(
                    self,
                    "配置成功",
                    f"已成功配置 {mirror['name']} 镜像源！\n\n请重启终端或新的 Python 环境以生效。"
                )
                self.load_current_config()
            else:
                QMessageBox.error(
                    self,
                    "配置失败",
                    f"配置 {mirror['name']} 镜像源失败，请检查网络连接或权限设置。"
                )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"配置镜像源时出错: {str(e)}")

    def start_test(self):
        """开始测试"""
        # 清空结果表格
        for row in range(self.result_table.rowCount()):
            self.result_table.setItem(row, 0, QTableWidgetItem("-"))
            self.result_table.setItem(row, 3, QTableWidgetItem("-"))
            self.result_table.setItem(row, 4, QTableWidgetItem("测试中..."))

        # 更新状态
        self.test_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.status_label.setText("正在测试镜像源速度...")

        # 创建并启动测试线程
        self.test_thread = MirrorTestThread(self.configurator)
        self.test_thread.progress_signal.connect(self.update_test_status)
        self.test_thread.result_signal.connect(self.show_test_results)
        self.test_thread.start()

    def stop_test(self):
        """停止测试"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.stop()
            self.test_thread.wait()

        self.test_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("测试已停止")

    def update_test_status(self, message):
        """更新测试状态"""
        self.status_label.setText(message)

    def show_test_results(self, results):
        """显示测试结果"""
        # 创建镜像源到表格行的映射
        mirror_to_row = {}
        for row in range(self.result_table.rowCount()):
            mirror_name = self.result_table.item(row, 1).text()
            for key, mirror in self.configurator.MIRRORS.items():
                if mirror['name'] == mirror_name:
                    mirror_to_row[key] = row
                    break

        # 更新表格结果
        for rank, (key, name, speed) in enumerate(results, 1):
            if key in mirror_to_row:
                row = mirror_to_row[key]

                # 排名
                rank_item = QTableWidgetItem(str(rank) if speed is not None else "-")
                rank_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 0, rank_item)

                # 响应时间
                if speed is not None:
                    time_text = f"{speed * 1000:.0f} ms"
                    status_text = "✓ 可用"
                    # 根据速度设置颜色
                    if speed < 0.5:
                        time_color = "green"
                        status_color = "green"
                    elif speed < 1.0:
                        time_color = "orange"
                        status_color = "orange"
                    else:
                        time_color = "red"
                        status_color = "red"
                else:
                    time_text = "超时"
                    status_text = "✗ 不可用"
                    time_color = "red"
                    status_color = "red"

                time_item = QTableWidgetItem(time_text)
                time_item.setTextAlignment(Qt.AlignCenter)
                time_item.setStyleSheet(f"color: {time_color}; font-weight: bold;")
                self.result_table.setItem(row, 3, time_item)

                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setStyleSheet(f"color: {status_color}; font-weight: bold;")
                self.result_table.setItem(row, 4, status_item)

        # 恢复按钮状态
        self.test_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # 显示推荐
        if results and results[0][2] is not None:
            fastest = results[0]
            self.status_label.setText(
                f"测试完成！推荐使用 {fastest[1]} (响应时间: {fastest[2] * 1000:.0f} ms)"
            )
        else:
            self.status_label.setText("测试完成！但所有镜像源都无法访问")

    def open_config_file(self):
        """打开配置文件"""
        import subprocess
        import os

        config_file = self.configurator.pip_config_file

        if not config_file.exists():
            reply = QMessageBox.question(
                self,
                "配置文件不存在",
                f"配置文件 {config_file} 不存在。\n\n是否创建该文件？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                try:
                    config_file.parent.mkdir(parents=True, exist_ok=True)
                    config_file.touch()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建配置文件失败: {str(e)}")
                    return
            else:
                return

        # 使用系统默认程序打开文件
        try:
            if sys.platform == "win32":
                os.startfile(config_file)
            elif sys.platform == "darwin":
                subprocess.run(["open", config_file])
            else:
                subprocess.run(["xdg-open", config_file])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法打开配置文件: {str(e)}")