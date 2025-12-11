#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composer 综合管理页面
提供 Composer 的安装和配置功能
"""

import sys
import time
import threading
from typing import Dict, Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QGroupBox, QMessageBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame, QTabWidget, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

from .composer_config import ComposerConfigurator
from .composer_install import ComposerInstaller


class ComposerInstallThread(QThread):
    """Composer安装线程"""
    progress_signal = Signal(str)  # 安装进度信号
    result_signal = Signal(bool)  # 安装结果信号

    def __init__(self, install_dir: str = None, local_install: bool = False):
        super().__init__()
        self.install_dir = install_dir
        self.local_install = local_install
        self.installer = ComposerInstaller()
        self.is_running = False

    def run(self):
        """执行安装"""
        self.is_running = True
        try:
            # 检查PHP环境
            if not self.installer.check_php_requirements():
                self.result_signal.emit(False)
                return

            # 安装Composer
            success = self.installer.install(
                install_dir=self.install_dir,
                global_install=not self.local_install
            )
            self.result_signal.emit(success)

        except Exception as e:
            self.progress_signal.emit(f"安装失败: {str(e)}")
            self.result_signal.emit(False)

    def stop(self):
        """停止安装"""
        self.is_running = False


class ComposerConfigTestThread(QThread):
    """Composer配置测试线程"""
    progress_signal = Signal(str)  # 测试进度信号
    result_signal = Signal(list)  # 测试结果信号

    def __init__(self, configurator: ComposerConfigurator, timeout: int = 5):
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


class ComposerTab(QWidget):
    """Composer 综合管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configurator = ComposerConfigurator()
        self.install_thread = None
        self.test_thread = None
        self.init_ui()
        self.load_status()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 安装标签页
        self.install_tab = self.create_install_tab()
        self.tab_widget.addTab(self.install_tab, "安装 Composer")

        # 配置标签页
        self.config_tab = self.create_config_tab()
        self.tab_widget.addTab(self.config_tab, "配置镜像源")

    def create_install_tab(self) -> QWidget:
        """创建安装标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title = QLabel("Composer 安装")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 环境检查组
        env_group = QGroupBox("环境检查")
        env_layout = QVBoxLayout(env_group)

        self.php_status_label = QLabel("PHP 状态: 检查中...")
        self.php_version_label = QLabel("PHP 版本: 检查中...")
        self.composer_status_label = QLabel("Composer 状态: 检查中...")

        env_layout.addWidget(self.php_status_label)
        env_layout.addWidget(self.php_version_label)
        env_layout.addWidget(self.composer_status_label)

        # 刷新状态按钮
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.load_status)
        env_layout.addWidget(refresh_btn)

        layout.addWidget(env_group)

        # 安装选项组
        install_group = QGroupBox("安装选项")
        install_layout = QGridLayout(install_group)

        # 全局安装单选
        self.global_radio = QPushButton("全局安装")
        self.global_radio.setCheckable(True)
        self.global_radio.setChecked(True)
        self.global_radio.clicked.connect(self.on_install_mode_changed)
        install_layout.addWidget(self.global_radio, 0, 0)

        self.global_info = QLabel("安装到系统目录，所有项目可用")
        install_layout.addWidget(self.global_info, 0, 1, 1, 2)

        # 本地安装单选
        self.local_radio = QPushButton("本地安装")
        self.local_radio.setCheckable(True)
        self.local_radio.clicked.connect(self.on_install_mode_changed)
        install_layout.addWidget(self.local_radio, 1, 0)

        self.local_info = QLabel("安装到当前目录，仅当前项目可用")
        install_layout.addWidget(self.local_info, 1, 1, 1, 2)

        # 自定义目录
        custom_label = QLabel("自定义目录:")
        install_layout.addWidget(custom_label, 2, 0)

        self.custom_dir_edit = QLineEdit()
        self.custom_dir_edit.setPlaceholderText("留空使用默认目录")
        install_layout.addWidget(self.custom_dir_edit, 2, 1)

        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_directory)
        install_layout.addWidget(browse_btn, 2, 2)

        layout.addWidget(install_group)

        # 安装控制组
        control_group = QGroupBox("安装控制")
        control_layout = QHBoxLayout(control_group)

        # 安装按钮
        self.install_btn = QPushButton("开始安装")
        self.install_btn.clicked.connect(self.start_install)
        control_layout.addWidget(self.install_btn)

        # 进度条
        self.install_progress = QProgressBar()
        self.install_progress.setVisible(False)
        control_layout.addWidget(self.install_progress)

        layout.addWidget(control_group)

        # 安装日志
        log_group = QGroupBox("安装日志")
        log_layout = QVBoxLayout(log_group)

        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMaximumHeight(200)
        log_layout.addWidget(self.install_log)

        layout.addWidget(log_group)

        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout(help_group)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(100)
        help_text.setPlainText("1. 环境检查：确认已安装PHP并满足版本要求\n"
                             "2. 选择安装模式：全局或本地安装\n"
                             "3. 开始安装：点击开始安装按钮\n"
                             "4. 配置镜像源：安装完成后切换到配置标签页")
        help_layout.addWidget(help_text)

        layout.addWidget(help_group)
        layout.addStretch()

        return tab

    def create_config_tab(self) -> QWidget:
        """创建配置标签页"""
        from .composer_config_tab import ComposerConfigTab
        return ComposerConfigTab(self)

    def load_status(self):
        """加载环境状态"""
        # 检查PHP
        installer = ComposerInstaller()
        if installer.php_executable:
            self.php_status_label.setText("PHP 状态: 已安装")

            version = installer.check_php_version()
            if version:
                self.php_version_label.setText(f"PHP 版本: {version}")
            else:
                self.php_version_label.setText("PHP 版本: 获取失败")
        else:
            self.php_status_label.setText("PHP 状态: 未找到")
            self.php_version_label.setText("PHP 版本: -")

        # 检查Composer
        if self.configurator.check_composer_installed():
            self.composer_status_label.setText("Composer 状态: 已安装")
            self.install_btn.setText("重新安装")
        else:
            self.composer_status_label.setText("Composer 状态: 未安装")
            self.install_btn.setText("开始安装")

    def on_install_mode_changed(self):
        """安装模式改变"""
        if self.global_radio.isChecked():
            self.local_radio.setChecked(False)
        else:
            self.global_radio.setChecked(False)

    def browse_directory(self):
        """浏览目录"""
        from PySide6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(
            self, "选择安装目录"
        )
        if directory:
            self.custom_dir_edit.setText(directory)

    def start_install(self):
        """开始安装"""
        if self.install_btn.text() == "重新安装":
            reply = QMessageBox.question(
                self,
                "确认重新安装",
                "检测到 Composer 已安装，是否要重新安装？\n这会覆盖现有的安装。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # 检查PHP环境
        installer = ComposerInstaller()
        if not installer.check_php_requirements():
            self.add_install_log("PHP 环境检查失败，无法安装")
            return

        # 获取安装选项
        local_install = self.local_radio.isChecked()
        install_dir = self.custom_dir_edit.text() if self.custom_dir_edit.text() else None

        # 开始安装
        self.install_btn.setEnabled(False)
        self.install_progress.setVisible(True)
        self.install_progress.setRange(0, 0)  # 无限进度条
        self.add_install_log("开始安装 Composer...")

        # 创建安装线程
        self.install_thread = ComposerInstallThread(install_dir, local_install)
        self.install_thread.progress_signal.connect(self.add_install_log)
        self.install_thread.result_signal.connect(self.on_install_finished)
        self.install_thread.start()

    def add_install_log(self, message):
        """添加安装日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.install_log.append(log_entry)

    def on_install_finished(self, success):
        """安装完成"""
        self.install_btn.setEnabled(True)
        self.install_progress.setVisible(False)

        if success:
            self.add_install_log("安装完成！")
            QMessageBox.information(
                self,
                "安装成功",
                "Composer 安装成功！\n\n请切换到\"配置镜像源\"标签页来配置国内镜像源。"
            )
        else:
            self.add_install_log("安装失败！")
            QMessageBox.critical(
                self,
                "安装失败",
                "Composer 安装失败，请检查安装日志了解详情。"
            )

        # 刷新状态
        self.load_status()