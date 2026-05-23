#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 安装和服务管理脚本
提供 MySQL 的安装、卸载、服务管理等功能
支持 MySQL 8.0.44 版本
"""

import os
import time
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any

from .mysql_config import MYSQL_VERSION, MYSQL_DOWNLOAD_URL, MySQLConfigManager
from app.download import create_downloader
from app.service import service_manager
from app.exec import ScriptExecutor


class MySQLInstaller:
    """MySQL 安装器和服务管理器"""

    def __init__(self, installation_path: Optional[str] = None):
        """初始化安装器

        Args:
            installation_path: 自定义安装路径，如果为None则使用默认路径
        """
        self.system = "windows"
        self.mysql_version = MYSQL_VERSION
        self.mysql_download_url = MYSQL_DOWNLOAD_URL
        self.installation_path = installation_path or self._get_default_installation_path()
        self.service_name = f"MySQL{self.mysql_version.replace('.', '')}"
        self.config_manager = MySQLConfigManager(self.installation_path)
        # 使用简化的服务管理器
        self.service_manager = service_manager
        # 初始化命令执行器
        self.executor = ScriptExecutor(
            work_dir=self.installation_path,
            verbose=True
        )

    def _get_default_installation_path(self) -> str:
        """获取默认安装路径"""
        return fr"D:\Env\mysql\mysql-{self.mysql_version}"

    def check_requirements(self) -> Dict[str, bool]:
        """检查安装要求"""
        requirements = {
            'internet': self._check_internet_connection(),
            'disk_space': self._check_disk_space(1024),  # 1GB
            'admin_privileges': self._check_admin_privileges(),
            'visual_cpp': self._check_visual_cpp(),
        }

        return requirements

    def _check_internet_connection(self) -> bool:
        """检查网络连接"""
        try:
            # 使用下载模块测试连接
            downloader = create_downloader(bypass_proxy=True)
            return downloader.test_connection("https://www.mysql.com", timeout=5)
        except:
            return False

    def _check_disk_space(self, required_mb: int) -> bool:
        """检查磁盘空间"""
        try:
            import psutil
            # 检查D盘空间（MySQL默认安装位置）
            disk_usage = psutil.disk_usage("D:\\")
            free_space_mb = disk_usage.free / (1024 * 1024)
            return free_space_mb >= required_mb
        except:
            # 如果D盘不存在或无法访问，返回True（假设有足够空间）
            return True

    def _check_admin_privileges(self) -> bool:
        """检查管理员权限"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

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
        return self._download_mysql_windows()

    def _download_mysql_windows(self) -> Optional[str]:
        """下载Windows版MySQL"""
        print("正在下载MySQL for Windows...")

        # 使用提供的MySQL 8.0.44下载链接
        download_url = self.mysql_download_url

        try:
            # 创建绕过系统代理的下载器
            downloader = create_downloader(bypass_proxy=True)

            # 定义进度回调函数
            def progress_callback(percent: float):
                print(f"\r下载进度: {percent:.1f}%", end='', flush=True)

            # 执行下载
            filepath = downloader.download(
                url=download_url,
                filename=f"mysql-{self.mysql_version}-winx64.zip",
                progress_callback=progress_callback,
                timeout=300
            )

            if filepath:
                print("\n下载完成")
                return filepath
            else:
                return None

        except Exception as e:
            print(f"下载过程出错: {e}")
            return None

    
    def install_mysql(self, installer_path: str = None) -> bool:
        """安装MySQL"""
        try:
            return self._install_mysql_windows(installer_path)
        except Exception as e:
            print(f"安装失败: {e}")
            return False

    def _install_mysql_windows(self, installer_path: str) -> bool:
        """安装Windows版MySQL"""
        print("正在安装MySQL for Windows...")

        if not installer_path:
            print("错误: 未指定安装包路径")
            return False

        # 检查安装包是否存在
        if not os.path.exists(installer_path):
            print(f"错误: 安装包不存在: {installer_path}")
            return False

        # 创建安装目录
        os.makedirs(self.installation_path, exist_ok=True)
        extract_path = os.path.dirname(self.installation_path)

        try:
            # 解压安装包
            print("正在解压安装包...")
            with zipfile.ZipFile(installer_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 查找解压后的MySQL目录
            extracted_mysql_dir = None
            for item in os.listdir(extract_path):
                if item.startswith(f"mysql-{self.mysql_version}-winx64"):
                    extracted_mysql_dir = os.path.join(extract_path, item)
                    break

            if not extracted_mysql_dir:
                print("错误: 未找到解压后的MySQL目录")
                return False

            # 移动文件到安装目录
            print(f"正在移动文件到: {self.installation_path}")
            if os.path.exists(self.installation_path):
                shutil.rmtree(self.installation_path)
            shutil.move(extracted_mysql_dir, self.installation_path)

            # 创建必要的目录（简化配置）
            data_dir = os.path.join(self.installation_path, "data")
            temp_dir = os.path.join(self.installation_path, "temp")

            for dir_path in [data_dir, temp_dir]:
                os.makedirs(dir_path, exist_ok=True)
                print(f"创建目录: {dir_path}")

            # 创建配置文件
            print("正在创建配置文件...")
            config_file = self.config_manager.create_config_file(
                installation_path=self.installation_path,
                data_dir=data_dir
            )

            # 初始化数据目录
            print("正在初始化数据目录...")
            if not self._initialize_data_directory(secure=False):
                raise Exception("数据目录初始化失败")

            # 安装服务
            print("正在安装Windows服务...")
            self._install_service_windows()

            print("MySQL安装完成")
            print(f"安装路径: {self.installation_path}")
            print(f"配置文件: {config_file}")
            return True

        except Exception as e:
            print(f"安装过程中出错: {e}")
            # 清理失败的安装
            if os.path.exists(self.installation_path):
                try:
                    shutil.rmtree(self.installation_path)
                    print("已清理失败的安装文件")
                except:
                    pass
            return False

    def _install_service_windows(self):
        """安装Windows服务"""
        print(f"正在安装MySQL服务: {self.service_name}")

        mysqld_path = os.path.join(self.installation_path, "bin", "mysqld.exe")
        config_file = os.path.join(self.installation_path, "my.ini")

        # 检查mysqld.exe是否存在
        if not os.path.exists(mysqld_path):
            print(f"错误: 找不到mysqld.exe: {mysqld_path}")
            return False

        # 检查配置文件是否存在
        if not os.path.exists(config_file):
            print(f"错误: 找不到配置文件: {config_file}")
            return False

        try:
            # 先删除可能存在的同名服务
            self._remove_service_windows()

            # 安装新服务
            cmd = [
                mysqld_path,
                "--install",
                self.service_name,
                f"--defaults-file={config_file}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"服务 {self.service_name} 安装成功")
                print("提示: 使用 'net start MySQL80' 启动服务")
                return True
            else:
                print(f"服务安装失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"安装服务时出错: {e}")
            return False

    def initialize_mysql(self, secure: bool = False, root_password: Optional[str] = None) -> bool:
        """
        初始化MySQL数据库

        Args:
            secure: 是否使用安全模式初始化(会生成临时密码)
            root_password: 可选的root密码，如果提供则设置root密码

        Returns:
            初始化是否成功
        """
        try:
            print("正在初始化MySQL数据库...")

            # 检查是否已经初始化
            if self._is_data_directory_initialized():
                print("MySQL数据目录已经初始化")
                return True

            # 初始化数据目录
            if not self._initialize_data_directory(secure=secure):
                return False

            # 如果提供了root密码，设置密码
            if root_password:
                return self._set_root_password(root_password)

            return True

        except Exception as e:
            print(f"MySQL初始化失败: {e}")
            return False

    def _initialize_data_directory(self, secure: bool = False) -> bool:
        """
        初始化数据目录

        Args:
            secure: 是否使用安全模式(会生成临时密码)

        Returns:
            初始化是否成功
        """
        print("正在初始化MySQL数据目录...")

        mysqld_path = os.path.join(self.installation_path, "bin", "mysqld.exe")
        data_dir = os.path.join(self.installation_path, "data")
        config_file = os.path.join(self.installation_path, "my.ini")

        # 检查mysqld.exe是否存在
        if not os.path.exists(mysqld_path):
            print(f"错误: 找不到mysqld.exe: {mysqld_path}")
            return False

        # 确保数据目录存在但为空
        if os.path.exists(data_dir):
            print(f"清空数据目录: {data_dir}")
            shutil.rmtree(data_dir)

        os.makedirs(data_dir, exist_ok=True)

        # 检查配置文件是否存在并显示内容
        if os.path.exists(config_file):
            print(f"使用配置文件: {config_file}")
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                    print("配置文件内容:")
                    print(config_content)
            except Exception as e:
                print(f"读取配置文件失败: {e}")
        else:
            print(f"警告: 配置文件不存在: {config_file}")

        cmd = [
            mysqld_path,
            "--initialize-insecure" if not secure else "--initialize",
            f"--basedir={self.installation_path}",
            f"--datadir={data_dir}",
            "--console"  # 添加console选项以显示详细输出
        ]

        # 使用配置文件
        if os.path.exists(config_file):
            cmd.append(f"--defaults-file={config_file}")

        # 使用执行器运行命令
        self.executor.run_command(cmd, raise_on_error=False)

        if self.executor.success():
            print("数据目录初始化成功")
            if secure:
                print("已使用安全模式初始化，临时密码已记录到错误日志中")
            else:
                print("已使用无密码模式初始化，root用户无密码")
            return True
        else:
            print(f"数据目录初始化失败: {self.executor.get_error()}")
            return False

    def _is_data_directory_initialized(self) -> bool:
        """检查数据目录是否已经初始化"""
        data_dir = os.path.join(self.installation_path, "data")
        if not os.path.exists(data_dir):
            return False

        # 检查是否存在MySQL系统数据库文件
        mysql_dir = os.path.join(data_dir, "mysql")
        return os.path.exists(mysql_dir) and os.listdir(mysql_dir)

    def _set_root_password(self, password: str) -> bool:
        """
        设置root密码

        Args:
            password: 新的root密码

        Returns:
            设置是否成功
        """
        try:
            print("正在设置root密码...")

            # 首先启动MySQL服务
            if not self.start_service():
                print("无法启动MySQL服务")
                return False

            mysql_exe = os.path.join(self.installation_path, "bin", "mysql.exe")

            # 等待服务启动
            time.sleep(3)

            # 设置root密码
            cmd = [
                mysql_exe,
                "-u", "root",
                "-e", f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{password}';"
            ]

            # 使用执行器运行命令
            self.executor.run_command(cmd, raise_on_error=False)

            if self.executor.success():
                print("root密码设置成功")
                return True
            else:
                print(f"设置root密码失败: {self.executor.get_error()}")
                return False

        except Exception as e:
            print(f"设置root密码时出错: {e}")
            return False

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

    
    def uninstall_mysql(self) -> bool:
        """卸载MySQL"""
        try:
            return self._uninstall_mysql_windows()
        except Exception as e:
            print(f"卸载失败: {e}")
            return False

    def _uninstall_mysql_windows(self) -> bool:
        """卸载Windows版MySQL"""
        print("正在卸载MySQL...")

        # 停止并删除服务
        if self.service_exists():
            print("停止服务...")
            self.service_manager.stop_service(self.service_name)
            print("删除服务...")
            self.service_manager.delete_service(self.service_name)

        # 删除安装目录
        if os.path.exists(self.installation_path):
            try:
                shutil.rmtree(self.installation_path)
                print(f"已删除安装目录: {self.installation_path}")
            except Exception as e:
                print(f"删除安装目录失败: {e}")
                return False

        print("MySQL卸载完成")
        return True

    
    def install_service(self) -> bool:
        """安装MySQL服务"""
        try:
            if not os.path.exists(self.installation_path):
                print("MySQL未安装")
                return False

            # 创建MySQL服务配置
            mysqld_path = os.path.join(self.installation_path, "bin", "mysqld.exe")
            config_file = os.path.join(self.installation_path, "my.ini")

            if not os.path.exists(mysqld_path):
                print(f"找不到mysqld.exe: {mysqld_path}")
                return False

            return self.service_manager.create_service(
                name=self.service_name,
                display_name=f"MySQL {self.mysql_version}",
                description=f"MySQL {self.mysql_version} Database Server",
                executable_path=mysqld_path,
                config_file=config_file
            )

        except Exception as e:
            print(f"服务安装失败: {e}")
            return False

    def start_service(self) -> bool:
        """启动MySQL服务"""
        try:
            return self.service_manager.start_service(self.service_name)
        except Exception as e:
            print(f"启动服务失败: {e}")
            return False

    def stop_service(self) -> bool:
        """停止MySQL服务"""
        try:
            return self.service_manager.stop_service(self.service_name)
        except Exception as e:
            print(f"停止服务失败: {e}")
            return False

    def restart_service(self) -> bool:
        """重启MySQL服务"""
        print("正在重启MySQL服务...")
        try:
            return self.service_manager.restart_service(self.service_name)
        except Exception as e:
            print(f"重启服务失败: {e}")
            return False

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            status = self.service_manager.get_service_status(self.service_name)
            return {
                "status": status.value,
                "service_name": self.service_name,
                "exists": self.service_manager.service_exists(self.service_name)
            }
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

    def service_exists(self) -> bool:
        """检查服务是否存在"""
        try:
            return self.service_manager.service_exists(self.service_name)
        except Exception as e:
            print(f"检查服务存在性失败: {e}")
            return False

    def is_mysql_installed(self) -> bool:
        """检查MySQL是否已安装"""
        return os.path.exists(self.installation_path)

    def get_mysql_version(self) -> Optional[str]:
        """获取MySQL版本"""
        try:
            mysql_path = os.path.join(self.installation_path, "bin", "mysql.exe")
            if os.path.exists(mysql_path):
                # 使用执行器的同步方法
                result = self.executor.run_command_sync([mysql_path, "--version"])
                if result.returncode == 0:
                    return result.stdout.split()[4]  # 提取版本号
        except:
            pass

        return None

    def set_root_password(self, password: str) -> bool:
        """设置root密码"""
        try:
            mysqladmin_path = os.path.join(self.installation_path, "bin", "mysqladmin.exe")
            if os.path.exists(mysqladmin_path):
                cmd = [mysqladmin_path, "-u", "root", "password", password]
            else:
                return False

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


