#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composer 独立安装脚本
自动下载并安装 Composer
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import urllib.request
import urllib.error
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional


class ComposerInstaller:
    """Composer 安装器"""

    def __init__(self):
        """初始化安装器"""
        self.temp_dir = Path(tempfile.gettempdir())
        self.php_executable = self._find_php_executable()

    def _find_php_executable(self) -> Optional[str]:
        """查找 PHP 可执行文件路径"""
        # 首先尝试系统 PATH 中的 php
        try:
            result = subprocess.run(
                ['php', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return 'php'
        except Exception:
            pass

        # Windows 系统下的常见 PHP 安装路径
        if sys.platform == 'win32':
            common_paths = [
                r'C:\PHP\php',
                r'C:\php',
                r'C:\xampp\php',
                r'C:\wamp64\bin\php',
                r'C:\laragon\bin\php',
                r'C:\DevSuite\php'
            ]

            for base_path in common_paths:
                php_path = Path(base_path)
                if php_path.exists():
                    # 查找最高版本的 PHP
                    php_versions = []
                    for item in php_path.iterdir():
                        if item.is_dir() and item.name.startswith('php'):
                            php_exe = item / 'php.exe'
                            if php_exe.exists():
                                php_versions.append((item.name, str(php_exe)))

                    if php_versions:
                        # 返回最高版本
                        latest_php = sorted(php_versions, reverse=True)[0]
                        return latest_php[1]

                    # 检查直接的 php.exe
                    php_exe = php_path / 'php.exe'
                    if php_exe.exists():
                        return str(php_exe)

        return None

    def check_php_version(self) -> Optional[str]:
        """检查 PHP 版本是否符合要求"""
        if not self.php_executable:
            return None

        try:
            result = subprocess.run(
                [self.php_executable, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                # 提取版本号
                import re
                match = re.search(r'PHP (\d+\.\d+\.\d+)', version_line)
                if match:
                    return match.group(1)
        except Exception:
            pass

        return None

    def check_php_requirements(self) -> bool:
        """检查 PHP 环境要求"""
        if not self.php_executable:
            print("错误: 未找到 PHP 可执行文件")
            print("请确保已安装 PHP 并将其添加到系统 PATH")
            return False

        version = self.check_php_version()
        if not version:
            print("错误: 无法获取 PHP 版本信息")
            return False

        # Composer 要求 PHP >= 7.2.5
        version_parts = list(map(int, version.split('.')))
        if version_parts[0] < 7 or (version_parts[0] == 7 and version_parts[1] < 2):
            print(f"错误: PHP 版本过低 ({version})")
            print("Composer 要求 PHP 版本 >= 7.2.5")
            return False

        print(f"✓ PHP 版本检查通过: {version}")

        # 检查必需的扩展
        required_extensions = ['openssl', 'phar', 'json', 'mbstring']
        missing_extensions = []

        for ext in required_extensions:
            try:
                result = subprocess.run(
                    [self.php_executable, '-m'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and ext not in result.stdout:
                    missing_extensions.append(ext)
            except Exception:
                missing_extensions.append(ext)

        if missing_extensions:
            print(f"警告: 缺少以下 PHP 扩展: {', '.join(missing_extensions)}")
            print("某些扩展可能会影响 Composer 的正常运行")

        return True

    def download_composer(self) -> Optional[Path]:
        """下载 Composer 安装器"""
        composer_setup_url = 'https://getcomposer.org/installer'
        setup_file = self.temp_dir / 'composer-setup.php'

        print(f"\n正在下载 Composer 安装器...")
        print(f"下载地址: {composer_setup_url}")

        try:
            def show_progress(block_num, block_size, total_size):
                """显示下载进度"""
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(downloaded * 100 / total_size, 100)
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    print(f"\r  下载进度: {percent:.1f}% ({downloaded_mb:.1f}MB / {total_mb:.1f}MB)", end='')

            urllib.request.urlretrieve(composer_setup_url, setup_file, show_progress)
            print("\n✓ 下载完成!")
            return setup_file

        except Exception as e:
            print(f"\n✗ 下载失败: {e}")
            return None

    def verify_installer(self, setup_file: Path) -> bool:
        """验证安装器签名"""
        print(f"\n正在验证安装器签名...")

        try:
            # 获取最新的签名
            sig_url = 'https://composer.github.io/installer.sig'
            sig_response = urllib.request.urlopen(sig_url, timeout=10)
            expected_signature = sig_response.read().decode().strip()

            # 计算本地文件的签名
            with open(setup_file, 'rb') as f:
                content = f.read()
                actual_signature = hashlib.sha384(content).hexdigest()

            if actual_signature == expected_signature:
                print("✓ 签名验证通过")
                return True
            else:
                print("✗ 签名验证失败")
                print(f"期望: {expected_signature[:16]}...")
                print(f"实际: {actual_signature[:16]}...")
                return False

        except Exception as e:
            print(f"✗ 签名验证失败: {e}")
            return False

    def install_composer(self, setup_file: Path, install_dir: str = None,
                        global_install: bool = True) -> bool:
        """安装 Composer

        Args:
            setup_file: 安装器文件路径
            install_dir: 安装目录
            global_install: 是否全局安装

        Returns:
            安装成功返回 True，失败返回 False
        """
        try:
            print(f"\n正在安装 Composer...")

            # 确定安装目录
            if install_dir:
                target_dir = Path(install_dir)
            elif global_install:
                # Windows 系统全局安装目录
                if sys.platform == 'win32':
                    target_dir = Path(r'C:\Composer')
                else:
                    target_dir = Path.home() / '.local' / 'bin'
            else:
                target_dir = Path.cwd()

            target_dir.mkdir(parents=True, exist_ok=True)
            composer_phar = target_dir / 'composer.phar'
            composer_bat = target_dir / 'composer.bat'
            composer_sh = target_dir / 'composer'

            # 使用安装器安装
            install_cmd = [self.php_executable, str(setup_file), '--install-dir', str(target_dir)]
            if global_install:
                install_cmd.append('--filename')
                install_cmd.append('composer')

            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✓ Composer 安装成功!")

                # Windows 系统创建 bat 文件
                if sys.platform == 'win32' and global_install:
                    bat_content = f'@echo off\r\n"{self.php_executable}" "%~dp0composer.phar" %*'
                    with open(composer_bat, 'w') as f:
                        f.write(bat_content)
                    print("✓ 已创建 Windows 批处理文件")

                # Unix/Linux 系统创建 shell 脚本
                elif sys.platform != 'win32' and global_install:
                    sh_content = f'#!/bin/sh\n{self.php_executable} "$0.phar" "$@"'
                    with open(composer_sh, 'w') as f:
                        f.write(sh_content)
                    # 设置执行权限
                    os.chmod(composer_sh, 0o755)
                    print("✓ 已创建 Shell 脚本")

                if global_install:
                    self._add_to_path(target_dir)
            else:
                print(f"✗ 安装失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ 安装失败: {e}")
            return False

        return True

    def _add_to_path(self, install_dir: Path) -> bool:
        """将安装目录添加到系统 PATH"""
        if sys.platform == 'win32':
            try:
                import winreg

                # 添加到用户 PATH
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0,
                    winreg.KEY_READ | winreg.KEY_SET_VALUE
                )

                try:
                    current_path, _ = winreg.QueryValueEx(key, "PATH")
                except WindowsError:
                    current_path = ""

                if str(install_dir) not in current_path:
                    new_path = current_path + ";" + str(install_dir) if current_path else str(install_dir)
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                    winreg.CloseKey(key)

                    # 通知系统环境变量已更改
                    import ctypes
                    ctypes.windll.user32.SendMessageTimeoutW(
                        0xFFFF, 0x001A, 0, "Environment",
                        0x0002, 5000, None
                    )

                    print("✓ 已添加到系统 PATH")
                    return True
                else:
                    print("✓ 已存在于 PATH 中")
                    return True

            except Exception as e:
                print(f"⚠ 添加到 PATH 失败: {e}")
                print(f"请手动将 {install_dir} 添加到系统 PATH")
                return False
        else:
            print(f"请手动将 {install_dir} 添加到系统 PATH")
            return False

    def verify_installation(self) -> bool:
        """验证安装"""
        try:
            # 首先尝试直接使用 composer 命令
            result = subprocess.run(
                ['composer', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"\n{version}")
                return True

            # 如果 composer 命令不可用，尝试使用 php composer.phar
            if self.php_executable:
                # 查找 composer.phar
                possible_paths = [
                    Path(r'C:\Composer\composer.phar'),
                    Path.home() / '.local' / 'bin' / 'composer.phar',
                    Path.cwd() / 'composer.phar'
                ]

                for composer_phar in possible_paths:
                    if composer_phar.exists():
                        result = subprocess.run(
                            [self.php_executable, str(composer_phar), '--version'],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip().split('\n')[0]
                            print(f"\n{version}")
                            print(f"注意: 请将 {composer_phar.parent} 添加到 PATH 或创建别名")
                            return True

        except Exception as e:
            print(f"验证安装失败: {e}")

        return False

    def install(self, install_dir: str = None, global_install: bool = True) -> bool:
        """执行完整安装流程"""
        print(f"\n{'='*60}")
        print("  Composer 安装程序")
        print(f"{'='*60}")

        # 检查 PHP 环境
        if not self.check_php_requirements():
            return False

        # 下载安装器
        setup_file = self.download_composer()
        if not setup_file:
            return False

        # 验证安装器
        if not self.verify_installer(setup_file):
            return False

        # 安装 Composer
        if not self.install_composer(setup_file, install_dir, global_install):
            return False

        # 清理临时文件
        try:
            setup_file.unlink()
            print(f"\n已清理临时文件")
        except Exception:
            pass

        print(f"\n{'='*60}")
        print("  安装完成!")
        print(f"{'='*60}")

        # 验证安装
        print("\n正在验证安装...")
        if self.verify_installation():
            print("\n✓ 安装验证成功")
        else:
            print("\n⚠ 安装可能未完成，请检查环境配置")

        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Composer 独立安装脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          安装到默认位置（全局安装）
  %(prog)s --dir "D:\\Composer"      安装到指定目录
  %(prog)s --local                   安装到当前目录（本地安装）
  %(prog)s --check                   仅检查 PHP 环境
        """
    )

    parser.add_argument(
        '--dir',
        metavar='DIRECTORY',
        help='指定安装目录（默认: 全局安装位置）'
    )

    parser.add_argument(
        '--local',
        action='store_true',
        help='本地安装到当前目录'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='仅检查 PHP 环境要求'
    )

    args = parser.parse_args()

    # 创建安装器
    installer = ComposerInstaller()

    # 处理命令行参数
    if args.check:
        success = installer.check_php_requirements()
        sys.exit(0 if success else 1)
    else:
        success = installer.install(
            install_dir=args.dir,
            global_install=not args.local
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        sys.exit(1)