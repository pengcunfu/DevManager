#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 配置管理模块
提供 Redis 配置文件的读取、修改和管理功能
"""

import os
import sys
import json
import shutil
import configparser
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any


class RedisConfigManager:
    """Redis 配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.default_paths = self._get_default_redis_paths()
        self.config_files = self._get_config_files()

    def _get_default_redis_paths(self) -> Dict[str, str]:
        """获取默认的Redis安装路径"""
        paths = {}

        if sys.platform == "win32":
            # Windows 常见安装路径
            possible_paths = [
                r"C:\Redis",
                r"C:\Program Files\Redis",
                r"D:\Redis",
                r"C:\Program Files (x86)\Redis"
            ]

            for base_path in possible_paths:
                if os.path.exists(base_path):
                    paths['installation'] = base_path
                    paths['bin'] = os.path.join(base_path, 'bin')
                    paths['config'] = os.path.join(base_path, 'redis.windows.conf')
                    break

            # 默认配置文件位置
            if 'config' not in paths:
                paths['config'] = r"C:\ProgramData\Redis\redis.windows.conf"

        else:
            # Linux/macOS 路径
            paths.update({
                'config': '/etc/redis/redis.conf',
                'config_d': '/etc/redis/conf.d',
                'data': '/var/lib/redis',
                'log': '/var/log/redis'
            })

        return paths

    def _get_config_files(self) -> List[str]:
        """获取Redis配置文件列表"""
        config_files = []

        if sys.platform == "win32":
            config_files.append(self.default_paths.get('config', ''))
            # 检查其他可能的位置
            program_data = os.environ.get('ProgramData', 'C:\\ProgramData')
            for root, dirs, files in os.walk(program_data):
                if 'Redis' in root and 'redis.conf' in files:
                    config_files.append(os.path.join(root, 'redis.conf'))
        else:
            config_files.extend([
                '/etc/redis/redis.conf',
                '/etc/redis.conf',
                '~/.redis/redis.conf'
            ])

        return [f for f in config_files if f and os.path.exists(f)]

    def find_redis_installation(self) -> Optional[str]:
        """查找Redis安装路径"""
        if sys.platform == "win32":
            # 通过注册表查找
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Redis") as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if "Redis" in subkey_name:
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    installation_path, _ = winreg.QueryValueEx(subkey, "InstallPath")
                                    return installation_path
                            i += 1
                        except WindowsError:
                            break
            except:
                pass

            # 通过PATH环境变量查找
            try:
                result = subprocess.run(['redis-server', '--version'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 从版本信息中可能无法直接获取路径，但可以确认redis已安装
                    pass
            except:
                pass

        else:
            # Linux/macOS 使用 which 命令
            try:
                result = subprocess.run(['which', 'redis-server'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    redis_path = result.stdout.strip()
                    # redis-server 通常在 bin 目录下
                    bin_path = os.path.dirname(redis_path)
                    # 返回上级目录作为安装路径
                    return os.path.dirname(bin_path)
            except:
                pass

        return None

    def read_config(self, config_file: str = None) -> Optional[Dict[str, Any]]:
        """读取Redis配置文件"""
        if not config_file:
            config_file = self.config_files[0] if self.config_files else None

        if not config_file or not os.path.exists(config_file):
            return None

        try:
            config = {}
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        # 简单的键值对解析
                        if '#' in line:
                            line = line[:line.index('#')]
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()

            return config
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None

    def write_config(self, config_data: Dict[str, Any], config_file: str = None) -> bool:
        """写入Redis配置文件"""
        if not config_file:
            config_file = self.config_files[0] if self.config_files else None

        if not config_file:
            print("未找到配置文件路径")
            return False

        try:
            # 备份原配置文件
            backup_file = config_file + '.backup'
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_file)
                print(f"已备份原配置文件到: {backup_file}")

            with open(config_file, 'w', encoding='utf-8') as f:
                for key, value in config_data.items():
                    f.write(f"{key} {value}\n")

            print(f"配置文件已更新: {config_file}")
            return True

        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前Redis配置"""
        config_info = {
            'installation_path': None,
            'config_file': None,
            'data_dir': None,
            'port': None,
            'bind': None,
            'maxmemory': None,
            'timeout': None,
            'databases': None
        }

        # 查找安装路径
        installation_path = self.find_redis_installation()
        if installation_path:
            config_info['installation_path'] = installation_path

        # 读取配置文件
        config_data = self.read_config()
        if config_data:
            # 保存配置文件路径
            if self.config_files:
                config_info['config_file'] = self.config_files[0]

            # 提取常用配置
            config_info['port'] = config_data.get('port', '6379')
            config_info['bind'] = config_data.get('bind', '127.0.0.1')
            config_info['maxmemory'] = config_data.get('maxmemory', '')
            config_info['timeout'] = config_data.get('timeout', '300')
            config_info['databases'] = config_data.get('databases', '16')

        return config_info

    def update_basic_config(self, port: int = 6379, bind: str = '127.0.0.1',
                           max_connections: int = 1000, timeout: int = 300,
                           maxmemory: str = '256mb') -> bool:
        """更新基本配置参数"""
        config_data = self.read_config() or {}

        # 更新配置
        config_data.update({
            'port': str(port),
            'bind': bind,
            'timeout': str(timeout),
            'maxclients': str(max_connections),
            'maxmemory': maxmemory
        })

        return self.write_config(config_data)

    def add_performance_config(self) -> bool:
        """添加性能优化配置"""
        config_data = self.read_config() or {}

        # 性能优化配置
        performance_config = {
            # 内存管理
            'maxmemory-policy': 'allkeys-lru',
            'maxmemory-samples': 5,

            # 持久化配置
            'save': '900 1 300 10 60 10000',
            'rdbcompression': 'yes',
            'rdbchecksum': 'yes',
            'stop-writes-on-bgsave-error': 'yes',

            # AOF配置
            'appendonly': 'yes',
            'appendfsync': 'everysec',
            'no-appendfsync-on-rewrite': 'no',
            'auto-aof-rewrite-percentage': '100',
            'auto-aof-rewrite-min-size': '64mb',

            # 网络优化
            'tcp-keepalive': '300',
            'tcp-backlog': '511',

            # 日志配置
            'syslog-enabled': 'no',
            'logfile': '',
            'loglevel': 'notice'
        }

        config_data.update(performance_config)

        return self.write_config(config_data)

    def add_security_config(self) -> bool:
        """添加安全配置"""
        config_data = self.read_config() or {}

        # 安全配置
        security_config = {
            # 认证配置
            'requirepass': 'your_redis_password_here',
            'protected-mode': 'yes',

            # 网络安全
            'bind': '127.0.0.1',

            # 命令重命名
            'rename-command': 'CONFIG ""',
            'rename-command': 'DEBUG ""',
            'rename-command': 'EVAL ""',
            'rename-command': 'FLUSHDB ""',
            'rename-command': 'FLUSHALL ""',
            'rename-command': 'KEYS ""',
            'rename-command': 'SHUTDOWN ""'
        }

        config_data.update(security_config)

        return self.write_config(config_data)

    def validate_config(self) -> Dict[str, Any]:
        """验证配置文件"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        config_data = self.read_config()
        if not config_data:
            result['valid'] = False
            result['errors'].append("无法读取配置文件")
            return result

        # 检查端口配置
        port = config_data.get('port', '6379')
        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                result['errors'].append(f"无效的端口号: {port}")
                result['valid'] = False
        except ValueError:
            result['errors'].append(f"端口号格式错误: {port}")
            result['valid'] = False

        # 检查数据目录
        if 'dir' in config_data:
            datadir = config_data['dir']
            if not os.path.exists(datadir):
                result['warnings'].append(f"数据目录不存在: {datadir}")

        # 检查内存限制
        maxmemory = config_data.get('maxmemory', '')
        if maxmemory and maxmemory.lower() == '0':
            result['warnings'].append("最大内存限制为0，可能导致系统内存耗尽")

        return result

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        config = self.get_current_config()

        summary = []
        summary.append("Redis 配置摘要:")
        summary.append("=" * 50)

        if config['installation_path']:
            summary.append(f"安装路径: {config['installation_path']}")

        if config['config_file']:
            summary.append(f"配置文件: {config['config_file']}")

        summary.append(f"端口: {config.get('port', '6379')}")
        summary.append(f"绑定地址: {config.get('bind', '127.0.0.1')}")

        if config.get('maxmemory'):
            summary.append(f"最大内存: {config['maxmemory']}")

        if config.get('timeout'):
            summary.append(f"超时时间: {config['timeout']}s")

        if config.get('databases'):
            summary.append(f"数据库数量: {config['databases']}")

        return "\n".join(summary)


def main():
    """主函数 - 用于命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="Redis 配置管理工具")
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--validate', action='store_true', help='验证配置文件')
    parser.add_argument('--add-performance', action='store_true', help='添加性能优化配置')
    parser.add_argument('--add-security', action='store_true', help='添加安全配置')
    parser.add_argument('--summary', action='store_true', help='显示配置摘要')

    args = parser.parse_args()

    config_manager = RedisConfigManager()

    if args.show:
        config = config_manager.get_current_config()
        print("当前 Redis 配置:")
        for key, value in config.items():
            if value:
                print(f"  {key}: {value}")

    elif args.validate:
        result = config_manager.validate_config()
        if result['valid']:
            print("✓ 配置文件有效")
        else:
            print("✗ 配置文件存在问题:")

        if result['errors']:
            print("\n错误:")
            for error in result['errors']:
                print(f"  - {error}")

        if result['warnings']:
            print("\n警告:")
            for warning in result['warnings']:
                print(f"  - {warning}")

    elif args.add_performance:
        if config_manager.add_performance_config():
            print("✓ 性能优化配置已添加")
        else:
            print("✗ 添加性能配置失败")

    elif args.add_security:
        if config_manager.add_security_config():
            print("✓ 安全配置已添加")
        else:
            print("✗ 添加安全配置失败")

    elif args.summary:
        print(config_manager.get_config_summary())

    else:
        # 默认显示配置摘要
        print(config_manager.get_config_summary())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)