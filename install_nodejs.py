#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node.js 独立安装脚本
支持从多个镜像源下载并安装 Node.js
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional


class NodejsInstaller:
    """Node.js 安装器"""
    
    def __init__(self, version_file: str = None):
        """初始化安装器
        
        Args:
            version_file: 版本配置文件路径
        """
        if version_file is None:
            # 默认使用脚本同目录下的配置文件
            script_dir = Path(__file__).parent
            version_file = script_dir / "software_versions" / "nodejs-windows.json"
        
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
        print("可用的 Node.js 版本:")
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
    
    def install_msi(self, msi_path: Path) -> bool:
        """安装 MSI 文件
        
        Args:
            msi_path: MSI 文件路径
            
        Returns:
            安装成功返回 True，失败返回 False
        """
        print(f"\n开始安装 Node.js...")
        print(f"安装包路径: {msi_path}")
        
        try:
            # 使用 msiexec 静默安装
            cmd = [
                "msiexec",
                "/i", str(msi_path),
                "/qn",  # 静默安装
                "/norestart"  # 不重启
            ]
            
            print("正在安装，请稍候...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                print("✓ Node.js 安装成功!")
                return True
            else:
                print(f"✗ 安装失败，返回码: {result.returncode}")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ 安装超时")
            return False
        except Exception as e:
            print(f"✗ 安装失败: {e}")
            return False
    
    def check_installation(self) -> bool:
        """检查 Node.js 是否安装成功"""
        try:
            # 检查 node 版本
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"\nNode.js 版本: {node_version}")
                
                # 检查 npm 版本
                result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    npm_version = result.stdout.strip()
                    print(f"npm 版本: {npm_version}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"检查安装状态失败: {e}")
            return False
    
    def configure_npm_registry(self, registry: str = "https://registry.npmmirror.com"):
        """配置 npm 镜像源
        
        Args:
            registry: npm 镜像源地址
        """
        try:
            print(f"\n配置 npm 镜像源: {registry}")
            result = subprocess.run(
                ["npm", "config", "set", "registry", registry],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ npm 镜像源配置成功")
            else:
                print("✗ npm 镜像源配置失败")
                
        except Exception as e:
            print(f"配置 npm 镜像源失败: {e}")
    
    def download_only(self, version: str, save_dir: str = None) -> bool:
        """仅下载指定版本的 Node.js 安装包
        
        Args:
            version: Node.js 版本号
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
        filename = f"node-v{version}-x64.msi"
        
        print(f"\n{'='*60}")
        print(f"  下载 Node.js v{version}")
        print(f"{'='*60}")
        
        # 下载安装包
        msi_path = self.download_file(urls, filename)
        if not msi_path:
            return False
        
        # 移动到指定目录
        if save_dir:
            save_dir_path = Path(save_dir)
            save_dir_path.mkdir(parents=True, exist_ok=True)
            final_path = save_dir_path / filename
            
            try:
                import shutil
                shutil.move(str(msi_path), str(final_path))
                print(f"\n✓ 安装包已保存到: {final_path}")
            except Exception as e:
                print(f"\n✗ 移动文件失败: {e}")
                print(f"文件仍在: {msi_path}")
        else:
            # 移动到当前目录
            final_path = Path.cwd() / filename
            try:
                import shutil
                shutil.move(str(msi_path), str(final_path))
                print(f"\n✓ 安装包已保存到: {final_path}")
            except Exception as e:
                print(f"\n✗ 移动文件失败: {e}")
                print(f"文件仍在: {msi_path}")
        
        print(f"\n{'='*60}")
        print("  下载完成!")
        print(f"{'='*60}")
        return True
    
    def install(self, version: str, configure_registry: bool = True, 
                keep_installer: bool = False, download_only: bool = False) -> bool:
        """安装指定版本的 Node.js
        
        Args:
            version: Node.js 版本号
            configure_registry: 是否配置国内镜像源
            keep_installer: 是否保留安装包
            download_only: 仅下载不安装
            
        Returns:
            安装成功返回 True，失败返回 False
        """
        # 如果只下载，调用download_only方法
        if download_only:
            return self.download_only(version)
        
        # 检查版本是否存在
        if version not in self.versions_config:
            print(f"错误: 版本 {version} 不存在")
            print("\n请使用 --list 参数查看所有可用版本")
            return False
        
        urls = self.versions_config[version]
        filename = f"node-v{version}-x64.msi"
        
        print(f"\n{'='*60}")
        print(f"  安装 Node.js v{version}")
        print(f"{'='*60}")
        
        # 下载安装包
        msi_path = self.download_file(urls, filename)
        if not msi_path:
            return False
        
        # 安装
        success = self.install_msi(msi_path)
        
        # 清理安装包
        if not keep_installer and msi_path.exists():
            try:
                msi_path.unlink()
                print(f"\n已删除安装包: {msi_path}")
            except Exception as e:
                print(f"\n删除安装包失败: {e}")
        elif keep_installer:
            print(f"\n安装包保存在: {msi_path}")
        
        # 验证安装
        if success:
            print("\n验证安装...")
            if self.check_installation():
                # 配置镜像源
                if configure_registry:
                    self.configure_npm_registry()
                
                print(f"\n{'='*60}")
                print("  Node.js 安装完成!")
                print(f"{'='*60}")
                print("\n提示: 您可能需要重新打开命令行窗口以使用 node 和 npm 命令")
                return True
            else:
                print("\n警告: 安装完成但验证失败，请重新打开命令行窗口后再试")
                return True
        
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Node.js 独立安装脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                      列出所有可用版本
  %(prog)s --install 20.18.1           安装 Node.js 20.18.1
  %(prog)s --download 20.18.1          仅下载 Node.js 20.18.1 安装包
  %(prog)s --install 18.20.5 --keep    安装并保留安装包
  %(prog)s --install 22.12.0 --no-registry  安装但不配置镜像源
        """
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有可用的 Node.js 版本'
    )
    
    parser.add_argument(
        '--install', '-i',
        metavar='VERSION',
        help='安装指定版本的 Node.js'
    )
    
    parser.add_argument(
        '--download', '-d',
        metavar='VERSION',
        help='仅下载指定版本的 Node.js 安装包（不安装）'
    )
    
    parser.add_argument(
        '--keep', '-k',
        action='store_true',
        help='保留下载的安装包'
    )
    
    parser.add_argument(
        '--no-registry',
        action='store_true',
        help='不配置 npm 国内镜像源'
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
        installer = NodejsInstaller(args.version_file)
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
            configure_registry=not args.no_registry,
            keep_installer=args.keep
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
