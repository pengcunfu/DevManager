#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 配置管理模块
提供 MySQL 配置文件的读取、修改和管理功能
"""

import os
import sys
import json
import shutil
import configparser
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any


class MySQLConfigManager:
    """MySQL 配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.default_paths = self._get_default_mysql_paths()
        self.config_files = self._get_config_files()

    def _get_default_mysql_paths(self) -> Dict[str, str]:
        """获取默认的MySQL安装路径"""
        paths = {}

        if sys.platform == "win32":
            # Windows 常见安装路径
            possible_paths = [
                r"C:\Program Files\MySQL",
                r"C:\Program Files (x86)\MySQL",
                r"D:\MySQL",
                r"E:\MySQL"
            ]

            for base_path in possible_paths:
                if os.path.exists(base_path):
                    # 查找MySQL版本目录
                    for item in os.listdir(base_path):
                        if item.startswith("MySQL Server"):
                            version_path = os.path.join(base_path, item)
                            if os.path.isdir(version_path):
                                paths['installation'] = version_path
                                paths['bin'] = os.path.join(version_path, 'bin')
                                paths['data'] = os.path.join(version_path, 'data')
                                paths['config'] = os.path.join(version_path, 'my.ini')
                                break
                    if 'installation' in paths:
                        break

            # 默认配置文件位置
            if 'config' not in paths:
                paths['config'] = r"C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"
                paths['data'] = r"C:\ProgramData\MySQL\MySQL Server 8.0\Data"

        else:
            # Linux/macOS 路径
            paths.update({
                'config': '/etc/mysql/my.cnf',
                'config_d': '/etc/mysql/conf.d',
                'data': '/var/lib/mysql',
                'log': '/var/log/mysql'
            })

        return paths

    def _get_config_files(self) -> List[str]:
        """获取MySQL配置文件列表"""
        config_files = []

        if sys.platform == "win32":
            config_files.append(self.default_paths.get('config', ''))
            # 检查其他可能的位置
            program_data = os.environ.get('ProgramData', 'C:\\ProgramData')
            for root, dirs, files in os.walk(program_data):
                if 'MySQL' in root and 'my.ini' in files:
                    config_files.append(os.path.join(root, 'my.ini'))
        else:
            config_files.extend([
                '/etc/mysql/my.cnf',
                '/etc/my.cnf',
                '~/.my.cnf'
            ])

        return [f for f in config_files if f and os.path.exists(f)]

    def find_mysql_installation(self) -> Optional[str]:
        """查找MySQL安装路径"""
        if sys.platform == "win32":
            # 通过注册表查找
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\MySQL AB") as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if "MySQL Server" in subkey_name:
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    installation_path, _ = winreg.QueryValueEx(subkey, "Location")
                                    return installation_path
                            i += 1
                        except WindowsError:
                            break
            except:
                pass

            # 通过PATH环境变量查找
            try:
                result = subprocess.run(['mysql', '--version'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 从版本信息中可能无法直接获取路径，但可以确认mysql已安装
                    pass
            except:
                pass

        else:
            # Linux/macOS 使用 which 命令
            try:
                result = subprocess.run(['which', 'mysql'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    mysql_path = result.stdout.strip()
                    # mysql 通常在 bin 目录下
                    bin_path = os.path.dirname(mysql_path)
                    # 返回上级目录作为安装路径
                    return os.path.dirname(bin_path)
            except:
                pass

        return None

    def read_config(self, config_file: str = None) -> Optional[Dict[str, Any]]:
        """读取MySQL配置文件"""
        if not config_file:
            config_file = self.config_files[0] if self.config_files else None

        if not config_file or not os.path.exists(config_file):
            return None

        try:
            config = configparser.ConfigParser()
            config.read(config_file, encoding='utf-8')

            result = {}
            for section_name in config.sections():
                result[section_name] = dict(config[section_name])

            return result
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None

    def write_config(self, config_data: Dict[str, Any], config_file: str = None) -> bool:
        """写入MySQL配置文件"""
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

            config = configparser.ConfigParser()

            for section_name, section_data in config_data.items():
                config.add_section(section_name)
                for key, value in section_data.items():
                    config.set(section_name, key, str(value))

            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)

            print(f"配置文件已更新: {config_file}")
            return True

        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前MySQL配置"""
        config_info = {
            'installation_path': None,
            'config_file': None,
            'data_dir': None,
            'port': None,
            'socket': None,
            'max_connections': None,
            'innodb_buffer_pool': None
        }

        # 查找安装路径
        installation_path = self.find_mysql_installation()
        if installation_path:
            config_info['installation_path'] = installation_path

        # 读取配置文件
        config_data = self.read_config()
        if config_data:
            # 保存配置文件路径
            if self.config_files:
                config_info['config_file'] = self.config_files[0]

            # 提取常用配置
            if 'mysqld' in config_data:
                mysqld_config = config_data['mysqld']
                config_info['port'] = mysqld_config.get('port', '3306')
                config_info['socket'] = mysqld_config.get('socket', '')
                config_info['max_connections'] = mysqld_config.get('max_connections', '')
                config_info['innodb_buffer_pool'] = mysqld_config.get('innodb_buffer_pool_size', '')

            if 'client' in config_data:
                client_config = config_data['client']
                if 'port' not in config_info:
                    config_info['port'] = client_config.get('port', '3306')

        return config_info

    def update_basic_config(self, port: int = 3306, max_connections: int = 151,
                           innodb_buffer: str = '128M') -> bool:
        """更新基本配置参数"""
        config_data = self.read_config() or {}

        # 确保 [mysqld] 节存在
        if 'mysqld' not in config_data:
            config_data['mysqld'] = {}

        # 更新配置
        config_data['mysqld'].update({
            'port': str(port),
            'max_connections': str(max_connections),
            'innodb_buffer_pool_size': innodb_buffer
        })

        # 确保 [client] 节存在
        if 'client' not in config_data:
            config_data['client'] = {}

        config_data['client']['port'] = str(port)

        return self.write_config(config_data)

    def add_performance_config(self) -> bool:
        """添加性能优化配置"""
        config_data = self.read_config() or {}

        # 确保 [mysqld] 节存在
        if 'mysqld' not in config_data:
            config_data['mysqld'] = {}

        # 性能优化配置
        performance_config = {
            # 缓冲区设置
            'innodb_buffer_pool_size': '256M',
            'innodb_log_file_size': '64M',
            'innodb_log_buffer_size': '8M',
            'key_buffer_size': '32M',
            'sort_buffer_size': '2M',
            'read_buffer_size': '2M',
            'read_rnd_buffer_size': '8M',

            # 连接设置
            'max_connections': '200',
            'max_connect_errors': '1000',
            'wait_timeout': '28800',
            'interactive_timeout': '28800',

            # 查询缓存
            'query_cache_type': '1',
            'query_cache_size': '64M',
            'query_cache_limit': '2M',

            # 临时表设置
            'tmp_table_size': '64M',
            'max_heap_table_size': '64M',

            # InnoDB 设置
            'innodb_flush_log_at_trx_commit': '2',
            'innodb_lock_wait_timeout': '50',
            'innodb_file_per_table': '1'
        }

        config_data['mysqld'].update(performance_config)

        return self.write_config(config_data)

    def add_security_config(self) -> bool:
        """添加安全配置"""
        config_data = self.read_config() or {}

        if 'mysqld' not in config_data:
            config_data['mysqld'] = {}

        # 安全配置
        security_config = {
            'local_infile': '0',  # 禁用 LOAD DATA LOCAL INFILE
            'skip_show_database': '1',  # 隐藏其他数据库
            'skip_name_resolve': '1',  # 禁用DNS解析
            'max_allowed_packet': '16M',  # 限制数据包大小

            # 日志设置
            'log_error': 'mysql_error.log',
            'slow_query_log': '1',
            'slow_query_log_file': 'mysql_slow.log',
            'long_query_time': '2',
            'log_queries_not_using_indexes': '1'
        }

        config_data['mysqld'].update(security_config)

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

        # 检查必要的节
        if 'mysqld' not in config_data:
            result['warnings'].append("缺少 [mysqld] 配置节")

        if 'client' not in config_data:
            result['warnings'].append("缺少 [client] 配置节")

        # 检查端口配置
        mysqld_config = config_data.get('mysqld', {})
        port = mysqld_config.get('port', '3306')
        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                result['errors'].append(f"无效的端口号: {port}")
                result['valid'] = False
        except ValueError:
            result['errors'].append(f"端口号格式错误: {port}")
            result['valid'] = False

        # 检查数据目录
        if 'datadir' in mysqld_config:
            datadir = mysqld_config['datadir']
            if not os.path.exists(datadir):
                result['warnings'].append(f"数据目录不存在: {datadir}")

        return result

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        config = self.get_current_config()

        summary = []
        summary.append("MySQL 配置摘要:")
        summary.append("=" * 50)

        if config['installation_path']:
            summary.append(f"安装路径: {config['installation_path']}")

        if config['config_file']:
            summary.append(f"配置文件: {config['config_file']}")

        summary.append(f"端口: {config.get('port', '3306')}")

        if config.get('max_connections'):
            summary.append(f"最大连接数: {config['max_connections']}")

        if config.get('innodb_buffer_pool'):
            summary.append(f"InnoDB缓冲池: {config['innodb_buffer_pool']}")

        return "\n".join(summary)


def main():
    """主函数 - 用于命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="MySQL 配置管理工具")
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--validate', action='store_true', help='验证配置文件')
    parser.add_argument('--add-performance', action='store_true', help='添加性能优化配置')
    parser.add_argument('--add-security', action='store_true', help='添加安全配置')
    parser.add_argument('--summary', action='store_true', help='显示配置摘要')

    args = parser.parse_args()

    config_manager = MySQLConfigManager()

    if args.show:
        config = config_manager.get_current_config()
        print("当前 MySQL 配置:")
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