#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 硬编码配置常量
存储 Redis 安装路径、下载地址、版本信息等硬编码数据
"""

import os
import platform
from typing import Dict, List, Tuple


class RedisConstants:
    """Redis 常量配置类"""

    # Redis 版本信息
    REDIS_VERSION = "7.2.4"
    REDIS_VERSION_SHORT = "7.2"

    # 系统架构映射
    ARCH_MAP = {
        "amd64": "x64",
        "x86_64": "x64",
        "arm64": "arm64",
        "armv7l": "arm64",
        "i386": "x86",
        "i686": "x86"
    }

    # Redis 下载配置
    DOWNLOAD_URLS = {
        "Windows": {
            "x64": f"https://github.com/microsoftarchive/redis/releases/download/win-{REDIS_VERSION_SHORT}/Redis-{REDIS_VERSION}-x64.msi",
            "x86": f"https://github.com/microsoftarchive/redis/releases/download/win-{REDIS_VERSION_SHORT}/Redis-{REDIS_VERSION}-x86.msi"
        },
        "Linux": {
            "source": f"http://download.redis.io/releases/redis-{REDIS_VERSION}.tar.gz"
        },
        "macOS": {
            "source": f"http://download.redis.io/releases/redis-{REDIS_VERSION}.tar.gz",
            "homebrew": "redis"
        }
    }

    # 默认安装路径
    DEFAULT_INSTALL_PATHS = {
        "Windows": [
            r"C:\Redis",
            r"C:\Program Files\Redis",
            r"C:\Program Files (x86)\Redis"
        ],
        "Linux": [
            "/usr/local/redis",
            "/opt/redis",
            "/usr/local/bin"
        ],
        "macOS": [
            "/usr/local/redis",
            "/opt/homebrew/opt/redis",
            "/usr/local/bin"
        ]
    }

    # 配置文件名称
    CONFIG_FILE_NAMES = {
        "Windows": "redis.windows.conf",
        "Linux": "redis.conf",
        "macOS": "redis.conf"
    }

    # 服务名称
    SERVICE_NAMES = {
        "Windows": "Redis",
        "Linux": "redis-server",
        "macOS": "redis"
    }

    # 可执行文件名
    EXECUTABLE_NAMES = {
        "server": {
            "Windows": "redis-server.exe",
            "Linux": "redis-server",
            "macOS": "redis-server"
        },
        "client": {
            "Windows": "redis-cli.exe",
            "Linux": "redis-cli",
            "macOS": "redis-cli"
        },
        "conf": {
            "Windows": "redis-cli.exe",
            "Linux": "redis-check-aof",
            "macOS": "redis-check-aof"
        }
    }

    # 默认端口配置
    DEFAULT_PORT = 6379

    # 默认配置选项
    DEFAULT_CONFIG_OPTIONS = {
        "bind": "127.0.0.1",
        "port": DEFAULT_PORT,
        "protected_mode": "yes",
        "daemonize": "no",
        "pidfile": "/var/run/redis_6379.pid",
        "logfile": "",
        "databases": 16,
        "save": ["900 1", "300 10", "60 10000"],
        "maxmemory": "256mb",
        "maxmemory_policy": "allkeys-lru"
    }

    # 包管理器安装命令
    PACKAGE_MANAGER_COMMANDS = {
        "Windows": {
            "choco": "choco install redis-64",
            "scoop": "scoop install redis",
            "winget": "winget install Microsoft.Redis"
        },
        "Linux": {
            "Ubuntu/Debian": [
                "sudo apt update",
                "sudo apt install redis-server"
            ],
            "CentOS/RHEL": [
                "sudo yum install epel-release",
                "sudo yum install redis"
            ],
            "Fedora": [
                "sudo dnf install redis"
            ],
            "Arch": [
                "sudo pacman -S redis"
            ]
        },
        "macOS": {
            "homebrew": "brew install redis",
            "macports": "sudo port install redis"
        }
    }

    # 启动命令
    START_COMMANDS = {
        "Windows": {
            "service": "net start Redis",
            "direct": "redis-server.exe"
        },
        "Linux": {
            "systemctl": "sudo systemctl start redis-server",
            "service": "sudo service redis-server start",
            "direct": "redis-server"
        },
        "macOS": {
            "brew_services": "brew services start redis",
            "launchctl": "launchctl load ~/Library/LaunchAgents/homebrew.mxcl.redis.plist",
            "direct": "redis-server"
        }
    }

    # 停止命令
    STOP_COMMANDS = {
        "Windows": {
            "service": "net stop Redis",
            "direct": "taskkill /f /im redis-server.exe"
        },
        "Linux": {
            "systemctl": "sudo systemctl stop redis-server",
            "service": "sudo service redis-server stop",
            "direct": "redis-cli shutdown"
        },
        "macOS": {
            "brew_services": "brew services stop redis",
            "launchctl": "launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.redis.plist",
            "direct": "redis-cli shutdown"
        }
    }

    # 文件权限配置
    FILE_PERMISSIONS = {
        "Windows": "666",
        "Linux": "644",
        "macOS": "644"
    }

    # 日志配置
    LOG_CONFIG = {
        "log_file": "redis.log",
        "log_level": "notice",  # debug, verbose, notice, warning
        "syslog_enabled": False,
        "syslog_ident": "redis"
    }

    # 数据目录配置
    DATA_DIRECTORIES = {
        "Windows": [
            r"C:\Redis\data",
            r"C:\ProgramData\Redis\data"
        ],
        "Linux": [
            "/var/lib/redis",
            "/usr/local/redis/data"
        ],
        "macOS": [
            "/usr/local/var/db/redis",
            "~/Library/Application Support/Redis/data"
        ]
    }

    # 性能配置预设
    PERFORMANCE_PRESETS = {
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

    @classmethod
    def get_current_platform(cls) -> str:
        """获取当前平台名称"""
        system = platform.system().lower()
        if system == "windows":
            return "Windows"
        elif system == "darwin":
            return "macOS"
        elif system == "linux":
            return "Linux"
        else:
            return system

    @classmethod
    def get_current_architecture(cls) -> str:
        """获取当前架构"""
        machine = platform.machine().lower()
        return cls.ARCH_MAP.get(machine, "x86")

    @classmethod
    def get_download_url(cls) -> str:
        """获取当前平台的下载URL"""
        platform_name = cls.get_current_platform()
        arch = cls.get_current_architecture()

        if platform_name == "Windows":
            return cls.DOWNLOAD_URLS[platform_name].get(arch, "")
        else:
            return cls.DOWNLOAD_URLS[platform_name].get("source", "")

    @classmethod
    def get_default_install_paths(cls) -> List[str]:
        """获取当前平台的默认安装路径"""
        platform_name = cls.get_current_platform()
        return cls.DEFAULT_INSTALL_PATHS.get(platform_name, [])

    @classmethod
    def get_service_name(cls) -> str:
        """获取当前平台的服务名称"""
        platform_name = cls.get_current_platform()
        return cls.SERVICE_NAMES.get(platform_name, "redis")

    @classmethod
    def get_executable_name(cls, exe_type: str = "server") -> str:
        """获取可执行文件名"""
        platform_name = cls.get_current_platform()
        return cls.EXECUTABLE_NAMES.get(exe_type, {}).get(platform_name, "redis-server")


# 全局实例
REDIS_CONSTANTS = RedisConstants()