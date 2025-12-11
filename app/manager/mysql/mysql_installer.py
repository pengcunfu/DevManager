#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 安装和服务管理脚本
提供 MySQL 的安装、卸载、服务管理等功能
"""

import os
import sys
import time
import shutil
import subprocess
import platform
import requests
import tempfile
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any


class MySQLInstaller:
    """MySQL 安装器和服务管理器"""

    def __init__(self):
        """初始化安装器"""
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.mysql_version = "8.0.35"
        self.installation_path = self._get_default_installation_path()
        self.service_name = "MySQL80" if self.system == "windows" else "mysql"

    def _get_default_installation_path(self) -> str:
        """获取默认安装路径"""
        if self.system == "windows":
            return r"C:\Program Files\MySQL\MySQL Server 8.0"
        else:
            return "/opt/mysql"

    def check_requirements(self) -> Dict[str, bool]:
        """检查安装要求"""
        requirements = {
            'internet': self._check_internet_connection(),
            'disk_space': self._check_disk_space(1024),  # 1GB
            'admin_privileges': self._check_admin_privileges(),
            'visual_cpp': True if self.system != "windows" else self._check_visual_cpp(),
        }

        return requirements

    def _check_internet_connection(self) -> bool:
        """检查网络连接"""
        try:
            response = requests.get("https://www.mysql.com", timeout=5)
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

    def _check_visual_cpp(self) -> bool:
        """检查Visual C++ Redistributable"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64") as key:
                return True
        except:
            # 可以通过其他方式检查或直接提示用户安装
            return True

    def download_mysql(self) -> Optional[str]:
        """下载MySQL安装包"""
        if self.system == "windows":
            return self._download_mysql_windows()
        elif self.system == "linux":
            return self._download_mysql_linux()
        elif self.system == "darwin":
            return self._download_mysql_macos()
        else:
            raise RuntimeError(f"不支持的操作系统: {self.system}")

    def _download_mysql_windows(self) -> Optional[str]:
        """下载Windows版MySQL"""
        print("正在下载MySQL for Windows...")

        # MySQL 8.0 Windows x64 ZIP下载链接
        download_url = f"https://dev.mysql.com/get/Downloads/MySQL-{self.mysql_version.split('.')[0]}.{self.mysql_version.split('.')[1]}/mysql-{self.mysql_version}-winx64.zip"

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # 保存到临时目录
            temp_dir = tempfile.gettempdir()
            filename = f"mysql-{self.mysql_version}-winx64.zip"
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

    def _download_mysql_linux(self) -> Optional[str]:
        """下载Linux版MySQL"""
        print("正在下载MySQL for Linux...")

        # 对于Linux，建议使用包管理器安装
        print("建议使用以下命令安装:")
        print("Ubuntu/Debian:")
        print("  sudo apt update")
        print("  sudo apt install mysql-server")
        print("CentOS/RHEL:")
        print("  sudo yum install mysql-server")
        print("  # 或者对于较新版本:")
        print("  sudo dnf install mysql-server")

        return None

    def _download_mysql_macos(self) -> Optional[str]:
        """下载macOS版MySQL"""
        print("正在下载MySQL for macOS...")

        # 使用Homebrew安装
        print("建议使用以下命令安装:")
        print("  brew install mysql")

        return None

    def install_mysql(self, installer_path: str = None) -> bool:
        """安装MySQL"""
        try:
            if self.system == "windows":
                return self._install_mysql_windows(installer_path)
            elif self.system == "linux":
                return self._install_mysql_linux()
            elif self.system == "darwin":
                return self._install_mysql_macos()
            else:
                print(f"不支持的操作系统: {self.system}")
                return False
        except Exception as e:
            print(f"安装失败: {e}")
            return False

    def _install_mysql_windows(self, installer_path: str) -> bool:
        """安装Windows版MySQL"""
        print("正在安装MySQL for Windows...")

        if not installer_path:
            print("错误: 未指定安装包路径")
            return False

        # 解压安装包
        print("正在解压安装包...")
        extract_path = os.path.dirname(self.installation_path)

        try:
            import zipfile
            with zipfile.ZipFile(installer_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 创建数据目录
            data_dir = os.path.join(self.installation_path, "data")
            os.makedirs(data_dir, exist_ok=True)

            # 创建配置文件
            self._create_config_file_windows()

            # 初始化数据目录
            self._initialize_data_directory()

            # 安装服务
            self._install_service_windows()

            print("MySQL安装完成")
            return True

        except Exception as e:
            print(f"安装过程中出错: {e}")
            return False

    def _create_config_file_windows(self):
        """创建Windows配置文件"""
        config_content = f"""[mysqld]
# 设置3306端口
port=3306

# 设置mysql的安装目录
basedir={self.installation_path}

# 设置mysql数据库的数据的存放目录
datadir={self.installation_path}\\data

# 允许最大连接数
max_connections=200

# 服务端使用的字符集默认为utf8mb4
character-set-server=utf8mb4

# 创建新表时将使用的默认存储引擎
default-storage-engine=INNODB

# 默认使用"mysql_native_password"插件认证
default_authentication_plugin=mysql_native_password

[mysql]
# 设置mysql客户端默认字符集
default-character-set=utf8mb4

[client]
# 设置mysql客户端连接服务端时默认使用的端口
port=3306
default-character-set=utf8mb4
"""

        config_file = os.path.join(self.installation_path, "my.ini")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)

    def _initialize_data_directory(self):
        """初始化数据目录"""
        print("正在初始化MySQL数据目录...")

        mysqld_path = os.path.join(self.installation_path, "bin", "mysqld.exe")

        cmd = [
            mysqld_path,
            "--initialize-insecure",
            f"--basedir={self.installation_path}",
            f"--datadir={os.path.join(self.installation_path, 'data')}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("数据目录初始化成功")
        else:
            print(f"数据目录初始化失败: {result.stderr}")

    def _install_service_windows(self):
        """安装Windows服务"""
        print("正在安装MySQL服务...")

        mysqld_path = os.path.join(self.installation_path, "bin", "mysqld.exe")

        cmd = [
            mysqld_path,
            "--install",
            self.service_name,
            f"--defaults-file={os.path.join(self.installation_path, 'my.ini')}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"服务 {self.service_name} 安装成功")
        else:
            print(f"服务安装失败: {result.stderr}")

    def _install_mysql_linux(self) -> bool:
        """安装Linux版MySQL"""
        print("请使用系统包管理器安装MySQL")
        return False

    def _install_mysql_macos(self) -> bool:
        """安装macOS版MySQL"""
        print("请使用Homebrew安装MySQL")
        return False

    def uninstall_mysql(self) -> bool:
        """卸载MySQL"""
        try:
            if self.system == "windows":
                return self._uninstall_mysql_windows()
            else:
                return self._uninstall_mysql_unix()
        except Exception as e:
            print(f"卸载失败: {e}")
            return False

    def _uninstall_mysql_windows(self) -> bool:
        """卸载Windows版MySQL"""
        print("正在卸载MySQL...")

        # 停止并删除服务
        if self.service_exists():
            self.stop_service()
            self._remove_service_windows()

        # 删除安装目录
        if os.path.exists(self.installation_path):
            try:
                shutil.rmtree(self.installation_path)
                print(f"已删除安装目录: {self.installation_path}")
            except Exception as e:
                print(f"删除安装目录失败: {e}")
                return False

        # 清理注册表（可选）
        print("MySQL卸载完成")
        return True

    def _remove_service_windows(self):
        """删除Windows服务"""
        print("正在删除MySQL服务...")

        mysqld_path = os.path.join(self.installation_path, "bin", "mysqld.exe")

        cmd = [mysqld_path, "--remove", self.service_name]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("服务删除成功")
        else:
            print(f"服务删除失败: {result.stderr}")

    def _uninstall_mysql_unix(self) -> bool:
        """卸载Unix系统版MySQL"""
        print("请使用系统包管理器卸载MySQL")
        return False

    def install_service(self) -> bool:
        """安装MySQL服务"""
        try:
            if self.system == "windows":
                if os.path.exists(self.installation_path):
                    self._install_service_windows()
                    return True
                else:
                    print("MySQL未安装")
                    return False
            else:
                print("Unix系统下服务安装由包管理器自动处理")
                return True
        except Exception as e:
            print(f"服务安装失败: {e}")
            return False

    def start_service(self) -> bool:
        """启动MySQL服务"""
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
            print("MySQL服务启动成功")
            return True
        else:
            print(f"启动服务失败: {result.stderr}")
            return False

    def _start_service_unix(self) -> bool:
        """启动Unix服务"""
        commands = [
            ["sudo", "systemctl", "start", "mysql"],
            ["sudo", "service", "mysql", "start"],
            ["sudo", "/etc/init.d/mysql", "start"]
        ]

        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("MySQL服务启动成功")
                return True

        print("启动服务失败")
        return False

    def stop_service(self) -> bool:
        """停止MySQL服务"""
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
            print("MySQL服务停止成功")
            return True
        else:
            print(f"停止服务失败: {result.stderr}")
            return False

    def _stop_service_unix(self) -> bool:
        """停止Unix服务"""
        commands = [
            ["sudo", "systemctl", "stop", "mysql"],
            ["sudo", "service", "mysql", "stop"],
            ["sudo", "/etc/init.d/mysql", "stop"]
        ]

        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("MySQL服务停止成功")
                return True

        print("停止服务失败")
        return False

    def restart_service(self) -> bool:
        """重启MySQL服务"""
        print("正在重启MySQL服务...")
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
            ["sudo", "systemctl", "status", "mysql"],
            ["sudo", "service", "mysql", "status"],
            ["sudo", "/etc/init.d/mysql", "status"]
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

    def is_mysql_installed(self) -> bool:
        """检查MySQL是否已安装"""
        if self.system == "windows":
            return os.path.exists(self.installation_path)
        else:
            # 检查mysql命令是否存在
            try:
                subprocess.run(["mysql", "--version"],
                             capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False

    def get_mysql_version(self) -> Optional[str]:
        """获取MySQL版本"""
        try:
            if self.system == "windows":
                mysql_path = os.path.join(self.installation_path, "bin", "mysql.exe")
                if os.path.exists(mysql_path):
                    result = subprocess.run([mysql_path, "--version"],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.split()[4]  # 提取版本号
            else:
                result = subprocess.run(["mysql", "--version"],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.split()[4]  # 提取版本号
        except:
            pass

        return None

    def set_root_password(self, password: str) -> bool:
        """设置root密码"""
        try:
            if self.system == "windows":
                mysqladmin_path = os.path.join(self.installation_path, "bin", "mysqladmin.exe")
                if os.path.exists(mysqladmin_path):
                    cmd = [mysqladmin_path, "-u", "root", "password", password]
                else:
                    return False
            else:
                cmd = ["mysqladmin", "-u", "root", "password", password]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("root密码设置成功")
                return True
            else:
                print(f"设置密码失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"设置密码失败: {e}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MySQL 安装和管理工具")
    parser.add_argument('--install', action='store_true', help='安装MySQL')
    parser.add_argument('--uninstall', action='store_true', help='卸载MySQL')
    parser.add_argument('--start', action='store_true', help='启动MySQL服务')
    parser.add_argument('--stop', action='store_true', help='停止MySQL服务')
    parser.add_argument('--restart', action='store_true', help='重启MySQL服务')
    parser.add_argument('--status', action='store_true', help='查看服务状态')
    parser.add_argument('--install-service', action='store_true', help='安装MySQL服务')
    parser.add_argument('--set-password', metavar='PASSWORD', help='设置root密码')
    parser.add_argument('--check', action='store_true', help='检查安装要求')
    parser.add_argument('--version', action='store_true', help='获取MySQL版本')

    args = parser.parse_args()

    installer = MySQLInstaller()

    if args.check:
        print("检查安装要求:")
        requirements = installer.check_requirements()
        for req, satisfied in requirements.items():
            status = "✓" if satisfied else "✗"
            print(f"  {status} {req}")

    elif args.install:
        print("开始安装MySQL...")
        if installer.is_mysql_installed():
            print("MySQL已经安装")
        else:
            # 检查要求
            requirements = installer.check_requirements()
            if all(requirements.values()):
                if installer.system == "windows":
                    installer_path = installer.download_mysql()
                    if installer_path:
                        installer.install_mysql(installer_path)
                    else:
                        print("下载失败，请手动下载并安装")
                else:
                    print("请使用系统包管理器安装MySQL")
            else:
                print("不满足安装要求")
                for req, satisfied in requirements.items():
                    if not satisfied:
                        print(f"  缺少: {req}")

    elif args.uninstall:
        if installer.uninstall_mysql():
            print("MySQL卸载完成")
        else:
            print("卸载失败")

    elif args.start:
        installer.start_service()

    elif args.stop:
        installer.stop_service()

    elif args.restart:
        installer.restart_service()

    elif args.status:
        if installer.is_mysql_installed():
            print(f"MySQL已安装")
            version = installer.get_mysql_version()
            if version:
                print(f"版本: {version}")

            status = installer.get_service_status()
            print(f"服务状态: {status.get('status', 'unknown')}")
        else:
            print("MySQL未安装")

    elif args.install_service:
        installer.install_service()

    elif args.set_password:
        installer.set_root_password(args.set_password)

    elif args.version:
        version = installer.get_mysql_version()
        if version:
            print(f"MySQL版本: {version}")
        else:
            print("无法获取MySQL版本，可能未安装")

    else:
        # 默认显示状态
        if installer.is_mysql_installed():
            print("MySQL已安装")
            version = installer.get_mysql_version()
            if version:
                print(f"版本: {version}")

            status = installer.get_service_status()
            print(f"服务状态: {status.get('status', 'unknown')}")
        else:
            print("MySQL未安装")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)