#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 配置管理模块
提供 MongoDB 配置文件的读取、修改和管理功能
"""

import os
import sys
import json
import shutil
import configparser
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any


class MongoDBConfigManager:
    """MongoDB 配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.default_paths = self._get_default_mongodb_paths()
        self.config_files = self._get_config_files()

    def _get_default_mongodb_paths(self) -> Dict[str, str]:
        """获取默认的MongoDB安装路径"""
        paths = {}

        if sys.platform == "win32":
            # Windows 常见安装路径
            possible_paths = [
                r"C:\MongoDB",
                r"C:\Program Files\MongoDB",
                r"D:\MongoDB",
                r"C:\Program Files (x86)\MongoDB"
            ]

            for base_path in possible_paths:
                if os.path.exists(base_path):
                    paths['installation'] = base_path
                    paths['bin'] = os.path.join(base_path, 'Server', 'bin')
                    paths['config'] = os.path.join(base_path, 'Server', 'bin', 'mongod.cfg')
                    paths['data'] = os.path.join(base_path, 'Server', 'data')
                    break

            # 默认配置文件位置
            if 'config' not in paths:
                program_data = os.environ.get('ProgramData', 'C:\\ProgramData')
                paths['config'] = os.path.join(program_data, 'MongoDB', 'mongod.cfg')
                paths['data'] = os.path.join(program_data, 'MongoDB', 'Data')
                paths['log'] = os.path.join(program_data, 'MongoDB', 'Log')

        else:
            # Linux/macOS 路径
            paths.update({
                'config': '/etc/mongod.conf',
                'data': '/var/lib/mongodb',
                'log': '/var/log/mongodb',
                'bin': '/usr/bin'
            })

        return paths

    def _get_config_files(self) -> List[str]:
        """获取MongoDB配置文件列表"""
        config_files = []

        if sys.platform == "win32":
            config_files.append(self.default_paths.get('config', ''))
            # 检查其他可能的位置
            program_data = os.environ.get('ProgramData', 'C:\\ProgramData')
            for root, dirs, files in os.walk(program_data):
                if 'MongoDB' in root and ('mongod.cfg' in files or 'mongod.conf' in files):
                    config_files.append(os.path.join(root, 'mongod.cfg' if 'mongod.cfg' in files else 'mongod.conf'))
        else:
            config_files.extend([
                '/etc/mongod.conf',
                '/etc/mongodb.conf',
                '~/.mongod.conf'
            ])

        return [f for f in config_files if f and os.path.exists(f)]

    def get_config_files(self) -> List[str]:
        """获取可用的配置文件列表"""
        return self._get_config_files()

    def find_mongodb_installation(self) -> Optional[str]:
        """查找MongoDB安装路径"""
        if sys.platform == "win32":
            # 通过注册表查找
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\MongoDB") as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if "MongoDB" in subkey_name:
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
                result = subprocess.run(['mongod', '--version'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 从版本信息中可能无法直接获取路径，但可以确认mongodb已安装
                    pass
            except:
                pass

        else:
            # Linux/macOS 使用 which 命令
            try:
                result = subprocess.run(['which', 'mongod'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    mongod_path = result.stdout.strip()
                    # mongod 通常在 bin 目录下
                    bin_path = os.path.dirname(mongod_path)
                    # 返回上级目录作为安装路径
                    return os.path.dirname(bin_path)
            except:
                pass

        return None

    def read_config(self, config_file: str = None) -> Optional[Dict[str, Any]]:
        """读取MongoDB配置文件"""
        if not config_file:
            config_file = self.config_files[0] if self.config_files else None

        if not config_file or not os.path.exists(config_file):
            return None

        try:
            config = {}
            with open(config_file, 'r', encoding='utf-8') as f:
                current_section = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # 检查是否是节（[section]）
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        config[current_section] = {}
                    else:
                        # 简单的键值对解析
                        if ':' in line and not line.startswith(' '):
                            if '#' in line:
                                line = line[:line.index('#')]
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()

                            if current_section:
                                config[current_section][key] = value
                            else:
                                config[key] = value

            return config
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None

    def write_config(self, config_data: Dict[str, Any], config_file: str = None) -> bool:
        """写入MongoDB配置文件"""
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
                    if isinstance(value, dict):
                        f.write(f"\n[{key}]\n")
                        for sub_key, sub_value in value.items():
                            f.write(f"  {sub_key}: {sub_value}\n")
                    else:
                        f.write(f"{key}: {value}\n")

            print(f"配置文件已更新: {config_file}")
            return True

        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前MongoDB配置"""
        config_info = {
            'installation_path': None,
            'config_file': None,
            'data_dir': None,
            'log_dir': None,
            'port': None,
            'bind_ip': None,
            'max_connections': None,
            'auth_enabled': None
        }

        # 查找安装路径
        installation_path = self.find_mongodb_installation()
        if installation_path:
            config_info['installation_path'] = installation_path

        # 读取配置文件
        config_data = self.read_config()
        if config_data:
            # 保存配置文件路径
            if self.config_files:
                config_info['config_file'] = self.config_files[0]

            # 提取常用配置
            if 'net' in config_data:
                net_config = config_data['net']
                config_info['port'] = net_config.get('port', '27017')
                config_info['bind_ip'] = net_config.get('bindIp', '127.0.0.1')

            if 'storage' in config_data:
                storage_config = config_data['storage']
                config_info['data_dir'] = storage_config.get('dbPath', self.default_paths.get('data', ''))

            if 'systemLog' in config_data:
                log_config = config_data['systemLog']
                config_info['log_dir'] = log_config.get('path', self.default_paths.get('log', ''))

            if 'security' in config_data:
                security_config = config_data['security']
                config_info['auth_enabled'] = security_config.get('authorization', 'disabled')

            if 'processManagement' in config_data:
                process_config = config_data['processManagement']
                config_info['max_connections'] = process_config.get('maxConns', '')

        return config_info

    def update_basic_config(self, port: int = 27017, bind_ip: str = '127.0.0.1',
                           max_connections: int = 1000, data_dir: str = None,
                           log_dir: str = None) -> bool:
        """更新基本配置参数"""
        config_data = self.read_config() or {}

        # 确保基本结构存在
        if 'net' not in config_data:
            config_data['net'] = {}
        if 'storage' not in config_data:
            config_data['storage'] = {}
        if 'systemLog' not in config_data:
            config_data['systemLog'] = {}
        if 'processManagement' not in config_data:
            config_data['processManagement'] = {}

        # 更新配置
        config_data['net'].update({
            'port': str(port),
            'bindIp': bind_ip
        })

        config_data['storage']['dbPath'] = data_dir or self.default_paths.get('data', '/var/lib/mongodb')
        config_data['systemLog']['path'] = log_dir or os.path.join(self.default_paths.get('log', '/var/log/mongodb'), 'mongod.log')
        config_data['processManagement']['maxConns'] = str(max_connections)

        return self.write_config(config_data)

    def enable_authentication(self) -> bool:
        """启用认证"""
        config_data = self.read_config() or {}

        if 'security' not in config_data:
            config_data['security'] = {}

        config_data['security']['authorization'] = 'enabled'

        return self.write_config(config_data)

    def disable_authentication(self) -> bool:
        """禁用认证"""
        config_data = self.read_config() or {}

        if 'security' not in config_data:
            config_data['security'] = {}

        config_data['security']['authorization'] = 'disabled'

        return self.write_config(config_data)

    def add_performance_config(self) -> bool:
        """添加性能优化配置"""
        config_data = self.read_config() or {}

        # 性能优化配置
        if 'processManagement' not in config_data:
            config_data['processManagement'] = {}
        if 'storage' not in config_data:
            config_data['storage'] = {}
        if 'operationProfiling' not in config_data:
            config_data['operationProfiling'] = {}

        config_data['processManagement'].update({
            'fork': 'true',
            'pidFilePath': '/var/run/mongodb/mongod.pid'
        })

        config_data['storage'].update({
            'journal': {'enabled': 'true'},
            'wiredTiger': {
                'engineConfig': {
                    'cacheSizeGB': '1'
                }
            }
        })

        config_data['operationProfiling'] = {
            'slowOpThresholdMs': '100',
            'mode': 'slowOp'
        }

        return self.write_config(config_data)

    def add_security_config(self) -> bool:
        """添加安全配置"""
        config_data = self.read_config() or {}

        # 安全配置
        if 'security' not in config_data:
            config_data['security'] = {}

        config_data['security'].update({
            'authorization': 'enabled',
            'javascriptEnabled': 'false'
        })

        # 网络安全配置
        if 'net' not in config_data:
            config_data['net'] = {}

        config_data['net'].update({
            'bindIp': '127.0.0.1',
            'maxIncomingConnections': '1000'
        })

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
        if 'net' in config_data:
            net_config = config_data['net']
            port = net_config.get('port', '27017')
            try:
                port_int = int(port)
                if port_int < 1 or port_int > 65535:
                    result['errors'].append(f"无效的端口号: {port}")
                    result['valid'] = False
            except ValueError:
                result['errors'].append(f"端口号格式错误: {port}")
                result['valid'] = False

        # 检查数据目录
        if 'storage' in config_data:
            storage_config = config_data['storage']
            data_dir = storage_config.get('dbPath', '')
            if data_dir and not os.path.exists(data_dir):
                result['warnings'].append(f"数据目录不存在: {data_dir}")

        # 检查日志目录
        if 'systemLog' in config_data:
            log_config = config_data['systemLog']
            log_path = log_config.get('path', '')
            if log_path:
                log_dir = os.path.dirname(log_path)
                if log_dir and not os.path.exists(log_dir):
                    result['warnings'].append(f"日志目录不存在: {log_dir}")

        return result

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        config = self.get_current_config()

        summary = []
        summary.append("MongoDB 配置摘要:")
        summary.append("=" * 50)

        if config['installation_path']:
            summary.append(f"安装路径: {config['installation_path']}")

        if config['config_file']:
            summary.append(f"配置文件: {config['config_file']}")

        summary.append(f"端口: {config.get('port', '27017')}")
        summary.append(f"绑定IP: {config.get('bind_ip', '127.0.0.1')}")

        if config['data_dir']:
            summary.append(f"数据目录: {config['data_dir']}")

        if config['log_dir']:
            summary.append(f"日志目录: {config['log_dir']}")

        if config['auth_enabled']:
            summary.append(f"认证状态: {'启用' if config['auth_enabled'] == 'enabled' else '禁用'}")

        return "\n".join(summary)


def main():
    """主函数 - 用于命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="MongoDB 配置管理工具")
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--validate', action='store_true', help='验证配置文件')
    parser.add_argument('--add-performance', action='store_true', help='添加性能优化配置')
    parser.add_argument('--add-security', action='store_true', help='添加安全配置')
    parser.add_argument('--enable-auth', action='store_true', help='启用认证')
    parser.add_argument('--disable-auth', action='store_true', help='禁用认证')
    parser.add_argument('--summary', action='store_true', help='显示配置摘要')

    args = parser.parse_args()

    config_manager = MongoDBConfigManager()

    if args.show:
        config = config_manager.get_current_config()
        print("当前 MongoDB 配置:")
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

    elif args.enable_auth:
        if config_manager.enable_authentication():
            print("✓ 认证已启用")
        else:
            print("✗ 启用认证失败")

    elif args.disable_auth:
        if config_manager.disable_authentication():
            print("✓ 认证已禁用")
        else:
            print("✗ 禁用认证失败")

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