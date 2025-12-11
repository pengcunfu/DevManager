#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 配置管理模块
提供 PostgreSQL 配置文件的读取、修改和管理功能
"""

import os
import sys
import json
import shutil
import configparser
import subprocess
import re
from pathlib import Path
from typing import Dict, Optional, List, Any


class PostgreSQLConfigManager:
    """PostgreSQL 配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.default_paths = self._get_default_postgresql_paths()
        self.config_files = self._get_config_files()

    def _get_default_postgresql_paths(self) -> Dict[str, str]:
        """获取默认的PostgreSQL安装路径"""
        paths = {}

        if sys.platform == "win32":
            # Windows 常见安装路径
            possible_paths = [
                r"C:\Program Files\PostgreSQL",
                r"C:\Program Files (x86)\PostgreSQL",
                r"D:\PostgreSQL",
                r"E:\PostgreSQL"
            ]

            for base_path in possible_paths:
                if os.path.exists(base_path):
                    # 查找PostgreSQL版本目录
                    for item in os.listdir(base_path):
                        if item.startswith("PostgreSQL"):
                            version_path = os.path.join(base_path, item)
                            if os.path.isdir(version_path):
                                paths['installation'] = version_path
                                paths['bin'] = os.path.join(version_path, 'bin')
                                paths['data'] = os.path.join(version_path, 'data')
                                paths['config'] = os.path.join(version_path, 'data', 'postgresql.conf')
                                paths['hba_config'] = os.path.join(version_path, 'data', 'pg_hba.conf')
                                break
                    if 'installation' in paths:
                        break

            # 默认配置文件位置
            if 'config' not in paths:
                paths['config'] = r"C:\Program Files\PostgreSQL\16\data\postgresql.conf"
                paths['hba_config'] = r"C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
                paths['data'] = r"C:\Program Files\PostgreSQL\16\data"

        else:
            # Linux/macOS 路径
            paths.update({
                'config': '/etc/postgresql/16/main/postgresql.conf',
                'hba_config': '/etc/postgresql/16/main/pg_hba.conf',
                'data': '/var/lib/postgresql/16/main',
                'log': '/var/log/postgresql',
                'bin': '/usr/lib/postgresql/16/bin'
            })

        return paths

    def _get_config_files(self) -> List[str]:
        """获取PostgreSQL配置文件列表"""
        config_files = []

        if sys.platform == "win32":
            config_files.extend([
                self.default_paths.get('config', ''),
                self.default_paths.get('hba_config', '')
            ])
            # 检查其他可能的位置
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            for root, dirs, files in os.walk(program_files):
                if 'PostgreSQL' in root:
                    if 'postgresql.conf' in files:
                        config_files.append(os.path.join(root, 'postgresql.conf'))
                    if 'pg_hba.conf' in files:
                        config_files.append(os.path.join(root, 'pg_hba.conf'))
        else:
            config_files.extend([
                '/etc/postgresql/16/main/postgresql.conf',
                '/etc/postgresql/16/main/pg_hba.conf',
                '/var/lib/postgresql/16/main/postgresql.conf',
                '/var/lib/postgresql/16/main/pg_hba.conf'
            ])

        return [f for f in config_files if f and os.path.exists(f)]

    def find_postgresql_installation(self) -> Optional[str]:
        """查找PostgreSQL安装路径"""
        if sys.platform == "win32":
            # 通过注册表查找
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\PostgreSQL\Installations") as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                installation_path, _ = winreg.QueryValueEx(subkey, "Base Directory")
                                return installation_path
                            i += 1
                        except WindowsError:
                            break
            except:
                pass

            # 通过PATH环境变量查找
            try:
                result = subprocess.run(['psql', '--version'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 从版本信息中可能无法直接获取路径，但可以确认psql已安装
                    pass
            except:
                pass

        else:
            # Linux/macOS 使用 which 命令
            try:
                result = subprocess.run(['which', 'psql'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    psql_path = result.stdout.strip()
                    # psql 通常在 bin 目录下
                    bin_path = os.path.dirname(psql_path)
                    # 返回上级目录作为安装路径
                    return os.path.dirname(bin_path)
            except:
                pass

        return None

    def read_config(self, config_file: str = None) -> Optional[Dict[str, Any]]:
        """读取PostgreSQL配置文件"""
        if not config_file:
            config_file = self.config_files[0] if self.config_files else None

        if not config_file or not os.path.exists(config_file):
            return None

        try:
            config = {}
            with open(config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue

                    # 解析配置项
                    match = re.match(r'^\s*(\w+)\s*=\s*(.+)$', line)
                    if match:
                        key = match.group(1)
                        value = match.group(2).strip("'\"")
                        config[key] = value

            return config
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None

    def read_hba_config(self, hba_file: str = None) -> Optional[List[Dict[str, Any]]]:
        """读取pg_hba.conf配置文件"""
        if not hba_file:
            hba_file = self.default_paths.get('hba_config', '')
            if not hba_file or not os.path.exists(hba_file):
                for config_file in self.config_files:
                    if 'pg_hba.conf' in config_file:
                        hba_file = config_file
                        break

        if not hba_file or not os.path.exists(hba_file):
            return None

        try:
            hba_rules = []
            with open(hba_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue

                    # 解析HBA规则
                    parts = line.split()
                    if len(parts) >= 4:
                        rule = {
                            'line_num': line_num,
                            'type': parts[0],
                            'database': parts[1],
                            'user': parts[2],
                            'address': parts[3] if len(parts) > 3 else '',
                            'method': parts[4] if len(parts) > 4 else '',
                            'options': parts[5:] if len(parts) > 5 else []
                        }
                        hba_rules.append(rule)

            return hba_rules
        except Exception as e:
            print(f"读取HBA配置文件失败: {e}")
            return None

    def write_config(self, config_data: Dict[str, Any], config_file: str = None) -> bool:
        """写入PostgreSQL配置文件"""
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

            # 读取原文件，保留注释
            lines = []
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            # 更新配置项
            updated_lines = []
            config_keys = set(config_data.keys())

            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    updated_lines.append(line)
                    continue

                # 检查是否是需要更新的配置项
                match = re.match(r'^\s*(\w+)\s*=', line)
                if match and match.group(1) in config_keys:
                    key = match.group(1)
                    value = config_data[key]
                    new_line = f"{key} = '{value}'\n"
                    updated_lines.append(new_line)
                    config_keys.remove(key)
                else:
                    updated_lines.append(line)

            # 添加新的配置项
            for key in config_keys:
                value = config_data[key]
                new_line = f"{key} = '{value}'\n"
                updated_lines.append(new_line)

            with open(config_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)

            print(f"配置文件已更新: {config_file}")
            return True

        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前PostgreSQL配置"""
        config_info = {
            'installation_path': None,
            'config_file': None,
            'hba_config_file': None,
            'data_dir': None,
            'port': None,
            'max_connections': None,
            'shared_buffers': None,
            'effective_cache_size': None,
            'work_mem': None,
            'maintenance_work_mem': None
        }

        # 查找安装路径
        installation_path = self.find_postgresql_installation()
        if installation_path:
            config_info['installation_path'] = installation_path

        # 读取配置文件
        config_data = self.read_config()
        if config_data:
            # 保存配置文件路径
            if self.config_files:
                for config_file in self.config_files:
                    if 'postgresql.conf' in config_file:
                        config_info['config_file'] = config_file
                    elif 'pg_hba.conf' in config_file:
                        config_info['hba_config_file'] = config_file

            # 提取常用配置
            config_info['port'] = config_data.get('port', '5432')
            config_info['max_connections'] = config_data.get('max_connections', '100')
            config_info['shared_buffers'] = config_data.get('shared_buffers', '128MB')
            config_info['effective_cache_size'] = config_data.get('effective_cache_size', '4GB')
            config_info['work_mem'] = config_data.get('work_mem', '4MB')
            config_info['maintenance_work_mem'] = config_data.get('maintenance_work_mem', '64MB')

        return config_info

    def update_basic_config(self, port: int = 5432, max_connections: int = 100,
                           shared_buffers: str = '128MB') -> bool:
        """更新基本配置参数"""
        config_data = self.read_config() or {}

        # 更新配置
        config_data.update({
            'port': str(port),
            'max_connections': str(max_connections),
            'shared_buffers': shared_buffers
        })

        return self.write_config(config_data)

    def add_performance_config(self) -> bool:
        """添加性能优化配置"""
        config_data = self.read_config() or {}

        # 性能优化配置
        performance_config = {
            # 内存设置
            'shared_buffers': '256MB',
            'effective_cache_size': '1GB',
            'work_mem': '4MB',
            'maintenance_work_mem': '64MB',

            # 检查点设置
            'checkpoint_completion_target': '0.9',
            'wal_buffers': '16MB',
            'default_statistics_target': '100',

            # 连接设置
            'max_connections': '200',
            'superuser_reserved_connections': '3',

            # 日志设置
            'logging_collector': 'on',
            'log_directory': 'pg_log',
            'log_filename': 'postgresql-%Y-%m-%d_%H%M%S.log',
            'log_rotation_age': '1d',
            'log_rotation_size': '100MB',
            'log_min_duration_statement': '1000',
            'log_checkpoints': 'on',
            'log_connections': 'on',
            'log_disconnections': 'on',
            'log_lock_waits': 'on',

            # 自动清理设置
            'autovacuum': 'on',
            'autovacuum_max_workers': '3',
            'autovacuum_naptime': '1min'
        }

        config_data.update(performance_config)

        return self.write_config(config_data)

    def add_security_config(self) -> bool:
        """添加安全配置"""
        config_data = self.read_config() or {}

        # 安全配置
        security_config = {
            # SSL设置
            'ssl': 'on',

            # 认证设置
            'password_encryption': 'scram-sha-256',

            # 连接安全
            'listen_addresses': 'localhost',

            # 日志安全
            'log_connections': 'on',
            'log_disconnections': 'on',
            'log_hostname': 'on',

            # 限制设置
            'superuser_reserved_connections': '3',
            'max_prepared_transactions': '0',

            # 其他安全设置
            'zero_damaged_pages': 'off'
        }

        config_data.update(security_config)

        # 更新HBA配置文件
        self._update_hba_security_config()

        return self.write_config(config_data)

    def _update_hba_security_config(self) -> bool:
        """更新HBA安全配置"""
        hba_file = self.default_paths.get('hba_config', '')
        if not hba_file or not os.path.exists(hba_file):
            for config_file in self.config_files:
                if 'pg_hba.conf' in config_file:
                    hba_file = config_file
                    break

        if not hba_file or not os.path.exists(hba_file):
            print("未找到pg_hba.conf文件")
            return False

        try:
            # 备份原文件
            backup_file = hba_file + '.backup'
            shutil.copy2(hba_file, backup_file)

            # 读取原配置
            with open(hba_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 更新配置，将trust改为md5或scram-sha-256
            updated_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    parts = stripped.split()
                    if len(parts) >= 5:
                        # 将本地连接的trust改为scram-sha-256
                        if parts[0] in ['local', 'host'] and parts[4] == 'trust':
                            parts[4] = 'scram-sha-256'
                            line = ' '.join(parts) + '\n'

                updated_lines.append(line)

            # 写入更新后的配置
            with open(hba_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)

            print("HBA安全配置已更新")
            return True

        except Exception as e:
            print(f"更新HBA配置失败: {e}")
            return False

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
        port = config_data.get('port', '5432')
        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                result['errors'].append(f"无效的端口号: {port}")
                result['valid'] = False
        except ValueError:
            result['errors'].append(f"端口号格式错误: {port}")
            result['valid'] = False

        # 检查连接数配置
        max_connections = config_data.get('max_connections', '100')
        try:
            connections_int = int(max_connections)
            if connections_int < 1 or connections_int > 8192:
                result['warnings'].append(f"连接数可能不合理: {max_connections}")
        except ValueError:
            result['warnings'].append(f"连接数格式错误: {max_connections}")

        # 检查数据目录
        data_dir = config_data.get('data_directory', '')
        if data_dir and not os.path.exists(data_dir):
            result['warnings'].append(f"数据目录不存在: {data_dir}")

        # 检查内存配置
        shared_buffers = config_data.get('shared_buffers', '128MB')
        if not self._validate_memory_size(shared_buffers):
            result['warnings'].append(f"shared_buffers格式可能不正确: {shared_buffers}")

        return result

    def _validate_memory_size(self, size_str: str) -> bool:
        """验证内存大小格式"""
        if not size_str:
            return False

        # 检查是否以数字开头
        if not size_str[0].isdigit():
            return False

        # 检查单位
        valid_units = ['B', 'kB', 'MB', 'GB', 'TB']
        for unit in valid_units:
            if size_str.endswith(unit):
                return True

        return False

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        config = self.get_current_config()

        summary = []
        summary.append("PostgreSQL 配置摘要:")
        summary.append("=" * 50)

        if config['installation_path']:
            summary.append(f"安装路径: {config['installation_path']}")

        if config['config_file']:
            summary.append(f"配置文件: {config['config_file']}")

        summary.append(f"端口: {config.get('port', '5432')}")

        if config.get('max_connections'):
            summary.append(f"最大连接数: {config['max_connections']}")

        if config.get('shared_buffers'):
            summary.append(f"共享缓冲区: {config['shared_buffers']}")

        if config.get('effective_cache_size'):
            summary.append(f"有效缓存大小: {config['effective_cache_size']}")

        return "\n".join(summary)


def main():
    """主函数 - 用于命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL 配置管理工具")
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--validate', action='store_true', help='验证配置文件')
    parser.add_argument('--add-performance', action='store_true', help='添加性能优化配置')
    parser.add_argument('--add-security', action='store_true', help='添加安全配置')
    parser.add_argument('--summary', action='store_true', help='显示配置摘要')

    args = parser.parse_args()

    config_manager = PostgreSQLConfigManager()

    if args.show:
        config = config_manager.get_current_config()
        print("当前 PostgreSQL 配置:")
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