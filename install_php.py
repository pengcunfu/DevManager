#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP 独立安装脚本
支持从多个镜像源下载并安装 PHP
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import urllib.request
import urllib.error
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional


class PHPInstaller:
    """PHP 安装器"""
    
    def __init__(self, version_file: str = None):
        """初始化安装器
        
        Args:
            version_file: 版本配置文件路径
        """
        if version_file is None:
            # 默认使用脚本同目录下的配置文件
            script_dir = Path(__file__).parent
            version_file = script_dir / "software_versions" / "php-windows.json"
        
        self.version_file = Path(version_file)
        self.versions_config = self._load_versions()
        self.temp_dir = Path(tempfile.gettempdir())
    
    def _load_versions(self) -> Dict[str, List[str]]:
        """加载版本配置文件"""
        if not self.version_file.exists():
            print(f"错误: 版本配置文件不存在: {self.version_file}")
            sys.exit(1)
        
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"错误: 无法读取版本配置文件: {e}")
            sys.exit(1)
    
    def list_versions(self):
        """列出所有可用版本"""
        print("可用的 PHP 版本:")
        print("-" * 50)
        for version in sorted(self.versions_config.keys(), reverse=True):
            print(f"  • {version}")
        print("-" * 50)
    
    def download_file(self, urls: List[str], filename: str) -> Optional[Path]:
        """从多个 URL 尝试下载文件
        
        Args:
            urls: URL 列表，按优先级排序
            filename: 保存的文件名
            
        Returns:
            下载成功返回文件路径，失败返回 None
        """
        save_path = self.temp_dir / filename
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n[{i}/{len(urls)}] 尝试从以下地址下载:")
                print(f"  {url}")
                
                # 下载文件
                def show_progress(block_num, block_size, total_size):
                    """显示下载进度"""
                    downloaded = block_num * block_size
                    if total_size > 0:
                        percent = min(downloaded * 100 / total_size, 100)
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        print(f"\r  下载进度: {percent:.1f}% ({downloaded_mb:.1f}MB / {total_mb:.1f}MB)", end='')
                
                urllib.request.urlretrieve(url, save_path, show_progress)
                print("\n  ✓ 下载成功!")
                return save_path
                
            except urllib.error.URLError as e:
                print(f"\n  ✗ 下载失败: {e.reason}")
            except Exception as e:
                print(f"\n  ✗ 下载失败: {e}")
        
        print("\n错误: 所有下载源均失败")
        return None
    
    def extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """解压 ZIP 文件
        
        Args:
            zip_path: ZIP 文件路径
            extract_to: 解压目标目录
            
        Returns:
            解压成功返回 True，失败返回 False
        """
        try:
            print(f"\n正在解压到: {extract_to}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            print("✓ 解压成功!")
            return True
            
        except Exception as e:
            print(f"✗ 解压失败: {e}")
            return False
    
    def configure_php_ini(self, php_dir: Path) -> bool:
        """配置 php.ini 文件
        
        Args:
            php_dir: PHP 安装目录
            
        Returns:
            配置成功返回 True，失败返回 False
        """
        try:
            php_ini_development = php_dir / "php.ini-development"
            php_ini = php_dir / "php.ini"
            
            if php_ini_development.exists() and not php_ini.exists():
                print("\n配置 php.ini...")
                shutil.copy(php_ini_development, php_ini)
                
                # 启用常用扩展
                with open(php_ini, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 启用扩展
                extensions_to_enable = [
                    'extension=curl',
                    'extension=fileinfo',
                    'extension=gd',
                    'extension=mbstring',
                    'extension=mysqli',
                    'extension=openssl',
                    'extension=pdo_mysql',
                    'extension=pdo_sqlite',
                    'extension=sqlite3',
                ]
                
                for ext in extensions_to_enable:
                    # 取消注释扩展
                    content = content.replace(f';{ext}', ext)
                
                # 设置时区
                content = content.replace(';date.timezone =', 'date.timezone = Asia/Shanghai')
                
                with open(php_ini, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✓ php.ini 配置完成")
                return True
            
            return True
            
        except Exception as e:
            print(f"✗ 配置 php.ini 失败: {e}")
            return False
    
    def add_to_path(self, php_dir: Path) -> bool:
        """将 PHP 目录添加到系统 PATH
        
        Args:
            php_dir: PHP 安装目录
            
        Returns:
            添加成功返回 True，失败返回 False
        """
        try:
            print(f"\n添加 PHP 到系统 PATH...")
            
            # 使用 PowerShell 添加到用户 PATH
            ps_script = f"""
$path = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($path -notlike '*{php_dir}*') {{
    [Environment]::SetEnvironmentVariable('Path', "$path;{php_dir}", 'User')
    Write-Host "已添加到 PATH"
}} else {{
    Write-Host "已存在于 PATH 中"
}}
"""
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ 已添加到系统 PATH")
                return True
            else:
                print(f"✗ 添加到 PATH 失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ 添加到 PATH 失败: {e}")
            return False
    
    def check_installation(self, php_dir: Path = None) -> bool:
        """检查 PHP 是否安装成功
        
        Args:
            php_dir: PHP 安装目录（可选）
        """
        try:
            # 如果指定了目录，直接检查该目录下的 php.exe
            if php_dir:
                php_exe = php_dir / "php.exe"
                if not php_exe.exists():
                    return False
                
                result = subprocess.run(
                    [str(php_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                # 检查系统 PATH 中的 php
                result = subprocess.run(
                    ["php", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                php_version = result.stdout.strip().split('\n')[0]
                print(f"\nPHP 版本: {php_version}")
                return True
            
            return False
            
        except Exception as e:
            print(f"检查安装状态失败: {e}")
            return False
    
    def download_only(self, version: str, save_dir: str = None) -> bool:
        """仅下载指定版本的 PHP 安装包
        
        Args:
            version: PHP 版本号
            save_dir: 保存目录，默认为当前目录
            
        Returns:
            下载成功返回 True，失败返回 False
        """
        # 检查版本是否存在
        if version not in self.versions_config:
            print(f"错误: 版本 {version} 不存在")
            print("\n请使用 --list 参数查看所有可用版本")
            return False
        
        urls = self.versions_config[version]
        # 从 URL 中提取文件名
        filename = urls[0].split('/')[-1]
        
        print(f"\n{'='*60}")
        print(f"  下载 PHP v{version}")
        print(f"{'='*60}")
        
        # 下载安装包
        zip_path = self.download_file(urls, filename)
        if not zip_path:
            return False
        
        # 移动到指定目录
        if save_dir:
            save_dir_path = Path(save_dir)
            save_dir_path.mkdir(parents=True, exist_ok=True)
            final_path = save_dir_path / filename
            
            try:
                shutil.move(str(zip_path), str(final_path))
                print(f"\n✓ 安装包已保存到: {final_path}")
            except Exception as e:
                print(f"\n✗ 移动文件失败: {e}")
                print(f"文件仍在: {zip_path}")
        else:
            # 移动到当前目录
            final_path = Path.cwd() / filename
            try:
                shutil.move(str(zip_path), str(final_path))
                print(f"\n✓ 安装包已保存到: {final_path}")
            except Exception as e:
                print(f"\n✗ 移动文件失败: {e}")
                print(f"文件仍在: {zip_path}")
        
        print(f"\n{'='*60}")
        print("  下载完成!")
        print(f"{'='*60}")
        return True
    
    def install(self, version: str, install_dir: str = None, 
                add_to_path: bool = True, configure_ini: bool = True,
                keep_zip: bool = False) -> bool:
        """安装指定版本的 PHP
        
        Args:
            version: PHP 版本号
            install_dir: 安装目录，默认为 C:\PHP\php-{version}
            add_to_path: 是否添加到 PATH
            configure_ini: 是否配置 php.ini
            keep_zip: 是否保留 ZIP 文件
            
        Returns:
            安装成功返回 True，失败返回 False
        """
        # 检查版本是否存在
        if version not in self.versions_config:
            print(f"错误: 版本 {version} 不存在")
            print("\n请使用 --list 参数查看所有可用版本")
            return False
        
        urls = self.versions_config[version]
        filename = urls[0].split('/')[-1]
        
        # 确定安装目录
        if install_dir:
            php_dir = Path(install_dir)
        else:
            php_dir = Path(f"C:\\PHP\\php-{version}")
        
        print(f"\n{'='*60}")
        print(f"  安装 PHP v{version}")
        print(f"{'='*60}")
        print(f"安装目录: {php_dir}")
        
        # 检查目录是否已存在
        if php_dir.exists():
            print(f"\n警告: 目录已存在: {php_dir}")
            response = input("是否覆盖? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("取消安装")
                return False
            shutil.rmtree(php_dir)
        
        # 下载安装包
        zip_path = self.download_file(urls, filename)
        if not zip_path:
            return False
        
        # 创建安装目录
        php_dir.mkdir(parents=True, exist_ok=True)
        
        # 解压
        if not self.extract_zip(zip_path, php_dir):
            return False
        
        # 配置 php.ini
        if configure_ini:
            self.configure_php_ini(php_dir)
        
        # 添加到 PATH
        if add_to_path:
            self.add_to_path(php_dir)
        
        # 清理 ZIP 文件
        if not keep_zip and zip_path.exists():
            try:
                zip_path.unlink()
                print(f"\n已删除安装包: {zip_path}")
            except Exception as e:
                print(f"\n删除安装包失败: {e}")
        elif keep_zip:
            print(f"\n安装包保存在: {zip_path}")
        
        # 验证安装
        print("\n验证安装...")
        if self.check_installation(php_dir):
            print(f"\n{'='*60}")
            print("  PHP 安装完成!")
            print(f"{'='*60}")
            print(f"\n安装位置: {php_dir}")
            print("\n提示:")
            print("  1. 您可能需要重新打开命令行窗口以使用 php 命令")
            print("  2. 可以编辑 php.ini 文件来自定义配置")
            print(f"  3. php.ini 位置: {php_dir / 'php.ini'}")
            return True
        else:
            print("\n警告: 安装完成但验证失败")
            print(f"请手动检查: {php_dir}")
            return True
        
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PHP 独立安装脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                      列出所有可用版本
  %(prog)s --install 8.3.14            安装 PHP 8.3.14
  %(prog)s --download 8.2.26           仅下载 PHP 8.2.26 安装包
  %(prog)s --install 8.1.31 --keep     安装并保留 ZIP 文件
  %(prog)s --install 8.3.14 --dir "D:\\PHP\\php83"  安装到指定目录
  %(prog)s --install 8.2.26 --no-path  安装但不添加到 PATH
        """
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有可用的 PHP 版本'
    )
    
    parser.add_argument(
        '--install', '-i',
        metavar='VERSION',
        help='安装指定版本的 PHP'
    )
    
    parser.add_argument(
        '--download', '-d',
        metavar='VERSION',
        help='仅下载指定版本的 PHP 安装包（不安装）'
    )
    
    parser.add_argument(
        '--dir',
        metavar='DIRECTORY',
        help='指定安装目录（默认: C:\\PHP\\php-{version}）'
    )
    
    parser.add_argument(
        '--keep', '-k',
        action='store_true',
        help='保留下载的 ZIP 文件'
    )
    
    parser.add_argument(
        '--no-path',
        action='store_true',
        help='不添加 PHP 到系统 PATH'
    )
    
    parser.add_argument(
        '--no-ini',
        action='store_true',
        help='不配置 php.ini 文件'
    )
    
    parser.add_argument(
        '--version-file',
        metavar='FILE',
        help='指定版本配置文件路径'
    )
    
    args = parser.parse_args()
    
    # 检查是否为 Windows 系统
    if sys.platform != 'win32':
        print("错误: 此脚本仅支持 Windows 系统")
        sys.exit(1)
    
    # 创建安装器
    try:
        installer = PHPInstaller(args.version_file)
    except Exception as e:
        print(f"错误: 初始化安装器失败: {e}")
        sys.exit(1)
    
    # 处理命令行参数
    if args.list:
        installer.list_versions()
    elif args.download:
        success = installer.download_only(args.download)
        sys.exit(0 if success else 1)
    elif args.install:
        success = installer.install(
            args.install,
            install_dir=args.dir,
            add_to_path=not args.no_path,
            configure_ini=not args.no_ini,
            keep_zip=args.keep
        )
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        sys.exit(1)
