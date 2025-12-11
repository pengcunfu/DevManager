#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maven 配置脚本
自动配置 Maven 阿里云国内镜像
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


class MavenConfigurator:
    """Maven 配置器"""
    
    def __init__(self):
        """初始化配置器"""
        # 获取用户主目录
        self.user_home = Path.home()
        self.m2_dir = self.user_home / ".m2"
        self.target_settings = self.m2_dir / "settings.xml"
        
        # 获取脚本所在目录
        script_dir = Path(__file__).parent
        self.source_settings = script_dir / "data" / "settings.xml"
    
    def check_source_file(self) -> bool:
        """检查源配置文件是否存在"""
        if not self.source_settings.exists():
            print(f"错误: 源配置文件不存在: {self.source_settings}")
            return False
        return True
    
    def backup_existing_settings(self) -> bool:
        """备份现有的 settings.xml 文件"""
        if self.target_settings.exists():
            backup_file = self.target_settings.with_suffix('.xml.backup')
            
            # 如果备份文件已存在，添加时间戳
            if backup_file.exists():
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.target_settings.parent / f"settings.xml.backup.{timestamp}"
            
            try:
                shutil.copy2(self.target_settings, backup_file)
                print(f"✓ 已备份现有配置文件到: {backup_file}")
                return True
            except Exception as e:
                print(f"✗ 备份配置文件失败: {e}")
                return False
        return True
    
    def create_m2_directory(self) -> bool:
        """创建 .m2 目录（如果不存在）"""
        try:
            self.m2_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ .m2 目录已准备: {self.m2_dir}")
            return True
        except Exception as e:
            print(f"✗ 创建 .m2 目录失败: {e}")
            return False
    
    def copy_settings_file(self) -> bool:
        """复制 settings.xml 文件到 .m2 目录"""
        try:
            shutil.copy2(self.source_settings, self.target_settings)
            print(f"✓ 配置文件已复制到: {self.target_settings}")
            return True
        except Exception as e:
            print(f"✗ 复制配置文件失败: {e}")
            return False
    
    def verify_configuration(self) -> bool:
        """验证配置是否成功"""
        if not self.target_settings.exists():
            print("✗ 配置文件不存在")
            return False
        
        try:
            # 读取文件内容，检查是否包含阿里云镜像配置
            with open(self.target_settings, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'aliyunmaven' in content and 'maven.aliyun.com' in content:
                    print("✓ 阿里云镜像配置验证成功")
                    return True
                else:
                    print("⚠ 配置文件存在，但未找到阿里云镜像配置")
                    return False
        except Exception as e:
            print(f"✗ 验证配置失败: {e}")
            return False
    
    def configure(self, backup: bool = True) -> bool:
        """执行配置
        
        Args:
            backup: 是否备份现有配置文件
            
        Returns:
            配置成功返回 True，失败返回 False
        """
        print(f"\n{'='*60}")
        print("  Maven 配置 - 阿里云国内镜像")
        print(f"{'='*60}")
        
        # 检查源文件
        if not self.check_source_file():
            return False
        
        # 创建 .m2 目录
        if not self.create_m2_directory():
            return False
        
        # 备份现有配置
        if backup:
            if not self.backup_existing_settings():
                response = input("\n备份失败，是否继续？(y/n): ")
                if response.lower() != 'y':
                    print("操作已取消")
                    return False
        
        # 复制配置文件
        if not self.copy_settings_file():
            return False
        
        # 验证配置
        if not self.verify_configuration():
            return False
        
        print(f"\n{'='*60}")
        print("  Maven 配置完成!")
        print(f"{'='*60}")
        print(f"\n配置文件位置: {self.target_settings}")
        print("\n配置内容:")
        print("  • 本地仓库: D:\\Data\\mvn-repository")
        print("  • 镜像源: 阿里云公共仓库")
        print("  • 镜像地址: https://maven.aliyun.com/repository/public")
        print("\n提示: 如需修改本地仓库路径，请编辑 settings.xml 文件中的 <localRepository> 标签")
        
        return True
    
    def show_current_config(self):
        """显示当前配置信息"""
        print(f"\n{'='*60}")
        print("  当前 Maven 配置信息")
        print(f"{'='*60}")
        
        print(f"\n用户主目录: {self.user_home}")
        print(f".m2 目录: {self.m2_dir}")
        print(f"配置文件: {self.target_settings}")
        
        if self.target_settings.exists():
            print(f"\n✓ 配置文件已存在")
            print(f"文件大小: {self.target_settings.stat().st_size} 字节")
            
            # 尝试读取并显示关键配置
            try:
                with open(self.target_settings, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 检查镜像配置
                    if 'aliyunmaven' in content:
                        print("✓ 已配置阿里云镜像")
                    else:
                        print("✗ 未配置阿里云镜像")
                    
                    # 检查本地仓库配置
                    if '<localRepository>' in content:
                        import re
                        match = re.search(r'<localRepository>(.*?)</localRepository>', content)
                        if match:
                            print(f"本地仓库: {match.group(1)}")
            except Exception as e:
                print(f"读取配置文件失败: {e}")
        else:
            print(f"\n✗ 配置文件不存在")
        
        print(f"\n{'='*60}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Maven 配置脚本 - 自动配置阿里云国内镜像",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    配置 Maven（自动备份现有配置）
  %(prog)s --no-backup        配置 Maven（不备份现有配置）
  %(prog)s --show             显示当前配置信息
        """
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不备份现有的 settings.xml 文件'
    )
    
    parser.add_argument(
        '--show',
        action='store_true',
        help='显示当前 Maven 配置信息'
    )
    
    args = parser.parse_args()
    
    # 创建配置器
    configurator = MavenConfigurator()
    
    # 处理命令行参数
    if args.show:
        configurator.show_current_config()
    else:
        success = configurator.configure(backup=not args.no_backup)
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
