#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevManager - 开发工具箱
提供常用开发工具的图形化界面
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QGroupBox, QMessageBox,
    QStackedWidget, QListWidget, QListWidgetItem, QStyleFactory,
    QMenuBar, QMenu, QDialog, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

# 导入各个工具页面
try:
    from app.manager.python.pip_config_tab import PipConfigTab
except ImportError:
    PipConfigTab = None

try:
    from app.manager.nodejs.npm_config_tab import NpmConfigTab
except ImportError:
    NpmConfigTab = None

try:
    from app.manager.php.composer_tab import ComposerTab
except ImportError:
    ComposerTab = None

try:
    from app.manager.java.maven_config_tab import MavenConfigTab
except ImportError:
    MavenConfigTab = None

try:
    from app.manager.mysql.mysql_tab import MySQLTab
except ImportError:
    MySQLTab = None

try:
    from app.manager.redis.redis_tab import RedisTab
except ImportError:
    RedisTab = None

try:
    from app.manager.minio.minio_tab import MinIOTab
except ImportError:
    MinIOTab = None

try:
    from app.manager.mongodb.mongodb_tab import MongoDBTab
except ImportError:
    MongoDBTab = None


class ToolInfo:
    """工具信息"""
    def __init__(self, name: str, description: str, icon: str, widget_class=None):
        self.name = name
        self.description = description
        self.icon = icon
        self.widget_class = widget_class


class DevManagerWindow(QMainWindow):
    """开发工具箱主窗口"""

    def __init__(self):
        super().__init__()
        self.tools = {}
        self.init_tools()
        self.init_ui()

    def init_tools(self):
        """初始化工具列表"""
        # Pip 镜像源配置工具
        if PipConfigTab:
            self.tools['pip'] = ToolInfo(
                name='Pip 镜像源配置',
                description='配置和管理 Python Pip 包管理器的国内镜像源，支持速度测试',
                icon='🐍',
                widget_class=PipConfigTab
            )

        # NPM 镜像源配置工具
        if NpmConfigTab:
            self.tools['npm'] = ToolInfo(
                name='NPM 镜像源配置',
                description='配置和管理 Node.js NPM 包管理器的国内镜像源，支持速度测试',
                icon='📦',
                widget_class=NpmConfigTab
            )

        # Composer 安装和配置工具
        if ComposerTab:
            self.tools['composer'] = ToolInfo(
                name='Composer 管理器',
                description='安装 Composer 并配置 PHP 包管理器的国内镜像源，支持速度测试',
                icon='🎵',
                widget_class=ComposerTab
            )

        # Maven 镜像源配置工具
        if MavenConfigTab:
            self.tools['maven'] = ToolInfo(
                name='Maven 镜像源配置',
                description='配置和管理 Java Maven 依赖管理器的国内镜像源，支持速度测试',
                icon='☕',
                widget_class=MavenConfigTab
            )

        # MySQL 管理工具
        if MySQLTab:
            self.tools['mysql'] = ToolInfo(
                name='MySQL 管理器',
                description='MySQL数据库的安装、配置、服务管理和监控',
                icon='🐬',
                widget_class=MySQLTab
            )

        # Redis 管理工具
        if RedisTab:
            self.tools['redis'] = ToolInfo(
                name='Redis 管理器',
                description='Redis内存数据库的安装、配置、服务管理和监控',
                icon='🔴',
                widget_class=RedisTab
            )

        # MinIO 管理工具
        if MinIOTab:
            self.tools['minio'] = ToolInfo(
                name='MinIO 管理器',
                description='MinIO对象存储的安装、配置、服务管理和监控',
                icon='🪣',
                widget_class=MinIOTab
            )

        # MongoDB 管理工具
        if MongoDBTab:
            self.tools['mongodb'] = ToolInfo(
                name='MongoDB 管理器',
                description='MongoDB文档数据库的安装、配置、服务管理和监控',
                icon='🍃',
                widget_class=MongoDBTab
            )

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("DevManager - 开发工具箱")
        self.setGeometry(200, 200, 1200, 800)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏
        self.create_status_bar()

        # 设置应用图标（如果有的话）
        # if os.path.exists("icon.png"):
        #     self.setWindowIcon(QIcon("icon.png"))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧工具列表
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧内容区域
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([300, 900])

        # 默认选择第一个工具
        if self.tool_list.count() > 0:
            self.tool_list.setCurrentRow(0)
            self.on_tool_selected(self.tool_list.item(0))

    def create_left_panel(self) -> QWidget:
        """创建左侧工具列表面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        
        # 工具列表
        self.tool_list = QListWidget()
        self.tool_list.setIconSize(QSize(24, 24))

        # 添加工具到列表
        for tool_id, tool_info in self.tools.items():
            item = QListWidgetItem(f"{tool_info.icon} {tool_info.name}")
            item.setToolTip(tool_info.description)
            item.setData(Qt.UserRole, tool_id)
            self.tool_list.addItem(item)

        self.tool_list.currentItemChanged.connect(self.on_tool_selected)
        layout.addWidget(self.tool_list)

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧内容面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 创建堆叠窗口来显示不同的工具页面
        self.stacked_widget = QStackedWidget()

        # 添加欢迎页面
        welcome_widget = self.create_welcome_page()
        self.stacked_widget.addWidget(welcome_widget)

        # 添加工具页面
        for tool_id, tool_info in self.tools.items():
            if tool_info.widget_class:
                try:
                    tool_widget = tool_info.widget_class()
                    self.stacked_widget.addWidget(tool_widget)
                except Exception as e:
                    # 如果工具页面加载失败，显示错误页面
                    error_widget = self.create_error_page(tool_info.name, str(e))
                    self.stacked_widget.addWidget(error_widget)
                    print(f"加载工具 {tool_info.name} 失败: {e}")

        layout.addWidget(self.stacked_widget)

        return panel

    def create_welcome_page(self) -> QWidget:
        """创建欢迎页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        # 欢迎标题
        title = QLabel("🎉 欢迎使用 DevManager")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2196F3; margin: 20px 0;")
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("专业的开发工具集合")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(subtitle)

        # 说明文字
        description = QLabel("""
        DevManager 是一个集成了常用开发工具的管理器，
        提供图形化界面来配置和管理各种开发环境工具。

        请从左侧选择一个工具开始使用。
        """)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("""
            color: #555;
            font-size: 14px;
            line-height: 1.6;
            margin: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        """)
        layout.addWidget(description)

        # 功能特性
        features_group = QGroupBox("✨ 主要特性")
        features_layout = QVBoxLayout()

        features = [
            "🚀 简洁易用的图形界面",
            "⚡ 快速配置开发环境",
            "🛡️ 安全可靠的配置管理",
            "🔧 持续更新和功能扩展"
        ]

        for feature in features:
            label = QLabel(feature)
            label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            features_layout.addWidget(label)

        features_group.setLayout(features_layout)
        layout.addWidget(features_group)

        layout.addStretch()

        return widget

    def create_error_page(self, tool_name: str, error_msg: str) -> QWidget:
        """创建错误页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        # 错误图标
        error_label = QLabel("❌")
        error_font = QFont()
        error_font.setPointSize(48)
        error_label.setFont(error_font)
        error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_label)

        # 错误标题
        title = QLabel(f"工具加载失败")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #f44336; margin: 20px 0;")
        layout.addWidget(title)

        # 工具名称
        tool_label = QLabel(f"工具: {tool_name}")
        tool_label.setAlignment(Qt.AlignCenter)
        tool_label.setStyleSheet("color: #333; font-size: 16px; margin: 10px 0;")
        layout.addWidget(tool_label)

        # 错误信息
        error_text = QLabel(f"错误信息: {error_msg}")
        error_text.setAlignment(Qt.AlignCenter)
        error_text.setStyleSheet("""
            color: #666;
            font-size: 14px;
            margin: 20px;
            padding: 15px;
            background-color: #ffebee;
            border-radius: 6px;
            border: 1px solid #ffcdd2;
        """)
        error_text.setWordWrap(True)
        layout.addWidget(error_text)

        # 解决建议
        suggestion = QLabel("💡 建议: 请检查相关依赖是否正确安装")
        suggestion.setAlignment(Qt.AlignCenter)
        suggestion.setStyleSheet("color: #ff9800; font-size: 14px; margin: 10px 0;")
        layout.addWidget(suggestion)

        layout.addStretch()

        return widget

    def on_tool_selected(self, current_item, previous_item=None):
        """工具选择事件处理"""
        if not current_item:
            self.stacked_widget.setCurrentIndex(0)  # 显示欢迎页面
            return

        tool_id = current_item.data(Qt.UserRole)
        if tool_id in self.tools:
            # 计算在堆叠窗口中的索引
            # 索引 0 是欢迎页面，所以工具页面从 1 开始
            tool_index = list(self.tools.keys()).index(tool_id) + 1
            self.stacked_widget.setCurrentIndex(tool_index)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')

        # 关于菜单项
        about_action = help_menu.addAction('关于(&A)')
        about_action.setShortcut('F1')
        about_action.triggered.connect(self.show_about_dialog)

    def create_status_bar(self):
        """创建状态栏"""
        status_bar = self.statusBar()

        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #666; font-size: 11px; padding: 0 10px;")

        # 工具统计信息
        tool_count = len(self.tools)
        stats_label = QLabel(f"可用工具: {tool_count} 个")
        stats_label.setStyleSheet("color: #666; font-size: 11px; padding: 0 10px;")

        # 添加到状态栏
        status_bar.addPermanentWidget(stats_label)
        status_bar.addPermanentWidget(version_label)

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('关于 DevManager')
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)

        # 应用图标和标题
        title_layout = QHBoxLayout()

        # 图标（使用文本替代）
        icon_label = QLabel('🛠️')
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(icon_label)

        # 应用信息
        info_layout = QVBoxLayout()

        # 应用名称
        app_name = QLabel('DevManager')
        app_name_font = QFont()
        app_name_font.setPointSize(24)
        app_name_font.setBold(True)
        app_name.setFont(app_name_font)
        info_layout.addWidget(app_name)

        # 应用描述
        app_desc = QLabel('开发工具箱')
        desc_font = QFont()
        desc_font.setPointSize(14)
        app_desc.setFont(desc_font)
        info_layout.addWidget(app_desc)

        # 版本信息
        version_label = QLabel('版本: 1.0.0')
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        info_layout.addWidget(version_label)

        title_layout.addLayout(info_layout)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 分隔线
        line = QLabel()
        line.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        layout.addWidget(line)

        # 功能描述
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setMaximumHeight(150)
        features_text.setPlainText(
            'DevManager 是一个集成了常用开发工具的管理器，提供图形化界面来配置和管理各种开发环境工具。\n\n'
            '主要功能：\n'
            '• Pip 镜像源配置 - 管理 Python 包管理器的国内镜像源\n'
            '• NPM 镜像源配置 - 管理 Node.js 包管理器的国内镜像源\n'
            '• Composer 管理器 - 安装和配置 PHP 包管理器\n'
            '• Maven 镜像源配置 - 管理 Java Maven 依赖管理器的国内镜像源\n'
            '• MySQL 管理器 - MySQL数据库的安装、配置和服务管理\n'
            '• Redis 管理器 - Redis内存数据库的安装、配置和服务管理\n'
            '• MinIO 管理器 - MinIO对象存储的安装、配置和服务管理\n'
            '• MongoDB 管理器 - MongoDB文档数据库的安装、配置和服务管理\n'
            '• 速度测试 - 测试各镜像源响应速度并推荐最佳选择\n'
            '• 一键配置 - 简单快捷的镜像源配置体验'
        )
        layout.addWidget(features_text)

        # 作者信息
        author_label = QLabel('作者: DevTools Team')
        author_font = QFont()
        author_font.setPointSize(11)
        author_label.setFont(author_font)
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        # 版权信息
        copyright_label = QLabel('© 2024 DevTools. All rights reserved.')
        copyright_font = QFont()
        copyright_font.setPointSize(10)
        copyright_label.setFont(copyright_font)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet('color: #666;')
        layout.addWidget(copyright_label)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton('确定')
        ok_button.setFixedWidth(80)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("DevManager")
    app.setApplicationDisplayName("DevManager - 开发工具箱")
    app.setOrganizationName("DevTools")
    app.setApplicationVersion("1.0.0")

    # 设置应用程序样式
    app.setStyle(QStyleFactory.create('windowsvista'))

    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 创建并显示主窗口
    try:
        window = DevManagerWindow()
        window.show()

        # 运行应用程序
        sys.exit(app.exec())

    except Exception as e:
        QMessageBox.critical(
            None,
            "启动错误",
            f"程序启动失败:\n\n{str(e)}\n\n请检查环境和依赖是否正确安装。"
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)