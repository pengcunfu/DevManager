#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立安装脚本的基类
提供通用的下载、版本管理等功能
"""

import sys
import json
import tempfile
import urllib.request
import urllib.error
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class BaseInstaller(ABC):
    """
    独立安装脚本的基类
    提供通用的下载、版本管理等功能
    """
    
    def __init__(self, software_name: str, version_file: str = None):
        """
        初始化基础安装器
        
        Args:
            software_name: 软件名称（用于显示和文件名）
            version_file: 版本配置文件路径
        """
        self.software_name = software_name
        
        if version_file is None:
            # 默认使用脚本同目录下的配置文件
            script_dir = Path(sys.argv[0]).parent.resolve()
            version_file = script_dir / "software_versions" / f"{software_name.lower()}-windows.json"
        
        self.version_file = Path(version_file)
        self.versions_config = self._load_versions()
        self.temp_dir = Path(tempfile.gettempdir())
    
    def _load_versions(self) -> Dict[str, List[str]]:
        """
        加载版本配置文件
        
        Returns:
            版本配置字典 {version: [url1, url2, ...]}
        """
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
        """
        列出所有可用版本
        """
        print(f"可用的 {self.software_name} 版本:")
        print("-" * 50)
        for version in sorted(self.versions_config.keys(), reverse=True):
            print(f"  • {version}")
        print("-" * 50)
    
    def download_file(self, urls: List[str], filename: str) -> Optional[Path]:
        """
        从多个 URL 尝试下载文件
        
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
    
    def move_file_to_destination(self, source: Path, filename: str, save_dir: str = None) -> bool:
        """
        将文件移动到目标目录
        
        Args:
            source: 源文件路径
            filename: 文件名
            save_dir: 目标目录，None 表示当前目录
            
        Returns:
            移动成功返回 True，失败返回 False
        """
        if save_dir:
            save_dir_path = Path(save_dir)
            save_dir_path.mkdir(parents=True, exist_ok=True)
            final_path = save_dir_path / filename
        else:
            final_path = Path.cwd() / filename
        
        try:
            shutil.move(str(source), str(final_path))
            print(f"\n✓ 安装包已保存到: {final_path}")
            return True
        except Exception as e:
            print(f"\n✗ 移动文件失败: {e}")
            print(f"文件仍在: {source}")
            return False
    
    def check_version_exists(self, version: str) -> bool:
        """
        检查版本是否存在
        
        Args:
            version: 版本号
            
        Returns:
            存在返回 True，不存在返回 False
        """
        if version not in self.versions_config:
            print(f"错误: 版本 {version} 不存在")
            print("\n请使用 --list 参数查看所有可用版本")
            return False
        return True
    
    def print_download_header(self, version: str):
        """
        打印下载头部信息
        
        Args:
            version: 版本号
        """
        print(f"\n{'='*60}")
        print(f"  下载 {self.software_name} v{version}")
        print(f"{'='*60}")
    
    def print_install_header(self, version: str):
        """
        打印安装头部信息
        
        Args:
            version: 版本号
        """
        print(f"\n{'='*60}")
        print(f"  安装 {self.software_name} v{version}")
        print(f"{'='*60}")
    
    def print_completion_message(self):
        """
        打印完成消息
        """
        print(f"\n{'='*60}")
        print("  下载完成!")
        print(f"{'='*60}")
    
    def print_install_completion_message(self):
        """
        打印安装完成消息
        """
        print(f"\n{'='*60}")
        print(f"  {self.software_name} 安装完成!")
        print(f"{'='*60}")
    
    @abstractmethod
    def download_only(self, version: str, save_dir: str = None) -> bool:
        """
        仅下载指定版本（子类必须实现）
        
        Args:
            version: 版本号
            save_dir: 保存目录
            
        Returns:
            下载成功返回 True，失败返回 False
        """
        pass
    
    @abstractmethod
    def install(self, version: str, **kwargs) -> bool:
        """
        安装指定版本（子类必须实现）
        
        Args:
            version: 版本号
            **kwargs: 其他安装选项
            
        Returns:
            安装成功返回 True，失败返回 False
        """
        pass
