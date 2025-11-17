#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
npm 配置脚本
自动配置 npm 国内镜像源
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


class NpmConfigurator:
    """npm 配置器"""
    
    # 国内镜像源配置
    MIRRORS = {
        'npmmirror': {
            'name': 'npmmirror (淘宝)',
            'url': 'https://registry.npmmirror.com',
            'home': 'https://npmmirror.com'
        },
        'tencent': {
            'name': '腾讯云',
            'url': 'https://mirrors.cloud.tencent.com/npm/',
            'home': 'https://mirrors.cloud.tencent.com'
        },
        'huawei': {
            'name': '华为云',
            'url': 'https://repo.huaweicloud.com/repository/npm/',
            'home': 'https://mirrors.huaweicloud.com'
        },
        'ustc': {
            'name': '中国科技大学',
            'url': 'https://npmreg.proxy.ustclug.org/',
            'home': 'https://mirrors.ustc.edu.cn'
        },
        'official': {
            'name': '官方源',
            'url': 'https://registry.npmjs.org/',
            'home': 'https://www.npmjs.com'
        }
    }
    
    def __init__(self):
        """初始化配置器"""
        pass
    
    def check_npm_installed(self) -> bool:
        """检查 npm 是否已安装"""
        try:
            result = subprocess.run(
                ['npm', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def list_mirrors(self):
        """列出所有可用的镜像源"""
        print(f"\n{'='*60}")
        print("  可用的 npm 镜像源")
        print(f"{'='*60}\n")
        
        for key, mirror in self.MIRRORS.items():
            print(f"  [{key:10s}] {mirror['name']}")
            print(f"              {mirror['url']}")
            print()
        
        print(f"{'='*60}")
    
    def get_current_registry(self) -> Optional[str]:
        """获取当前配置的镜像源"""
        try:
            result = subprocess.run(
                ['npm', 'config', 'get', 'registry'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            return None
            
        except Exception as e:
            print(f"获取当前配置失败: {e}")
            return None
    
    def show_current_config(self):
        """显示当前配置信息"""
        print(f"\n{'='*60}")
        print("  当前 npm 配置信息")
        print(f"{'='*60}")
        
        if not self.check_npm_installed():
            print("\n✗ npm 未安装或不在 PATH 中")
            print(f"\n{'='*60}")
            return
        
        # 获取 npm 版本
        try:
            result = subprocess.run(
                ['npm', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"\nnpm 版本: {result.stdout.strip()}")
        except Exception:
            pass
        
        # 获取当前镜像源
        registry = self.get_current_registry()
        if registry:
            print(f"\n当前镜像源: {registry}")
            
            # 查找匹配的镜像源
            for key, mirror in self.MIRRORS.items():
                if mirror['url'].rstrip('/') in registry or registry.rstrip('/') in mirror['url'].rstrip('/'):
                    print(f"镜像名称: {mirror['name']}")
                    break
        else:
            print(f"\n✗ 无法获取当前镜像源配置")
        
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
            
            # 尝试访问镜像源
            req = urllib.request.Request(
                mirror['url'],
                headers={'User-Agent': 'npm/10.0.0'}
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
        print("  测试 npm 镜像源速度")
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
        
        if not self.check_npm_installed():
            print("错误: npm 未安装或不在 PATH 中")
            print("请先安装 Node.js 和 npm")
            return False
        
        mirror = self.MIRRORS[mirror_key]
        
        print(f"\n{'='*60}")
        print(f"  配置 npm 镜像源 - {mirror['name']}")
        print(f"{'='*60}")
        
        # 使用 npm config 命令配置
        try:
            print(f"\n正在配置镜像源...")
            result = subprocess.run(
                ['npm', 'config', 'set', 'registry', mirror['url']],
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
        registry = self.get_current_registry()
        if registry and mirror['url'].rstrip('/') in registry:
            print(f"✓ 配置验证成功")
        else:
            print(f"⚠ 配置可能未生效，请手动检查")
        
        print(f"\n{'='*60}")
        print("  npm 镜像源配置完成!")
        print(f"{'='*60}")
        print(f"\n镜像源: {mirror['name']}")
        print(f"镜像地址: {mirror['url']}")
        
        return True
    
    def interactive_configure(self):
        """交互式配置镜像源"""
        print(f"\n{'='*60}")
        print("  npm 镜像源交互式配置")
        print(f"{'='*60}\n")
        
        if not self.check_npm_installed():
            print("✗ npm 未安装或不在 PATH 中")
            print("请先安装 Node.js 和 npm")
            return False
        
        # 显示当前配置
        registry = self.get_current_registry()
        if registry:
            print(f"当前镜像源: {registry}\n")
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="npm 配置脚本 - 自动配置国内镜像源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                列出所有可用镜像源
  %(prog)s --show                显示当前配置信息
  %(prog)s --test                测试所有镜像源速度并排序
  %(prog)s --test --timeout 10   测试所有镜像源（超时10秒）
  %(prog)s --mirror npmmirror    配置 npmmirror (淘宝) 镜像源
  %(prog)s --mirror tencent      配置腾讯云镜像源
  %(prog)s --interactive         交互式选择镜像源

可用镜像源:
  npmmirror - npmmirror (淘宝)
  tencent   - 腾讯云
  huawei    - 华为云
  ustc      - 中国科技大学
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
        help='配置指定的镜像源 (npmmirror/tencent/huawei/ustc/official)'
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
    configurator = NpmConfigurator()
    
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
