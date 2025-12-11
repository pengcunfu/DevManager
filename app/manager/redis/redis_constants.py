#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 配置模块
直接返回当前平台所需的配置信息
"""

import os
import platform
from typing import Dict, List


# 版本信息
def get_version() -> str:
    """获取Redis版本"""
    return "7.2.4"


def get_version_short() -> str:
    """获取Redis短版本号"""
    return "7.2"


def get_default_port() -> int:
    """获取默认端口"""
    return 6379


# 下载相关
def get_download_url() -> str:
    """获取当前平台的下载URL"""
    system = platform.system().lower()
    if system == "windows":
        return f"https://github.com/microsoftarchive/redis/releases/download/win-{get_version_short()}/Redis-{get_version()}-x64.msi"
    else:
        return f"http://download.redis.io/releases/redis-{get_version()}.tar.gz"


# 安装路径
def get_install_path() -> str:
    """获取当前平台的默认安装路径"""
    system = platform.system().lower()
    if system == "windows":
        return r"C:\Redis"
    elif system == "linux":
        return "/usr/local/redis"
    else:  # macOS
        return "/usr/local/redis"


# 可执行文件
def get_server_executable() -> str:
    """获取Redis服务器可执行文件名"""
    system = platform.system().lower()
    if system == "windows":
        return "redis-server.exe"
    return "redis-server"


def get_client_executable() -> str:
    """获取Redis客户端可执行文件名"""
    system = platform.system().lower()
    if system == "windows":
        return "redis-cli.exe"
    return "redis-cli"


def get_check_executable() -> str:
    """获取Redis检查工具可执行文件名"""
    system = platform.system().lower()
    if system == "windows":
        return "redis-check-aof.exe"
    return "redis-check-aof"


def get_executable_name(exe_type: str = "server") -> str:
    """获取可执行文件名"""
    if exe_type == "client":
        return get_client_executable()
    elif exe_type == "check":
        return get_check_executable()
    else:
        return get_server_executable()


# 服务管理
def get_service_name() -> str:
    """获取当前平台的服务名称"""
    system = platform.system().lower()
    if system == "windows":
        return "Redis"
    elif system == "linux":
        return "redis-server"
    else:
        return "redis"


def get_start_commands() -> Dict[str, str]:
    """获取启动命令"""
    system = platform.system().lower()
    if system == "windows":
        return {
            "service": "net start Redis",
            "direct": "redis-server.exe"
        }
    elif system == "linux":
        return {
            "systemctl": "sudo systemctl start redis-server",
            "service": "sudo service redis-server start",
            "direct": "redis-server"
        }
    else:  # macOS
        return {
            "brew_services": "brew services start redis",
            "launchctl": "launchctl load ~/Library/LaunchAgents/homebrew.mxcl.redis.plist",
            "direct": "redis-server"
        }


def get_stop_commands() -> Dict[str, str]:
    """获取停止命令"""
    system = platform.system().lower()
    if system == "windows":
        return {
            "service": "net stop Redis",
            "direct": "taskkill /f /im redis-server.exe"
        }
    elif system == "linux":
        return {
            "systemctl": "sudo systemctl stop redis-server",
            "service": "sudo service redis-server stop",
            "direct": "redis-cli shutdown"
        }
    else:  # macOS
        return {
            "brew_services": "brew services stop redis",
            "launchctl": "launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.redis.plist",
            "direct": "redis-cli shutdown"
        }


# 包管理器
def get_package_managers() -> Dict[str, str]:
    """获取包管理器安装命令"""
    system = platform.system().lower()
    if system == "windows":
        return {
            "choco": "choco install redis-64",
            "scoop": "scoop install redis",
            "winget": "winget install Microsoft.Redis"
        }
    elif system == "linux":
        return {
            "apt": "sudo apt update && sudo apt install redis-server",
            "yum": "sudo yum install epel-release && sudo yum install redis",
            "dnf": "sudo dnf install redis",
            "pacman": "sudo pacman -S redis"
        }
    else:  # macOS
        return {
            "brew": "brew install redis",
            "port": "sudo port install redis"
        }


# 配置文件
def get_config_file_name() -> str:
    """获取配置文件名"""
    system = platform.system().lower()
    if system == "windows":
        return "redis.windows.conf"
    return "redis.conf"


def get_data_directories() -> List[str]:
    """获取数据目录"""
    system = platform.system().lower()
    if system == "windows":
        return [
            r"C:\Redis\data",
            r"C:\ProgramData\Redis\data"
        ]
    elif system == "linux":
        return [
            "/var/lib/redis",
            "/usr/local/redis/data"
        ]
    else:  # macOS
        return [
            "/usr/local/var/db/redis",
            "~/Library/Application Support/Redis/data"
        ]


# 默认配置
def get_default_config_options() -> Dict[str, any]:
    """获取默认配置选项"""
    return {
        "bind": "127.0.0.1",
        "port": get_default_port(),
        "protected_mode": "yes",
        "daemonize": "no",
        "databases": 16,
        "save": ["900 1", "300 10", "60 10000"],
        "maxmemory": "256mb",
        "maxmemory_policy": "allkeys-lru"
    }


# 性能预设
def get_performance_preset(preset_type: str = "development") -> Dict[str, any]:
    """获取性能预设配置"""
    presets = {
        "development": {
            "maxmemory": "256mb",
            "save": ["900 1", "300 10", "60 10000"],
            "appendonly": "yes",
            "appendfsync": "everysec"
        },
        "production": {
            "maxmemory": "2gb",
            "save": ["900 1", "300 10", "60 10000"],
            "appendonly": "yes",
            "appendfsync": "always"
        },
        "cache_server": {
            "maxmemory": "1gb",
            "maxmemory_policy": "allkeys-lru",
            "save": [],
            "appendonly": "no"
        }
    }
    return presets.get(preset_type, presets["development"])


# 文件权限
def get_file_permissions() -> str:
    """获取文件权限"""
    system = platform.system().lower()
    if system == "windows":
        return "666"
    return "644"


# 日志配置
def get_log_config() -> Dict[str, str]:
    """获取日志配置"""
    return {
        "log_file": "redis.log",
        "log_level": "notice",
        "syslog_enabled": False,
        "syslog_ident": "redis"
    }


# 服务配置文件模板
def get_systemd_service_template() -> str:
    """获取systemd服务文件模板"""
    return """[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
User=redis
Group=redis
ExecStart=/usr/local/bin/{server_executable} /etc/redis/redis.conf
ExecStop=/usr/local/bin/{client_executable} shutdown
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""


def get_launchd_plist_template() -> str:
    """获取macOS launchd plist文件模板"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>io.redis.redis-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/{server_executable}</string>
        <string>/usr/local/etc/redis.conf</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""