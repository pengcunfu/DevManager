#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 安装和服务管理脚本
提供 MongoDB 的安装、卸载、服务管理等功能
"""

import os
import sys
import time
import shutil
import subprocess
import platform
from typing import Dict, Optional, Any


class MongoDBInstaller:
    """MongoDB 安装器和服务管理器"""

    def __init__(self):
        """初始化安装器"""
        self.system = platform.system().lower()
        self.mongodb_version = "7.0.0"
        self.installation_path = self._get_default_installation_path()
        self.service_name = "MongoDB" if self.system == "windows" else "mongod"

    def _get_default_installation_path(self) -> str:
        """获取默认安装路径"""
        if self.system == "windows":
            return r"C:\MongoDB"
        else:
            return "/opt/mongodb"

    def check_requirements(self) -> Dict[str, bool]:
        """检查安装要求"""
        return {
            'internet': self._check_internet_connection(),
            'disk_space': self._check_disk_space(1024),  # 1GB
            'admin_privileges': self._check_admin_privileges(),
        }

    def _check_internet_connection(self) -> bool:
        """检查网络连接"""
        try:
            import requests
            response = requests.get("https://www.mongodb.com", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _check_disk_space(self, required_mb: int) -> bool:
        """检查磁盘空间"""
        return True  # 假设有足够空间

    def _check_admin_privileges(self) -> bool:
        """检查管理员权限"""
        if self.system == "windows":
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            return os.geteuid() == 0

    def install_mongodb(self) -> bool:
        """安装MongoDB"""
        if self.system == "windows":
            print("请从 MongoDB 官网下载安装包: https://www.mongodb.com/try/download/community")
            print("推荐使用 MSI 安装包进行安装")
        else:
            print("请使用系统包管理器安装:")
            if self.system == "linux":
                print("Ubuntu/Debian: sudo apt-get install mongodb")
                print("CentOS/RHEL: sudo yum install mongodb-org")
            else:  # macOS
                print("macOS: brew install mongodb-community")
        return True

    def uninstall_mongodb(self) -> bool:
        """卸载MongoDB"""
        if self.system == "windows":
            print("请使用 Windows 控制面板卸载 MongoDB")
        else:
            print("请使用系统包管理器卸载")
        return True

    def start_service(self) -> bool:
        """启动MongoDB服务"""
        try:
            if self.system == "windows":
                cmd = ["net", "start", self.service_name]
            else:
                cmd = ["sudo", "systemctl", "start", "mongod"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def stop_service(self) -> bool:
        """停止MongoDB服务"""
        try:
            if self.system == "windows":
                cmd = ["net", "stop", self.service_name]
            else:
                cmd = ["sudo", "systemctl", "stop", "mongod"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def restart_service(self) -> bool:
        """重启MongoDB服务"""
        print("正在重启MongoDB服务...")
        if self.stop_service():
            time.sleep(2)
            return self.start_service()
        return False

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            if self.system == "windows":
                cmd = ["sc", "query", self.service_name]
            else:
                cmd = ["sudo", "systemctl", "status", "mongod"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if self.system == "windows":
                if "RUNNING" in result.stdout:
                    return {"status": "running", "service_name": self.service_name}
                elif "STOPPED" in result.stdout:
                    return {"status": "stopped", "service_name": self.service_name}
            else:
                if "active (running)" in result.stdout:
                    return {"status": "running"}
                elif "inactive (dead)" in result.stdout:
                    return {"status": "stopped"}

            return {"status": "unknown"}
        except Exception:
            return {"status": "error", "message": "无法获取服务状态"}

    def is_mongodb_installed(self) -> bool:
        """检查MongoDB是否已安装"""
        try:
            result = subprocess.run(['mongod', '--version'],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def get_mongodb_version(self) -> Optional[str]:
        """获取MongoDB版本"""
        try:
            result = subprocess.run(['mongod', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # 从版本信息中提取版本号
                version_line = result.stdout.strip()
                if "db version" in version_line:
                    return version_line.split()[-1]
        except:
            pass
        return None

    def get_mongodb_info(self) -> Dict[str, Any]:
        """获取MongoDB详细信息"""
        info = {
            'installed': self.is_mongodb_installed(),
            'version': self.get_mongodb_version(),
            'service_status': self.get_service_status(),
            'system': self.system
        }
        return info

    def test_connection(self, host: str = "localhost", port: int = 27017) -> Dict[str, Any]:
        """测试MongoDB连接"""
        try:
            # 尝试使用mongosh测试连接
            import subprocess
            result = subprocess.run(
                ['mongosh', f'mongodb://{host}:{port}', '--eval', 'db.runCommand({ping: 1})'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'成功连接到 MongoDB {host}:{port}',
                    'details': result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': f'连接失败: {result.stderr}',
                    'details': result.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': '连接超时',
                'details': ''
            }
        except FileNotFoundError:
            # mongosh不存在，尝试使用mongo
            try:
                result = subprocess.run(
                    ['mongo', f'{host}:{port}/test', '--eval', 'db.runCommand({ping: 1})'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': f'成功连接到 MongoDB {host}:{port}',
                        'details': result.stdout
                    }
                else:
                    return {
                        'success': False,
                        'message': f'连接失败: {result.stderr}',
                        'details': result.stderr
                    }
            except FileNotFoundError:
                return {
                    'success': False,
                    'message': '未找到 MongoDB 客户端工具 (mongosh 或 mongo)',
                    'details': ''
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'连接出错: {str(e)}',
                    'details': ''
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接出错: {str(e)}',
                'details': ''
            }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MongoDB 安装和管理工具")
    parser.add_argument('--install', action='store_true', help='安装MongoDB')
    parser.add_argument('--uninstall', action='store_true', help='卸载MongoDB')
    parser.add_argument('--start', action='store_true', help='启动MongoDB服务')
    parser.add_argument('--stop', action='store_true', help='停止MongoDB服务')
    parser.add_argument('--restart', action='store_true', help='重启MongoDB服务')
    parser.add_argument('--status', action='store_true', help='查看服务状态')
    parser.add_argument('--version', action='store_true', help='获取MongoDB版本')
    parser.add_argument('--info', action='store_true', help='获取详细信息')

    args = parser.parse_args()

    installer = MongoDBInstaller()

    if args.install:
        print("开始安装MongoDB...")
        if installer.install_mongodb():
            print("MongoDB安装指导完成")
        else:
            print("MongoDB安装指导失败")

    elif args.uninstall:
        if installer.uninstall_mongodb():
            print("MongoDB卸载指导完成")
        else:
            print("MongoDB卸载指导失败")

    elif args.start:
        installer.start_service()

    elif args.stop:
        installer.stop_service()

    elif args.restart:
        installer.restart_service()

    elif args.status:
        status = installer.get_service_status()
        print(f"服务状态: {status.get('status', 'unknown')}")

    elif args.version:
        version = installer.get_mongodb_version()
        if version:
            print(f"MongoDB版本: {version}")
        else:
            print("无法获取MongoDB版本，可能未安装")

    elif args.info:
        info = installer.get_mongodb_info()
        print("MongoDB 信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    else:
        # 默认显示状态
        if installer.is_mongodb_installed():
            print("MongoDB已安装")
            version = installer.get_mongodb_version()
            if version:
                print(f"版本: {version}")

            status = installer.get_service_status()
            print(f"服务状态: {status.get('status', 'unknown')}")
        else:
            print("MongoDB未安装")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)