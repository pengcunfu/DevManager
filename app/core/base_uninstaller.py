#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卸载脚本
用于卸载通过本系统安装的工具（实验性功能）
"""

import sys
import os
import json
import argparse
import subprocess
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.installer import PlatformDetector, CommandRunner
import logging


class ToolUninstaller:
    """工具卸载器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.runner = CommandRunner(self.logger)
        self.os_info = PlatformDetector.get_os_info()
    
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger("uninstaller")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def uninstall_git(self) -> bool:
        """卸载Git"""
        try:
            if self.os_info["system"] == "linux":
                if "ubuntu" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo apt remove -y git")
                elif "centos" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo yum remove -y git")
                elif "arch" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo pacman -R --noconfirm git")
            elif self.os_info["system"] == "darwin":
                self.runner.run_command("brew uninstall git")
            elif self.os_info["system"] == "windows":
                self.runner.run_command("choco uninstall git -y")
            
            self.logger.info("Git卸载完成")
            return True
        except Exception as e:
            self.logger.error(f"Git卸载失败: {e}")
            return False
    
    def uninstall_docker(self) -> bool:
        """卸载Docker"""
        try:
            if self.os_info["system"] == "linux":
                if "ubuntu" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo apt remove -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
                    self.runner.run_command("sudo rm -rf /var/lib/docker")
                elif "centos" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo yum remove -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
                    self.runner.run_command("sudo rm -rf /var/lib/docker")
            elif self.os_info["system"] == "darwin":
                self.runner.run_command("brew uninstall --cask docker")
            elif self.os_info["system"] == "windows":
                self.runner.run_command("choco uninstall docker-desktop -y")
            
            self.logger.info("Docker卸载完成")
            return True
        except Exception as e:
            self.logger.error(f"Docker卸载失败: {e}")
            return False
    
    def uninstall_nodejs(self) -> bool:
        """卸载Node.js"""
        try:
            # 通过NVM安装的Node.js
            nvm_dir = os.path.expanduser("~/.nvm")
            if os.path.exists(nvm_dir):
                self.logger.info("检测到NVM安装的Node.js")
                # 卸载所有Node.js版本
                result = self.runner.run_command("nvm list", capture_output=True, check=False)
                if result.returncode == 0:
                    # 解析版本列表并卸载
                    for line in result.stdout.split('\n'):
                        if 'v' in line and not '->' in line:
                            version = line.strip().replace('*', '').strip()
                            if version.startswith('v'):
                                self.runner.run_command(f"nvm uninstall {version}", check=False)
                
                # 删除NVM
                self.runner.run_command(f"rm -rf {nvm_dir}")
                
                # 清理shell配置
                self._remove_from_shell_config("NVM_DIR")
                self._remove_from_shell_config("nvm.sh")
            
            # 系统级安装的Node.js
            if self.os_info["system"] == "linux":
                if "ubuntu" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo apt remove -y nodejs npm", check=False)
            elif self.os_info["system"] == "darwin":
                self.runner.run_command("brew uninstall node npm", check=False)
            elif self.os_info["system"] == "windows":
                self.runner.run_command("choco uninstall nodejs -y", check=False)
            
            self.logger.info("Node.js卸载完成")
            return True
        except Exception as e:
            self.logger.error(f"Node.js卸载失败: {e}")
            return False
    
    def uninstall_python(self) -> bool:
        """卸载Python (pyenv)"""
        try:
            pyenv_root = os.path.expanduser("~/.pyenv")
            if os.path.exists(pyenv_root):
                self.logger.info("检测到pyenv安装的Python")
                
                # 删除pyenv
                self.runner.run_command(f"rm -rf {pyenv_root}")
                
                # 清理shell配置
                self._remove_from_shell_config("PYENV_ROOT")
                self._remove_from_shell_config("pyenv init")
            
            self.logger.info("Python (pyenv) 卸载完成")
            self.logger.warning("注意: 系统自带的Python未被卸载")
            return True
        except Exception as e:
            self.logger.error(f"Python卸载失败: {e}")
            return False
    
    def uninstall_java(self) -> bool:
        """卸载Java"""
        try:
            if self.os_info["system"] == "linux":
                if "ubuntu" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo apt remove -y openjdk-*")
                elif "centos" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo yum remove -y java-*-openjdk*")
            elif self.os_info["system"] == "darwin":
                self.runner.run_command("brew uninstall openjdk@17", check=False)
                self.runner.run_command("sudo rm -rf /Library/Java/JavaVirtualMachines/openjdk-17.jdk", check=False)
            elif self.os_info["system"] == "windows":
                self.runner.run_command("choco uninstall openjdk17 -y")
            
            # 清理环境变量
            self._remove_from_shell_config("JAVA_HOME")
            
            self.logger.info("Java卸载完成")
            return True
        except Exception as e:
            self.logger.error(f"Java卸载失败: {e}")
            return False
    
    def uninstall_php(self) -> bool:
        """卸载PHP"""
        try:
            if self.os_info["system"] == "linux":
                if "ubuntu" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo apt remove -y php8.2*")
                elif "centos" in self.os_info.get("distro", ""):
                    self.runner.run_command("sudo yum remove -y php*")
            elif self.os_info["system"] == "darwin":
                self.runner.run_command("brew uninstall php@8.2")
            elif self.os_info["system"] == "windows":
                self.runner.run_command("choco uninstall php -y")
                self.runner.run_command("choco uninstall composer -y")
            
            # 删除Composer
            composer_path = os.path.expanduser("~/.composer")
            if os.path.exists(composer_path):
                self.runner.run_command(f"rm -rf {composer_path}")
            
            self.logger.info("PHP卸载完成")
            return True
        except Exception as e:
            self.logger.error(f"PHP卸载失败: {e}")
            return False
    
    def _remove_from_shell_config(self, pattern: str):
        """从shell配置文件中移除指定模式的行"""
        shell_configs = ["~/.bashrc", "~/.zshrc", "~/.profile"]
        
        for config_file in shell_configs:
            config_path = os.path.expanduser(config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        lines = f.readlines()
                    
                    # 过滤掉包含指定模式的行
                    filtered_lines = [line for line in lines if pattern not in line]
                    
                    if len(filtered_lines) < len(lines):
                        with open(config_path, 'w') as f:
                            f.writelines(filtered_lines)
                        self.logger.info(f"已从 {config_file} 中移除 {pattern} 相关配置")
                except Exception as e:
                    self.logger.warning(f"清理 {config_file} 失败: {e}")
    
    def list_installed_tools(self) -> List[str]:
        """列出已安装的工具"""
        installed = []
        
        # 检查各种工具
        tools_check = {
            "git": "git --version",
            "docker": "docker --version",
            "node": "node --version",
            "python": "python --version",
            "java": "java --version",
            "php": "php --version"
        }
        
        for tool, command in tools_check.items():
            try:
                result = self.runner.run_command(command, capture_output=True, check=False)
                if result.returncode == 0:
                    installed.append(tool)
            except:
                pass
        
        return installed
    
    def uninstall_tool(self, tool_name: str) -> bool:
        """卸载指定工具"""
        uninstall_methods = {
            "git": self.uninstall_git,
            "docker": self.uninstall_docker,
            "nodejs": self.uninstall_nodejs,
            "node": self.uninstall_nodejs,
            "python": self.uninstall_python,
            "java": self.uninstall_java,
            "php": self.uninstall_php
        }
        
        method = uninstall_methods.get(tool_name.lower())
        if method:
            return method()
        else:
            self.logger.error(f"不支持卸载工具: {tool_name}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="卸载开发工具")
    parser.add_argument('--list', action='store_true', help='列出已安装的工具')
    parser.add_argument('--uninstall', nargs='+', help='卸载指定的工具')
    parser.add_argument('--force', action='store_true', help='强制卸载（跳过确认）')
    
    args = parser.parse_args()
    
    uninstaller = ToolUninstaller()
    
    if args.list:
        installed = uninstaller.list_installed_tools()
        if installed:
            print("已安装的工具:")
            for tool in installed:
                print(f"  - {tool}")
        else:
            print("未检测到已安装的工具")
    
    elif args.uninstall:
        print("⚠️  警告: 卸载操作可能会删除重要文件和配置")
        print("⚠️  建议在卸载前备份重要数据")
        print()
        
        if not args.force:
            tools_str = ", ".join(args.uninstall)
            confirm = input(f"确认卸载以下工具? {tools_str} (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("取消卸载")
                return
        
        success_count = 0
        for tool in args.uninstall:
            print(f"\n正在卸载 {tool}...")
            if uninstaller.uninstall_tool(tool):
                success_count += 1
                print(f"✓ {tool} 卸载成功")
            else:
                print(f"✗ {tool} 卸载失败")
        
        print(f"\n卸载完成: {success_count}/{len(args.uninstall)} 个工具卸载成功")
        print("注意: 请重新加载shell环境或重启终端以应用更改")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)
