#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 图形化管理界面
提供 MongoDB 的安装、配置、服务管理和监控功能
"""

import os
import sys
import time
import json
import platform
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QMessageBox, QFileDialog,
    QComboBox, QSpinBox, QCheckBox, QFrame, QSplitter,
    QScrollArea, QFormLayout, QSlider, QToolTip
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor, QPixmap, QIcon

from .mongodb_install import MongoDBInstaller
from .mongodb_config import MongoDBConfigManager


class MongoDBWorkerThread(QThread):
    """MongoDB操作工作线程"""
    progress = Signal(str)
    log = Signal(str)
    finished = Signal(bool, str)
    status_updated = Signal(dict)

    def __init__(self, operation: str, installer, config_manager=None, **kwargs):
        super().__init__()
        self.operation = operation
        self.installer = installer
        self.config_manager = config_manager
        self.kwargs = kwargs

    def run(self):
        """执行操作"""
        try:
            if self.operation == "install":
                self._install_mongodb()
            elif self.operation == "uninstall":
                self._uninstall_mongodb()
            elif self.operation == "start_service":
                self._start_service()
            elif self.operation == "stop_service":
                self._stop_service()
            elif self.operation == "restart_service":
                self._restart_service()
            elif self.operation == "get_info":
                self._get_info()
            elif self.operation == "test_connection":
                self._test_connection()
            elif self.operation == "save_config":
                self._save_config()
            else:
                self.finished.emit(False, f"未知操作: {self.operation}")
        except Exception as e:
            self.log.emit(f"操作失败: {str(e)}")
            self.finished.emit(False, str(e))

    def _install_mongodb(self):
        """安装MongoDB"""
        self.progress.emit("正在检查安装要求...")
        self.log.emit("检查系统要求...")

        requirements = self.installer.check_requirements()

        # 检查要求
        if not requirements.get('internet', False):
            self.finished.emit(False, "网络连接不可用，无法下载MongoDB")
            return

        if not requirements.get('disk_space', False):
            self.finished.emit(False, "磁盘空间不足")
            return

        if not requirements.get('admin_privileges', False):
            self.log.emit("警告: 缺少管理员权限，可能无法安装服务")

        self.progress.emit("正在安装MongoDB...")
        self.log.emit("开始安装MongoDB...")

        if self.installer.install_mongodb():
            self.log.emit("MongoDB安装指导完成")
            self.progress.emit("安装完成")
            self.finished.emit(True, "MongoDB安装成功")
        else:
            self.finished.emit(False, "MongoDB安装失败")

    def _uninstall_mongodb(self):
        """卸载MongoDB"""
        self.progress.emit("正在卸载MongoDB...")
        self.log.emit("开始卸载MongoDB...")

        if self.installer.uninstall_mongodb():
            self.log.emit("MongoDB卸载指导完成")
            self.progress.emit("卸载完成")
            self.finished.emit(True, "MongoDB卸载成功")
        else:
            self.finished.emit(False, "MongoDB卸载失败")

    def _start_service(self):
        """启动服务"""
        self.progress.emit("正在启动MongoDB服务...")
        self.log.emit("启动MongoDB服务...")

        if self.installer.start_service():
            self.log.emit("MongoDB服务启动成功")
            self.progress.emit("服务已启动")
            self.finished.emit(True, "MongoDB服务启动成功")
        else:
            self.finished.emit(False, "MongoDB服务启动失败")

    def _stop_service(self):
        """停止服务"""
        self.progress.emit("正在停止MongoDB服务...")
        self.log.emit("停止MongoDB服务...")

        if self.installer.stop_service():
            self.log.emit("MongoDB服务停止成功")
            self.progress.emit("服务已停止")
            self.finished.emit(True, "MongoDB服务停止成功")
        else:
            self.finished.emit(False, "MongoDB服务停止失败")

    def _restart_service(self):
        """重启服务"""
        self.progress.emit("正在重启MongoDB服务...")
        self.log.emit("重启MongoDB服务...")

        if self.installer.restart_service():
            self.log.emit("MongoDB服务重启成功")
            self.progress.emit("服务已重启")
            self.finished.emit(True, "MongoDB服务重启成功")
        else:
            self.finished.emit(False, "MongoDB服务重启失败")

    def _get_info(self):
        """获取MongoDB信息"""
        self.progress.emit("正在获取MongoDB信息...")
        info = self.installer.get_mongodb_info()
        self.status_updated.emit(info)
        self.finished.emit(True, "获取信息成功")

    def _test_connection(self):
        """测试MongoDB连接"""
        self.progress.emit("正在测试MongoDB连接...")

        # 使用mongosh测试连接
        try:
            result = self.installer.test_connection()
            if result['success']:
                self.log.emit(f"连接测试成功: {result['message']}")
                self.finished.emit(True, "连接测试成功")
            else:
                self.log.emit(f"连接测试失败: {result['message']}")
                self.finished.emit(False, result['message'])
        except Exception as e:
            self.log.emit(f"连接测试出错: {str(e)}")
            self.finished.emit(False, str(e))

    def _save_config(self):
        """保存配置"""
        if not self.config_manager:
            self.finished.emit(False, "配置管理器未初始化")
            return

        config_file = self.kwargs.get('config_file')
        config_data = self.kwargs.get('config_data')

        self.progress.emit("正在保存配置...")
        self.log.emit("保存MongoDB配置...")

        try:
            if self.config_manager.save_config(config_data, config_file):
                self.log.emit("配置保存成功")
                self.progress.emit("配置已保存")
                self.finished.emit(True, "配置保存成功")
            else:
                self.finished.emit(False, "配置保存失败")
        except Exception as e:
            self.log.emit(f"保存配置出错: {str(e)}")
            self.finished.emit(False, str(e))


class MongoDBTab(QWidget):
    """MongoDB管理标签页"""

    def __init__(self):
        super().__init__()
        self.installer = MongoDBInstaller()
        self.config_manager = MongoDBConfigManager()
        self.worker_thread = None
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 安装管理标签页
        self.install_tab = self.create_install_tab()
        self.tab_widget.addTab(self.install_tab, "安装管理")

        # 服务管理标签页
        self.service_tab = self.create_service_tab()
        self.tab_widget.addTab(self.service_tab, "服务管理")

        # 配置管理标签页
        self.config_tab = self.create_config_tab()
        self.tab_widget.addTab(self.config_tab, "配置管理")

        # 监控信息标签页
        self.monitor_tab = self.create_monitor_tab()
        self.tab_widget.addTab(self.monitor_tab, "监控信息")

        layout.addWidget(self.tab_widget)

    def create_install_tab(self) -> QWidget:
        """创建安装管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 安装信息组
        info_group = QGroupBox("MongoDB 信息")
        info_layout = QFormLayout(info_group)

        # 版本选择
        self.version_combo = QComboBox()
        self.version_combo.addItems([
            "7.0.0", "6.0.0", "5.0.0", "4.4.0"
        ])
        self.version_combo.setCurrentText(self.installer.mongodb_version)
        info_layout.addRow("版本:", self.version_combo)

        # 安装路径
        self.install_path_edit = QLineEdit(self.installer.installation_path)
        install_path_btn = QPushButton("浏览")
        install_path_btn.clicked.connect(self.browse_install_path)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.install_path_edit)
        path_layout.addWidget(install_path_btn)
        info_layout.addRow("安装路径:", path_layout)

        layout.addWidget(info_group)

        # 系统要求组
        requirements_group = QGroupBox("系统要求")
        requirements_layout = QGridLayout(requirements_group)

        # 要求检查标签
        self.internet_label = QLabel("检查中...")
        self.disk_label = QLabel("检查中...")
        self.privileges_label = QLabel("检查中...")

        requirements_layout.addWidget(QLabel("网络连接:"), 0, 0)
        requirements_layout.addWidget(self.internet_label, 0, 1)

        requirements_layout.addWidget(QLabel("磁盘空间:"), 1, 0)
        requirements_layout.addWidget(self.disk_label, 1, 1)

        requirements_layout.addWidget(QLabel("管理员权限:"), 2, 0)
        requirements_layout.addWidget(self.privileges_label, 2, 1)

        layout.addWidget(requirements_group)

        # 安装操作按钮
        button_layout = QHBoxLayout()

        self.check_req_btn = QPushButton("检查系统要求")
        self.check_req_btn.clicked.connect(self.check_requirements)

        self.install_btn = QPushButton("安装 MongoDB")
        self.install_btn.clicked.connect(self.install_mongodb)
        
        self.uninstall_btn = QPushButton("卸载 MongoDB")
        self.uninstall_btn.clicked.connect(self.uninstall_mongodb)
        
        button_layout.addWidget(self.check_req_btn)
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.uninstall_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 安装状态
        self.install_status_label = QLabel("准备就绪")
        self.install_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.install_status_label)

        # 进度条
        self.install_progress = QProgressBar()
        self.install_progress.setVisible(False)
        layout.addWidget(self.install_progress)

        # 日志区域
        log_group = QGroupBox("安装日志")
        log_layout = QVBoxLayout(log_group)

        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMaximumHeight(150)
        self.install_log.setFont(QFont("Consolas", 9))

        log_layout.addWidget(self.install_log)
        layout.addWidget(log_group)

        # 初始化检查
        self.check_requirements()

        return widget

    def create_service_tab(self) -> QWidget:
        """创建服务管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 服务状态组
        status_group = QGroupBox("服务状态")
        status_layout = QFormLayout(status_group)

        self.service_status_label = QLabel("检查中...")
        self.service_version_label = QLabel("检查中...")
        self.service_install_label = QLabel("检查中...")

        status_layout.addRow("服务状态:", self.service_status_label)
        status_layout.addRow("MongoDB版本:", self.service_version_label)
        status_layout.addRow("安装状态:", self.service_install_label)

        layout.addWidget(status_group)

        # 服务操作按钮
        control_group = QGroupBox("服务控制")
        control_layout = QGridLayout(control_group)

        self.start_service_btn = QPushButton("启动服务")
        self.start_service_btn.clicked.connect(self.start_service)
        
        self.stop_service_btn = QPushButton("停止服务")
        self.stop_service_btn.clicked.connect(self.stop_service)
        
        self.restart_service_btn = QPushButton("重启服务")
        self.restart_service_btn.clicked.connect(self.restart_service)
        
        control_layout.addWidget(self.start_service_btn, 0, 0)
        control_layout.addWidget(self.stop_service_btn, 0, 1)
        control_layout.addWidget(self.restart_service_btn, 0, 2)

        layout.addWidget(control_group)

        # 连接测试
        connection_group = QGroupBox("连接测试")
        connection_layout = QVBoxLayout(connection_group)

        # 连接参数
        param_layout = QFormLayout()

        self.connection_host_edit = QLineEdit("localhost")
        self.connection_port_edit = QLineEdit("27017")

        param_layout.addRow("主机:", self.connection_host_edit)
        param_layout.addRow("端口:", self.connection_port_edit)

        connection_layout.addLayout(param_layout)

        # 测试按钮
        self.test_connection_btn = QPushButton("测试连接")
        self.test_connection_btn.clicked.connect(self.test_connection)
        
        connection_layout.addWidget(self.test_connection_btn)

        layout.addWidget(connection_group)

        # 服务日志
        log_group = QGroupBox("服务日志")
        log_layout = QVBoxLayout(log_group)

        self.service_log = QTextEdit()
        self.service_log.setReadOnly(True)
        self.service_log.setMaximumHeight(120)
        self.service_log.setFont(QFont("Consolas", 9))

        log_layout.addWidget(self.service_log)
        layout.addWidget(log_group)

        # 服务状态
        self.service_status_label2 = QLabel("就绪")
        self.service_status_label2.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.service_status_label2)

        # 进度条
        self.service_progress = QProgressBar()
        self.service_progress.setVisible(False)
        layout.addWidget(self.service_progress)

        layout.addStretch()

        return widget

    def create_config_tab(self) -> QWidget:
        """创建配置管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 配置文件选择
        file_group = QGroupBox("配置文件")
        file_layout = QHBoxLayout(file_group)

        self.config_file_combo = QComboBox()
        self.config_file_combo.setMinimumWidth(300)
        self.config_file_combo.currentTextChanged.connect(self.load_config_file)

        self.browse_config_btn = QPushButton("浏览")
        self.browse_config_btn.clicked.connect(self.browse_config_file)

        self.reload_config_btn = QPushButton("重新加载")
        self.reload_config_btn.clicked.connect(self.load_current_config)

        file_layout.addWidget(QLabel("配置文件:"))
        file_layout.addWidget(self.config_file_combo)
        file_layout.addWidget(self.browse_config_btn)
        file_layout.addWidget(self.reload_config_btn)

        layout.addWidget(file_group)

        # 配置编辑区域 - 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧：配置编辑
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 网络配置
        net_group = QGroupBox("网络配置")
        net_layout = QFormLayout(net_group)

        self.net_port_edit = QLineEdit("27017")
        self.net_bind_ip_edit = QLineEdit("127.0.0.1")

        net_layout.addRow("端口:", self.net_port_edit)
        net_layout.addRow("绑定IP:", self.net_bind_ip_edit)

        left_layout.addWidget(net_group)

        # 存储配置
        storage_group = QGroupBox("存储配置")
        storage_layout = QFormLayout(storage_group)

        self.storage_db_path_edit = QLineEdit("/var/lib/mongodb")
        self.storage_journal_edit = QLineEdit("true")

        storage_layout.addRow("数据路径:", self.storage_db_path_edit)
        storage_layout.addRow("日志启用:", self.storage_journal_edit)

        left_layout.addWidget(storage_group)

        # 系统日志配置
        log_group = QGroupBox("系统日志")
        log_layout = QFormLayout(log_group)

        self.log_path_edit = QLineEdit("/var/log/mongodb/mongod.log")
        self.log_append_edit = QLineEdit("true")

        log_layout.addRow("日志路径:", self.log_path_edit)
        log_layout.addRow("追加模式:", self.log_append_edit)

        left_layout.addWidget(log_group)

        splitter.addWidget(left_widget)

        # 右侧：配置预览
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        preview_label = QLabel("配置预览:")
        preview_label.setFont(QFont("", 10, QFont.Bold))
        right_layout.addWidget(preview_label)

        self.config_preview = QTextEdit()
        self.config_preview.setReadOnly(True)
        self.config_preview.setFont(QFont("Consolas", 9))
        self.config_preview.setMaximumHeight(300)
        right_layout.addWidget(self.config_preview)

        # 配置说明
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setPlainText("""
MongoDB配置说明:

1. net.network配置:
   - port: MongoDB服务端口 (默认27017)
   - bindIp: 绑定的IP地址

2. storage配置:
   - dbPath: 数据文件存储路径
   - journal: 是否启用日志

3. systemLog配置:
   - path: 日志文件路径
   - logAppend: 是否追加日志

注意: 修改配置后需要重启MongoDB服务生效。
        """)
        right_layout.addWidget(info_text)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])

        # 操作按钮
        button_layout = QHBoxLayout()

        self.validate_config_btn = QPushButton("验证配置")
        self.validate_config_btn.clicked.connect(self.validate_config)

        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)
        
        button_layout.addWidget(self.validate_config_btn)
        button_layout.addWidget(self.save_config_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 加载配置文件列表
        self.load_config_files()

        return widget

    def create_monitor_tab(self) -> QWidget:
        """创建监控信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 数据库信息
        info_group = QGroupBox("数据库信息")
        info_layout = QFormLayout(info_group)

        self.monitor_status_label = QLabel("检查中...")
        self.monitor_version_label = QLabel("检查中...")
        self.monitor_uptime_label = QLabel("检查中...")

        info_layout.addRow("服务状态:", self.monitor_status_label)
        info_layout.addRow("MongoDB版本:", self.monitor_version_label)
        info_layout.addRow("运行时间:", self.monitor_uptime_label)

        layout.addWidget(info_group)

        # 性能指标
        perf_group = QGroupBox("性能指标")
        perf_layout = QGridLayout(perf_group)

        # 连接数
        self.connections_label = QLabel("0")
        perf_layout.addWidget(QLabel("当前连接数:"), 0, 0)
        perf_layout.addWidget(self.connections_label, 0, 1)

        # 数据库大小
        self.db_size_label = QLabel("0 MB")
        perf_layout.addWidget(QLabel("数据库大小:"), 1, 0)
        perf_layout.addWidget(self.db_size_label, 1, 1)

        # 集合数量
        self.collections_label = QLabel("0")
        perf_layout.addWidget(QLabel("集合数量:"), 2, 0)
        perf_layout.addWidget(self.collections_label, 2, 1)

        # 文档数量
        self.documents_label = QLabel("0")
        perf_layout.addWidget(QLabel("文档数量:"), 3, 0)
        perf_layout.addWidget(self.documents_label, 3, 1)

        layout.addWidget(perf_group)

        # 数据库列表
        db_group = QGroupBox("数据库列表")
        db_layout = QVBoxLayout(db_group)

        self.database_table = QTableWidget()
        self.database_table.setColumnCount(4)
        self.database_table.setHorizontalHeaderLabels(["数据库名", "大小", "集合数", "文档数"])

        header = self.database_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.database_table.setAlternatingRowColors(True)
        self.database_table.setSelectionBehavior(QTableWidget.SelectRows)

        db_layout.addWidget(self.database_table)
        layout.addWidget(db_group)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.refresh_monitor_btn = QPushButton("刷新信息")
        self.refresh_monitor_btn.clicked.connect(self.refresh_monitor_info)
        
        self.open_shell_btn = QPushButton("打开 Shell")
        self.open_shell_btn.clicked.connect(self.open_mongo_shell)
        
        button_layout.addWidget(self.refresh_monitor_btn)
        button_layout.addWidget(self.open_shell_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        layout.addStretch()

        # 初始加载
        self.refresh_monitor_info()

        return widget

    def browse_install_path(self):
        """浏览安装路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择MongoDB安装路径", self.install_path_edit.text()
        )
        if path:
            self.install_path_edit.setText(path)

    def check_requirements(self):
        """检查系统要求"""
        requirements = self.installer.check_requirements()

        # 更新界面显示
        if requirements.get('internet', False):
            self.internet_label.setText("✓ 可用")
        else:
            self.internet_label.setText("✗ 不可用")

        if requirements.get('disk_space', False):
            self.disk_label.setText("✓ 充足")
        else:
            self.disk_label.setText("✗ 不足")

        if requirements.get('admin_privileges', False):
            self.privileges_label.setText("✓ 具备管理员权限")
        else:
            self.privileges_label.setText("⚠ 缺少管理员权限")

        # 更新按钮状态
        can_install = all(requirements.values())
        self.install_btn.setEnabled(can_install)

    def install_mongodb(self):
        """安装MongoDB"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        # 更新版本设置
        self.installer.mongodb_version = self.version_combo.currentText()
        self.installer.installation_path = self.install_path_edit.text()

        # 禁用按钮
        self.install_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)
        self.check_req_btn.setEnabled(False)

        # 显示进度
        self.install_progress.setVisible(True)
        self.install_progress.setValue(0)

        # 启动工作线程
        self.worker_thread = MongoDBWorkerThread("install", self.installer)
        self.worker_thread.progress.connect(self.update_install_progress)
        self.worker_thread.log.connect(self.append_install_log)
        self.worker_thread.finished.connect(self.on_install_finished)
        self.worker_thread.start()

    def uninstall_mongodb(self):
        """卸载MongoDB"""
        reply = QMessageBox.question(
            self, "确认卸载",
            "确定要卸载MongoDB吗？这将删除所有MongoDB相关文件。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if self.worker_thread and self.worker_thread.isRunning():
            return

        # 禁用按钮
        self.install_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)
        self.check_req_btn.setEnabled(False)

        # 显示进度
        self.install_progress.setVisible(True)
        self.install_progress.setValue(0)

        # 启动工作线程
        self.worker_thread = MongoDBWorkerThread("uninstall", self.installer)
        self.worker_thread.progress.connect(self.update_install_progress)
        self.worker_thread.log.connect(self.append_install_log)
        self.worker_thread.finished.connect(self.on_install_finished)
        self.worker_thread.start()

    def on_install_finished(self, success: bool, message: str):
        """安装完成处理"""
        # 隐藏进度
        self.install_progress.setVisible(False)

        # 重新启用按钮
        self.install_btn.setEnabled(True)
        self.uninstall_btn.setEnabled(True)
        self.check_req_btn.setEnabled(True)

        # 更新状态
        if success:
            self.install_status_label.setText(f"✓ {message}")
        else:
            self.install_status_label.setText(f"✗ {message}")

        # 刷新状态
        self.refresh_status()

    def start_service(self):
        """启动服务"""
        self.run_service_operation("start_service")

    def stop_service(self):
        """停止服务"""
        self.run_service_operation("stop_service")

    def restart_service(self):
        """重启服务"""
        self.run_service_operation("restart_service")

    def test_connection(self):
        """测试连接"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        # 禁用按钮
        self.test_connection_btn.setEnabled(False)

        # 显示进度
        self.service_progress.setVisible(True)
        self.service_progress.setValue(0)

        # 设置连接参数
        host = self.connection_host_edit.text()
        port = self.connection_port_edit.text()

        # 启动工作线程
        self.worker_thread = MongoDBWorkerThread(
            "test_connection",
            self.installer,
            host=host,
            port=port
        )
        self.worker_thread.progress.connect(self.update_service_progress)
        self.worker_thread.log.connect(self.append_service_log)
        self.worker_thread.finished.connect(self.on_connection_test_finished)
        self.worker_thread.start()

    def on_connection_test_finished(self, success: bool, message: str):
        """连接测试完成处理"""
        # 隐藏进度
        self.service_progress.setVisible(False)

        # 重新启用按钮
        self.test_connection_btn.setEnabled(True)

        # 更新状态
        if success:
            self.service_status_label2.setText("✓ 连接测试成功")
        else:
            self.service_status_label2.setText(f"✗ 连接测试失败: {message}")

    def run_service_operation(self, operation: str):
        """运行服务操作"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        # 禁用服务按钮
        self.start_service_btn.setEnabled(False)
        self.stop_service_btn.setEnabled(False)
        self.restart_service_btn.setEnabled(False)

        # 显示进度
        self.service_progress.setVisible(True)
        self.service_progress.setValue(0)

        # 启动工作线程
        self.worker_thread = MongoDBWorkerThread(operation, self.installer)
        self.worker_thread.progress.connect(self.update_service_progress)
        self.worker_thread.log.connect(self.append_service_log)
        self.worker_thread.finished.connect(self.on_service_operation_finished)
        self.worker_thread.start()

    def on_service_operation_finished(self, success: bool, message: str):
        """服务操作完成处理"""
        # 隐藏进度
        self.service_progress.setVisible(False)

        # 重新启用按钮
        self.start_service_btn.setEnabled(True)
        self.stop_service_btn.setEnabled(True)
        self.restart_service_btn.setEnabled(True)

        # 更新状态
        if success:
            self.service_status_label2.setText(f"✓ {message}")
        else:
            self.service_status_label2.setText(f"✗ {message}")

        # 刷新状态
        self.refresh_status()

    def load_config_files(self):
        """加载配置文件列表"""
        config_files = self.config_manager.get_config_files()
        self.config_file_combo.clear()

        if config_files:
            for file_path in config_files:
                self.config_file_combo.addItem(file_path)

            # 加载第一个配置文件
            if config_files:
                self.load_config_file(config_files[0])

    def load_config_file(self, file_path: str):
        """加载配置文件内容"""
        if not file_path:
            return

        try:
            config = self.config_manager.read_config(file_path)
            if config:
                # 更新编辑框
                net_config = config.get('net', {})
                self.net_port_edit.setText(str(net_config.get('port', '27017')))
                self.net_bind_ip_edit.setText(net_config.get('bindIp', '127.0.0.1'))

                storage_config = config.get('storage', {})
                self.storage_db_path_edit.setText(storage_config.get('dbPath', '/var/lib/mongodb'))
                self.storage_journal_edit.setText(str(storage_config.get('journal', {}).get('enabled', True)).lower())

                system_log_config = config.get('systemLog', {})
                self.log_path_edit.setText(system_log_config.get('path', '/var/log/mongodb/mongod.log'))
                self.log_append_edit.setText(str(system_log_config.get('logAppend', True)).lower())

                # 更新预览
                self.update_config_preview()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置文件失败：{str(e)}")

    def browse_config_file(self):
        """浏览配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择MongoDB配置文件", "", "配置文件 (*.conf *.cfg);;所有文件 (*.*)"
        )
        if file_path:
            self.config_file_combo.addItem(file_path)
            self.config_file_combo.setCurrentText(file_path)
            self.load_config_file(file_path)

    def load_current_config(self):
        """重新加载当前配置文件"""
        current_file = self.config_file_combo.currentText()
        if current_file:
            self.load_config_file(current_file)

    def update_config_preview(self):
        """更新配置预览"""
        try:
            # 构建配置
            config = {
                'net': {
                    'port': int(self.net_port_edit.text()),
                    'bindIp': self.net_bind_ip_edit.text()
                },
                'storage': {
                    'dbPath': self.storage_db_path_edit.text(),
                    'journal': {
                        'enabled': self.storage_journal_edit.text().lower() == 'true'
                    }
                },
                'systemLog': {
                    'path': self.log_path_edit.text(),
                    'logAppend': self.log_append_edit.text().lower() == 'true'
                }
            }

            # 生成配置文本
            config_text = self.config_manager.generate_config_text(config)
            self.config_preview.setPlainText(config_text)
        except Exception as e:
            self.config_preview.setPlainText(f"配置生成错误: {str(e)}")

    def validate_config(self):
        """验证配置"""
        try:
            # 获取配置值
            port = int(self.net_port_edit.text())
            if port < 1 or port > 65535:
                raise ValueError("端口号必须在1-65535范围内")

            # 验证路径
            db_path = self.storage_db_path_edit.text()
            if not db_path.strip():
                raise ValueError("数据库路径不能为空")

            log_path = self.log_path_edit.text()
            if not log_path.strip():
                raise ValueError("日志路径不能为空")

            # 如果所有验证通过
            QMessageBox.information(self, "配置验证", "配置验证通过！")
        except ValueError as e:
            QMessageBox.warning(self, "配置验证", f"配置验证失败：{str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "配置验证", f"配置验证出错：{str(e)}")

    def save_config(self):
        """保存配置"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        try:
            # 构建配置
            config = {
                'net': {
                    'port': int(self.net_port_edit.text()),
                    'bindIp': self.net_bind_ip_edit.text()
                },
                'storage': {
                    'dbPath': self.storage_db_path_edit.text(),
                    'journal': {
                        'enabled': self.storage_journal_edit.text().lower() == 'true'
                    }
                },
                'systemLog': {
                    'path': self.log_path_edit.text(),
                    'logAppend': self.log_append_edit.text().lower() == 'true'
                }
            }

            config_file = self.config_file_combo.currentText()

            # 启动工作线程保存配置
            self.worker_thread = MongoDBWorkerThread(
                "save_config",
                self.installer,
                self.config_manager,
                config_file=config_file,
                config_data=config
            )
            self.worker_thread.finished.connect(self.on_config_saved)
            self.worker_thread.start()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败：{str(e)}")

    def on_config_saved(self, success: bool, message: str):
        """配置保存完成处理"""
        if success:
            QMessageBox.information(self, "成功", "配置保存成功！\n\n注意：需要重启MongoDB服务使配置生效。")
        else:
            QMessageBox.warning(self, "错误", f"配置保存失败：{message}")

    def refresh_monitor_info(self):
        """刷新监控信息"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        # 启动工作线程获取信息
        self.worker_thread = MongoDBWorkerThread("get_info", self.installer)
        self.worker_thread.status_updated.connect(self.update_monitor_info)
        self.worker_thread.start()

    def update_monitor_info(self, info: dict):
        """更新监控信息"""
        # 更新基本信息
        installed = info.get('installed', False)
        version = info.get('version', '未知')
        service_status = info.get('service_status', {})
        status = service_status.get('status', 'unknown')

        # 更新标签
        self.monitor_version_label.setText(version if version else "未安装")

        if installed:
            self.monitor_status_label.setText(
                "运行中" if status == "running" else
                "已停止" if status == "stopped" else
                "未知"
            )
        else:
            self.monitor_status_label.setText("未安装")

        # 更新运行时间
        self.monitor_uptime_label.setText("获取中...")

        # 获取更详细的信息
        self._get_detailed_info()

    def _get_detailed_info(self):
        """获取详细信息"""
        try:
            # 这里可以连接MongoDB获取更详细的信息
            # 目前使用模拟数据
            import random

            # 更新性能指标
            self.connections_label.setText(str(random.randint(5, 50)))
            self.db_size_label.setText(f"{random.randint(100, 5000)} MB")
            self.collections_label.setText(str(random.randint(10, 100)))
            self.documents_label.setText(str(random.randint(1000, 50000)))

            # 更新数据库列表
            self.update_database_table()

        except Exception:
            # 如果无法获取详细信息，显示默认值
            self.connections_label.setText("无法获取")
            self.db_size_label.setText("无法获取")
            self.collections_label.setText("无法获取")
            self.documents_label.setText("无法获取")

    def update_database_table(self):
        """更新数据库列表表格"""
        # 模拟数据库数据
        databases = [
            ("admin", "1 MB", "3", "50"),
            ("config", "2 MB", "5", "120"),
            ("local", "10 MB", "8", "200"),
            ("test", "50 MB", "12", "1500"),
        ]

        self.database_table.setRowCount(len(databases))

        for row, (name, size, collections, documents) in enumerate(databases):
            self.database_table.setItem(row, 0, QTableWidgetItem(name))
            self.database_table.setItem(row, 1, QTableWidgetItem(size))
            self.database_table.setItem(row, 2, QTableWidgetItem(collections))
            self.database_table.setItem(row, 3, QTableWidgetItem(documents))

    def open_mongo_shell(self):
        """打开MongoDB Shell"""
        try:
            import subprocess
            subprocess.Popen(['mongosh'], shell=True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开MongoDB Shell：{str(e)}")

    def refresh_status(self):
        """刷新所有状态信息"""
        # 刷新安装状态
        self.check_requirements()

        # 刷新服务状态
        self._refresh_service_status()

        # 刷新监控信息
        self.refresh_monitor_info()

    def _refresh_service_status(self):
        """刷新服务状态"""
        try:
            status = self.installer.get_service_status()
            version = self.installer.get_mongodb_version()
            installed = self.installer.is_mongodb_installed()

            # 更新服务标签页状态
            status_text = status.get('status', 'unknown')
            self.service_status_label.setText(
                "运行中" if status_text == "running" else
                "已停止" if status_text == "stopped" else
                "未知"
            )

            
            self.service_version_label.setText(version if version else "未安装")
            self.service_install_label.setText("已安装" if installed else "未安装")

            # 更新安装状态
            if installed:
                self.install_status_label.setText("MongoDB已安装")
                self.install_btn.setText("重新安装")
            else:
                self.install_status_label.setText("MongoDB未安装")
                self.install_btn.setText("安装 MongoDB")

        except Exception as e:
            self.service_status_label.setText("获取状态失败")
            
    def update_install_progress(self, message: str):
        """更新安装进度"""
        self.install_status_label.setText(message)
        self.install_progress.setValue(50)  # 简单进度显示

    def update_service_progress(self, message: str):
        """更新服务操作进度"""
        self.service_status_label2.setText(message)
        self.service_progress.setValue(50)  # 简单进度显示

    def append_install_log(self, message: str):
        """添加安装日志"""
        self.install_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        cursor = self.install_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.install_log.setTextCursor(cursor)

    def append_service_log(self, message: str):
        """添加服务日志"""
        self.service_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        cursor = self.service_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.service_log.setTextCursor(cursor)