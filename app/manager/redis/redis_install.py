#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 安装和服务管理模块
提供 Redis 的安装、卸载、服务管理等功能
"""

import os
import sys
import platform
import subprocess
import shutil
import time
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import logging

# 导入配置模块
from . import redis_constants

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RedisInstaller:
    """Redis 安装和服务管理器"""

    def __init__(self):
        """初始化安装器"""
        self.system = platform.system().lower()
        # 使用配置模块获取版本和安装路径
        self.redis_version = redis_constants.get_version()
        self.installation_path = redis_constants.get_install_path()
        self.download_url = redis_constants.get_download_url()

    def check_redis_installed(self) -> bool:
        """检查 Redis 是否已安装"""
        try:
            if self.system == "windows":
                # 检查 Windows 安装
                result = subprocess.run(['redis-server', '--version'],
                                      capture_output=True, text=True)
                return result.returncode == 0
            else:
                # 检查 Linux/macOS 安装
                result = subprocess.run(['redis-server', '--version'],
                                      capture_output=True, text=True)
                return result.returncode == 0
        except FileNotFoundError:
            return False

    def get_redis_version(self) -> Optional[str]:
        """获取已安装的 Redis 版本"""
        try:
            result = subprocess.run(['redis-server', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def install_redis(self) -> Tuple[bool, str]:
        """安装 Redis"""
        try:
            if self.check_redis_installed():
                return True, "Redis 已经安装"

            logger.info("开始安装 Redis...")

            if self.system == "windows":
                return self._install_redis_windows()
            else:
                return self._install_redis_unix()

        except Exception as e:
            error_msg = f"安装 Redis 失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _install_redis_windows(self) -> Tuple[bool, str]:
        """Windows 下安装 Redis"""
        try:
            # 创建安装目录
            os.makedirs(self.installation_path, exist_ok=True)

            # 下载 Redis
            logger.info("下载 Redis for Windows...")
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()

            installer_path = os.path.join(self.installation_path, "redis.msi")
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 静默安装
            logger.info("安装 Redis...")
            result = subprocess.run([
                'msiexec', '/i', installer_path,
                '/quiet', '/norestart',
                f'INSTALLDIR={self.installation_path}'
            ], check=True)

            # 添加到 PATH
            self._add_to_windows_path()

            # 创建配置文件
            self._create_default_config_windows()

            return True, "Redis 安装成功"

        except Exception as e:
            return False, f"Windows 安装失败: {str(e)}"

    def _install_redis_unix(self) -> Tuple[bool, str]:
        """Linux/macOS 下安装 Redis"""
        try:
            # 检查是否使用包管理器
            if self._try_package_manager():
                return True, "Redis 通过包管理器安装成功"

            # 源码编译安装
            return self._compile_redis()

        except Exception as e:
            return False, f"Unix 安装失败: {str(e)}"

    def _try_package_manager(self) -> bool:
        """尝试使用包管理器安装"""
        package_managers = redis_constants.get_package_managers()

        for pm, cmd in package_managers.items():
            try:
                if shutil.which(pm):
                    logger.info(f"使用 {pm} 安装 Redis...")
                    # 配置返回的是字符串命令，需要转换为列表
                    if isinstance(cmd, str):
                        cmd_list = cmd.split()
                    else:
                        cmd_list = cmd
                    subprocess.run(cmd_list, check=True)
                    return True
            except subprocess.CalledProcessError:
                continue

        return False

    def _compile_redis(self) -> Tuple[bool, str]:
        """源码编译安装 Redis"""
        try:
            # 下载源码
            logger.info("下载 Redis 源码...")
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()

            tar_path = "/tmp/redis.tar.gz"
            with open(tar_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 解压
            extract_path = "/tmp/redis_source"
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(extract_path)

            # 编译安装
            redis_dir = os.path.join(extract_path, f"redis-{self.redis_version}")
            os.chdir(redis_dir)

            logger.info("编译 Redis...")
            subprocess.run(['make'], check=True)

            if self.system == "linux":
                subprocess.run(['sudo', 'make', 'install'], check=True)
            else:  # macOS
                subprocess.run(['make', 'install'], check=True)

            # 创建配置目录
            config_dir = "/etc/redis"
            if self.system == "linux":
                subprocess.run(['sudo', 'mkdir', '-p', config_dir], check=True)
                subprocess.run(['sudo', 'cp', 'redis.conf', '/etc/redis/'], check=True)
            else:
                os.makedirs(config_dir, exist_ok=True)
                shutil.copy('redis.conf', config_dir)

            # 创建数据目录
            data_dir = "/var/lib/redis"
            if self.system == "linux":
                subprocess.run(['sudo', 'mkdir', '-p', data_dir], check=True)
                subprocess.run(['sudo', 'chown', 'redis:redis', data_dir], check=True)
            else:
                os.makedirs(data_dir, exist_ok=True)

            return True, "Redis 源码编译安装成功"

        except Exception as e:
            return False, f"编译安装失败: {str(e)}"

    def _add_to_windows_path(self):
        """添加 Redis 到 Windows PATH"""
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                              0, winreg.KEY_READ) as key:
                current_path = winreg.QueryValueEx(key, "PATH")[0]

            redis_bin = os.path.join(self.installation_path, "bin")
            if redis_bin not in current_path:
                new_path = current_path + ";" + redis_bin

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                  r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                                  0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

                # 通知系统更新环境变量
                subprocess.run(['rundll32', 'user32.dll,UpdatePerUserSystemParameters'],
                             check=True)
        except Exception as e:
            logger.warning(f"添加 PATH 失败: {e}")

    def _create_default_config_windows(self):
        """创建 Windows 默认配置文件"""
        # 使用配置模块获取默认配置
        default_config = redis_constants.get_default_config_options()
        data_dirs = redis_constants.get_data_directories()
        config_name = redis_constants.get_config_file_name()

        config_content = f"""# Redis Windows 配置文件

# 网络配置
bind {default_config['bind']}
port {default_config['port']}
tcp-backlog 511
timeout 300
tcp-keepalive 300

# 通用配置
daemonize {default_config['daemonize']}
supervised no
pidfile "C:/ProgramData/Redis/redis.pid"

# 日志配置
loglevel notice
logfile "C:/ProgramData/Redis/redis.log"

# 数据库配置
databases {default_config['databases']}

# 快照配置
save {default_config['save'][0]}
save {default_config['save'][1]}
save {default_config['save'][2]}
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir "{data_dirs[0]}/"

# 复制配置
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5

# 安全配置
# requirepass your_password_here

# 内存管理
maxmemory {default_config['maxmemory']}
maxmemory-policy {default_config['maxmemory_policy']}
maxmemory-samples 5

# AOF 配置
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 慢查询日志
slowlog-log-slower-than 10000
slowlog-max-len 128

# 客户端配置
maxclients 10000
"""

        config_dir = data_dirs[0].replace("data", "")  # 移除data子目录
        if "ProgramData" in config_dir:
            config_dir = config_dir.replace("\\data", "")
        else:
            config_dir = "C:/ProgramData/Redis"

        os.makedirs(config_dir, exist_ok=True)

        config_file = os.path.join(config_dir, config_name)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)

    def uninstall_redis(self) -> Tuple[bool, str]:
        """卸载 Redis"""
        try:
            # 先停止服务
            self.stop_service()

            if self.system == "windows":
                return self._uninstall_redis_windows()
            else:
                return self._uninstall_redis_unix()

        except Exception as e:
            error_msg = f"卸载 Redis 失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _uninstall_redis_windows(self) -> Tuple[bool, str]:
        """Windows 卸载 Redis"""
        try:
            # 卸载程序
            if os.path.exists(self.installation_path):
                shutil.rmtree(self.installation_path)

            # 删除配置和数据
            program_data = os.environ.get('ProgramData', 'C:\\ProgramData')
            redis_data = os.path.join(program_data, 'Redis')
            if os.path.exists(redis_data):
                shutil.rmtree(redis_data)

            return True, "Redis 卸载成功"

        except Exception as e:
            return False, f"Windows 卸载失败: {str(e)}"

    def _uninstall_redis_unix(self) -> Tuple[bool, str]:
        """Linux/macOS 卸载 Redis"""
        try:
            # 尝试包管理器卸载
            if shutil.which('apt'):
                subprocess.run(['sudo', 'apt', 'remove', '--purge', '-y', 'redis-server'],
                             check=True)
                return True, "Redis 通过 apt 卸载成功"
            elif shutil.which('yum'):
                subprocess.run(['sudo', 'yum', 'remove', '-y', 'redis'], check=True)
                return True, "Redis 通过 yum 卸载成功"
            elif shutil.which('dnf'):
                subprocess.run(['sudo', 'dnf', 'remove', '-y', 'redis'], check=True)
                return True, "Redis 通过 dnf 卸载成功"
            elif shutil.which('brew'):
                subprocess.run(['brew', 'uninstall', 'redis'], check=True)
                return True, "Redis 通过 brew 卸载成功"

            # 手动删除
            redis_dirs = ['/usr/local/bin/redis-*', '/etc/redis', '/var/lib/redis']
            for pattern in redis_dirs:
                if os.path.exists(pattern):
                    if os.path.isdir(pattern):
                        shutil.rmtree(pattern)
                    else:
                        os.remove(pattern)

            return True, "Redis 手动卸载成功"

        except Exception as e:
            return False, f"Unix 卸载失败: {str(e)}"

    def install_service(self) -> Tuple[bool, str]:
        """安装 Redis 服务"""
        try:
            if self.system == "windows":
                return self._install_windows_service()
            else:
                return self._install_unix_service()

        except Exception as e:
            error_msg = f"安装服务失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _install_windows_service(self) -> Tuple[bool, str]:
        """安装 Windows 服务"""
        try:
            redis_server = os.path.join(self.installation_path, "bin", redis_constants.get_server_executable())
            config_file = "C:/ProgramData/Redis/" + redis_constants.get_config_file_name()

            # 安装服务
            cmd = [redis_server, '--service-install', config_file, '--service-name', redis_constants.get_service_name()]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Redis Windows 服务安装成功"
            else:
                return False, f"服务安装失败: {result.stderr}"

        except Exception as e:
            return False, f"Windows 服务安装失败: {str(e)}"

    def _install_unix_service(self) -> Tuple[bool, str]:
        """安装 Unix 服务"""
        try:
            if self.system == "linux":
                # 创建 systemd 服务文件
                service_name = redis_constants.get_service_name()
                service_template = redis_constants.get_systemd_service_template()
                service_content = service_template.format(
                    server_executable=redis_constants.get_server_executable(),
                    client_executable=redis_constants.get_client_executable()
                )

                service_file = f"/etc/systemd/system/{service_name}.service"
                with open(f'/tmp/{service_name}.service', 'w') as f:
                    f.write(service_content)

                subprocess.run(['sudo', 'mv', f'/tmp/{service_name}.service', service_file], check=True)
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True)

                return True, "Redis systemd 服务安装成功"

            else:  # macOS
                # 使用 launchd
                plist_template = redis_constants.get_launchd_plist_template()
                plist_content = plist_template.format(
                    server_executable=redis_constants.get_server_executable()
                )

                with open('/tmp/io.redis.redis-server.plist', 'w') as f:
                    f.write(plist_content)

                subprocess.run(['launchctl', 'load', '/tmp/io.redis.redis-server.plist'], check=True)

                return True, "Redis launchd 服务安装成功"

        except Exception as e:
            return False, f"Unix 服务安装失败: {str(e)}"

    def start_service(self) -> Tuple[bool, str]:
        """启动 Redis 服务"""
        try:
            service_name = redis_constants.get_service_name()

            if self.system == "windows":
                result = subprocess.run([redis_constants.get_server_executable(), '--service-start', '--service-name', service_name],
                                      capture_output=True, text=True)
            elif self.system == "linux":
                result = subprocess.run(['sudo', 'systemctl', 'start', service_name],
                                      capture_output=True, text=True)
            else:  # macOS
                result = subprocess.run(['launchctl', 'start', 'io.redis.redis-server'],
                                      capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Redis 服务启动成功"
            else:
                return False, f"启动服务失败: {result.stderr}"

        except Exception as e:
            error_msg = f"启动服务失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def stop_service(self) -> Tuple[bool, str]:
        """停止 Redis 服务"""
        try:
            service_name = redis_constants.get_service_name()

            if self.system == "windows":
                result = subprocess.run([redis_constants.get_server_executable(), '--service-stop', '--service-name', service_name],
                                      capture_output=True, text=True)
            elif self.system == "linux":
                result = subprocess.run(['sudo', 'systemctl', 'stop', service_name],
                                      capture_output=True, text=True)
            else:  # macOS
                result = subprocess.run(['launchctl', 'stop', 'io.redis.redis-server'],
                                      capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Redis 服务停止成功"
            else:
                return False, f"停止服务失败: {result.stderr}"

        except Exception as e:
            error_msg = f"停止服务失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def restart_service(self) -> Tuple[bool, str]:
        """重启 Redis 服务"""
        try:
            if self.system == "windows":
                result = subprocess.run(['redis-server', '--service-restart', '--service-name', 'Redis'],
                                      capture_output=True, text=True)
            elif self.system == "linux":
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'redis'],
                                      capture_output=True, text=True)
            else:  # macOS
                self.stop_service()
                time.sleep(2)
                return self.start_service()

            if result.returncode == 0:
                return True, "Redis 服务重启成功"
            else:
                return False, f"重启服务失败: {result.stderr}"

        except Exception as e:
            error_msg = f"重启服务失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def uninstall_service(self) -> Tuple[bool, str]:
        """卸载 Redis 服务"""
        try:
            if self.system == "windows":
                result = subprocess.run(['redis-server', '--service-uninstall', '--service-name', 'Redis'],
                                      capture_output=True, text=True)
            elif self.system == "linux":
                result = subprocess.run(['sudo', 'systemctl', 'disable', 'redis'],
                                      capture_output=True, text=True)
                subprocess.run(['sudo', 'rm', '-f', '/etc/systemd/system/redis.service'],
                             check=True)
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            else:  # macOS
                result = subprocess.run(['launchctl', 'unload', '/Library/LaunchDaemons/io.redis.redis-server.plist'],
                                      capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Redis 服务卸载成功"
            else:
                return False, f"卸载服务失败: {result.stderr}"

        except Exception as e:
            error_msg = f"卸载服务失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_service_status(self) -> Dict[str, any]:
        """获取服务状态"""
        status = {
            'installed': False,
            'running': False,
            'enabled': False,
            'version': None,
            'pid': None,
            'memory_usage': None,
            'connections': 0,
            'uptime': None,
            'error': None
        }

        try:
            # 检查安装状态
            if self.check_redis_installed():
                status['installed'] = True
                status['version'] = self.get_redis_version()

            # 检查服务状态
            if self.system == "windows":
                result = subprocess.run(['redis-server', '--service-query', '--service-name', 'Redis'],
                                      capture_output=True, text=True)
                status['running'] = "RUNNING" in result.stdout
                status['enabled'] = "START" in result.stdout

            elif self.system == "linux":
                result = subprocess.run(['systemctl', 'is-active', 'redis'],
                                      capture_output=True, text=True)
                status['running'] = result.returncode == 0

                result = subprocess.run(['systemctl', 'is-enabled', 'redis'],
                                      capture_output=True, text=True)
                status['enabled'] = result.returncode == 0

            else:  # macOS
                result = subprocess.run(['launchctl', 'list', 'io.redis.redis-server'],
                                      capture_output=True, text=True)
                status['running'] = result.returncode == 0

            # 获取运行状态信息
            if status['running']:
                try:
                    # 连接到 Redis 获取详细信息
                    import redis
                    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                    info = r.info()

                    status['pid'] = info.get('process_id')
                    status['memory_usage'] = info.get('used_memory_human')
                    status['connections'] = info.get('connected_clients')
                    status['uptime'] = info.get('uptime_in_seconds')

                except Exception:
                    pass

        except Exception as e:
            status['error'] = str(e)

        return status


def main():
    """主函数 - 用于命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="Redis 安装和服务管理工具")
    parser.add_argument('--install', action='store_true', help='安装 Redis')
    parser.add_argument('--uninstall', action='store_true', help='卸载 Redis')
    parser.add_argument('--install-service', action='store_true', help='安装服务')
    parser.add_argument('--uninstall-service', action='store_true', help='卸载服务')
    parser.add_argument('--start', action='store_true', help='启动服务')
    parser.add_argument('--stop', action='store_true', help='停止服务')
    parser.add_argument('--restart', action='store_true', help='重启服务')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--check', action='store_true', help='检查安装')

    args = parser.parse_args()

    installer = RedisInstaller()

    if args.install:
        success, message = installer.install_redis()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.uninstall:
        success, message = installer.uninstall_redis()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.install_service:
        success, message = installer.install_service()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.uninstall_service:
        success, message = installer.uninstall_service()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.start:
        success, message = installer.start_service()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.stop:
        success, message = installer.stop_service()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.restart:
        success, message = installer.restart_service()
        print(f"{'✓' if success else '✗'} {message}")

    elif args.status or args.check:
        status = installer.get_service_status()
        print("Redis 状态:")
        print(f"  已安装: {'是' if status['installed'] else '否'}")
        if status['version']:
            print(f"  版本: {status['version']}")
        print(f"  服务运行: {'是' if status['running'] else '否'}")
        print(f"  开机启动: {'是' if status['enabled'] else '否'}")
        if status['pid']:
            print(f"  进程ID: {status['pid']}")
        if status['memory_usage']:
            print(f"  内存使用: {status['memory_usage']}")
        print(f"  连接数: {status['connections']}")
        if status['uptime']:
            print(f"  运行时间: {status['uptime']}秒")
        if status['error']:
            print(f"  错误: {status['error']}")

    else:
        # 默认显示状态
        status = installer.get_service_status()
        print("Redis 状态:")
        print(f"  已安装: {'是' if status['installed'] else '否'}")
        if status['version']:
            print(f"  版本: {status['version']}")
        print(f"  服务运行: {'是' if status['running'] else '否'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)