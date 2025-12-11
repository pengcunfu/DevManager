#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO 安装和服务管理脚本
提供 MinIO 的安装、卸载、服务管理等功能
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
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any


class MinIOInstaller:
    """MinIO 安装器和服务管理器"""

    def __init__(self):
        """初始化安装器"""
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.minio_version = "RELEASE.2025-01-16T16-07-38Z"
        self.installation_path = self._get_default_installation_path()
        self.service_name = "MinIO" if self.system == "windows" else "minio"

    def _get_default_installation_path(self) -> str:
        """获取默认安装路径"""
        if self.system == "windows":
            return r"C:\MinIO"
        else:
            return "/opt/minio"

    def _get_download_url(self) -> str:
        """获取MinIO下载URL"""
        # 确定架构
        if self.architecture in ['x86_64', 'amd64']:
            arch = 'amd64'
        elif self.architecture in ['arm64', 'aarch64']:
            arch = 'arm64'
        else:
            arch = 'amd64'  # 默认

        if self.system == "windows":
            return f"https://dl.min.io/server/minio/release/windows-{arch}/minio.exe"
        elif self.system == "linux":
            return f"https://dl.min.io/server/minio/release/linux-{arch}/minio"
        elif self.system == "darwin":
            return f"https://dl.min.io/server/minio/release/darwin-{arch}/minio"
        else:
            raise RuntimeError(f"不支持的操作系统: {self.system}")

    def check_requirements(self) -> Dict[str, bool]:
        """检查安装要求"""
        requirements = {
            'internet': self._check_internet_connection(),
            'disk_space': self._check_disk_space(100),  # 100MB
            'admin_privileges': self._check_admin_privileges(),
        }

        return requirements

    def _check_internet_connection(self) -> bool:
        """检查网络连接"""
        try:
            response = requests.get("https://min.io", timeout=5)
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

    def download_minio(self) -> Optional[str]:
        """下载MinIO"""
        download_url = self._get_download_url()
        print(f"正在下载MinIO from: {download_url}")

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # 保存到临时目录
            temp_dir = tempfile.gettempdir()
            if self.system == "windows":
                filename = "minio.exe"
            else:
                filename = "minio"
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

    def install_minio(self, installer_path: str = None) -> bool:
        """安装MinIO"""
        try:
            if not installer_path:
                # 自动下载
                installer_path = self.download_minio()
                if not installer_path:
                    print("下载MinIO失败")
                    return False

            # 创建安装目录
            os.makedirs(self.installation_path, exist_ok=True)

            # 复制可执行文件
            if self.system == "windows":
                target_path = os.path.join(self.installation_path, "minio.exe")
            else:
                target_path = os.path.join(self.installation_path, "minio")

            shutil.copy2(installer_path, target_path)

            # 设置执行权限 (Linux/macOS)
            if self.system != "windows":
                os.chmod(target_path, 0o755)

            # 创建配置和数据目录
            config_dir = os.path.join(self.installation_path, "config")
            data_dir = os.path.join(self.installation_path, "data")
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(data_dir, exist_ok=True)

            # 创建环境配置文件
            self._create_env_file()

            print(f"MinIO安装完成: {self.installation_path}")
            return True

        except Exception as e:
            print(f"安装失败: {e}")
            return False

    def _create_env_file(self):
        """创建环境配置文件"""
        env_content = f"""# MinIO Environment Configuration
# Generated by DevManager

# MinIO访问凭证 (请修改这些值)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# MinIO数据目录
MINIO_VOLUMES={os.path.join(self.installation_path, 'data')}

# MinIO服务地址
MINIO_ADDRESS=:9000

# MinIO区域
MINIO_REGION=us-east-1

# MinIO控制台
MINIO_BROWSER=on

# SSL/TLS (默认关闭)
# MINIO_CERT_FILE=public.crt
# MINIO_KEY_FILE=private.key
"""

        env_file = os.path.join(self.installation_path, "minio.env")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)

    def uninstall_minio(self) -> bool:
        """卸载MinIO"""
        try:
            # 停止并删除服务
            if self.service_exists():
                self.stop_service()
                self._remove_service()

            # 删除安装目录
            if os.path.exists(self.installation_path):
                try:
                    shutil.rmtree(self.installation_path)
                    print(f"已删除安装目录: {self.installation_path}")
                except Exception as e:
                    print(f"删除安装目录失败: {e}")
                    return False

            print("MinIO卸载完成")
            return True

        except Exception as e:
            print(f"卸载失败: {e}")
            return False

    def install_service(self) -> bool:
        """安装MinIO服务"""
        try:
            if self.system == "windows":
                return self._install_service_windows()
            else:
                return self._install_service_unix()
        except Exception as e:
            print(f"服务安装失败: {e}")
            return False

    def _install_service_windows(self) -> bool:
        """安装Windows服务"""
        try:
            import win32serviceutil
            import win32service
            import win32event
            import servicemanager

            # MinIO服务类
            class MinIOService(win32serviceutil.ServiceFramework):
                _svc_name_ = self.service_name
                _svc_display_name_ = "MinIO Object Storage"
                _svc_description_ = "MinIO is a High Performance Object Storage"

                def __init__(self, args):
                    win32serviceutil.ServiceFramework.__init__(self, args)
                    self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

                def SvcStop(self):
                    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                    win32event.SetEvent(self.hWaitStop)

                def SvcDoRun(self):
                    # 启动MinIO进程
                    minio_exe = os.path.join(self.installation_path, "minio.exe")
                    cmd = [minio_exe, "server", os.path.join(self.installation_path, "data")]
                    subprocess.Popen(cmd)

            # 安装服务
            win32serviceutil.InstallService(
                MinIOService._svc_name_,
                MinIOService._svc_display_name_,
                MinIOService._svc_description_
            )

            print(f"Windows服务安装成功: {self.service_name}")
            return True

        except ImportError:
            print("需要安装pywin32库来创建Windows服务")
            print("请运行: pip install pywin32")
            return False
        except Exception as e:
            print(f"安装Windows服务失败: {e}")
            return False

    def _install_service_unix(self) -> bool:
        """安装Unix系统服务"""
        try:
            if self.system == "linux":
                # 创建systemd服务文件
                service_content = f"""[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
Type=simple
User=minio
Group=minio
ExecStart={os.path.join(self.installation_path, 'minio')} server {os.path.join(self.installation_path, 'data')}
EnvironmentFile={os.path.join(self.installation_path, 'minio.env')}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

                service_file = "/etc/systemd/system/minio.service"
                with open(service_file, 'w') as f:
                    f.write(service_content)

                # 创建minio用户
                subprocess.run(["useradd", "-r", "-s", "/sbin/nologin", "minio"], check=False)

                # 设置目录权限
                subprocess.run(["chown", "-R", "minio:minio", self.installation_path], check=False)

                # 重新加载systemd
                subprocess.run(["systemctl", "daemon-reload"], check=True)

                print(f"Systemd服务创建成功: {service_file}")
                return True

            elif self.system == "darwin":
                # 创建launchd服务文件
                service_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.minio.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>{os.path.join(self.installation_path, 'minio')}</string>
        <string>server</string>
        <string>{os.path.join(self.installation_path, 'data')}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/minio.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/minio.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>MINIO_ROOT_USER</key>
        <string>minioadmin</string>
        <key>MINIO_ROOT_PASSWORD</key>
        <string>minioadmin</string>
    </dict>
</dict>
</plist>
"""

                service_file = "/Library/LaunchDaemons/com.minio.server.plist"
                with open(service_file, 'w') as f:
                    f.write(service_content)

                print(f"LaunchDaemons服务创建成功: {service_file}")
                return True

        except Exception as e:
            print(f"创建Unix服务失败: {e}")
            return False

    def start_service(self) -> bool:
        """启动MinIO服务"""
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
        try:
            import win32serviceutil
            win32serviceutil.StartService(self.service_name)
            print("MinIO服务启动成功")
            return True
        except ImportError:
            # 备用方案：直接启动进程
            minio_exe = os.path.join(self.installation_path, "minio.exe")
            data_dir = os.path.join(self.installation_path, "data")
            cmd = [minio_exe, "server", data_dir]
            subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS)
            print("MinIO进程启动成功")
            return True

    def _start_service_unix(self) -> bool:
        """启动Unix服务"""
        if self.system == "linux":
            commands = [
                ["systemctl", "start", "minio"],
                ["service", "minio", "start"]
            ]
        else:  # macOS
            commands = [
                ["launchctl", "load", "/Library/LaunchDaemons/com.minio.server.plist"]
            ]

        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print("MinIO服务启动成功")
                return True
            except subprocess.CalledProcessError:
                continue

        print("启动服务失败")
        return False

    def stop_service(self) -> bool:
        """停止MinIO服务"""
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
        try:
            import win32serviceutil
            win32serviceutil.StopService(self.service_name)
            print("MinIO服务停止成功")
            return True
        except ImportError:
            # 备用方案：终止进程
            try:
                subprocess.run(["taskkill", "/f", "/im", "minio.exe"], check=True)
                print("MinIO进程已终止")
                return True
            except subprocess.CalledProcessError:
                print("无法终止MinIO进程")
                return False

    def _stop_service_unix(self) -> bool:
        """停止Unix服务"""
        if self.system == "linux":
            commands = [
                ["systemctl", "stop", "minio"],
                ["service", "minio", "stop"]
            ]
        else:  # macOS
            commands = [
                ["launchctl", "unload", "/Library/LaunchDaemons/com.minio.server.plist"]
            ]

        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print("MinIO服务停止成功")
                return True
            except subprocess.CalledProcessError:
                continue

        print("停止服务失败")
        return False

    def restart_service(self) -> bool:
        """重启MinIO服务"""
        print("正在重启MinIO服务...")
        if self.stop_service():
            time.sleep(2)
            return self.start_service()
        return False

    def _remove_service(self):
        """删除服务"""
        try:
            if self.system == "windows":
                import win32serviceutil
                win32serviceutil.RemoveService(self.service_name)
                print(f"Windows服务删除成功: {self.service_name}")
            elif self.system == "linux":
                subprocess.run(["systemctl", "disable", "minio"], check=False)
                subprocess.run(["systemctl", "stop", "minio"], check=False)
                os.remove("/etc/systemd/system/minio.service")
                subprocess.run(["systemctl", "daemon-reload"], check=True)
                print("Systemd服务删除成功")
            elif self.system == "darwin":
                subprocess.run(["launchctl", "unload", "/Library/LaunchDaemons/com.minio.server.plist"], check=False)
                os.remove("/Library/LaunchDaemons/com.minio.server.plist")
                print("LaunchDaemons服务删除成功")
        except Exception as e:
            print(f"删除服务失败: {e}")

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

        except:
            # 备用方案：检查进程
            try:
                result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq minio.exe"],
                                      capture_output=True, text=True)
                if "minio.exe" in result.stdout:
                    return {"status": "running", "service_name": self.service_name}
                else:
                    return {"status": "stopped", "service_name": self.service_name}
            except:
                return {"status": "unknown", "message": "无法获取服务状态"}

    def _get_service_status_unix(self) -> Dict[str, Any]:
        """获取Unix服务状态"""
        if self.system == "linux":
            commands = [
                ["systemctl", "status", "minio"],
                ["service", "minio", "status"]
            ]

            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode in [0, 3]:  # 0=running, 3=stopped
                        if "active (running)" in result.stdout:
                            return {"status": "running"}
                        elif "inactive (dead)" in result.stdout or "stopped" in result.stdout:
                            return {"status": "stopped"}
                except:
                    continue
        else:  # macOS
            try:
                result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
                if "com.minio.server" in result.stdout:
                    return {"status": "running"}
                else:
                    return {"status": "stopped"}
            except:
                pass

        return {"status": "unknown"}

    def service_exists(self) -> bool:
        """检查服务是否存在"""
        status = self.get_service_status()
        return status.get("status") != "error"

    def is_minio_installed(self) -> bool:
        """检查MinIO是否已安装"""
        if self.system == "windows":
            minio_exe = os.path.join(self.installation_path, "minio.exe")
        else:
            minio_exe = os.path.join(self.installation_path, "minio")

        return os.path.exists(minio_exe)

    def get_minio_version(self) -> Optional[str]:
        """获取MinIO版本"""
        try:
            if self.system == "windows":
                minio_exe = os.path.join(self.installation_path, "minio.exe")
            else:
                minio_exe = os.path.join(self.installation_path, "minio")

            if os.path.exists(minio_exe):
                result = subprocess.run([minio_exe, "--version"],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # 从版本信息中提取版本号
                    version_line = result.stdout.strip()
                    if "Version" in version_line:
                        return version_line.split()[-1]
        except:
            pass

        return None

    def get_minio_info(self) -> Dict[str, Any]:
        """获取MinIO详细信息"""
        info = {
            'installed': self.is_minio_installed(),
            'version': self.get_minio_version(),
            'installation_path': self.installation_path if self.is_minio_installed() else None,
            'service_status': self.get_service_status(),
            'system': self.system,
            'architecture': self.architecture
        }

        return info


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MinIO 安装和管理工具")
    parser.add_argument('--install', action='store_true', help='安装MinIO')
    parser.add_argument('--uninstall', action='store_true', help='卸载MinIO')
    parser.add_argument('--start', action='store_true', help='启动MinIO服务')
    parser.add_argument('--stop', action='store_true', help='停止MinIO服务')
    parser.add_argument('--restart', action='store_true', help='重启MinIO服务')
    parser.add_argument('--status', action='store_true', help='查看服务状态')
    parser.add_argument('--install-service', action='store_true', help='安装MinIO服务')
    parser.add_argument('--check', action='store_true', help='检查安装要求')
    parser.add_argument('--version', action='store_true', help='获取MinIO版本')
    parser.add_argument('--info', action='store_true', help='获取详细信息')

    args = parser.parse_args()

    installer = MinIOInstaller()

    if args.check:
        print("检查安装要求:")
        requirements = installer.check_requirements()
        for req, satisfied in requirements.items():
            status = "✓" if satisfied else "✗"
            print(f"  {status} {req}")

    elif args.install:
        print("开始安装MinIO...")
        if installer.is_minio_installed():
            print("MinIO已经安装")
        else:
            # 检查要求
            requirements = installer.check_requirements()
            if all(requirements.values()):
                if installer.install_minio():
                    print("MinIO安装成功")
                else:
                    print("MinIO安装失败")
            else:
                print("不满足安装要求")
                for req, satisfied in requirements.items():
                    if not satisfied:
                        print(f"  缺少: {req}")

    elif args.uninstall:
        if installer.uninstall_minio():
            print("MinIO卸载完成")
        else:
            print("卸载失败")

    elif args.start:
        installer.start_service()

    elif args.stop:
        installer.stop_service()

    elif args.restart:
        installer.restart_service()

    elif args.status:
        status = installer.get_service_status()
        print(f"服务状态: {status.get('status', 'unknown')}")

    elif args.install_service:
        installer.install_service()

    elif args.version:
        version = installer.get_minio_version()
        if version:
            print(f"MinIO版本: {version}")
        else:
            print("无法获取MinIO版本，可能未安装")

    elif args.info:
        info = installer.get_minio_info()
        print("MinIO 信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    else:
        # 默认显示状态
        if installer.is_minio_installed():
            print("MinIO已安装")
            version = installer.get_minio_version()
            if version:
                print(f"版本: {version}")

            status = installer.get_service_status()
            print(f"服务状态: {status.get('status', 'unknown')}")
        else:
            print("MinIO未安装")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)