#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maven 配置脚本
自动配置 Maven 国内镜像源和仓库配置
"""

import os
import sys
import json
import argparse
import shutil
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class MavenConfigurator:
    """Maven 配置器"""

    # 国内镜像源配置
    MIRRORS = {
        'aliyun': {
            'name': '阿里云公共仓库',
            'url': 'https://maven.aliyun.com/repository/public',
            'home': 'https://developer.aliyun.com/mvn/'
        },
        'huawei': {
            'name': '华为云镜像',
            'url': 'https://repo.huaweicloud.com/repository/maven/',
            'home': 'https://mirrors.huaweicloud.com/'
        },
        'tencent': {
            'name': '腾讯云镜像',
            'url': 'https://mirrors.cloud.tencent.com/nexus/repository/maven-public/',
            'home': 'https://mirrors.cloud.tencent.com/'
        },
        'netease': {
            'name': '网易镜像',
            'url': 'https://mirrors.163.com/maven/repository/maven-public/',
            'home': 'https://mirrors.163.com/'
        },
        'ustc': {
            'name': '中科大镜像',
            'url': 'https://mirrors.ustc.edu.cn/maven/',
            'home': 'https://mirrors.ustc.edu.cn/'
        },
        'official': {
            'name': 'Maven中央仓库',
            'url': 'https://repo1.maven.org/maven2/',
            'home': 'https://maven.apache.org/'
        }
    }

    def __init__(self):
        """初始化配置器"""
        # 获取用户主目录
        self.user_home = Path.home()
        self.m2_dir = self.user_home / ".m2"
        self.target_settings = self.m2_dir / "settings.xml"

        # 获取资源文件路径
        script_dir = Path(__file__).parent.parent.parent.parent
        self.source_settings = script_dir / "resources" / "settings.xml"
    
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
            config = self.get_current_config()
            if config and 'mirrors' in config and config['mirrors']:
                mirror = config['mirrors'][0]
                print(f"✓ 镜像源配置验证成功: {mirror.get('name', 'Unknown')}")
                return True
            else:
                print("⚠ 配置文件存在，但未找到镜像源配置")
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
    
    def check_maven_installed(self) -> bool:
        """检查 Maven 是否已安装"""
        try:
            result = subprocess.run(
                ['mvn', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_maven_version(self) -> Optional[str]:
        """获取 Maven 版本"""
        try:
            result = subprocess.run(
                ['mvn', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 提取版本号
                version_line = result.stdout.split('\n')[1] if len(result.stdout.split('\n')) > 1 else ""
                if "Apache Maven" in version_line:
                    return version_line.split()[2]
            return None
        except Exception:
            return None

    def list_mirrors(self):
        """列出所有可用的镜像源"""
        print(f"\n{'='*60}")
        print("  可用的 Maven 镜像源")
        print(f"{'='*60}\n")

        for key, mirror in self.MIRRORS.items():
            print(f"  [{key:8s}] {mirror['name']}")
            print(f"            {mirror['url']}")
            print()

        print(f"{'='*60}")

    def get_current_config(self) -> Optional[Dict]:
        """获取当前配置信息"""
        if not self.target_settings.exists():
            return None

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(self.target_settings)
            root = tree.getroot()

            config = {}

            # 获取本地仓库路径
            local_repo = root.find('localRepository')
            if local_repo is not None and local_repo.text:
                config['local_repository'] = local_repo.text

            # 获取镜像配置
            mirrors = root.find('mirrors')
            if mirrors is not None:
                mirror_list = []
                for mirror in mirrors.findall('mirror'):
                    mirror_info = {
                        'id': mirror.find('id').text if mirror.find('id') is not None else '',
                        'name': mirror.find('name').text if mirror.find('name') is not None else '',
                        'url': mirror.find('url').text if mirror.find('url') is not None else '',
                        'mirrorOf': mirror.find('mirrorOf').text if mirror.find('mirrorOf') is not None else ''
                    }
                    mirror_list.append(mirror_info)
                config['mirrors'] = mirror_list

            return config
        except Exception:
            return None

    def get_current_mirror(self) -> Optional[str]:
        """获取当前配置的镜像源"""
        config = self.get_current_config()
        if not config or 'mirrors' not in config:
            return None

        mirrors = config['mirrors']
        if mirrors:
            # 返回第一个镜像源的ID或名称
            return mirrors[0].get('name', mirrors[0].get('id', ''))

        return None

    def show_current_config(self):
        """显示当前配置信息"""
        print(f"\n{'='*60}")
        print("  当前 Maven 配置信息")
        print(f"{'='*60}")

        # 检查Maven是否安装
        if not self.check_maven_installed():
            print("\n✗ Maven 未安装或不在 PATH 中")
            print(f"\n{'='*60}")
            return

        # 获取Maven版本
        version = self.get_maven_version()
        if version:
            print(f"\nMaven 版本: {version}")

        print(f"\n用户主目录: {self.user_home}")
        print(f".m2 目录: {self.m2_dir}")
        print(f"配置文件: {self.target_settings}")

        if self.target_settings.exists():
            print(f"\n✓ 配置文件已存在")
            print(f"文件大小: {self.target_settings.stat().st_size} 字节")

            # 获取详细配置信息
            config = self.get_current_config()
            if config:
                if 'local_repository' in config:
                    print(f"本地仓库: {config['local_repository']}")
                else:
                    print("本地仓库: 使用默认路径")

                if 'mirrors' in config and config['mirrors']:
                    print("\n已配置的镜像源:")
                    for mirror in config['mirrors']:
                        print(f"  • {mirror.get('name', 'Unknown')} ({mirror.get('url', 'No URL')})")
                else:
                    print("\n未配置镜像源")
            else:
                print("无法解析配置文件内容")
        else:
            print(f"\n✗ 配置文件不存在")

        print(f"\n{'='*60}")

    def test_mirror_speed(self, mirror_key: str, mirror: Dict[str, str], timeout: int = 10) -> Optional[float]:
        """测试单个镜像源的响应速度

        Args:
            mirror_key: 镜像源键名
            mirror: 镜像源配置
            timeout: 超时时间（秒）

        Returns:
            响应时间（秒），失败返回 None
        """
        try:
            start_time = time.time()

            # 尝试访问镜像源的根路径
            test_url = mirror['url']
            if not test_url.endswith('/'):
                test_url += '/'

            req = urllib.request.Request(
                test_url,
                headers={
                    'User-Agent': 'Apache-Maven/3.8.0',
                    'Accept': 'text/html,application/xml'
                }
            )

            with urllib.request.urlopen(req, timeout=timeout) as response:
                response.read(1024)  # 读取少量数据

            elapsed_time = time.time() - start_time
            return elapsed_time

        except urllib.error.URLError as e:
            return None
        except Exception as e:
            return None

    def test_all_mirrors(self, timeout: int = 10) -> List[Tuple[str, str, Optional[float]]]:
        """测试所有镜像源的速度并排序

        Args:
            timeout: 超时时间（秒）

        Returns:
            排序后的镜像源列表 [(key, name, speed), ...]
        """
        print(f"\n{'='*60}")
        print("  测试 Maven 镜像源速度")
        print(f"{'='*60}\n")
        print("正在测试各镜像源响应速度，请稍候...\n")

        results = []

        for key, mirror in self.MIRRORS.items():
            print(f"测试 {mirror['name']:20s} ... ", end='', flush=True)

            speed = self.test_mirror_speed(key, mirror, timeout)

            if speed is not None:
                print(f"✓ {speed*1000:.0f} ms")
                results.append((key, mirror['name'], speed))
            else:
                print(f"✗ 超时或失败")
                results.append((key, mirror['name'], None))

        # 排序：有效的按速度排序，失败的放在最后
        results.sort(key=lambda x: (x[2] is None, x[2] if x[2] is not None else float('inf')))

        # 显示排序结果
        print(f"\n{'='*60}")
        print("  测试结果（按速度排序）")
        print(f"{'='*60}\n")

        for i, (key, name, speed) in enumerate(results, 1):
            if speed is not None:
                print(f"  {i}. {name:20s} - {speed*1000:6.0f} ms  [{key}]")
            else:
                print(f"  {i}. {name:20s} - 超时/失败  [{key}]")

        print(f"\n{'='*60}")

        # 推荐最快的镜像源
        if results and results[0][2] is not None:
            fastest_key, fastest_name, fastest_speed = results[0]
            print(f"\n推荐使用: {fastest_name} ({fastest_speed*1000:.0f} ms)")
            print(f"配置命令: python {sys.argv[0]} --mirror {fastest_key}")

        return results

    def configure_mirror(self, mirror_key: str) -> bool:
        """配置指定的镜像源

        Args:
            mirror_key: 镜像源键名

        Returns:
            配置成功返回 True，失败返回 False
        """
        if mirror_key not in self.MIRRORS:
            print(f"错误: 未知的镜像源 '{mirror_key}'")
            print("\n请使用 --list 参数查看所有可用镜像源")
            return False

        mirror = self.MIRRORS[mirror_key]

        print(f"\n{'='*60}")
        print(f"  配置 Maven 镜像源 - {mirror['name']}")
        print(f"{'='*60}")

        # 确保源配置文件存在
        if not self.source_settings.exists():
            print(f"错误: 源配置文件不存在: {self.source_settings}")
            return False

        # 创建 .m2 目录
        if not self.create_m2_directory():
            return False

        # 备份现有配置
        if not self.backup_existing_settings():
            response = input("\n备份失败，是否继续？(y/n): ")
            if response.lower() != 'y':
                print("操作已取消")
                return False

        try:
            # 复制基础配置文件
            shutil.copy2(self.source_settings, self.target_settings)

            # 修改配置文件，更新镜像源
            self._update_mirror_in_settings(mirror)

            # 验证配置
            if not self.verify_configuration():
                print("⚠ 配置可能未生效，请手动检查")
                return False

            print(f"✓ 镜像源配置成功")

        except Exception as e:
            print(f"✗ 配置失败: {e}")
            return False

        print(f"\n{'='*60}")
        print("  Maven 镜像源配置完成!")
        print(f"{'='*60}")
        print(f"\n镜像源: {mirror['name']}")
        print(f"镜像地址: {mirror['url']}")
        print(f"配置文件: {self.target_settings}")

        return True

    def _update_mirror_in_settings(self, mirror: Dict[str, str]):
        """更新配置文件中的镜像源"""
        try:
            with open(self.target_settings, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换镜像配置
            import re
            mirror_pattern = r'<mirror>.*?</mirror>'
            new_mirror = f'''    <mirror>
      <id>{mirror["url"].split("//")[1].split("/")[0]}</id>
      <mirrorOf>*</mirrorOf>
      <name>{mirror["name"]}</name>
      <url>{mirror["url"]}</url>
    </mirror>'''

            # 查找并替换现有的mirror配置
            match = re.search(mirror_pattern, content, re.DOTALL)
            if match:
                content = content.replace(match.group(0), new_mirror)
            else:
                # 如果没有找到mirror配置，在mirrors标签内添加
                mirrors_pattern = r'<mirrors>.*?</mirrors>'
                mirrors_match = re.search(mirrors_pattern, content, re.DOTALL)
                if mirrors_match:
                    old_mirrors = mirrors_match.group(0)
                    new_mirrors = old_mirrors.replace('</mirrors>', f'  {new_mirror}\n  </mirrors>')
                    content = content.replace(old_mirrors, new_mirrors)

            # 写回文件
            with open(self.target_settings, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            raise Exception(f"更新配置文件失败: {e}")

    def interactive_configure(self):
        """交互式配置镜像源"""
        print(f"\n{'='*60}")
        print("  Maven 镜像源交互式配置")
        print(f"{'='*60}\n")

        # 显示当前配置
        current_mirror = self.get_current_mirror()
        if current_mirror:
            print(f"当前镜像源: {current_mirror}\n")
        else:
            print(f"当前使用默认源\n")

        # 显示可用镜像源
        print("可用的镜像源:\n")
        mirror_list = []
        for i, (key, mirror) in enumerate(self.MIRRORS.items(), 1):
            print(f"  {i}. {mirror['name']:20s} - {mirror['url']}")
            mirror_list.append(key)

        # 获取用户选择
        while True:
            try:
                choice = input(f"\n请选择镜像源 (1-{len(mirror_list)}) 或输入 q 退出: ").strip()

                if choice.lower() == 'q':
                    print("操作已取消")
                    return False

                index = int(choice) - 1
                if 0 <= index < len(mirror_list):
                    mirror_key = mirror_list[index]
                    return self.configure_mirror(mirror_key)
                else:
                    print(f"请输入 1-{len(mirror_list)} 之间的数字")
            except ValueError:
                print("输入无效，请输入数字")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return False

    def open_config_file(self):
        """打开配置文件"""
        try:
            import subprocess
            if sys.platform == "win32":
                os.startfile(self.target_settings)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.target_settings])
            else:
                subprocess.run(["xdg-open", self.target_settings])
            print(f"已打开配置文件: {self.target_settings}")
        except Exception as e:
            print(f"无法打开配置文件: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Maven 配置脚本 - 自动配置国内镜像源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                列出所有可用镜像源
  %(prog)s --show                显示当前配置信息
  %(prog)s --test                测试所有镜像源速度并排序
  %(prog)s --test --timeout 10   测试所有镜像源（超时10秒）
  %(prog)s --mirror aliyun       配置阿里云镜像源
  %(prog)s --mirror tencent       配置腾讯云镜像源
  %(prog)s --interactive         交互式选择镜像源
  %(prog)s --open-config         打开配置文件

可用镜像源:
  aliyun    - 阿里云公共仓库
  huawei    - 华为云镜像
  tencent   - 腾讯云镜像
  netease   - 网易镜像
  ustc      - 中科大镜像
  official  - Maven中央仓库
        """
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有可用的镜像源'
    )

    parser.add_argument(
        '--show', '-s',
        action='store_true',
        help='显示当前配置信息'
    )

    parser.add_argument(
        '--mirror', '-m',
        metavar='MIRROR',
        help='配置指定的镜像源 (aliyun/huawei/tencent/netease/ustc/official)'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='交互式选择镜像源'
    )

    parser.add_argument(
        '--open-config',
        action='store_true',
        help='打开 Maven 配置文件'
    )

    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='测试所有镜像源的速度并排序'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        metavar='SECONDS',
        help='测试超时时间（秒），默认 10 秒'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不备份现有的 settings.xml 文件'
    )

    args = parser.parse_args()

    # 创建配置器
    configurator = MavenConfigurator()

    # 处理命令行参数
    if args.list:
        configurator.list_mirrors()
    elif args.show:
        configurator.show_current_config()
    elif args.test:
        configurator.test_all_mirrors(timeout=args.timeout)
    elif args.mirror:
        success = configurator.configure_mirror(args.mirror)
        sys.exit(0 if success else 1)
    elif args.interactive:
        success = configurator.interactive_configure()
        sys.exit(0 if success else 1)
    elif args.open_config:
        configurator.open_config_file()
    else:
        # 默认配置阿里云镜像（保持向后兼容）
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
