#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO 管理标签页
提供 MinIO 安装、配置、服务管理的图形界面
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

from .minio_install import MinIOInstaller
from .minio_config import MinIOConfigManager


class MinIOWorkerThread(QThread):
    """MinIO操作工作线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, operation: str, installer: MinIOInstaller, **kwargs):
        super().__init__()
        self.operation = operation
        self.installer = installer
        self.kwargs = kwargs

    def run(self):
        """执行操作"""
        try:
            if self.operation == "install":
                self._install_minio()
            elif self.operation == "uninstall":
                self._uninstall_minio()
            elif self.operation == "start_service":
                self._start_service()
            elif self.operation == "stop_service":
                self._stop_service()
            elif self.operation == "restart_service":
                self._restart_service()
            elif self.operation == "install_service":
                self._install_service()
            elif self.operation == "check_requirements":
                self._check_requirements()
            else:
                self.finished_signal.emit(False, f"未知操作: {self.operation}")

        except Exception as e:
            self.log_signal.emit(f"操作失败: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def _install_minio(self):
        """安装MinIO"""
        self.log_signal.emit("开始安装MinIO...")
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

        # 下载MinIO
        self.log_signal.emit("正在下载MinIO...")
        installer_path = self.installer.download_minio()
        self.progress_signal.emit(50)

        if not installer_path:
            error_msg = "下载MinIO失败"
            self.log_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg)
            return

        # 安装MinIO
        self.log_signal.emit("正在安装MinIO...")
        success = self.installer.install_minio(installer_path)
        self.progress_signal.emit(80)

        if success:
            self.log_signal.emit("MinIO安装成功")
            self.finished_signal.emit(True, "MinIO安装成功")
        else:
            error_msg = "MinIO安装失败"
            self.log_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg)

        self.progress_signal.emit(100)

    def _uninstall_minio(self):
        """卸载MinIO"""
        self.log_signal.emit("开始卸载MinIO...")
        success = self.installer.uninstall_minio()

        if success:
            self.log_signal.emit("MinIO卸载成功")
            self.finished_signal.emit(True, "MinIO卸载成功")
        else:
            self.log_signal.emit("MinIO卸载失败")
            self.finished_signal.emit(False, "MinIO卸载失败")

    def _start_service(self):
        """启动服务"""
        self.log_signal.emit("正在启动MinIO服务...")
        success = self.installer.start_service()

        if success:
            self.log_signal.emit("MinIO服务启动成功")
            self.finished_signal.emit(True, "MinIO服务启动成功")
        else:
            self.log_signal.emit("MinIO服务启动失败")
            self.finished_signal.emit(False, "MinIO服务启动失败")

    def _stop_service(self):
        """停止服务"""
        self.log_signal.emit("正在停止MinIO服务...")
        success = self.installer.stop_service()

        if success:
            self.log_signal.emit("MinIO服务停止成功")
            self.finished_signal.emit(True, "MinIO服务停止成功")
        else:
            self.log_signal.emit("MinIO服务停止失败")
            self.finished_signal.emit(False, "MinIO服务停止失败")

    def _restart_service(self):
        """重启服务"""
        self.log_signal.emit("正在重启MinIO服务...")
        success = self.installer.restart_service()

        if success:
            self.log_signal.emit("MinIO服务重启成功")
            self.finished_signal.emit(True, "MinIO服务重启成功")
        else:
            self.log_signal.emit("MinIO服务重启失败")
            self.finished_signal.emit(False, "MinIO服务重启失败")

    def _install_service(self):
        """安装服务"""
        self.log_signal.emit("正在安装MinIO服务...")
        success = self.installer.install_service()

        if success:
            self.log_signal.emit("MinIO服务安装成功")
            self.finished_signal.emit(True, "MinIO服务安装成功")
        else:
            self.log_signal.emit("MinIO服务安装失败")
            self.finished_signal.emit(False, "MinIO服务安装失败")

    def _check_requirements(self):
        """检查安装要求"""
        self.log_signal.emit("检查安装要求...")
        requirements = self.installer.check_requirements()

        for req, satisfied in requirements.items():
            status = "✓" if satisfied else "✗"
            self.log_signal.emit(f"  {status} {req}")

        self.finished_signal.emit(True, "安装要求检查完成")


class MinIOTab(QWidget):
    """MinIO管理标签页"""

    def __init__(self):
        super().__init__()
        self.installer = MinIOInstaller()
        self.config_manager = MinIOConfigManager()
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

        info_layout.addWidget(QLabel("MinIO版本:"), 1, 2)
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
        self.install_btn = QPushButton("安装MinIO")
        self.install_btn.clicked.connect(self.install_minio)
        install_layout.addWidget(self.install_btn)

        # 卸载按钮
        self.uninstall_btn = QPushButton("卸载MinIO")
        self.uninstall_btn.clicked.connect(self.uninstall_minio)
        install_layout.addWidget(self.uninstall_btn)

        # 安装服务按钮
        self.install_service_btn = QPushButton("安装MinIO服务")
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

        # 访问信息组
        access_group = QGroupBox("访问信息")
        access_layout = QGridLayout(access_group)

        access_layout.addWidget(QLabel("API地址:"), 0, 0)
        self.api_url_label = QLabel("http://localhost:9000")
        access_layout.addWidget(self.api_url_label, 0, 1)

        access_layout.addWidget(QLabel("控制台:"), 0, 2)
        self.console_url_label = QLabel("http://localhost:9001")
        access_layout.addWidget(self.console_url_label, 0, 3)

        layout.addWidget(access_group)

        # 快速操作组
        quick_group = QGroupBox("快速操作")
        quick_layout = QHBoxLayout(quick_group)

        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.refresh_status)
        quick_layout.addWidget(refresh_btn)

        open_env_btn = QPushButton("打开环境配置")
        open_env_btn.clicked.connect(self.open_env_file)
        quick_layout.addWidget(open_env_btn)

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

        basic_layout.addWidget(QLabel("访问密钥:"), 0, 0)
        self.access_key_edit = QLineEdit()
        self.access_key_edit.setPlaceholderText("minioadmin")
        basic_layout.addWidget(self.access_key_edit, 0, 1)

        basic_layout.addWidget(QLabel("秘密密钥:"), 0, 2)
        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setEchoMode(QLineEdit.Password)
        self.secret_key_edit.setPlaceholderText("minioadmin")
        basic_layout.addWidget(self.secret_key_edit, 0, 3)

        basic_layout.addWidget(QLabel("服务端口:"), 1, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(9000)
        basic_layout.addWidget(self.port_spin, 1, 1)

        basic_layout.addWidget(QLabel("区域:"), 1, 2)
        self.region_combo = QComboBox()
        self.region_combo.setEditable(True)
        self.region_combo.addItems(["us-east-1", "us-west-1", "eu-west-1", "ap-southeast-1"])
        self.region_combo.setCurrentText("us-east-1")
        basic_layout.addWidget(self.region_combo, 1, 3)

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

        generate_env_btn = QPushButton("生成环境文件")
        generate_env_btn.clicked.connect(self.generate_env_file)
        config_ops_layout.addWidget(generate_env_btn)

        layout.addWidget(config_ops_group)

        # 配置信息组
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

        monitor_layout.addWidget(QLabel("版本信息:"), 1, 0)
        self.monitor_version_label = QLabel("未知")
        monitor_layout.addWidget(self.monitor_version_label, 1, 1)

        monitor_layout.addWidget(QLabel("系统架构:"), 1, 2)
        self.arch_label = QLabel(self.installer.architecture)
        monitor_layout.addWidget(self.arch_label, 1, 3)

        layout.addWidget(monitor_group)

        # 连接信息组
        connection_group = QGroupBox("连接信息")
        connection_layout = QGridLayout(connection_group)

        connection_layout.addWidget(QLabel("API端点:"), 0, 0)
        self.api_endpoint_label = QLabel("http://localhost:9000")
        self.api_endpoint_label.setWordWrap(True)
        connection_layout.addWidget(self.api_endpoint_label, 0, 1)

        connection_layout.addWidget(QLabel("控制台:"), 0, 2)
        self.console_label = QLabel("http://localhost:9001")
        connection_layout.addWidget(self.console_label, 0, 3)

        connection_layout.addWidget(QLabel("数据目录:"), 1, 0, 1, 2)
        self.data_dir_label = QLabel(os.path.join(self.installer.installation_path, 'data'))
        self.data_dir_label.setWordWrap(True)
        connection_layout.addWidget(self.data_dir_label, 1, 2)

        layout.addWidget(connection_group)

        # 快速链接组
        links_group = QGroupBox("快速链接")
        links_layout = QHBoxLayout(links_group)

        open_api_btn = QPushButton("打开API文档")
        open_api_btn.clicked.connect(self.open_api_docs)
        links_layout.addWidget(open_api_btn)

        open_console_btn = QPushButton("打开控制台")
        open_console_btn.clicked.connect(self.open_console)
        links_layout.addWidget(open_console_btn)

        layout.addWidget(links_group)

        layout.addStretch()
        return widget

    def check_requirements(self):
        """检查安装要求"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.requirements_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread = MinIOWorkerThread("check_requirements", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def install_minio(self):
        """安装MinIO"""
        reply = QMessageBox.question(
            self, "确认安装", "确定要安装MinIO吗？\n这将下载并安装MinIO对象存储服务。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.log_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread = MinIOWorkerThread("install", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def uninstall_minio(self):
        """卸载MinIO"""
        reply = QMessageBox.question(
            self, "确认卸载", "确定要卸载MinIO吗？\n这将删除所有MinIO数据和配置。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.log_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread = MinIOWorkerThread("uninstall", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def start_service(self):
        """启动服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MinIOWorkerThread("start_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def stop_service(self):
        """停止服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MinIOWorkerThread("stop_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def restart_service(self):
        """重启服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MinIOWorkerThread("restart_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def install_service(self):
        """安装服务"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = MinIOWorkerThread("install_service", self.installer)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.finished_signal.connect(self.on_operation_finished)
        self.worker_thread.start()

    def apply_basic_config(self):
        """应用基本配置"""
        try:
            access_key = self.access_key_edit.text().strip()
            secret_key = self.secret_key_edit.text().strip()
            port = self.port_spin.value()
            region = self.region_combo.currentText().strip()
            address = f":{port}"

            success = self.config_manager.update_basic_config(
                access_key=access_key,
                secret_key=secret_key,
                region=region,
                address=address
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
            self, "确认添加", "确定要添加性能优化配置吗？\n这将修改MinIO配置文件。",
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
            self, "确认添加", "确定要添加安全配置吗？\n这将修改MinIO配置文件。",
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

    def generate_env_file(self):
        """生成环境配置文件"""
        access_key = self.access_key_edit.text().strip() or "minioadmin"
        secret_key = self.secret_key_edit.text().strip() or "minioadmin"
        port = self.port_spin.value()
        address = f":{port}"
        data_dir = os.path.join(self.installer.installation_path, 'data')

        env_content = self.config_manager.generate_minio_env(
            access_key=access_key,
            secret_key=secret_key,
            data_dir=data_dir,
            address=address
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存环境配置文件", "minio.env", "环境文件 (*.env)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                QMessageBox.information(self, "成功", f"环境配置文件已保存: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")

    def open_env_file(self):
        """打开环境配置文件"""
        env_file = os.path.join(self.installer.installation_path, "minio.env")
        try:
            if os.path.exists(env_file):
                if sys.platform == "win32":
                    os.startfile(env_file)
                else:
                    subprocess.run(["xdg-open", env_file])
            else:
                QMessageBox.warning(self, "警告", "环境配置文件不存在")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开配置文件出错: {str(e)}")

    def open_api_docs(self):
        """打开API文档"""
        import webbrowser
        webbrowser.open("https://min.io/docs/minio/linux/operations/")

    def open_console(self):
        """打开MinIO控制台"""
        import webbrowser
        webbrowser.open("http://localhost:9001")

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
        if self.installer.is_minio_installed():
            self.install_status_label.setText("已安装")
            version = self.installer.get_minio_version()
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

        # 更新版本信息
        version = self.installer.get_minio_version()
        if version:
            self.monitor_version_label.setText(version)

        # 更新配置信息
        config_info = self.config_manager.get_config_summary()
        self.config_info_text.setPlainText(config_info)

        # 更新按钮状态
        is_installed = self.installer.is_minio_installed()
        self.install_btn.setEnabled(not is_installed)
        self.uninstall_btn.setEnabled(is_installed)
        self.start_service_btn.setEnabled(is_installed and status_text != 'running')
        self.stop_service_btn.setEnabled(is_installed and status_text == 'running')
        self.restart_service_btn.setEnabled(is_installed)
        self.install_service_btn.setEnabled(is_installed)