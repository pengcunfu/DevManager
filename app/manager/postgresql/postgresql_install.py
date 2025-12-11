#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 安装和服务管理脚本
提供 PostgreSQL 的安装、卸载、服务管理等功能
"""

import os
import sys
import time
import shutil
import subprocess
import platform
import requests
import tempfile
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any


class PostgreSQLInstaller:
    """PostgreSQL 安装器和服务管理器"""

    def __init__(self):
        """初始化安装器"""
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.postgresql_version = "16.1"
        self.installation_path = self._get_default_installation_path()
        self.service_name = "postgresql-x64-16" if self.system == "windows" else "postgresql"

    def _get_default_installation_path(self) -> str:
        """获取默认安装路径"""
        if self.system == "windows":
            return r"C:\Program Files\PostgreSQL\16"
        else:
            return "/usr/local/pgsql"

    def check_requirements(self) -> Dict[str, bool]:
        """检查安装要求"""
        requirements = {
            'internet': self._check_internet_connection(),
            'disk_space': self._check_disk_space(500),  # 500MB
            'admin_privileges': self._check_admin_privileges(),
        }

        return requirements

    def _check_internet_connection(self) -> bool:
        """检查网络连接"""
        try:
            response = requests.get("https://www.postgresql.org", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _check_disk_space(self, required_mb: int) -> bool:
        """检查磁盘空间"""
        try:
            if self.system == "windows":
                import psutil
                disk_usage = psutil.disk_usage("C:\\")
                free_space_mb = disk_usage.free / (1024 * 1024)
            else:
                stat = os.statvfs("/")
                free_space_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)

            return free_space_mb >= required_mb
        except:
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

    def download_postgresql(self) -> Optional[str]:
        """下载PostgreSQL安装包"""
        if self.system == "windows":
            return self._download_postgresql_windows()
        elif self.system == "linux":
            return self._download_postgresql_linux()
        elif self.system == "darwin":
            return self._download_postgresql_macos()
        else:
            raise RuntimeError(f"不支持的操作系统: {self.system}")

    def _download_postgresql_windows(self) -> Optional[str]:
        """下载Windows版PostgreSQL"""
        print("正在下载PostgreSQL for Windows...")

        # PostgreSQL 16 Windows x64 安装包下载链接
        download_url = "https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows-x64.exe"

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # 保存到临时目录
            temp_dir = tempfile.gettempdir()
            filename = "postgresql-16.1-1-windows-x64.exe"
            filepath = os.path.join(temp_dir, filename)

            print(f"正在下载到: {filepath}")
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print("下载完成")
            return filepath

        except Exception as e:
            print(f"下载失败: {e}")
            return None

    def _download_postgresql_linux(self) -> Optional[str]:
        """下载Linux版PostgreSQL"""
        print("正在准备安装PostgreSQL for Linux...")

        # 对于Linux，建议使用包管理器安装
        print("建议使用以下命令安装:")
        print("Ubuntu/Debian:")
        print("  sudo apt update")
        print("  sudo apt install postgresql postgresql-contrib")
        print("CentOS/RHEL:")
        print("  sudo yum install postgresql-server postgresql-contrib")
        print("  sudo postgresql-setup initdb")
        print("  sudo systemctl enable postgresql")
        print("  sudo systemctl start postgresql")

        return None

    def _download_postgresql_macos(self) -> Optional[str]:
        """下载macOS版PostgreSQL"""
        print("正在准备安装PostgreSQL for macOS...")

        # 使用Homebrew安装
        print("建议使用以下命令安装:")
        print("  brew install postgresql")
        print("  brew services start postgresql")

        return None

    def install_postgresql(self, installer_path: str = None) -> bool:
        """安装PostgreSQL"""
        try:
            if self.system == "windows":
                return self._install_postgresql_windows(installer_path)
            elif self.system == "linux":
                return self._install_postgresql_linux()
            elif self.system == "darwin":
                return self._install_postgresql_macos()
            else:
                print(f"不支持的操作系统: {self.system}")
                return False
        except Exception as e:
            print(f"安装失败: {e}")
            return False

    def _install_postgresql_windows(self, installer_path: str) -> bool:
        """安装Windows版PostgreSQL"""
        print("正在安装PostgreSQL for Windows...")

        if not installer_path:
            print("错误: 未指定安装包路径")
            return False

        try:
            # 静默安装参数
            install_cmd = [
                installer_path,
                "--mode", "unattended",
                "--prefix", self.installation_path,
                "--datadir", os.path.join(self.installation_path, "data"),
                "--superpassword", "postgres",
                "--servicename", self.service_name,
                "--serviceaccount", "NT AUTHORITY\\NetworkService",
                "--servicepassword", ""
            ]

            print("正在运行安装程序...")
            result = subprocess.run(install_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("PostgreSQL安装成功")
                return True
            else:
                print(f"安装失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"安装过程中出错: {e}")
            return False

    def _install_postgresql_linux(self) -> bool:
        """安装Linux版PostgreSQL"""
        print("请使用系统包管理器安装PostgreSQL")
        return False

    def _install_postgresql_macos(self) -> bool:
        """安装macOS版PostgreSQL"""
        print("请使用Homebrew安装PostgreSQL")
        return False

    def uninstall_postgresql(self) -> bool:
        """卸载PostgreSQL"""
        try:
            if self.system == "windows":
                return self._uninstall_postgresql_windows()
            else:
                return self._uninstall_postgresql_unix()
        except Exception as e:
            print(f"卸载失败: {e}")
            return False

    def _uninstall_postgresql_windows(self) -> bool:
        """卸载Windows版PostgreSQL"""
        print("正在卸载PostgreSQL...")

        # 停止并删除服务
        if self.service_exists():
            self.stop_service()

        # 删除安装目录
        if os.path.exists(self.installation_path):
            try:
                shutil.rmtree(self.installation_path)
                print(f"已删除安装目录: {self.installation_path}")
            except Exception as e:
                print(f"删除安装目录失败: {e}")
                return False

        # 清理注册表（可选）
        print("PostgreSQL卸载完成")
        return True

    def _uninstall_postgresql_unix(self) -> bool:
        """卸载Unix系统版PostgreSQL"""
        print("请使用系统包管理器卸载PostgreSQL")
        return False

    def install_service(self) -> bool:
        """安装PostgreSQL服务"""
        try:
            if self.system == "windows":
                if os.path.exists(self.installation_path):
                    return self._install_service_windows()
                else:
                    print("PostgreSQL未安装")
                    return False
            else:
                print("Unix系统下服务安装由包管理器自动处理")
                return True
        except Exception as e:
            print(f"服务安装失败: {e}")
            return False

    def _install_service_windows(self) -> bool:
        """安装Windows服务"""
        print("正在安装PostgreSQL服务...")

        pg_ctl_path = os.path.join(self.installation_path, "bin", "pg_ctl.exe")
        data_dir = os.path.join(self.installation_path, "data")

        if not os.path.exists(pg_ctl_path):
            print("未找到pg_ctl.exe")
            return False

        try:
            cmd = [
                pg_ctl_path,
                "register",
                "-N", self.service_name,
                "-P", "postgres",
                "-D", data_dir
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"服务 {self.service_name} 注册成功")
                return True
            else:
                print(f"服务注册失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"注册服务失败: {e}")
            return False

    def start_service(self) -> bool:
        """启动PostgreSQL服务"""
        try:
            if self.system == "windows":
                return self._start_service_windows()
            else:
                return self._start_service_unix()
        except Exception as e:
            print(f"启动服务失败: {e}")
            return False

    def _start_service_windows(self) -> bool:
        """启动Windows服务"""
        cmd = ["net", "start", self.service_name]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("PostgreSQL服务启动成功")
            return True
        else:
            # 尝试使用pg_ctl启动
            pg_ctl_path = os.path.join(self.installation_path, "bin", "pg_ctl.exe")
            data_dir = os.path.join(self.installation_path, "data")

            if os.path.exists(pg_ctl_path):
                cmd = [pg_ctl_path, "start", "-D", data_dir]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("PostgreSQL服务启动成功")
                    return True

            print(f"启动服务失败: {result.stderr}")
            return False

    def _start_service_unix(self) -> bool:
        """启动Unix服务"""
        commands = [
            ["sudo", "systemctl", "start", "postgresql"],
            ["sudo", "service", "postgresql", "start"],
            ["sudo", "/etc/init.d/postgresql", "start"]
        ]

        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("PostgreSQL服务启动成功")
                return True

        print("启动服务失败")
        return False

    def stop_service(self) -> bool:
        """停止PostgreSQL服务"""
        try:
            if self.system == "windows":
                return self._stop_service_windows()
            else:
                return self._stop_service_unix()
        except Exception as e:
            print(f"停止服务失败: {e}")
            return False

    def _stop_service_windows(self) -> bool:
        """停止Windows服务"""
        cmd = ["net", "stop", self.service_name]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("PostgreSQL服务停止成功")
            return True
        else:
            # 尝试使用pg_ctl停止
            pg_ctl_path = os.path.join(self.installation_path, "bin", "pg_ctl.exe")
            data_dir = os.path.join(self.installation_path, "data")

            if os.path.exists(pg_ctl_path):
                cmd = [pg_ctl_path, "stop", "-D", data_dir]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("PostgreSQL服务停止成功")
                    return True

            print(f"停止服务失败: {result.stderr}")
            return False

    def _stop_service_unix(self) -> bool:
        """停止Unix服务"""
        commands = [
            ["sudo", "systemctl", "stop", "postgresql"],
            ["sudo", "service", "postgresql", "stop"],
            ["sudo", "/etc/init.d/postgresql", "stop"]
        ]

        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("PostgreSQL服务停止成功")
                return True

        print("停止服务失败")
        return False

    def restart_service(self) -> bool:
        """重启PostgreSQL服务"""
        print("正在重启PostgreSQL服务...")
        if self.stop_service():
            time.sleep(2)
            return self.start_service()
        return False

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            if self.system == "windows":
                return self._get_service_status_windows()
            else:
                return self._get_service_status_unix()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_service_status_windows(self) -> Dict[str, Any]:
        """获取Windows服务状态"""
        try:
            import win32service
            import win32con

            scm = win32service.OpenSCManager(None, None, win32con.GENERIC_READ)
            service = win32service.OpenService(scm, self.service_name, win32con.GENERIC_READ)
            status = win32service.QueryServiceStatus(service)

            status_map = {
                win32service.SERVICE_STOPPED: "stopped",
                win32service.SERVICE_START_PENDING: "starting",
                win32service.SERVICE_STOP_PENDING: "stopping",
                win32service.SERVICE_RUNNING: "running",
                win32service.SERVICE_CONTINUE_PENDING: "resuming",
                win32service.SERVICE_PAUSE_PENDING: "pausing",
                win32service.SERVICE_PAUSED: "paused"
            }

            return {
                "status": status_map.get(status[1], "unknown"),
                "service_name": self.service_name
            }

        except ImportError:
            # 使用sc命令作为备选方案
            cmd = ["sc", "query", self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if "RUNNING" in result.stdout:
                return {"status": "running", "service_name": self.service_name}
            elif "STOPPED" in result.stdout:
                return {"status": "stopped", "service_name": self.service_name}
            else:
                return {"status": "unknown", "message": result.stderr}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_service_status_unix(self) -> Dict[str, Any]:
        """获取Unix服务状态"""
        commands = [
            ["sudo", "systemctl", "status", "postgresql"],
            ["sudo", "service", "postgresql", "status"],
            ["sudo", "/etc/init.d/postgresql", "status"]
        ]

        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode in [0, 3]:  # 0=running, 3=stopped
                if "active (running)" in result.stdout:
                    return {"status": "running"}
                elif "inactive (dead)" in result.stdout or "stopped" in result.stdout:
                    return {"status": "stopped"}

        return {"status": "unknown"}

    def service_exists(self) -> bool:
        """检查服务是否存在"""
        status = self.get_service_status()
        return status.get("status") != "error"

    def is_postgresql_installed(self) -> bool:
        """检查PostgreSQL是否已安装"""
        if self.system == "windows":
            return os.path.exists(self.installation_path)
        else:
            # 检查psql命令是否存在
            try:
                subprocess.run(["psql", "--version"],
                             capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False

    def get_postgresql_version(self) -> Optional[str]:
        """获取PostgreSQL版本"""
        try:
            if self.system == "windows":
                psql_path = os.path.join(self.installation_path, "bin", "psql.exe")
                if os.path.exists(psql_path):
                    result = subprocess.run([psql_path, "--version"],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        # 提取版本号: psql (PostgreSQL) 16.1
                        return result.stdout.split()[-1]
            else:
                result = subprocess.run(["psql", "--version"],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 提取版本号
                    return result.stdout.split()[-1]
        except:
            pass

        return None

    def init_database(self, data_dir: str = None) -> bool:
        """初始化数据库"""
        try:
            if not data_dir:
                data_dir = os.path.join(self.installation_path, "data")

            if self.system == "windows":
                initdb_path = os.path.join(self.installation_path, "bin", "initdb.exe")
            else:
                initdb_path = "initdb"

            if not os.path.exists(initdb_path) and self.system != "windows":
                initdb_path = "/usr/lib/postgresql/16/bin/initdb"

            cmd = [initdb_path, "-D", data_dir, "-U", "postgres"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("数据库初始化成功")
                return True
            else:
                print(f"数据库初始化失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"初始化数据库失败: {e}")
            return False

    def create_user(self, username: str, password: str = None) -> bool:
        """创建数据库用户"""
        try:
            if self.system == "windows":
                createuser_path = os.path.join(self.installation_path, "bin", "createuser.exe")
                psql_path = os.path.join(self.installation_path, "bin", "psql.exe")
            else:
                createuser_path = "createuser"
                psql_path = "psql"

            # 创建用户
            cmd = [createuser_path, "-U", "postgres", username]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"创建用户失败: {result.stderr}")
                return False

            # 如果提供了密码，设置密码
            if password:
                sql_cmd = f"ALTER USER {username} PASSWORD '{password}';"
                cmd = [psql_path, "-U", "postgres", "-c", sql_cmd]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"用户 {username} 创建成功")
                    return True
                else:
                    print(f"设置密码失败: {result.stderr}")
                    return False

            print(f"用户 {username} 创建成功")
            return True

        except Exception as e:
            print(f"创建用户失败: {e}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL 安装和管理工具")
    parser.add_argument('--install', action='store_true', help='安装PostgreSQL')
    parser.add_argument('--uninstall', action='store_true', help='卸载PostgreSQL')
    parser.add_argument('--start', action='store_true', help='启动PostgreSQL服务')
    parser.add_argument('--stop', action='store_true', help='停止PostgreSQL服务')
    parser.add_argument('--restart', action='store_true', help='重启PostgreSQL服务')
    parser.add_argument('--status', action='store_true', help='查看服务状态')
    parser.add_argument('--install-service', action='store_true', help='安装PostgreSQL服务')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    parser.add_argument('--create-user', metavar='USERNAME', help='创建数据库用户')
    parser.add_argument('--check', action='store_true', help='检查安装要求')
    parser.add_argument('--version', action='store_true', help='获取PostgreSQL版本')

    args = parser.parse_args()

    installer = PostgreSQLInstaller()

    if args.check:
        print("检查安装要求:")
        requirements = installer.check_requirements()
        for req, satisfied in requirements.items():
            status = "✓" if satisfied else "✗"
            print(f"  {status} {req}")

    elif args.install:
        print("开始安装PostgreSQL...")
        if installer.is_postgresql_installed():
            print("PostgreSQL已经安装")
        else:
            # 检查要求
            requirements = installer.check_requirements()
            if all(requirements.values()):
                if installer.system == "windows":
                    installer_path = installer.download_postgresql()
                    if installer_path:
                        installer.install_postgresql(installer_path)
                    else:
                        print("下载失败，请手动下载并安装")
                else:
                    print("请使用系统包管理器安装PostgreSQL")
            else:
                print("不满足安装要求")
                for req, satisfied in requirements.items():
                    if not satisfied:
                        print(f"  缺少: {req}")

    elif args.uninstall:
        if installer.uninstall_postgresql():
            print("PostgreSQL卸载完成")
        else:
            print("卸载失败")

    elif args.start:
        installer.start_service()

    elif args.stop:
        installer.stop_service()

    elif args.restart:
        installer.restart_service()

    elif args.status:
        if installer.is_postgresql_installed():
            print(f"PostgreSQL已安装")
            version = installer.get_postgresql_version()
            if version:
                print(f"版本: {version}")

            status = installer.get_service_status()
            print(f"服务状态: {status.get('status', 'unknown')}")
        else:
            print("PostgreSQL未安装")

    elif args.install_service:
        installer.install_service()

    elif args.init_db:
        installer.init_database()

    elif args.create_user:
        installer.create_user(args.create_user)

    elif args.version:
        version = installer.get_postgresql_version()
        if version:
            print(f"PostgreSQL版本: {version}")
        else:
            print("无法获取PostgreSQL版本，可能未安装")

    else:
        # 默认显示状态
        if installer.is_postgresql_installed():
            print("PostgreSQL已安装")
            version = installer.get_postgresql_version()
            if version:
                print(f"版本: {version}")

            status = installer.get_service_status()
            print(f"服务状态: {status.get('status', 'unknown')}")
        else:
            print("PostgreSQL未安装")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)