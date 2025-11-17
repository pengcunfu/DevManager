#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用开发工具一键安装系统 - 主入口脚本
作者: AI Assistant
版本: 1.0.0

使用方法:
    python install.py --list                    # 列出所有可用工具
    python install.py --info git               # 查看工具信息
    python install.py --install git            # 安装单个工具
    python install.py --install git docker     # 安装多个工具
    python install.py --install-all            # 安装所有工具
    python install.py --force git              # 强制重新安装工具
    python install.py --interactive            # 交互式安装
"""

import sys
import argparse
import json
from typing import List, Dict
from core.installer import InstallerManager, PlatformDetector


class InteractiveInstaller:
    """交互式安装器"""
    
    def __init__(self, manager: InstallerManager):
        self.manager = manager
    
    def run(self):
        """运行交互式安装"""
        print("=== 通用开发工具一键安装系统 ===")
        print()
        
        # 显示平台信息
        os_info = PlatformDetector.get_os_info()
        print(f"检测到的系统: {os_info['system']} {os_info['version']}")
        if os_info['system'] == 'linux':
            print(f"发行版: {os_info['distro']}")
        print()
        
        # 显示可用工具
        tools = self.manager.list_available_tools()
        if not tools:
            print("没有找到可用的工具配置")
            return
        
        print("可用工具:")
        for i, tool in enumerate(tools, 1):
            info = self.manager.get_tool_info(tool)
            description = info.get('description', '无描述') if info else '无描述'
            category = info.get('category', '其他') if info else '其他'
            print(f"  {i:2d}. {tool:<15} - {description} [{category}]")
        print()
        
        # 选择工具
        while True:
            try:
                choice = input("请选择要安装的工具 (输入数字，多个用空格分隔，'all'表示全部，'q'退出): ").strip()
                
                if choice.lower() == 'q':
                    print("退出安装程序")
                    return
                
                if choice.lower() == 'all':
                    selected_tools = tools
                    break
                
                # 解析数字选择
                numbers = choice.split()
                selected_tools = []
                
                for num_str in numbers:
                    try:
                        num = int(num_str)
                        if 1 <= num <= len(tools):
                            selected_tools.append(tools[num - 1])
                        else:
                            print(f"无效的选择: {num}")
                            break
                    except ValueError:
                        print(f"无效的输入: {num_str}")
                        break
                else:
                    if selected_tools:
                        break
                
                print("请输入有效的选择")
                
            except KeyboardInterrupt:
                print("\n用户取消安装")
                return
        
        # 确认安装
        print(f"\n将要安装的工具: {', '.join(selected_tools)}")
        confirm = input("确认安装? (y/N): ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("取消安装")
            return
        
        # 执行安装
        print("\n开始安装...")
        results = self.manager.install_multiple_tools(selected_tools)
        
        # 显示结果
        print("\n=== 安装结果 ===")
        success_count = 0
        for tool, success in results.items():
            status = "✓ 成功" if success else "✗ 失败"
            print(f"{tool:<15} - {status}")
            if success:
                success_count += 1
        
        print(f"\n安装完成: {success_count}/{len(selected_tools)} 个工具安装成功")
        
        if success_count < len(selected_tools):
            print("请查看日志文件 install.log 了解失败原因")


def print_tool_info(manager: InstallerManager, tool_name: str):
    """打印工具详细信息"""
    info = manager.get_tool_info(tool_name)
    if not info:
        print(f"未找到工具: {tool_name}")
        return
    
    print(f"=== {info['name']} ===")
    print(f"描述: {info.get('description', '无')}")
    print(f"版本: {info.get('version', '未指定')}")
    print(f"分类: {info.get('category', '其他')}")
    
    supported_platforms = info.get('supported_platforms', [])
    if supported_platforms:
        print(f"支持平台: {', '.join(supported_platforms)}")
    
    dependencies = info.get('dependencies', [])
    if dependencies:
        print(f"依赖: {', '.join(dependencies)}")
    
    config_options = info.get('config_options', {})
    if config_options:
        print("配置选项:")
        for key, value in config_options.items():
            print(f"  {key}: {value}")
    
    notes = info.get('notes')
    if notes:
        print(f"备注: {notes}")
    
    manual_install = info.get('manual_install')
    if manual_install:
        print("手动安装信息:")
        for platform, details in manual_install.items():
            print(f"  {platform}:")
            print(f"    说明: {details.get('description', '无')}")
            if 'download_url' in details:
                print(f"    下载地址: {details['download_url']}")
            instructions = details.get('instructions', [])
            if instructions:
                print("    安装步骤:")
                for instruction in instructions:
                    print(f"      {instruction}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="通用开发工具一键安装系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                    列出所有可用工具
  %(prog)s --info git               查看Git工具信息
  %(prog)s --install git            安装Git
  %(prog)s --install git docker     安装Git和Docker
  %(prog)s --install-all            安装所有工具
  %(prog)s --force git              强制重新安装Git
  %(prog)s --interactive            交互式安装
        """
    )
    
    parser.add_argument('--list', action='store_true', help='列出所有可用工具')
    parser.add_argument('--info', metavar='TOOL', help='查看指定工具的详细信息')
    parser.add_argument('--install', nargs='+', metavar='TOOL', help='安装指定的工具')
    parser.add_argument('--install-all', action='store_true', help='安装所有工具')
    parser.add_argument('--force', nargs='+', metavar='TOOL', help='强制重新安装指定的工具')
    parser.add_argument('--interactive', action='store_true', help='交互式安装')
    parser.add_argument('--config-dir', default='configs', help='配置文件目录 (默认: configs)')
    parser.add_argument('--tools-dir', default='tools', help='工具模块目录 (默认: tools)')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细输出')
    
    args = parser.parse_args()
    
    # 检查平台支持
    if not PlatformDetector.is_supported_platform():
        print("错误: 不支持的操作系统平台", file=sys.stderr)
        sys.exit(1)
    
    # 创建安装管理器
    try:
        manager = InstallerManager(args.config_dir, args.tools_dir)
    except Exception as e:
        print(f"错误: 初始化安装管理器失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 设置日志级别
    if args.verbose:
        import logging
        logging.getLogger("installer").setLevel(logging.DEBUG)
    
    # 处理命令行参数
    if args.list:
        # 列出所有工具
        tools = manager.list_available_tools()
        if not tools:
            print("没有找到可用的工具配置")
            return
        
        print("可用工具:")
        categories = {}
        
        # 按分类组织工具
        for tool in tools:
            info = manager.get_tool_info(tool)
            category = info.get('category', '其他') if info else '其他'
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        # 显示工具
        for category, category_tools in categories.items():
            print(f"\n{category}:")
            for tool in category_tools:
                info = manager.get_tool_info(tool)
                description = info.get('description', '无描述') if info else '无描述'
                print(f"  {tool:<15} - {description}")
    
    elif args.info:
        # 显示工具信息
        print_tool_info(manager, args.info)
    
    elif args.install:
        # 安装指定工具
        print(f"安装工具: {', '.join(args.install)}")
        results = manager.install_multiple_tools(args.install)
        
        success_count = sum(results.values())
        print(f"\n安装完成: {success_count}/{len(args.install)} 个工具安装成功")
        
        if success_count < len(args.install):
            print("失败的工具:")
            for tool, success in results.items():
                if not success:
                    print(f"  - {tool}")
            sys.exit(1)
    
    elif args.install_all:
        # 安装所有工具
        tools = manager.list_available_tools()
        if not tools:
            print("没有找到可用的工具")
            return
        
        print(f"安装所有工具: {', '.join(tools)}")
        results = manager.install_multiple_tools(tools)
        
        success_count = sum(results.values())
        print(f"\n安装完成: {success_count}/{len(tools)} 个工具安装成功")
        
        if success_count < len(tools):
            print("失败的工具:")
            for tool, success in results.items():
                if not success:
                    print(f"  - {tool}")
    
    elif args.force:
        # 强制重新安装
        print(f"强制重新安装工具: {', '.join(args.force)}")
        results = manager.install_multiple_tools(args.force, force=True)
        
        success_count = sum(results.values())
        print(f"\n安装完成: {success_count}/{len(args.force)} 个工具安装成功")
        
        if success_count < len(args.force):
            print("失败的工具:")
            for tool, success in results.items():
                if not success:
                    print(f"  - {tool}")
            sys.exit(1)
    
    elif args.interactive:
        # 交互式安装
        interactive = InteractiveInstaller(manager)
        interactive.run()
    
    else:
        # 没有指定操作，显示帮助
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}", file=sys.stderr)
        sys.exit(1)
