#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 脚本执行器
扫描并执行 config_scripts 和 install_scripts 目录下的脚本
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTextEdit, QLabel, QSplitter,
    QGroupBox, QLineEdit, QComboBox, QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QProcess
from PySide6.QtGui import QFont, QTextCursor


class ScriptInfo:
    """脚本信息类"""
    
    def __init__(self, path: Path, category: str):
        self.path = path
        self.name = path.stem
        self.category = category
        self.description = self._extract_description()
    
    def _extract_description(self) -> str:
        """从脚本中提取描述信息"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 查找文档字符串
                in_docstring = False
                description_lines = []
                
                for line in lines[:20]:  # 只读取前20行
                    if '"""' in line or "'''" in line:
                        if in_docstring:
                            break
                        in_docstring = True
                        # 提取同一行的内容
                        content = line.split('"""')[1] if '"""' in line else line.split("'''")[1]
                        if content.strip():
                            description_lines.append(content.strip())
                        continue
                    
                    if in_docstring:
                        description_lines.append(line.strip())
                
                return ' '.join(description_lines[:2]) if description_lines else "无描述"
        except Exception:
            return "无描述"


class ScriptRunner(QThread):
    """脚本运行线程"""
    
    output_signal = Signal(str)
    finished_signal = Signal(int)
    
    def __init__(self, script_path: Path, args: List[str] = None):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.process = None
    
    def run(self):
        """运行脚本"""
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时读取输出
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_signal.emit(line.rstrip())
            
            self.process.wait()
            self.finished_signal.emit(self.process.returncode)
            
        except Exception as e:
            self.output_signal.emit(f"错误: {str(e)}")
            self.finished_signal.emit(-1)
    
    def stop(self):
        """停止脚本执行"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=3)


class ScriptLauncher(QMainWindow):
    """脚本启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.scripts: Dict[str, List[ScriptInfo]] = {
            'config_scripts': [],
            'install_scripts': []
        }
        self.current_runner = None
        
        self.init_ui()
        self.scan_scripts()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Python 脚本执行器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 脚本列表
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 执行区域
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border: none;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget:focus {
                border: 1px solid #2196F3;
                outline: none;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
        """)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("📂 可用脚本")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 分类选择
        category_layout = QHBoxLayout()
        category_label = QLabel("分类:")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "配置脚本", "安装脚本"])
        self.category_combo.currentTextChanged.connect(self.filter_scripts)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入脚本名称...")
        self.search_input.textChanged.connect(self.filter_scripts)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 脚本列表
        self.script_list = QListWidget()
        self.script_list.itemDoubleClicked.connect(self.on_script_double_clicked)
        self.script_list.currentItemChanged.connect(self.on_script_selected)
        layout.addWidget(self.script_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新脚本列表")
        refresh_btn.clicked.connect(self.scan_scripts)
        layout.addWidget(refresh_btn)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 脚本信息组
        info_group = QGroupBox("脚本信息")
        info_layout = QVBoxLayout()
        
        self.script_name_label = QLabel("未选择脚本")
        self.script_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(self.script_name_label)
        
        self.script_desc_label = QLabel("")
        self.script_desc_label.setWordWrap(True)
        info_layout.addWidget(self.script_desc_label)
        
        self.script_path_label = QLabel("")
        self.script_path_label.setStyleSheet("color: #666666; font-size: 10px;")
        info_layout.addWidget(self.script_path_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 参数输入组
        args_group = QGroupBox("命令行参数")
        args_layout = QVBoxLayout()
        
        args_hint = QLabel("常用参数: --help, --list, --show, --test")
        args_hint.setStyleSheet("color: #666666; font-size: 10px;")
        args_layout.addWidget(args_hint)
        
        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("例如: --list 或 --help")
        args_layout.addWidget(self.args_input)
        
        args_group.setLayout(args_layout)
        layout.addWidget(args_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("▶ 运行脚本")
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setEnabled(False)
        button_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
        button_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑 清空输出")
        self.clear_btn.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # 输出区域
        output_group = QGroupBox("执行输出")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        return panel
    
    def scan_scripts(self):
        """扫描脚本目录"""
        self.scripts = {
            'config_scripts': [],
            'install_scripts': []
        }
        
        base_dir = Path(__file__).parent
        
        # 扫描配置脚本
        config_dir = base_dir / "config_scripts"
        if config_dir.exists():
            for script_file in config_dir.glob("*.py"):
                if script_file.name != "__init__.py":
                    self.scripts['config_scripts'].append(
                        ScriptInfo(script_file, "配置脚本")
                    )
        
        # 扫描安装脚本
        install_dir = base_dir / "install_scripts"
        if install_dir.exists():
            for script_file in install_dir.glob("*.py"):
                if script_file.name != "__init__.py":
                    self.scripts['install_scripts'].append(
                        ScriptInfo(script_file, "安装脚本")
                    )
        
        self.update_script_list()
        self.append_output(f"✓ 扫描完成: 找到 {len(self.scripts['config_scripts'])} 个配置脚本, "
                          f"{len(self.scripts['install_scripts'])} 个安装脚本")
    
    def update_script_list(self):
        """更新脚本列表显示"""
        self.script_list.clear()
        
        category = self.category_combo.currentText()
        search_text = self.search_input.text().lower()
        
        # 添加配置脚本
        if category in ["全部", "配置脚本"]:
            for script in self.scripts['config_scripts']:
                if search_text in script.name.lower():
                    item = QListWidgetItem(f"⚙️ {script.name}")
                    item.setData(Qt.UserRole, script)
                    self.script_list.addItem(item)
        
        # 添加安装脚本
        if category in ["全部", "安装脚本"]:
            for script in self.scripts['install_scripts']:
                if search_text in script.name.lower():
                    item = QListWidgetItem(f"📦 {script.name}")
                    item.setData(Qt.UserRole, script)
                    self.script_list.addItem(item)
    
    def filter_scripts(self):
        """过滤脚本列表"""
        self.update_script_list()
    
    def on_script_selected(self, current, previous):
        """脚本选择事件"""
        if current:
            script: ScriptInfo = current.data(Qt.UserRole)
            self.script_name_label.setText(f"📄 {script.name}")
            self.script_desc_label.setText(script.description)
            self.script_path_label.setText(f"路径: {script.path}")
            self.run_btn.setEnabled(True)
        else:
            self.script_name_label.setText("未选择脚本")
            self.script_desc_label.setText("")
            self.script_path_label.setText("")
            self.run_btn.setEnabled(False)
    
    def on_script_double_clicked(self, item):
        """双击脚本直接运行"""
        self.run_script()
    
    def run_script(self):
        """运行选中的脚本"""
        current_item = self.script_list.currentItem()
        if not current_item:
            return
        
        script: ScriptInfo = current_item.data(Qt.UserRole)
        args_text = self.args_input.text().strip()
        args = args_text.split() if args_text else []
        
        self.clear_output()
        self.append_output(f"{'='*60}")
        self.append_output(f"运行脚本: {script.name}")
        self.append_output(f"参数: {' '.join(args) if args else '(无)'}")
        self.append_output(f"{'='*60}\n")
        
        # 创建并启动运行线程
        self.current_runner = ScriptRunner(script.path, args)
        self.current_runner.output_signal.connect(self.append_output)
        self.current_runner.finished_signal.connect(self.on_script_finished)
        self.current_runner.start()
        
        # 更新按钮状态
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_script(self):
        """停止脚本执行"""
        if self.current_runner:
            self.append_output("\n⚠ 正在停止脚本...")
            self.current_runner.stop()
            self.current_runner = None
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def on_script_finished(self, return_code):
        """脚本执行完成"""
        self.append_output(f"\n{'='*60}")
        if return_code == 0:
            self.append_output("✓ 脚本执行成功")
        else:
            self.append_output(f"✗ 脚本执行失败 (返回码: {return_code})")
        self.append_output(f"{'='*60}\n")
        
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_runner = None
    
    def append_output(self, text: str):
        """追加输出文本"""
        self.output_text.append(text)
        # 自动滚动到底部
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output_text.setTextCursor(cursor)
    
    def clear_output(self):
        """清空输出"""
        self.output_text.clear()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Python 脚本执行器")
    app.setOrganizationName("PyInstallDevTools")
    
    # 创建并显示主窗口
    window = ScriptLauncher()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
