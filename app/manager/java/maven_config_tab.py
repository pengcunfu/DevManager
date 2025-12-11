#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maven 配置页面 GUI
提供图形化的 Maven 镜像源配置功能
"""

import sys
import time
import threading
import shutil
from typing import Dict, Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QGroupBox, QMessageBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

from .maven_config import MavenConfigurator


class MavenMirrorTestThread(QThread):
    """Maven镜像源测试线程"""
    progress_signal = Signal(str)  # 测试进度信号
    result_signal = Signal(list)  # 测试结果信号

    def __init__(self, configurator: MavenConfigurator, timeout: int = 10):
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


class MavenConfigTab(QWidget):
    """Maven 配置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configurator = MavenConfigurator()
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
        title = QLabel("Maven 镜像源配置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 当前配置信息组
        current_group = QGroupBox("当前配置")
        current_layout = QVBoxLayout(current_group)

        self.maven_version_label = QLabel("Maven 版本: 加载中...")
        self.m2_dir_label = QLabel("M2 目录: 加载中...")
        self.config_file_label = QLabel("配置文件: 加载中...")
        self.current_mirror_label = QLabel("当前镜像源: 加载中...")
        self.local_repo_label = QLabel("本地仓库: 加载中...")

        current_layout.addWidget(self.maven_version_label)
        current_layout.addWidget(self.m2_dir_label)
        current_layout.addWidget(self.config_file_label)
        current_layout.addWidget(self.current_mirror_label)
        current_layout.addWidget(self.local_repo_label)

        layout.addWidget(current_group)

        # 镜像源选择组
        select_group = QGroupBox("选择镜像源")
        select_layout = QVBoxLayout(select_group)

        # 镜像源下拉框
        self.mirror_combo = QComboBox()
        self.populate_mirror_combo()
        select_layout.addWidget(self.mirror_combo)

        # 配置按钮
        config_btn = QPushButton("应用配置")
        config_btn.clicked.connect(self.configure_mirror)
        select_layout.addWidget(config_btn)

        # 恢复官方源按钮
        official_btn = QPushButton("恢复官方源")
        official_btn.clicked.connect(lambda: self.configure_mirror('official'))
        select_layout.addWidget(official_btn)

        layout.addWidget(select_group)

        # 本地仓库配置组
        repo_group = QGroupBox("本地仓库配置")
        repo_layout = QGridLayout(repo_group)

        repo_label = QLabel("仓库路径:")
        self.repo_path_edit = QLineEdit()
        self.repo_path_edit.setPlaceholderText("自定义本地仓库路径")
        repo_layout.addWidget(repo_label, 0, 0)
        repo_layout.addWidget(self.repo_path_edit, 0, 1)

        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_repository)
        repo_layout.addWidget(browse_btn, 0, 2)

        apply_repo_btn = QPushButton("应用路径")
        apply_repo_btn.clicked.connect(self.apply_repository_path)
        repo_layout.addWidget(apply_repo_btn, 1, 0, 1, 3)

        layout.addWidget(repo_group)

        # 操作按钮组
        button_group = QGroupBox("快捷操作")
        button_layout = QGridLayout(button_group)

        # 刷新配置按钮
        refresh_btn = QPushButton("刷新配置")
        refresh_btn.clicked.connect(self.load_current_config)
        button_layout.addWidget(refresh_btn, 0, 0)

        # 打开配置文件按钮
        open_config_btn = QPushButton("打开配置文件")
        open_config_btn.clicked.connect(self.open_config_file)
        button_layout.addWidget(open_config_btn, 0, 1)

        # 清理仓库按钮
        clean_btn = QPushButton("清理仓库缓存")
        clean_btn.clicked.connect(self.clean_repository)
        button_layout.addWidget(clean_btn, 1, 0)

        # 重置配置按钮
        reset_btn = QPushButton("重置配置")
        reset_btn.clicked.connect(self.reset_configuration)
        button_layout.addWidget(reset_btn, 1, 1)

        layout.addWidget(button_group)

        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout(help_group)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(120)
        help_text.setPlainText("1. 选择镜像源：从下拉框中选择合适的镜像源\n"
                             "2. 应用配置：点击\"应用配置\"按钮\n"
                             "3. 测试速度：在右侧面板测试各镜像源速度\n"
                             "4. 本地仓库：可自定义本地Maven仓库路径\n"
                             "5. 恢复默认：点击\"恢复官方源\"使用默认源\n\n"
                             "建议：选择响应速度最快的镜像源以获得最佳下载体验。")
        help_layout.addWidget(help_text)

        layout.addWidget(help_group)
        layout.addStretch()

        return panel

    def create_test_panel(self) -> QWidget:
        """创建测试面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("镜像源速度测试")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 测试控制组
        control_group = QGroupBox("测试控制")
        control_layout = QHBoxLayout(control_group)

        # 开始测试按钮
        self.test_btn = QPushButton("开始测试")
        self.test_btn.clicked.connect(self.start_test)
        control_layout.addWidget(self.test_btn)

        # 停止测试按钮
        self.stop_btn = QPushButton("停止测试")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)

        layout.addWidget(control_group)

        # 测试结果表格
        result_group = QGroupBox("测试结果")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.setup_result_table()
        result_layout.addWidget(self.result_table)

        layout.addWidget(result_group)

        # 测试状态
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)

        return panel

    def populate_mirror_combo(self):
        """填充镜像源下拉框"""
        self.mirror_combo.clear()

        # 按推荐顺序排序
        recommended_order = ['aliyun', 'tencent', 'huawei', 'netease', 'ustc', 'official']

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
            # 检查Maven是否安装
            if not self.configurator.check_maven_installed():
                self.maven_version_label.setText("Maven 版本: 未安装")
                self.m2_dir_label.setText("M2 目录: -")
                self.config_file_label.setText("配置文件: -")
                self.current_mirror_label.setText("当前镜像源: Maven未安装")
                self.local_repo_label.setText("本地仓库: -")
                return

            # 获取Maven版本
            version = self.configurator.get_maven_version()
            if version:
                self.maven_version_label.setText(f"Maven 版本: {version}")
            else:
                self.maven_version_label.setText("Maven 版本: 获取失败")

            self.m2_dir_label.setText(f"M2 目录: {self.configurator.m2_dir}")
            self.config_file_label.setText(f"配置文件: {self.configurator.target_settings}")

            # 获取详细配置信息
            config = self.configurator.get_current_config()
            if config:
                # 本地仓库
                if 'local_repository' in config:
                    repo_path = config['local_repository']
                    self.local_repo_label.setText(f"本地仓库: {repo_path}")
                    self.repo_path_edit.setText(repo_path)
                else:
                    self.local_repo_label.setText("本地仓库: 使用默认路径")

                # 镜像源
                if 'mirrors' in config and config['mirrors']:
                    mirror = config['mirrors'][0]
                    mirror_name = mirror.get('name', '未知源')
                    self.current_mirror_label.setText(f"当前镜像源: {mirror_name}")

                    # 更新下拉框选择
                    for i in range(self.mirror_combo.count()):
                        if mirror_name in self.mirror_combo.itemText(i):
                            self.mirror_combo.setCurrentIndex(i)
                            break
                else:
                    self.current_mirror_label.setText("当前镜像源: 官方源（默认）")
                    self.mirror_combo.setCurrentIndex(self.mirror_combo.count() - 1)  # 选择官方源
            else:
                self.current_mirror_label.setText("当前镜像源: 无法解析配置")
                self.local_repo_label.setText("本地仓库: 无法解析配置")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")

    def configure_mirror(self, mirror_key=None):
        """配置镜像源"""
        if mirror_key is None:
            mirror_key = self.mirror_combo.currentData()

        if not mirror_key:
            QMessageBox.warning(self, "错误", "请选择镜像源")
            return

        # 检查Maven是否安装
        if not self.configurator.check_maven_installed():
            QMessageBox.warning(self, "错误", "Maven未安装，请先安装Maven")
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
                    f"已成功配置 {mirror['name']} 镜像源！\n\n配置已生效。"
                )
                self.load_current_config()
            else:
                QMessageBox.warning(
                    self,
                    "配置失败",
                    f"配置 {mirror['name']} 镜像源失败，请检查文件权限或网络连接。"
                )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"配置镜像源时出错: {str(e)}")

    def browse_repository(self):
        """浏览仓库目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择Maven本地仓库目录"
        )
        if directory:
            self.repo_path_edit.setText(directory)

    def apply_repository_path(self):
        """应用本地仓库路径"""
        repo_path = self.repo_path_edit.text().strip()
        if not repo_path:
            QMessageBox.warning(self, "错误", "请输入本地仓库路径")
            return

        try:
            # 更新配置文件中的本地仓库路径
            self._update_local_repository(repo_path)

            QMessageBox.information(
                self,
                "配置成功",
                f"本地仓库路径已更新为:\n{repo_path}"
            )

            self.load_current_config()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新本地仓库路径失败: {str(e)}")

    def _update_local_repository(self, repo_path: str):
        """更新配置文件中的本地仓库路径"""
        if not self.configurator.target_settings.exists():
            # 如果配置文件不存在，先创建一个基础配置
            self.configurator.create_m2_directory()
            # 复制基础配置文件
            shutil.copy2(self.configurator.source_settings, self.configurator.target_settings)

        try:
            with open(self.configurator.target_settings, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换本地仓库配置
            import re
            repo_pattern = r'<localRepository>.*?</localRepository>'
            new_repo = f'<localRepository>{repo_path}</localRepository>'

            if '<localRepository>' in content:
                content = re.sub(repo_pattern, new_repo, content, flags=re.DOTALL)
            else:
                # 在settings标签后添加
                if '<settings' in content:
                    insert_pos = content.find('>', content.find('<settings')) + 1
                    content = content[:insert_pos] + f'\n  <localRepository>{repo_path}</localRepository>' + content[insert_pos:]

            # 写回文件
            with open(self.configurator.target_settings, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            raise Exception(f"更新本地仓库路径失败: {e}")

    def clean_repository(self):
        """清理仓库缓存"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理本地Maven仓库缓存吗？\n\n这将删除所有下载的依赖文件，下次构建时需要重新下载。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            config = self.configurator.get_current_config()
            repo_path = None

            if config and 'local_repository' in config:
                repo_path = config['local_repository']
            else:
                repo_path = self.configurator.user_home / ".m2" / "repository"

            if repo_path and Path(repo_path).exists():
                import shutil
                shutil.rmtree(repo_path)
                Path(repo_path).mkdir(parents=True, exist_ok=True)

                QMessageBox.information(
                    self,
                    "清理完成",
                    f"本地仓库缓存已清理:\n{repo_path}"
                )
            else:
                QMessageBox.warning(self, "警告", "未找到本地仓库目录")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"清理仓库缓存失败: {str(e)}")

    def reset_configuration(self):
        """重置配置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置Maven配置吗？\n\n这将删除当前的settings.xml文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            if self.configurator.target_settings.exists():
                self.configurator.target_settings.unlink()

            QMessageBox.information(
                self,
                "重置完成",
                "Maven配置已重置为默认状态。"
            )

            self.load_current_config()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"重置配置失败: {str(e)}")

    def open_config_file(self):
        """打开配置文件"""
        try:
            if not self.configurator.target_settings.exists():
                QMessageBox.warning(self, "警告", "配置文件不存在")
                return

            self.configurator.open_config_file()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"打开配置文件失败: {str(e)}")

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
        self.test_thread = MavenMirrorTestThread(self.configurator)
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
                    status_text = "可用"
                else:
                    time_text = "超时"
                    status_text = "不可用"

                time_item = QTableWidgetItem(time_text)
                time_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 3, time_item)

                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
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