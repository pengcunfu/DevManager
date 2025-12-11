#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composer 配置脚本
自动配置 Composer 国内镜像源
"""

import os
import sys
import argparse
import subprocess
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class ComposerConfigurator:
    """Composer 配置器"""

    # 国内镜像源配置
    MIRRORS = {
        'aliyun': {
            'name': '阿里云',
            'url': 'https://mirrors.aliyun.com/composer/',
            'home': 'https://developer.aliyun.com/composer'
        },
        'tencent': {
            'name': '腾讯云',
            'url': 'https://mirrors.cloud.tencent.com/composer/',
            'home': 'https://mirrors.cloud.tencent.com'
        },
        'huawei': {
            'name': '华为云',
            'url': 'https://repo.huaweicloud.com/repository/php/',
            'home': 'https://mirrors.huaweicloud.com'
        },
        'cnpkg': {
            'name': '中国全量镜像',
            'url': 'https://packagist.cn/',
            'home': 'https://packagist.cn'
        },
        'sjtug': {
            'name': '上海交通大学',
            'url': 'https://mirrors.sjtug.sjtu.edu.cn/composer/',
            'home': 'https://mirrors.sjtug.sjtu.edu.cn'
        },
        'official': {
            'name': '官方源',
            'url': 'https://repo.packagist.org/',
            'home': 'https://packagist.org'
        }
    }

    def __init__(self):
        """初始化配置器"""
        self.composer_home = self._get_composer_home()

    def _get_composer_home(self) -> Path:
        """获取 Composer 主目录"""
        # 优先使用环境变量
        composer_home = os.environ.get('COMPOSER_HOME')
        if composer_home:
            return Path(composer_home)

        # Windows 系统
        if sys.platform == 'win32':
            app_data = os.environ.get('APPDATA', '')
            if app_data:
                return Path(app_data) / 'Composer'
            return Path.home() / 'AppData' / 'Roaming' / 'Composer'

        # Unix/Linux 系统
        return Path.home() / '.composer'

    def check_composer_installed(self) -> bool:
        """检查 Composer 是否已安装"""
        try:
            result = subprocess.run(
                ['composer', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_composer_version(self) -> Optional[str]:
        """获取 Composer 版本"""
        try:
            result = subprocess.run(
                ['composer', '--version', '--no-ansi'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 提取版本号
                version_line = result.stdout.strip()
                if 'version' in version_line.lower():
                    return version_line.split()[2]
            return None
        except Exception:
            return None

    def list_mirrors(self):
        """列出所有可用的镜像源"""
        print(f"\n{'='*60}")
        print("  可用的 Composer 镜像源")
        print(f"{'='*60}\n")

        for key, mirror in self.MIRRORS.items():
            print(f"  [{key:8s}] {mirror['name']}")
            print(f"            {mirror['url']}")
            print()

        print(f"{'='*60}")

    def get_current_config(self) -> Optional[Dict]:
        """获取当前配置"""
        config_file = self.composer_home / 'config.json'

        if not config_file.exists():
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def get_current_mirror(self) -> Optional[str]:
        """获取当前配置的镜像源"""
        config = self.get_current_config()
        if not config:
            return None

        # 查找 repos.packagist.org 配置
        repos = config.get('repositories', {})
        if isinstance(repos, dict) and 'packagist.org' in repos:
            packagist_config = repos['packagist.org']
            if isinstance(packagist_config, dict):
                packagist_url = packagist_config.get('url', '')
                if packagist_url:
                    return packagist_url

        return None

    def show_current_config(self):
        """显示当前配置信息"""
        print(f"\n{'='*60}")
        print("  当前 Composer 配置信息")
        print(f"{'='*60}")

        if not self.check_composer_installed():
            print("\n✗ Composer 未安装或不在 PATH 中")
            print(f"\n{'='*60}")
            return

        # 获取 Composer 版本
        version = self.get_composer_version()
        if version:
            print(f"\nComposer 版本: {version}")

        # 获取 Composer 主目录
        print(f"Composer 主目录: {self.composer_home}")

        # 获取当前镜像源
        current_mirror = self.get_current_mirror()
        if current_mirror:
            print(f"\n当前镜像源: {current_mirror}")

            # 查找匹配的镜像源
            for key, mirror in self.MIRRORS.items():
                if mirror['url'].rstrip('/') in current_mirror or current_mirror.rstrip('/') in mirror['url'].rstrip('/'):
                    print(f"镜像名称: {mirror['name']}")
                    break
            else:
                print(f"镜像名称: 未知源")
        else:
            print(f"\n当前镜像源: 官方源（默认）")

        print(f"\n{'='*60}")

    def test_mirror_speed(self, mirror_key: str, mirror: Dict[str, str], timeout: int = 5) -> Optional[float]:
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

            # 尝试访问镜像源的 packages.json
            test_url = mirror['url'] + 'packages.json'

            req = urllib.request.Request(
                test_url,
                headers={
                    'User-Agent': 'Composer/2.0.0',
                    'Accept': 'application/json'
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

    def test_all_mirrors(self, timeout: int = 5) -> List[Tuple[str, str, Optional[float]]]:
        """测试所有镜像源的速度并排序

        Args:
            timeout: 超时时间（秒）

        Returns:
            排序后的镜像源列表 [(key, name, speed), ...]
        """
        print(f"\n{'='*60}")
        print("  测试 Composer 镜像源速度")
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

        if not self.check_composer_installed():
            print("错误: Composer 未安装或不在 PATH 中")
            print("请先安装 Composer")
            return False

        mirror = self.MIRRORS[mirror_key]

        print(f"\n{'='*60}")
        print(f"  配置 Composer 镜像源 - {mirror['name']}")
        print(f"{'='*60}")

        # 确保 Composer 主目录存在
        self.composer_home.mkdir(parents=True, exist_ok=True)

        try:
            print(f"\n正在配置镜像源...")

            if mirror_key == 'official':
                # 恢复官方源，删除配置
                result = subprocess.run(
                    ['composer', 'config', '--unset', 'repos.packagist.org'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # 配置镜像源
                result = subprocess.run(
                    ['composer', 'config', '--global', 'repos.packagist.org', 'composer', mirror['url']],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            if result.returncode != 0:
                print(f"✗ 配置镜像源失败: {result.stderr}")
                return False

            print(f"✓ 镜像源配置成功")

        except subprocess.TimeoutExpired:
            print("✗ 配置超时")
            return False
        except Exception as e:
            print(f"✗ 配置失败: {e}")
            return False

        # 验证配置
        print(f"\n验证配置...")
        current_mirror = self.get_current_mirror()
        if mirror_key == 'official' and current_mirror is None:
            print(f"✓ 配置验证成功，已恢复官方源")
        elif current_mirror and mirror['url'].rstrip('/') in current_mirror:
            print(f"✓ 配置验证成功")
        else:
            print(f"⚠ 配置可能未生效，请手动检查")

        print(f"\n{'='*60}")
        print("  Composer 镜像源配置完成!")
        print(f"{'='*60}")
        print(f"\n镜像源: {mirror['name']}")
        print(f"镜像地址: {mirror['url']}")

        return True

    def interactive_configure(self):
        """交互式配置镜像源"""
        print(f"\n{'='*60}")
        print("  Composer 镜像源交互式配置")
        print(f"{'='*60}\n")

        if not self.check_composer_installed():
            print("✗ Composer 未安装或不在 PATH 中")
            print("请先安装 Composer")
            return False

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
        import subprocess

        config_file = self.composer_home / 'config.json'

        if not config_file.exists():
            print(f"配置文件不存在: {config_file}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(config_file)
            elif sys.platform == "darwin":
                subprocess.run(["open", config_file])
            else:
                subprocess.run(["xdg-open", config_file])
            print(f"已打开配置文件: {config_file}")
        except Exception as e:
            print(f"无法打开配置文件: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Composer 配置脚本 - 自动配置国内镜像源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                列出所有可用镜像源
  %(prog)s --show                显示当前配置信息
  %(prog)s --test                测试所有镜像源速度并排序
  %(prog)s --test --timeout 10   测试所有镜像源（超时10秒）
  %(prog)s --mirror aliyun      配置阿里云镜像源
  %(prog)s --mirror tencent      配置腾讯云镜像源
  %(prog)s --interactive         交互式选择镜像源
  %(prog)s --open-config         打开配置文件

可用镜像源:
  aliyun   - 阿里云
  tencent  - 腾讯云
  huawei   - 华为云
  cnpkg    - 中国全量镜像
  sjtug    - 上海交通大学
  official - 官方源
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
        help='配置指定的镜像源 (aliyun/tencent/huawei/cnpkg/sjtug/official)'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='交互式选择镜像源'
    )

    parser.add_argument(
        '--open-config',
        action='store_true',
        help='打开 Composer 配置文件'
    )

    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='测试所有镜像源的速度并排序'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=5,
        metavar='SECONDS',
        help='测试超时时间（秒），默认 5 秒'
    )

    args = parser.parse_args()

    # 创建配置器
    configurator = ComposerConfigurator()

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
        # 默认显示帮助信息
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