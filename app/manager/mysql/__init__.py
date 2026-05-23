#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL管理模块 (Windows版)
提供MySQL 8.0.44在Windows系统下的下载、安装、配置和服务管理功能

主要功能:
- MySQL 8.0.44 Windows版下载和安装
- Windows服务管理（创建、启动、停止、删除）
- MySQL配置文件管理
- Windows环境变量配置

作者: DevManager
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "DevManager"

# 导入核心类
from .mysql_config import MySQLConfigManager, MYSQL_VERSION, MYSQL_DOWNLOAD_URL
from .mysql_installer import MySQLInstaller
from .mysql_tab import MySQLTab, MySQLWorkerThread

# 导出的公共接口
__all__ = [
    # 版本信息
    "__version__",
    "__author__",

    # 核心类
    "MySQLConfigManager",
    "MySQLInstaller",
    "MySQLTab",
    "MySQLWorkerThread",

    # 常量
    "MYSQL_VERSION",
    "MYSQL_DOWNLOAD_URL",

    # 便捷函数
    "create_mysql_manager",
    "get_mysql_status",
    "install_mysql_8044",
    "manage_mysql_service",
]


def create_mysql_manager(installation_path: str = None) -> tuple:
    """创建MySQL管理器实例

    Args:
        installation_path: MySQL安装路径，如果为None则使用默认路径

    Returns:
        (installer, config_manager): 安装器和配置管理器实例

    Example:
        installer, config_manager = create_mysql_manager()
        installer.download_mysql()
        config_manager.create_config_file(installer.installation_path)
    """
    installer = MySQLInstaller(installation_path)
    config_manager = MySQLConfigManager(installation_path)
    return installer, config_manager


def get_mysql_status(installation_path: str = None) -> dict:
    """获取MySQL状态信息

    Args:
        installation_path: MySQL安装路径

    Returns:
        包含状态信息的字典
    """
    installer = MySQLInstaller(installation_path)
    config_manager = MySQLConfigManager(installation_path)

    status = {
        "version": MYSQL_VERSION,
        "installed": installer.is_mysql_installed(),
        "service_status": None,
        "installation_path": installer.installation_path,
        "config_info": None
    }

    if status["installed"]:
        status["service_status"] = installer.get_service_status()
        status["config_info"] = config_manager.get_current_config()
        status["mysql_version"] = installer.get_mysql_version()

    return status


def install_mysql_8044(installation_path: str = None, auto_start: bool = False) -> bool:
    """一键安装MySQL 8.0.44

    Args:
        installation_path: 安装路径，如果为None则使用默认路径
        auto_start: 是否自动启动服务

    Returns:
        bool: 安装是否成功

    Example:
        success = install_mysql_8044()
        if success:
            print("MySQL安装成功")
    """
    try:
        print(f"开始安装MySQL {MYSQL_VERSION}...")

        # 创建安装器
        installer = MySQLInstaller(installation_path)

        # 检查是否已安装
        if installer.is_mysql_installed():
            print("MySQL已经安装，跳过安装步骤")
            return True

        # 检查安装要求
        print("检查安装要求...")
        requirements = installer.check_requirements()
        failed_requirements = [req for req, satisfied in requirements.items() if not satisfied]

        if failed_requirements:
            print(f"不满足安装要求: {', '.join(failed_requirements)}")
            return False

        print("安装要求检查通过")

        # 下载MySQL
        print("正在下载MySQL...")
        installer_path = installer.download_mysql()
        if not installer_path:
            print("下载MySQL失败")
            return False

        # 安装MySQL
        print("正在安装MySQL...")
        success = installer.install_mysql(installer_path)
        if not success:
            print("MySQL安装失败")
            return False

        print("MySQL安装完成")

        # 自动启动服务
        if auto_start:
            print("正在启动MySQL服务...")
            installer.start_service()

        return True

    except Exception as e:
        print(f"安装过程出错: {e}")
        return False


def manage_mysql_service(action: str, installation_path: str = None) -> bool:
    """管理MySQL服务

    Args:
        action: 操作类型 ('start', 'stop', 'restart', 'install', 'status')
        installation_path: MySQL安装路径

    Returns:
        bool: 操作是否成功

    Example:
        manage_mysql_service('start')
        manage_mysql_service('stop')
        manage_mysql_service('restart')
    """
    installer = MySQLInstaller(installation_path)

    action_map = {
        'start': installer.start_service,
        'stop': installer.stop_service,
        'restart': installer.restart_service,
        'install': installer.install_service,
    }

    if action == 'status':
        status = installer.get_service_status()
        print(f"服务状态: {status.get('status', 'unknown')}")
        return True

    if action not in action_map:
        print(f"不支持的操作: {action}")
        print("支持的操作: start, stop, restart, install, status")
        return False

    try:
        return action_map[action]()
    except Exception as e:
        print(f"执行{action}操作失败: {e}")
        return False


# 模块信息
def get_info():
    """获取模块信息"""
    return {
        "name": "MySQL Manager (Windows)",
        "version": __version__,
        "author": __author__,
        "mysql_version": MYSQL_VERSION,
        "download_url": MYSQL_DOWNLOAD_URL,
        "supported_platforms": ["Windows"],
        "features": [
            "MySQL 8.0.44 Windows版下载和安装",
            "Windows服务管理（创建、启动、停止、删除）",
            "配置文件动态生成和管理",
            "Windows环境变量配置",
            "图形界面支持"
        ]
    }


