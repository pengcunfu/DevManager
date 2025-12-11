#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 管理图形界面模块
提供 Redis 的安装、配置、服务管理的图形界面
"""

import sys
import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QGroupBox, QGridLayout, QFormLayout,
    QProgressBar, QMessageBox, QSpinBox,
    QCheckBox, QComboBox, QFileDialog,
    QFrame, QScrollArea, QSplitter
)
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QFont, QPixmap, QPalette, QColor

from .redis_config import RedisConfigManager
from .redis_install import RedisInstaller


class RedisWorkerThread(QThread):
    """Redis 操作工作线程"""
    operation_finished = Signal(bool, str)
    progress_updated = Signal(int)
    status_updated = Signal(str)

    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
        self.is_running = True

    def run(self):
        """执行操作"""
        try:
            if self.is_running:
                if self.operation == 'install':
                    success, message = self.installer.install_redis()
                elif self.operation == 'uninstall':
                    success, message = self.installer.uninstall_redis()
                elif self.operation == 'install_service':
                    success, message = self.installer.install_service()
                elif self.operation == 'uninstall_service':
                    success, message = self.installer.uninstall_service()
                elif self.operation == 'start_service':
                    success, message = self.installer.start_service()
                elif self.operation == 'stop_service':
                    success, message = self.installer.stop_service()
                elif self.operation == 'restart_service':
                    success, message = self.installer.restart_service()
                else:
                    success, message = False, f"未知操作: {self.operation}"

                if self.is_running:
                    self.operation_finished.emit(success, message)

        except Exception as e:
            if self.is_running:
                self.operation_finished.emit(False, f"操作失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self.is_running = False


class RedisTab(QWidget):
    """Redis 管理主标签页"""

    def __init__(self):
        super().__init__()
        self.installer = RedisInstaller()
        self.config_manager = RedisConfigManager()
        self.worker_thread = None
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        
        # 创建选项卡
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

        # 状态监控标签页
        self.status_tab = self.create_status_tab()
        self.tab_widget.addTab(self.status_tab, "状态监控")

        layout.addWidget(self.tab_widget)

        # 创建状态栏
        self.create_status_bar(layout)

        self.setLayout(layout)

    def create_install_tab(self):
        """创建安装管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 安装信息组
        info_group = QGroupBox("安装信息")
        info_layout = QFormLayout()

        self.version_label = QLabel("检查中...")
        self.install_path_label = QLabel(self.installer.installation_path)

        info_layout.addRow("Redis 版本:", self.version_label)
        info_layout.addRow("安装路径:", self.install_path_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 安装操作组
        action_group = QGroupBox("安装操作")
        action_layout = QGridLayout()

        self.install_btn = QPushButton("安装 Redis")
        self.install_btn.clicked.connect(self.install_redis)
        self.install_btn.setMinimumHeight(40)

        self.uninstall_btn = QPushButton("卸载 Redis")
        self.uninstall_btn.clicked.connect(self.uninstall_redis)
        self.uninstall_btn.setMinimumHeight(40)

        self.check_install_btn = QPushButton("检查安装")
        self.check_install_btn.clicked.connect(self.check_installation)
        self.check_install_btn.setMinimumHeight(40)

        action_layout.addWidget(self.install_btn, 0, 0)
        action_layout.addWidget(self.uninstall_btn, 0, 1)
        action_layout.addWidget(self.check_install_btn, 1, 0, 1, 2)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()

        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMaximumHeight(150)

        log_layout.addWidget(self.install_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        tab.setLayout(layout)
        return tab

    def create_service_tab(self):
        """创建服务管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 服务状态组
        status_group = QGroupBox("服务状态")
        status_layout = QFormLayout()

        self.service_status_label = QLabel("检查中...")
        self.service_enabled_label = QLabel("检查中...")
        self.service_port_label = QLabel("6379")

        status_layout.addRow("服务状态:", self.service_status_label)
        status_layout.addRow("开机启动:", self.service_enabled_label)
        status_layout.addRow("监听端口:", self.service_port_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 服务控制组
        control_group = QGroupBox("服务控制")
        control_layout = QGridLayout()

        self.install_service_btn = QPushButton("安装服务")
        self.install_service_btn.clicked.connect(self.install_service)
        self.install_service_btn.setMinimumHeight(40)

        self.start_service_btn = QPushButton("启动服务")
        self.start_service_btn.clicked.connect(self.start_service)
        self.start_service_btn.setMinimumHeight(40)

        self.stop_service_btn = QPushButton("停止服务")
        self.stop_service_btn.clicked.connect(self.stop_service)
        self.stop_service_btn.setMinimumHeight(40)

        self.restart_service_btn = QPushButton("重启服务")
        self.restart_service_btn.clicked.connect(self.restart_service)
        self.restart_service_btn.setMinimumHeight(40)

        self.uninstall_service_btn = QPushButton("卸载服务")
        self.uninstall_service_btn.clicked.connect(self.uninstall_service)
        self.uninstall_service_btn.setMinimumHeight(40)

        control_layout.addWidget(self.install_service_btn, 0, 0)
        control_layout.addWidget(self.start_service_btn, 1, 0)
        control_layout.addWidget(self.stop_service_btn, 1, 1)
        control_layout.addWidget(self.restart_service_btn, 2, 0)
        control_layout.addWidget(self.uninstall_service_btn, 2, 1)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 服务操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()

        self.service_log = QTextEdit()
        self.service_log.setReadOnly(True)
        self.service_log.setMaximumHeight(150)

        log_layout.addWidget(self.service_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        tab.setLayout(layout)
        return tab

    def create_config_tab(self):
        """创建配置管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 配置文件信息
        config_info_group = QGroupBox("配置文件信息")
        config_info_layout = QFormLayout()

        self.config_file_label = QLabel("检查中...")
        self.config_modified_label = QLabel("检查中...")

        config_info_layout.addRow("配置文件:", self.config_file_label)
        config_info_layout.addRow("最后修改:", self.config_modified_label)

        config_info_group.setLayout(config_info_layout)
        layout.addWidget(config_info_group)

        # 基本配置
        basic_group = QGroupBox("基本配置")
        basic_layout = QFormLayout()

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(6379)

        self.bind_edit = QLineEdit()
        self.bind_edit.setText("127.0.0.1")

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600)
        self.timeout_spin.setValue(300)

        self.max_memory_combo = QComboBox()
        self.max_memory_combo.setEditable(True)
        self.max_memory_combo.addItems(["256mb", "512mb", "1gb", "2gb", "4gb"])
        self.max_memory_combo.setCurrentText("256mb")

        self.databases_spin = QSpinBox()
        self.databases_spin.setRange(1, 32)
        self.databases_spin.setValue(16)

        basic_layout.addRow("端口:", self.port_spin)
        basic_layout.addRow("绑定地址:", self.bind_edit)
        basic_layout.addRow("超时时间(秒):", self.timeout_spin)
        basic_layout.addRow("最大内存:", self.max_memory_combo)
        basic_layout.addRow("数据库数量:", self.databases_spin)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 性能优化配置
        performance_group = QGroupBox("性能优化")
        performance_layout = QVBoxLayout()

        self.enable_aof_cb = QCheckBox("启用 AOF 持久化")
        self.enable_aof_cb.setChecked(True)

        self.enable_rdb_cb = QCheckBox("启用 RDB 快照")
        self.enable_rdb_cb.setChecked(True)

        self.memory_policy_combo = QComboBox()
        self.memory_policy_combo.addItems([
            "noeviction", "allkeys-lru", "volatile-lru", "allkeys-random",
            "volatile-random", "volatile-ttl"
        ])
        self.memory_policy_combo.setCurrentText("allkeys-lru")

        performance_layout.addWidget(self.enable_aof_cb)
        performance_layout.addWidget(self.enable_rdb_cb)

        # 内存淘汰策略布局
        memory_policy_layout = QHBoxLayout()
        memory_policy_layout.addWidget(QLabel("内存淘汰策略:"))
        memory_policy_layout.addWidget(self.memory_policy_combo)
        performance_layout.addLayout(memory_policy_layout)

        performance_group.setLayout(performance_layout)
        layout.addWidget(performance_group)

        # 配置操作按钮
        config_btn_layout = QHBoxLayout()

        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.clicked.connect(self.load_config)

        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)

        self.validate_config_btn = QPushButton("验证配置")
        self.validate_config_btn.clicked.connect(self.validate_config)

        config_btn_layout.addWidget(self.load_config_btn)
        config_btn_layout.addWidget(self.save_config_btn)
        config_btn_layout.addWidget(self.validate_config_btn)

        layout.addLayout(config_btn_layout)

        # 配置日志
        config_log_group = QGroupBox("操作日志")
        config_log_layout = QVBoxLayout()

        self.config_log = QTextEdit()
        self.config_log.setReadOnly(True)
        self.config_log.setMaximumHeight(100)

        config_log_layout.addWidget(self.config_log)
        config_log_group.setLayout(config_log_layout)
        layout.addWidget(config_log_group)

        tab.setLayout(layout)
        return tab

    def create_status_tab(self):
        """创建状态监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 运行状态信息
        status_group = QGroupBox("运行状态")
        status_layout = QGridLayout()

        # 创建状态显示标签
        self.redis_running_label = QLabel("检查中...")
        self.redis_version_label = QLabel("检查中...")
        self.redis_pid_label = QLabel("检查中...")
        self.redis_uptime_label = QLabel("检查中...")
        self.redis_memory_label = QLabel("检查中...")
        self.redis_connections_label = QLabel("检查中...")
        self.redis_clients_label = QLabel("检查中...")
        self.redis_commands_label = QLabel("检查中...")

        status_layout.addWidget(QLabel("运行状态:"), 0, 0)
        status_layout.addWidget(self.redis_running_label, 0, 1)

        status_layout.addWidget(QLabel("版本:"), 1, 0)
        status_layout.addWidget(self.redis_version_label, 1, 1)

        status_layout.addWidget(QLabel("进程ID:"), 2, 0)
        status_layout.addWidget(self.redis_pid_label, 2, 1)

        status_layout.addWidget(QLabel("运行时间:"), 3, 0)
        status_layout.addWidget(self.redis_uptime_label, 3, 1)

        status_layout.addWidget(QLabel("内存使用:"), 0, 2)
        status_layout.addWidget(self.redis_memory_label, 0, 3)

        status_layout.addWidget(QLabel("连接数:"), 1, 2)
        status_layout.addWidget(self.redis_connections_label, 1, 3)

        status_layout.addWidget(QLabel("客户端数:"), 2, 2)
        status_layout.addWidget(self.redis_clients_label, 2, 3)

        status_layout.addWidget(QLabel("命令数:"), 3, 2)
        status_layout.addWidget(self.redis_commands_label, 3, 3)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 性能指标
        performance_group = QGroupBox("性能指标")
        performance_layout = QGridLayout()

        self.redis_hits_label = QLabel("检查中...")
        self.redis_misses_label = QLabel("检查中...")
        self.redis_keyspace_label = QLabel("检查中...")
        self.redis_ops_label = QLabel("检查中...")

        performance_layout.addWidget(QLabel("命中率:"), 0, 0)
        performance_layout.addWidget(self.redis_hits_label, 0, 1)

        performance_layout.addWidget(QLabel("未命中数:"), 1, 0)
        performance_layout.addWidget(self.redis_misses_label, 1, 1)

        performance_layout.addWidget(QLabel("键空间:"), 2, 0)
        performance_layout.addWidget(self.redis_keyspace_label, 2, 1)

        performance_layout.addWidget(QLabel("每秒操作:"), 3, 0)
        performance_layout.addWidget(self.redis_ops_label, 3, 1)

        performance_group.setLayout(performance_layout)
        layout.addWidget(performance_group)

        # 刷新按钮
        refresh_layout = QHBoxLayout()

        self.refresh_status_btn = QPushButton("刷新状态")
        self.refresh_status_btn.clicked.connect(self.refresh_detailed_status)
        self.refresh_status_btn.setMinimumHeight(40)

        self.auto_refresh_cb = QCheckBox("自动刷新 (10秒)")
        self.auto_refresh_cb.toggled.connect(self.toggle_auto_refresh)

        refresh_layout.addWidget(self.refresh_status_btn)
        refresh_layout.addWidget(self.auto_refresh_cb)
        refresh_layout.addStretch()

        layout.addLayout(refresh_layout)

        tab.setLayout(layout)
        return tab

    def create_status_bar(self, layout):
        """创建状态栏"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QHBoxLayout()

        self.status_label = QLabel("就绪")
        
        status_layout.addWidget(QLabel("状态:"))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

        # 设置定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)  # 每5秒刷新一次

    def install_redis(self):
        """安装 Redis"""
        self.run_worker_thread('install')

    def uninstall_redis(self):
        """卸载 Redis"""
        reply = QMessageBox.question(
            self, '确认卸载',
            '确定要卸载 Redis 吗？这将删除所有相关文件。',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.run_worker_thread('uninstall')

    def install_service(self):
        """安装服务"""
        self.run_worker_thread('install_service')

    def uninstall_service(self):
        """卸载服务"""
        reply = QMessageBox.question(
            self, '确认卸载',
            '确定要卸载 Redis 服务吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.run_worker_thread('uninstall_service')

    def start_service(self):
        """启动服务"""
        self.run_worker_thread('start_service')

    def stop_service(self):
        """停止服务"""
        self.run_worker_thread('stop_service')

    def restart_service(self):
        """重启服务"""
        self.run_worker_thread('restart_service')

    def run_worker_thread(self, operation):
        """运行工作线程"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()

        # 禁用按钮
        self.set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条

        # 创建并启动线程
        self.worker_thread = RedisWorkerThread(operation)
        self.worker_thread.installer = self.installer
        self.worker_thread.operation_finished.connect(self.on_operation_finished)
        self.worker_thread.start()

    def on_operation_finished(self, success, message):
        """操作完成回调"""
        # 恢复按钮
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

        # 更新状态
        if success:
            self.status_label.setText("操作成功")
        else:
            self.status_label.setText("操作失败")

        # 添加日志
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # 安装管理
            self.install_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        elif current_tab == 1:  # 服务管理
            self.service_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

        # 刷新状态
        self.refresh_status()

        # 显示消息框
        if success:
            QMessageBox.information(self, "操作成功", message)
        else:
            QMessageBox.warning(self, "操作失败", message)

    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        # 安装管理按钮
        self.install_btn.setEnabled(enabled)
        self.uninstall_btn.setEnabled(enabled)
        self.check_install_btn.setEnabled(enabled)

        # 服务管理按钮
        self.install_service_btn.setEnabled(enabled)
        self.start_service_btn.setEnabled(enabled)
        self.stop_service_btn.setEnabled(enabled)
        self.restart_service_btn.setEnabled(enabled)
        self.uninstall_service_btn.setEnabled(enabled)

    def check_installation(self):
        """检查安装状态"""
        if self.installer.check_redis_installed():
            version = self.installer.get_redis_version()
            self.version_label.setText(version or "已安装")
            self.install_log.append(f"[{time.strftime('%H:%M:%S')}] Redis 已安装: {version}")
        else:
            self.version_label.setText("未安装")
            self.install_log.append(f"[{time.strftime('%H:%M:%S')}] Redis 未安装")

    def load_config(self):
        """加载配置"""
        config = self.config_manager.get_current_config()

        if config:
            self.port_spin.setValue(int(config.get('port', 6379)))
            self.bind_edit.setText(config.get('bind', '127.0.0.1'))
            self.timeout_spin.setValue(int(config.get('timeout', 300)))
            self.max_memory_combo.setCurrentText(config.get('maxmemory', '256mb'))
            self.databases_spin.setValue(int(config.get('databases', 16)))

            self.config_file_label.setText(config.get('config_file', '未找到'))
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 配置加载成功")
        else:
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 无法加载配置文件")

    def save_config(self):
        """保存配置"""
        success = self.config_manager.update_basic_config(
            port=self.port_spin.value(),
            bind=self.bind_edit.text(),
            timeout=self.timeout_spin.value(),
            maxmemory=self.max_memory_combo.currentText()
        )

        if success:
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 配置保存成功")
        else:
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 配置保存失败")

    def validate_config(self):
        """验证配置"""
        result = self.config_manager.validate_config()

        if result['valid']:
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] ✓ 配置验证通过")
        else:
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] ✗ 配置验证失败")
            for error in result['errors']:
                self.config_log.append(f"  错误: {error}")

        for warning in result['warnings']:
            self.config_log.append(f"  警告: {warning}")

    def refresh_status(self):
        """刷新状态"""
        # 获取服务状态
        status = self.installer.get_service_status()

        # 更新安装标签页
        if status['installed']:
            self.version_label.setText(status['version'] or "已安装")
        else:
            self.version_label.setText("未安装")

        # 更新服务标签页
        if status['running']:
            self.service_status_label.setText("运行中")
        else:
            self.service_status_label.setText("已停止")

        self.service_enabled_label.setText("是" if status['enabled'] else "否")

        # 更新状态监控标签页
        self.redis_running_label.setText("运行中" if status['running'] else "已停止")
        
        if status['version']:
            self.redis_version_label.setText(status['version'])

        if status['pid']:
            self.redis_pid_label.setText(str(status['pid']))

        if status['uptime']:
            hours = status['uptime'] // 3600
            minutes = (status['uptime'] % 3600) // 60
            self.redis_uptime_label.setText(f"{hours}小时{minutes}分钟")

        if status['memory_usage']:
            self.redis_memory_label.setText(status['memory_usage'])

        self.redis_connections_label.setText(str(status['connections']))

    def refresh_detailed_status(self):
        """刷新详细状态"""
        self.refresh_status()
        self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 状态已刷新")

    def toggle_auto_refresh(self, checked):
        """切换自动刷新"""
        if checked:
            self.auto_refresh_timer = QTimer()
            self.auto_refresh_timer.timeout.connect(self.refresh_detailed_status)
            self.auto_refresh_timer.start(10000)  # 10秒
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 已启用自动刷新")
        else:
            if hasattr(self, 'auto_refresh_timer'):
                self.auto_refresh_timer.stop()
            self.config_log.append(f"[{time.strftime('%H:%M:%S')}] 已停止自动刷新")

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()

        if hasattr(self, 'auto_refresh_timer'):
            self.auto_refresh_timer.stop()

        event.accept()