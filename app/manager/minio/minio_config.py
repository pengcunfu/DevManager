#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO 配置管理模块
提供 MinIO 配置文件的读取、修改和管理功能
"""

import os
import sys
import json
import shutil
import configparser
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any


class MinIOConfigManager:
    """MinIO 配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.default_paths = self._get_default_minio_paths()
        self.config_files = self._get_config_files()

    def _get_default_minio_paths(self) -> Dict[str, str]:
        """获取默认的MinIO安装路径"""
        paths = {}

        if sys.platform == "win32":
            # Windows 常见安装路径
            possible_paths = [
                r"C:\MinIO",
                r"C:\Program Files\MinIO",
                r"D:\MinIO",
                r"C:\Program Files (x86)\MinIO"
            ]

            for base_path in possible_paths:
                if os.path.exists(base_path):
                    paths['installation'] = base_path
                    paths['bin'] = os.path.join(base_path, 'minio.exe')
                    paths['config'] = os.path.join(base_path, 'config')
                    paths['data'] = os.path.join(base_path, 'data')
                    break

            # 默认配置文件位置
            if 'config' not in paths:
                minio_home = os.path.expanduser("~\\.minio")
                paths['config'] = minio_home
                paths['data'] = os.path.join(minio_home, 'data')

        else:
            # Linux/macOS 路径
            minio_home = os.path.expanduser("~/.minio")
            paths.update({
                'config': minio_home,
                'data': os.path.join(minio_home, 'data'),
                'bin': '/usr/local/bin/minio',
                'config_file': '/etc/minio/config.json'
            })

        return paths

    def _get_config_files(self) -> List[str]:
        """获取MinIO配置文件列表"""
        config_files = []

        if sys.platform == "win32":
            minio_home = os.path.expanduser("~\\.minio")
            config_files.append(os.path.join(minio_home, "config.json"))

            # 检查其他可能的位置
            program_data = os.environ.get('ProgramData', 'C:\\ProgramData')
            for root, dirs, files in os.walk(program_data):
                if 'MinIO' in root and 'config.json' in files:
                    config_files.append(os.path.join(root, 'config.json'))
        else:
            config_files.extend([
                '/etc/minio/config.json',
                os.path.expanduser("~/.minio/config.json")
            ])

        return [f for f in config_files if f and os.path.exists(f)]

    def find_minio_installation(self) -> Optional[str]:
        """查找MinIO安装路径"""
        if sys.platform == "win32":
            # 通过注册表查找
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\MinIO") as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if "MinIO" in subkey_name:
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
                result = subprocess.run(['minio', '--version'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 从版本信息中可能无法直接获取路径，但可以确认minio已安装
                    pass
            except:
                pass

        else:
            # Linux/macOS 使用 which 命令
            try:
                result = subprocess.run(['which', 'minio'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    minio_path = result.stdout.strip()
                    return minio_path
            except:
                pass

        return None

    def read_config(self, config_file: str = None) -> Optional[Dict[str, Any]]:
        """读取MinIO配置文件"""
        if not config_file:
            config_file = self.config_files[0] if self.config_files else None

        if not config_file or not os.path.exists(config_file):
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None

    def write_config(self, config_data: Dict[str, Any], config_file: str = None) -> bool:
        """写入MinIO配置文件"""
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
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            print(f"配置文件已更新: {config_file}")
            return True

        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前MinIO配置"""
        config_info = {
            'installation_path': None,
            'config_file': None,
            'data_dir': None,
            'access_key': None,
            'secret_key': None,
            'region': None,
            'address': None,
            'port': None
        }

        # 查找安装路径
        installation_path = self.find_minio_installation()
        if installation_path:
            config_info['installation_path'] = installation_path

        # 读取配置文件
        config_data = self.read_config()
        if config_data:
            # 保存配置文件路径
            if self.config_files:
                config_info['config_file'] = self.config_files[0]

            # 提取常用配置
            if 'credential' in config_data:
                credential = config_data['credential']
                config_info['access_key'] = credential.get('accessKey', '')
                config_info['secret_key'] = '********' if credential.get('secretKey') else ''

            if 'region' in config_data:
                config_info['region'] = config_data['region'].get('name', '')

            if 'server' in config_data:
                server = config_data['server']
                config_info['address'] = server.get('address', ':9000')
                if ':' in server.get('address', ':9000'):
                    config_info['port'] = server.get('address', ':9000').split(':')[-1]

        # 获取数据目录
        config_info['data_dir'] = self.default_paths.get('data', '')

        return config_info

    def update_basic_config(self, access_key: str = None, secret_key: str = None,
                           region: str = None, address: str = ':9000') -> bool:
        """更新基本配置参数"""
        config_data = self.read_config() or {}

        # 确保基本结构存在
        if 'credential' not in config_data:
            config_data['credential'] = {}
        if 'region' not in config_data:
            config_data['region'] = {}
        if 'server' not in config_data:
            config_data['server'] = {}

        # 更新配置
        if access_key:
            config_data['credential']['accessKey'] = access_key
        if secret_key:
            config_data['credential']['secretKey'] = secret_key
        if region:
            config_data['region']['name'] = region
        if address:
            config_data['server']['address'] = address

        return self.write_config(config_data)

    def add_performance_config(self) -> bool:
        """添加性能优化配置"""
        config_data = self.read_config() or {}

        # 性能优化配置
        performance_config = {
            # 缓存设置
            'cache': {
                'drives': [],
                'exclude': [],
                'expiry': 90,
                'maxuse': 80
            },
            # 压缩设置
            'compression': {
                'enabled': True,
                'extensions': ['.txt', '.log', '.csv', '.json', '.xml'],
                'mime_types': ['text/*', 'application/json', 'application/xml']
            }
        }

        config_data.update(performance_config)

        return self.write_config(config_data)

    def add_security_config(self) -> bool:
        """添加安全配置"""
        config_data = self.read_config() or {}

        # 安全配置
        security_config = {
            # SSL/TLS配置
            'tls': {
                'enabled': False,
                'cert_file': '',
                'key_file': ''
            },
            # 策略配置
            'policy': {
                'default': 'none',
                'builtin': ['readonly', 'readwrite', 'writeonly']
            }
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

        # 检查凭证配置
        if 'credential' not in config_data:
            result['errors'].append("缺少凭证配置")
            result['valid'] = False
        else:
            credential = config_data['credential']
            if not credential.get('accessKey'):
                result['warnings'].append("访问密钥为空")
            if not credential.get('secretKey'):
                result['errors'].append("秘密密钥为空")
                result['valid'] = False

        # 检查服务器配置
        if 'server' in config_data:
            server = config_data['server']
            address = server.get('address', ':9000')
            if ':' in address:
                try:
                    port = int(address.split(':')[-1])
                    if port < 1 or port > 65535:
                        result['errors'].append(f"无效的端口号: {port}")
                        result['valid'] = False
                except ValueError:
                    result['errors'].append(f"端口号格式错误: {address}")
                    result['valid'] = False

        # 检查数据目录
        data_dir = self.default_paths.get('data', '')
        if data_dir and not os.path.exists(data_dir):
            result['warnings'].append(f"数据目录不存在: {data_dir}")

        return result

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        config = self.get_current_config()

        summary = []
        summary.append("MinIO 配置摘要:")
        summary.append("=" * 50)

        if config['installation_path']:
            summary.append(f"安装路径: {config['installation_path']}")

        if config['config_file']:
            summary.append(f"配置文件: {config['config_file']}")

        if config['data_dir']:
            summary.append(f"数据目录: {config['data_dir']}")

        if config['address']:
            summary.append(f"服务地址: {config['address']}")

        if config['access_key']:
            summary.append(f"访问密钥: {config['access_key']}")

        if config['region']:
            summary.append(f"区域: {config['region']}")

        return "\n".join(summary)

    def generate_minio_env(self, access_key: str, secret_key: str,
                          data_dir: str = None, address: str = ":9000") -> str:
        """生成MinIO环境配置文件内容"""
        env_content = f"""# MinIO Environment Configuration
# Generated by DevManager

# MinIO访问凭证
MINIO_ROOT_USER={access_key}
MINIO_ROOT_PASSWORD={secret_key}

# MinIO数据目录
MINIO_VOLUMES={data_dir or self.default_paths.get('data', '/data')}

# MinIO服务地址
MINIO_ADDRESS={address}

# MinIO区域
MINIO_REGION=us-east-1

# MinIO日志级别 (debug, info, warn, error)
MINIO_LOGGER_HTTP_TARGET=
MINIO_LOGGER_HTTP_ENABLE=on

# 控制台日志
MINIO_BROWSER=on

# SSL/TLS (取消注释以启用)
# MINIO_CERT_FILE=/path/to/cert.pem
# MINIO_KEY_FILE=/path/to/key.pem

# 环境变量
MINIO_PROMETHEUS_AUTH_TYPE=public
MINIO_KMS_SECRET_KEY_FILE=
MINIO_NOTIFY_WEBHOOK_ENABLE=off
"""

        return env_content


def main():
    """主函数 - 用于命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="MinIO 配置管理工具")
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--validate', action='store_true', help='验证配置文件')
    parser.add_argument('--add-performance', action='store_true', help='添加性能优化配置')
    parser.add_argument('--add-security', action='store_true', help='添加安全配置')
    parser.add_argument('--summary', action='store_true', help='显示配置摘要')
    parser.add_argument('--generate-env', action='store_true', help='生成环境配置文件')

    args = parser.parse_args()

    config_manager = MinIOConfigManager()

    if args.show:
        config = config_manager.get_current_config()
        print("当前 MinIO 配置:")
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

    elif args.generate_env:
        access_key = input("请输入访问密钥: ").strip()
        secret_key = input("请输入秘密密钥: ").strip()
        env_content = config_manager.generate_minio_env(access_key, secret_key)

        env_file = "minio.env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✓ 环境配置文件已生成: {env_file}")

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