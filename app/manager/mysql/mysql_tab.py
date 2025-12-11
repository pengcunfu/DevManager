#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 管理标签页
提供 MySQL 安装、配置、服务管理的图形界面
"""

import sys
import os
import subprocess
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QComboBox,
    QSpinBox, QCheckBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

from .mysql_installer import MySQLInstaller
from .mysql_config import MySQLConfigManager


class MySQLWorkerThread(QThread):
    """MySQL操作工作线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, operation: str, installer: MySQLInstaller, **kwargs):
        super().__init__()
        self.operation = operation
        self.installer = installer
        self.kwargs = kwargs

    def run(self):
        """执行操作"""
        try:
            if self.operation == "install":
                self._install_mysql()
            elif self.operation == "uninstall":
                self._uninstall_mysql()
            elif self.operation == "start_service":
                self._start_service()
            elif self.operation == "stop_service":
                self._stop_service()
            elif self.operation == "restart_service":
                self._restart_service()
            elif self.operation == "install_service":
                self._install_service()
            elif self.operation == "set_password":
                self._set_password()
            elif self.operation == "check_requirements":
                self._check_requirements()
            else:
                self.finished_signal.emit(False, f"未知操作: {self.operation}")

        except Exception as e:
            self.log_signal.emit(f"操作失败: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def _install_mysql(self):
        """安装MySQL"""
        self.log_signal.emit("开始安装MySQL...")
        self.progress_signal.emit(10)

        # 检查安装要求
        requirements = self.installer.check_requirements()
        self.log_signal.emit("检查安装要求...")
        self.progress_signal.emit(20)

        failed_requirements = [req for req, satisfied in requirements.items() if not satisfied]
        if failed_requirements:
            error_msg = f"不满足安装要求: {', '.join(failed_requirements)}"
            self.log_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg)
            return

        self.log_signal.emit("安装要求检查通过")
        self.progress_signal.emit(30)

        if self.installer.system == "windows":
            # 下载MySQL
            self.log_signal.emit("正在下载MySQL...")
            installer_path = self.installer.download_mysql()
            self.progress_signal.emit(50)

            if not installer_path:
                error_msg = "下载MySQL失败"
                self.log_signal.emit(error_msg)
                self.finished_signal.emit(False, error_msg)
                return

            # 安装MySQL
            self.log_signal.emit("正在安装MySQL...")
            success = self.installer.install_mysql(installer_path)
            self.progress_signal.emit(80)

            if success:
                self.log_signal.emit("MySQL安装成功")
                self.finished_signal.emit(True, "MySQL安装成功")
            else:
                error_msg = "MySQL安装失败"
                self.log_signal.emit(error_msg)
                self.finished_signal.emit(False, error_msg)
        else:
            self.log_signal.emit("请使用系统包管理器安装MySQL")
            self.finished_signal.emit(False, "请使用系统包管理器安装MySQL")

        self.progress_signal.emit(100)

    def _uninstall_mysql(self):
        """卸载MySQL"""
        self.log_signal.emit("开始卸载MySQL...")
        success = self.installer.uninstall_mysql()

        if success:
            self.log_signal.emit("MySQL卸载成功")
            self.finished_signal.emit(True, "MySQL卸载成功")
        else:
            self.log_signal.emit("MySQL卸载失败")
            self.finished_signal.emit(False, "MySQL卸载失败")

    def _start_service(self):
        """启动服务"""
        self.log_signal.emit("正在启动MySQL服务...")
        success = self.installer.start_service()

        if success:
            self.log_signal.emit("MySQL服务启动成功")
            self.finished_signal.emit(True, "MySQL服务启动成功")
        else:
            self.log_signal.emit("MySQL服务启动失败")
            self.finished_signal.emit(False, "MySQL服务启动失败")

    def _stop_service(self):
        """停止服务"""
        self.log_signal.emit("正在停止MySQL服务...")
        success = self.installer.stop_service()

        if success:
            self.log_signal.emit("MySQL服务停止成功")
            self.finished_signal.emit(True, "MySQL服务停止成功")
        else:
            self.log_signal.emit("MySQL服务停止失败")
            self.finished_signal.emit(False, "MySQL服务停止失败")

    def _restart_service(self):
        """重启服务"""
        self.log_signal.emit("正在重启MySQL服务...")
        success = self.installer.restart_service()

        if success:
            self.log_signal.emit("MySQL服务重启成功")
            self.finished_signal.emit(True, "MySQL服务重启成功")
        else:
            self.log_signal.emit("MySQL服务重启失败")
            self.finished_signal.emit(False, "MySQL服务重启失败")

    def _install_service(self):
        """安装服务"""
        self.log_signal.emit("正在安装MySQL服务...")
        success = self.installer.install_service()

        if success:
            self.log_signal.emit("MySQL服务安装成功")
            self.finished_signal.emit(True, "MySQL服务安装成功")
        else:
            self.log_signal.emit("MySQL服务安装失败")
            self.finished_signal.emit(False, "MySQL服务安装失败")

    def _set_password(self):
        """设置密码"""
        password = self.kwargs.get('password', '')
        self.log_signal.emit("正在设置root密码...")
        success = self.installer.set_root_password(password)

        if success:
            self.log_signal.emit("root密码设置成功")
            self.finished_signal.emit(True, "root密码设置成功")
        else:
            self.log_signal.emit("root密码设置失败")
            self.finished_signal.emit(False, "root密码设置失败")

    def _check_requirements(self):
        """检查安装要求"""
        self.log_signal.emit("检查安装要求...")
        requirements = self.installer.check_requirements()

        for req, satisfied in requirements.items():
            status = "✓" if satisfied else "✗"
            self.log_signal.emit(f"  {status} {req}")

        self.finished_signal.emit(True, "安装要求检查完成")


class MySQLTab(QWidget):
    """MySQL管理标签页"""

    def __init__(self):
        super().__init__()
        self.installer = MySQLInstaller()
        self.config_manager = MySQLConfigManager()
        self.worker_thread = None
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 安装管理标签页
        self.install_tab = self._create_install_tab()
        self.tab_widget.addTab(self.install_tab, "安装管理")

        # 服务管理标签页
        self.service_tab = self._create_service_tab()
        self.tab_widget.addTab(self.service_tab, "服务管理")

        # 配置管理标签页
        self.config_tab = self._create_config_tab()
        self.tab_widget.addTab(self.config_tab, "配置管理")

        # 状态监控标签页
        self.monitor_tab = self._create_monitor_tab()
        self.tab_widget.addTab(self.monitor_tab, "状态监控")

        # 设置定时刷新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(5000)  # 每5秒刷新一次

    def _create_install_tab(self) -> QWidget:
        """创建安装管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 系统信息组
        info_group = QGroupBox("系统信息")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("操作系统:"), 0, 0)
        self.os_label = QLabel(self.installer.system.title())
        info_layout.addWidget(self.os_label, 0, 1)

        info_layout.addWidget(QLabel("架构:"), 0, 2)
        self.arch_label = QLabel(self.installer.architecture)
        info_layout.addWidget(self.arch_label, 0, 3)

        info_layout.addWidget(QLabel("安装状态:"), 1, 0)
        self.install_status_label = QLabel("检查中...")
        info_layout.addWidget(self.install_status_label, 1, 1)

        info_layout.addWidget(QLabel("MySQL版本:"), 1, 2)
        self.version_label = QLabel("未安装")
        info_layout.addWidget(self.version_label, 1, 3)

        layout.addWidget(info_group)

        # 安装要求检查组
        requirements_group = QGroupBox("安装要求检查")
        requirements_layout = QVBoxLayout(requirements_group)

        self.requirements_text = QTextEdit()
        self.requirements_text.setMaximumHeight(100)
        self.requirements_text.setReadOnly(True)
        requirements_layout.addWidget(self.requirements_text)

        check_btn = QPushButton("检查安装要求")
        check_btn.clicked.connect(self.check_requirements)
        requirements_layout.addWidget(check_btn)

        layout.addWidget(requirements_group)

        # 安装操作组
        install_group = QGroupBox("安装操作")
        install_layout = QVBoxLayout(install_group)

        # 安装按钮
        self.install_btn = QPushButton("安装MySQL")
        self.install_btn.clicked.connect(self.install_mysql)
        install_layout.addWidget(self.install_btn)

        # 卸载按钮
        self.uninstall_btn = QPushButton("卸载MySQL")
        self.uninstall_btn.clicked.connect(self.uninstall_mysql)
        install_layout.addWidget(self.uninstall_btn)

        # 安装服务按钮
        self.install_service_btn = QPushButton("安装MySQL服务")
        self.install_service_btn.clicked.connect(self.install_service)
        install_layout.addWidget(self.install_service_btn)

        layout.addWidget(install_group)

        # 操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return widget

    def _create_service_tab(self) -> QWidget:
        """创建服务管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 服务状态组
        status_group = QGroupBox("服务状态")
        status_layout = QGridLayout(status_group)

        status_layout.addWidget(QLabel("服务名称:"), 0, 0)
        self.service_name_label = QLabel(self.installer.service_name)
        status_layout.addWidget(self.service_name_label, 0, 1)

        status_layout.addWidget(QLabel("运行状态:"), 0, 2)
        self.service_status_label = QLabel("检查中...")
        status_layout.addWidget(self.service_status_label, 0, 3)

        status_layout.addWidget(QLabel("安装路径:"), 1, 0, 1, 2)
        self.install_path_label = QLabel(self.installer.installation_path)
        self.install_path_label.setWordWrap(True)
        status_layout.addWidget(self.install_path_label, 1, 2, 1, 2)

        layout.addWidget(status_group)

        # 服务控制组
        control_group = QGroupBox("服务控制")
        control_layout = QHBoxLayout(control_group)

        self.start_service_btn = QPushButton("启动服务")
        self.start_service_btn.clicked.connect(self.start_service)
        control_layout.addWidget(self.start_service_btn)

        self.stop_service_btn = QPushButton("停止服务")
        self.stop_service_btn.clicked.connect(self.stop_service)
        control_layout.addWidget(self.stop_service_btn)

        self.restart_service_btn = QPushButton("重启服务")
        self.restart_service_btn.clicked.connect(self.restart_service)
        control_layout.addWidget(self.restart_service_btn)

        layout.addWidget(control_group)

        # 密码管理组
        password_group = QGroupBox("密码管理")
        password_layout = QGridLayout(password_group)

        password_layout.addWidget(QLabel("Root密码:"), 0, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_input, 0, 1)

        self.set_password_btn = QPushButton("设置密码")
        self.set_password_btn.clicked.connect(self.set_root_password)
        password_layout.addWidget(self.set_password_btn, 0, 2)

        layout.addWidget(password_group)

        # 快速操作组
        quick_group = QGroupBox("快速操作")
        quick_layout = QHBoxLayout(quick_group)

        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.refresh_status)
        quick_layout.addWidget(refresh_btn)

        open_config_btn = QPushButton("打开配置文件")
        open_config_btn.clicked.connect(self.open_config_file)
        quick_layout.addWidget(open_config_btn)

        layout.addWidget(quick_group)

        layout.addStretch()
        return widget

    def _create_config_tab(self) -> QWidget:
        """创建配置管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 基本配置组
        basic_group = QGroupBox("基本配置")
        basic_layout = QGridLayout(basic_group)

        basic_layout.addWidget(QLabel("端口:"), 0, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(3306)
        basic_layout.addWidget(self.port_spin, 0, 1)

        basic_layout.addWidget(QLabel("最大连接数:"), 0, 2)
        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 10000)
        self.max_connections_spin.setValue(200)
        basic_layout.addWidget(self.max_connections_spin, 0, 3)

        basic_layout.addWidget(QLabel("InnoDB缓冲池:"), 1, 0)
        self.innodb_buffer_combo = QComboBox()
        self.innodb_buffer_combo.addItems(["64M", "128M", "256M", "512M", "1G", "2G"])
        self.innodb_buffer_combo.setCurrentText("256M")
        basic_layout.addWidget(self.innodb_buffer_combo, 1, 1)

        layout.addWidget(basic_group)

        # 配置操作组
        config_ops_group = QGroupBox("配置操作")
        config_ops_layout = QHBoxLayout(config_ops_group)

        apply_basic_btn = QPushButton("应用基本配置")
        apply_basic_btn.clicked.connect(self.apply_basic_config)
        config_ops_layout.addWidget(apply_basic_btn)

        add_performance_btn = QPushButton("添加性能优化")
        add_performance_btn.clicked.connect(self.add_performance_config)
        config_ops_layout.addWidget(add_performance_btn)

        add_security_btn = QPushButton("添加安全配置")
        add_security_btn.clicked.connect(self.add_security_config)
        config_ops_layout.addWidget(add_security_btn)

        validate_btn = QPushButton("验证配置")
        validate_btn.clicked.connect(self.validate_config)
        config_ops_layout.addWidget(validate_btn)

        layout.addWidget(config_ops_group)

        # 配置文件信息组
        config_info_group = QGroupBox("配置文件信息")
        config_info_layout = QVBoxLayout(config_info_group)

        self.config_info_text = QTextEdit()
        self.config_info_text.setMaximumHeight(150)
        self.config_info_text.setReadOnly(True)
        config_info_layout.addWidget(self.config_info_text)

        layout.addWidget(config_info_group)

        layout.addStretch()
        return widget

    def _create_monitor_tab(self) -> QWidget:
        """创建状态监控标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 系统监控组
        monitor_group = QGroupBox("系统监控")
        monitor_layout = QGridLayout(monitor_group)

        monitor_layout.addWidget(QLabel("服务状态:"), 0, 0)
        self.monitor_status_label = QLabel("检查中...")
        monitor_layout.addWidget(self.monitor_status_label, 0, 1)

        monitor_layout.addWidget(QLabel("运行时间:"), 0, 2)
        self.uptime_label = QLabel("未知")
        monitor_layout.addWidget(self.uptime_label, 0, 3)

        monitor_layout.addWidget(QLabel("连接数:"), 1, 0)
        self.connections_label = QLabel("未知")
        monitor_layout.addWidget(self.connections_label, 1, 1)

        monitor_layout.addWidget(QLabel("当前查询:"), 1, 2)
        self.queries_label = QLabel("未知")
        monitor_layout.addWidget(self.queries_label, 1, 3)

        layout.addWidget(monitor_group)

        # 状态历史表格
        history_group = QGroupBox("状态历史")
        history_layout = QVBoxLayout(history_group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "状态", "连接数", "查询数"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.history_table)

        clear_history_btn = QPushButton("清除历史")
        clear_history_btn.clicked.connect(self.clear_history)
        history_layout.addWidget(clear_history_btn)

        layout.addWidget(history_group)

        layout.addStretch()
        return widget

    def check_requirements(self):
        """检查安装要求"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.requirements_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread = MySQLWorkerThread("check_requirements", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def install_mysql(self):
        """安装MySQL"""
        reply = QMessageBox.question(
            self, "确认安装", "确定要安装MySQL吗？\n这将下载并安装MySQL数据库。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.log_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread = MySQLWorkerThread("install", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def uninstall_mysql(self):
        """卸载MySQL"""
        reply = QMessageBox.question(
            self, "确认卸载", "确定要卸载MySQL吗？\n这将删除所有MySQL数据和配置。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.log_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread = MySQLWorkerThread("uninstall", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def start_service(self):
        """启动服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MySQLWorkerThread("start_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def stop_service(self):
        """停止服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MySQLWorkerThread("stop_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def restart_service(self):
        """重启服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MySQLWorkerThread("restart_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def install_service(self):
        """安装服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MySQLWorkerThread("install_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def set_root_password(self):
        """设置root密码"""
        password = self.password_input.text().strip()
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码")
            return

        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MySQLWorkerThread("set_password", self.installer, password=password)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def apply_basic_config(self):
        """应用基本配置"""
        try:
            port = self.port_spin.value()
            max_connections = self.max_connections_spin.value()
            innodb_buffer = self.innodb_buffer_combo.currentText()

            success = self.config_manager.update_basic_config(
                port=port,
                max_connections=max_connections,
                innodb_buffer=innodb_buffer
            )

            if success:
                QMessageBox.information(self, "成功", "基本配置应用成功")
            else:
                QMessageBox.warning(self, "失败", "基本配置应用失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"配置应用出错: {str(e)}")

    def add_performance_config(self):
        """添加性能优化配置"""
        reply = QMessageBox.question(
            self, "确认添加", "确定要添加性能优化配置吗？\n这将修改MySQL配置文件。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            success = self.config_manager.add_performance_config()
            if success:
                QMessageBox.information(self, "成功", "性能优化配置添加成功")
            else:
                QMessageBox.warning(self, "失败", "性能优化配置添加失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加性能配置出错: {str(e)}")

    def add_security_config(self):
        """添加安全配置"""
        reply = QMessageBox.question(
            self, "确认添加", "确定要添加安全配置吗？\n这将修改MySQL配置文件。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            success = self.config_manager.add_security_config()
            if success:
                QMessageBox.information(self, "成功", "安全配置添加成功")
            else:
                QMessageBox.warning(self, "失败", "安全配置添加失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加安全配置出错: {str(e)}")

    def validate_config(self):
        """验证配置"""
        try:
            result = self.config_manager.validate_config()

            message = "配置验证结果:\n\n"
            if result['valid']:
                message += "✓ 配置文件有效\n"
            else:
                message += "✗ 配置文件存在问题\n"

            if result['errors']:
                message += "\n错误:\n"
                for error in result['errors']:
                    message += f"  - {error}\n"

            if result['warnings']:
                message += "\n警告:\n"
                for warning in result['warnings']:
                    message += f"  - {warning}\n"

            QMessageBox.information(self, "配置验证", message)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证配置出错: {str(e)}")

    def open_config_file(self):
        """打开配置文件"""
        try:
            config = self.config_manager.get_current_config()
            config_file = config.get('config_file')

            if config_file and os.path.exists(config_file):
                if sys.platform == "win32":
                    os.startfile(config_file)
                else:
                    subprocess.run(["xdg-open", config_file])
            else:
                QMessageBox.warning(self, "警告", "配置文件不存在")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开配置文件出错: {str(e)}")

    def clear_history(self):
        """清除历史记录"""
        self.history_table.setRowCount(0)

    def add_log(self, message: str):
        """添加日志"""
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.End)

    def on_operation_finished(self, success: bool, message: str):
        """操作完成回调"""
        self.progress_bar.setVisible(False)
        self.refresh_status()

        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "失败", message)

    def refresh_status(self):
        """刷新状态"""
        # 更新安装状态
        if self.installer.is_mysql_installed():
            self.install_status_label.setText("已安装")
            version = self.installer.get_mysql_version()
            if version:
                self.version_label.setText(version)
            else:
                self.version_label.setText("已安装")
        else:
            self.install_status_label.setText("未安装")
            self.version_label.setText("未安装")

        # 更新服务状态
        status = self.installer.get_service_status()
        status_text = status.get('status', 'unknown')
        self.service_status_label.setText(status_text)
        self.monitor_status_label.setText(status_text)

        # 更新配置信息
        config = self.config_manager.get_current_config()
        config_info = self.config_manager.get_config_summary()
        self.config_info_text.setPlainText(config_info)

        # 更新按钮状态
        is_installed = self.installer.is_mysql_installed()
        self.install_btn.setEnabled(not is_installed)
        self.uninstall_btn.setEnabled(is_installed)
        self.start_service_btn.setEnabled(is_installed and status_text != 'running')
        self.stop_service_btn.setEnabled(is_installed and status_text == 'running')
        self.restart_service_btn.setEnabled(is_installed)
        self.install_service_btn.setEnabled(is_installed)
        self.set_password_btn.setEnabled(is_installed)

        # 添加历史记录
        if status_text != 'unknown':
            self.add_history_record(status_text)

    def add_history_record(self, status_text: str):
        """添加历史记录"""
        import datetime

        row = self.history_table.rowCount()
        self.history_table.insertRow(row)

        # 时间
        time_item = QTableWidgetItem(datetime.datetime.now().strftime("%H:%M:%S"))
        self.history_table.setItem(row, 0, time_item)

        # 状态
        status_item = QTableWidgetItem(status_text)
        self.history_table.setItem(row, 1, status_item)

        # 连接数和查询数（这里可以根据实际情况实现）
        connections_item = QTableWidgetItem("N/A")
        self.history_table.setItem(row, 2, connections_item)

        queries_item = QTableWidgetItem("N/A")
        self.history_table.setItem(row, 3, queries_item)

        # 限制历史记录数量
        if self.history_table.rowCount() > 100:
            self.history_table.removeRow(0)