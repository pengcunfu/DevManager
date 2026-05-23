#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 配置管理模块
提供 MySQL 配置文件的读取、修改和管理功能
支持 MySQL 8.0.44 版本
"""

import os
import json
import shutil
import configparser
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any


# MySQL 8.0.44 常量配置
MYSQL_VERSION = "8.0.44"
MYSQL_DOWNLOAD_URL = "https://cdn.mysql.com//Downloads/MySQL-8.0/mysql-8.0.44-winx64.zip"
DEFAULT_PORT = 3306
DEFAULT_DATA_DIR = "data"
DEFAULT_CHARSET = "utf8mb4"
DEFAULT_COLLATION = "utf8mb4_unicode_ci"

# 默认配置模板
DEFAULT_CONFIG_TEMPLATE = {
    "mysqld": {
        "port": DEFAULT_PORT,
        "basedir": None,  # 运行时设置
        "datadir": None,  # 运行时设置
        "character-set-server": DEFAULT_CHARSET,
        "collation-server": DEFAULT_COLLATION,
        "default-storage-engine": "INNODB",
        "default_authentication_plugin": "mysql_native_password",
        # 临时目录
        "tmpdir": None,  # 运行时设置
        # 可选的初始化配置，用户可后续自行调整
        # "skip-grant-tables": None,  # 如需无密码登录可取消注释
    },
    "client": {
        "port": DEFAULT_PORT,
        "default-character-set": DEFAULT_CHARSET,
    },
    "mysql": {
        "default-character-set": DEFAULT_CHARSET,
    }
}


class MySQLConfigManager:
    """MySQL 配置管理器"""

    def __init__(self, installation_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            installation_path: MySQL安装路径，如果为None则自动检测
        """
        self.installation_path = installation_path
        self.mysql_version = MYSQL_VERSION
        self.default_paths = self._get_default_mysql_paths()
        self.config_files = self._get_config_files()

    def _get_default_mysql_paths(self) -> Dict[str, str]:
        """获取默认的MySQL安装路径"""
        paths = {}

        # 默认安装目录
        default_install_path = fr"D:\Env\mysql\mysql-{MYSQL_VERSION}"

        # 如果有指定安装路径，使用指定路径
        if self.installation_path:
            installation_path = self.installation_path
        else:
            installation_path = default_install_path

        # 设置路径
        paths['installation'] = installation_path
        paths['bin'] = os.path.join(installation_path, 'bin')
        paths['data'] = os.path.join(installation_path, 'data')
        paths['config'] = os.path.join(installation_path, 'my.ini')
        paths['log'] = os.path.join(installation_path, 'logs')
        paths['temp'] = os.path.join(installation_path, 'temp')

        # 检查D:\Env\mysql目录下是否有其他版本作为备选
        if not os.path.exists(paths['installation']):
            base_mysql_dir = "D:\\Env\\mysql"
            if os.path.exists(base_mysql_dir):
                for item in os.listdir(base_mysql_dir):
                    item_path = os.path.join(base_mysql_dir, item)
                    if os.path.isdir(item_path) and item.startswith("mysql-"):
                        # 检查是否有bin目录（表示这是一个完整的MySQL安装）
                        bin_path = os.path.join(item_path, 'bin')
                        if os.path.exists(bin_path):
                            paths['installation'] = item_path
                            paths['bin'] = bin_path
                            paths['data'] = os.path.join(item_path, 'data')
                            paths['config'] = os.path.join(item_path, 'my.ini')
                            paths['log'] = os.path.join(item_path, 'logs')
                            paths['temp'] = os.path.join(item_path, 'temp')
                            break

        return paths

    def _get_config_files(self) -> List[str]:
        """获取MySQL配置文件列表"""
        config_files = []

        # 优先使用当前安装路径的配置文件
        config_file = self.default_paths.get('config', '')
        if config_file:
            config_files.append(config_file)

        # 检查其他可能的位置
        possible_locations = [
            # 默认安装目录
            fr"D:\Env\mysql\mysql-{MYSQL_VERSION}\my.ini",
            # 其他可能的安装位置
            fr"D:\Env\mysql\mysql-{MYSQL_VERSION}\\conf\\my.ini",
        ]

        # 检查D:\Env\mysql目录下是否有其他版本
        base_mysql_dir = "D:\\Env\\mysql"
        if os.path.exists(base_mysql_dir):
            for item in os.listdir(base_mysql_dir):
                item_path = os.path.join(base_mysql_dir, item)
                if os.path.isdir(item_path) and item.startswith("mysql-"):
                    config_file = os.path.join(item_path, 'my.ini')
                    if os.path.exists(config_file):
                        possible_locations.append(config_file)

        # 去重并过滤存在的文件
        unique_files = list(set(possible_locations))
        return [f for f in unique_files if f and os.path.exists(f)]

    def find_mysql_installation(self) -> Optional[str]:
        """查找MySQL安装路径"""
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

    def create_config_file(self, installation_path: str, data_dir: Optional[str] = None,
                          port: int = DEFAULT_PORT) -> str:
        """创建MySQL配置文件

        Args:
            installation_path: MySQL安装路径
            data_dir: 数据目录，默认为安装路径下的data目录
            port: 端口号，默认3306

        Returns:
            配置文件路径
        """
        if data_dir is None:
            data_dir = os.path.join(installation_path, DEFAULT_DATA_DIR)

        # 创建必要的目录
        dirs_to_create = [
            data_dir,
            os.path.join(installation_path, 'temp'),  # 简化配置只需要临时目录
        ]

        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)
            print(f"确保目录存在: {dir_path}")

        # 基于模板创建配置
        config_data = DEFAULT_CONFIG_TEMPLATE.copy()
        config_data["mysqld"]["basedir"] = installation_path
        config_data["mysqld"]["datadir"] = data_dir
        config_data["mysqld"]["port"] = str(port)

        # 使用原始Windows路径格式
        temp_dir = os.path.join(installation_path, 'temp')
        config_data["mysqld"]["tmpdir"] = temp_dir
        config_data["client"]["port"] = str(port)

        # 写入配置文件
        config_file = os.path.join(installation_path, "my.ini")

        try:
            # 直接删除原配置文件，确保使用新的简化配置
            if os.path.exists(config_file):
                os.remove(config_file)
                print(f"已删除原配置文件: {config_file}")

            # 创建新的配置文件
            config = configparser.ConfigParser()
            for section_name, section_data in config_data.items():
                if section_data:  # 跳过空节
                    config.add_section(section_name)
                    for key, value in section_data.items():
                        if value is not None:  # 跳过None值
                            # 确保路径中没有None值，并且路径格式正确
                            if value and 'None' not in str(value):
                                config.set(section_name, key, str(value))

            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)

            print(f"配置文件已创建: {config_file}")
            print(f"数据目录: {data_dir}")
            print(f"临时目录: {os.path.join(installation_path, 'temp')}")
            return config_file

        except Exception as e:
            print(f"创建配置文件失败: {e}")
            raise

    def get_template_config(self) -> Dict[str, Any]:
        """获取默认配置模板"""
        return DEFAULT_CONFIG_TEMPLATE.copy()


