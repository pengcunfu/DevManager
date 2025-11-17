#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pip 配置脚本
自动配置 Pip 国内镜像源
"""

import os
import sys
import argparse
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class PipConfigurator:
    """Pip 配置器"""
    
    # 国内镜像源配置
    MIRRORS = {
        'tsinghua': {
            'name': '清华大学',
            'url': 'https://pypi.tuna.tsinghua.edu.cn/simple',
            'trusted_host': 'pypi.tuna.tsinghua.edu.cn'
        },
        'aliyun': {
            'name': '阿里云',
            'url': 'https://mirrors.aliyun.com/pypi/simple/',
            'trusted_host': 'mirrors.aliyun.com'
        },
        'tencent': {
            'name': '腾讯云',
            'url': 'https://mirrors.cloud.tencent.com/pypi/simple',
            'trusted_host': 'mirrors.cloud.tencent.com'
        },
        'douban': {
            'name': '豆瓣',
            'url': 'https://pypi.douban.com/simple/',
            'trusted_host': 'pypi.douban.com'
        },
        'ustc': {
            'name': '中国科技大学',
            'url': 'https://pypi.mirrors.ustc.edu.cn/simple/',
            'trusted_host': 'pypi.mirrors.ustc.edu.cn'
        },
        'huawei': {
            'name': '华为云',
            'url': 'https://repo.huaweicloud.com/repository/pypi/simple',
            'trusted_host': 'repo.huaweicloud.com'
        },
        'official': {
            'name': '官方源',
            'url': 'https://pypi.org/simple',
            'trusted_host': 'pypi.org'
        }
    }
    
    def __init__(self):
        """初始化配置器"""
        self.user_home = Path.home()
        
        # Windows 和 Linux/macOS 的配置文件路径不同
        if sys.platform == 'win32':
            self.pip_config_dir = self.user_home / 'pip'
            self.pip_config_file = self.pip_config_dir / 'pip.ini'
        else:
            self.pip_config_dir = self.user_home / '.pip'
            self.pip_config_file = self.pip_config_dir / 'pip.conf'
    
    def list_mirrors(self):
        """列出所有可用的镜像源"""
        print(f"\n{'='*60}")
        print("  可用的 Pip 镜像源")
        print(f"{'='*60}\n")
        
        for key, mirror in self.MIRRORS.items():
            print(f"  [{key:10s}] {mirror['name']}")
            print(f"              {mirror['url']}")
            print()
        
        print(f"{'='*60}")
    
    def get_current_config(self) -> Optional[Dict[str, str]]:
        """获取当前配置"""
        try:
            result = subprocess.run(
                ['pip', 'config', 'get', 'global.index-url'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                index_url = result.stdout.strip()
                
                # 查找匹配的镜像源
                for key, mirror in self.MIRRORS.items():
                    if mirror['url'] in index_url or index_url in mirror['url']:
                        return {
                            'key': key,
                            'name': mirror['name'],
                            'url': index_url
                        }
                
                return {
                    'key': 'custom',
                    'name': '自定义源',
                    'url': index_url
                }
            
            return None
            
        except Exception as e:
            print(f"获取当前配置失败: {e}")
            return None
    
    def show_current_config(self):
        """显示当前配置信息"""
        print(f"\n{'='*60}")
        print("  当前 Pip 配置信息")
        print(f"{'='*60}")
        
        print(f"\n配置文件位置: {self.pip_config_file}")
        
        if self.pip_config_file.exists():
            print(f"✓ 配置文件已存在")
            print(f"文件大小: {self.pip_config_file.stat().st_size} 字节")
        else:
            print(f"✗ 配置文件不存在")
        
        # 获取当前镜像源
        current = self.get_current_config()
        if current:
            print(f"\n当前镜像源: {current['name']}")
            print(f"镜像地址: {current['url']}")
        else:
            print(f"\n✗ 未配置镜像源（使用官方源）")
        
        print(f"\n{'='*60}")
    
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
        print(f"  配置 Pip 镜像源 - {mirror['name']}")
        print(f"{'='*60}")
        
        # 创建配置目录
        try:
            self.pip_config_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ 配置目录已准备: {self.pip_config_dir}")
        except Exception as e:
            print(f"✗ 创建配置目录失败: {e}")
            return False
        
        # 使用 pip config 命令配置
        try:
            # 设置 index-url
            print(f"\n正在配置镜像源...")
            result = subprocess.run(
                ['pip', 'config', 'set', 'global.index-url', mirror['url']],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"✗ 配置镜像源失败: {result.stderr}")
                return False
            
            print(f"✓ 镜像源配置成功")
            
            # 设置 trusted-host
            result = subprocess.run(
                ['pip', 'config', 'set', 'global.trusted-host', mirror['trusted_host']],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✓ 信任主机配置成功")
            else:
                print(f"⚠ 信任主机配置失败（可能不影响使用）")
            
        except subprocess.TimeoutExpired:
            print("✗ 配置超时")
            return False
        except Exception as e:
            print(f"✗ 配置失败: {e}")
            return False
        
        # 验证配置
        print(f"\n验证配置...")
        current = self.get_current_config()
        if current and current['key'] == mirror_key:
            print(f"✓ 配置验证成功")
        else:
            print(f"⚠ 配置可能未生效，请手动检查")
        
        print(f"\n{'='*60}")
        print("  Pip 镜像源配置完成!")
        print(f"{'='*60}")
        print(f"\n镜像源: {mirror['name']}")
        print(f"镜像地址: {mirror['url']}")
        print(f"配置文件: {self.pip_config_file}")
        
        return True
    
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
            
            # 尝试访问镜像源
            req = urllib.request.Request(
                mirror['url'],
                headers={'User-Agent': 'pip/23.0'}
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
        print("  测试 Pip 镜像源速度")
        print(f"{'='*60}\n")
        print("正在测试各镜像源响应速度，请稍候...\n")
        
        results = []
        
        for key, mirror in self.MIRRORS.items():
            print(f"测试 {mirror['name']:12s} ... ", end='', flush=True)
            
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
                print(f"  {i}. {name:12s} - {speed*1000:6.0f} ms  [{key}]")
            else:
                print(f"  {i}. {name:12s} - 超时/失败  [{key}]")
        
        print(f"\n{'='*60}")
        
        # 推荐最快的镜像源
        if results and results[0][2] is not None:
            fastest_key, fastest_name, fastest_speed = results[0]
            print(f"\n推荐使用: {fastest_name} ({fastest_speed*1000:.0f} ms)")
            print(f"配置命令: python {sys.argv[0]} --mirror {fastest_key}")
        
        return results
    
    def interactive_configure(self):
        """交互式配置镜像源"""
        print(f"\n{'='*60}")
        print("  Pip 镜像源交互式配置")
        print(f"{'='*60}\n")
        
        # 显示当前配置
        current = self.get_current_config()
        if current:
            print(f"当前镜像源: {current['name']} ({current['url']})\n")
        else:
            print(f"当前使用官方源\n")
        
        # 显示可用镜像源
        print("可用的镜像源:\n")
        mirror_list = []
        for i, (key, mirror) in enumerate(self.MIRRORS.items(), 1):
            print(f"  {i}. {mirror['name']:12s} - {mirror['url']}")
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Pip 配置脚本 - 自动配置国内镜像源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                列出所有可用镜像源
  %(prog)s --show                显示当前配置信息
  %(prog)s --test                测试所有镜像源速度并排序
  %(prog)s --test --timeout 10   测试所有镜像源（超时10秒）
  %(prog)s --mirror tsinghua     配置清华大学镜像源
  %(prog)s --mirror aliyun       配置阿里云镜像源
  %(prog)s --interactive         交互式选择镜像源

可用镜像源:
  tsinghua  - 清华大学
  aliyun    - 阿里云
  tencent   - 腾讯云
  douban    - 豆瓣
  ustc      - 中国科技大学
  huawei    - 华为云
  official  - 官方源
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
        help='配置指定的镜像源 (tsinghua/aliyun/tencent/douban/ustc/huawei/official)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='交互式选择镜像源'
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
    configurator = PipConfigurator()
    
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
