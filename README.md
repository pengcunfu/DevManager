# 通用开发工具一键安装系统

一个基于Python的通用开发工具自动化安装系统，支持一键安装Git、Docker、Node.js、Python、Java、PHP、ROS2、小皮面板、宝塔面板等多种开发工具。

## ✨ 特性

- 🚀 **一键安装**: 支持单个或批量安装多种开发工具
- 🌍 **跨平台支持**: 支持Linux (Ubuntu/CentOS/Arch)、macOS、Windows
- 🔧 **模块化设计**: 易于扩展和维护的插件式架构
- 🎯 **智能检测**: 自动检测系统环境和已安装工具
- 📋 **交互式界面**: 提供友好的命令行交互界面
- 🔄 **版本管理**: 支持特定版本安装和管理
- 🌐 **镜像源支持**: 内置国内镜像源，加速下载安装
- 📝 **详细日志**: 完整的安装日志记录和错误诊断

## 🛠️ 支持的工具

### 版本控制
- **Git** - 分布式版本控制系统

### 容器化
- **Docker** - 容器化平台

### 编程语言环境
- **Node.js** - JavaScript运行时环境 (支持NVM版本管理)
- **Python** - Python开发环境 (支持pyenv版本管理)
- **Java** - Java开发环境 (OpenJDK)
- **PHP** - PHP开发环境 (包含Composer)

### Web面板
- **小皮面板** - PHP集成开发环境
- **宝塔面板** - Linux服务器运维面板

### 机器人开发
- **ROS2** - 机器人操作系统2.0 (Humble版本)

## 📦 安装

### 系统要求

- **Linux**: Ubuntu 18.04+, CentOS 7+, Arch Linux
- **macOS**: macOS 10.14+
- **Windows**: Windows 10+
- **Python**: 3.7+

### 快速开始

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd InstallDevTools
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **开始使用**
   ```bash
   python install.py --interactive
   ```

## 🎯 使用方法

### 命令行参数

```bash
# 列出所有可用工具
python install.py --list

# 查看工具详细信息
python install.py --info git

# 安装单个工具
python install.py --install git

# 安装多个工具
python install.py --install git docker nodejs

# 安装所有工具
python install.py --install-all

# 强制重新安装
python install.py --force git

# 交互式安装（推荐）
python install.py --interactive

# 显示详细输出
python install.py --install git --verbose
```

### 交互式安装

运行交互式安装程序：

```bash
python install.py --interactive
```

程序会自动：
1. 检测您的操作系统环境
2. 显示所有可用的工具列表
3. 让您选择要安装的工具
4. 自动执行安装过程
5. 显示安装结果和状态

### 工具分组

系统预定义了几个工具分组，方便批量安装：

- **basic**: 基础开发工具 (git, docker)
- **languages**: 编程语言环境 (python, nodejs, java, php)
- **panels**: Web开发面板 (xiaopi_panel, bt_panel)
- **robotics**: 机器人开发 (ros2)

## 🔧 配置

### 全局配置

编辑 `config.yaml` 文件可以自定义：

- 日志级别和文件位置
- 命令执行超时时间
- 镜像源配置
- 工具版本设置

### 工具配置

每个工具都有独立的JSON配置文件位于 `configs/` 目录：

- `configs/git.json` - Git配置
- `configs/docker.json` - Docker配置
- `configs/nodejs.json` - Node.js配置
- 等等...

### 自定义工具配置

可以通过修改配置文件中的 `config_options` 部分来自定义工具安装：

```json
{
  "config_options": {
    "user_name": "Your Name",
    "user_email": "your.email@example.com",
    "node_version": "18.17.0",
    "python_version": "3.11.0"
  }
}
```

## 🏗️ 架构设计

### 核心组件

- **InstallerManager**: 安装管理器，负责协调整个安装过程
- **ToolInstaller**: 工具安装器基类，定义安装接口
- **PlatformDetector**: 平台检测器，识别操作系统和发行版
- **CommandRunner**: 命令执行器，安全执行系统命令

### 目录结构

```
InstallDevTools/
├── core/                   # 核心模块
│   └── installer.py        # 核心安装器类
├── configs/                # 工具配置文件
│   ├── git.json
│   ├── docker.json
│   ├── nodejs.json
│   └── ...
├── tools/                  # 工具安装器实现
│   ├── git.py
│   ├── docker.py
│   ├── nodejs.py
│   └── ...
├── install.py              # 主入口脚本
├── config.yaml             # 全局配置文件
├── requirements.txt        # Python依赖
└── README.md               # 说明文档
```

## 🔌 扩展开发

### 添加新工具

1. **创建配置文件**
   在 `configs/` 目录创建 `your_tool.json`：

   ```json
   {
     "name": "Your Tool",
     "description": "工具描述",
     "version": "latest",
     "category": "分类",
     "supported_platforms": ["linux", "darwin", "windows"],
     "platforms": {
       "linux": {
         "install_commands": ["sudo apt install -y your-tool"],
         "check_command": "your-tool --version",
         "post_install": []
       }
     }
   }
   ```

2. **实现安装器类**
   在 `tools/` 目录创建 `your_tool.py`：

   ```python
   from core.installer import ToolInstaller

   class YourToolInstaller(ToolInstaller):
       def check_installed(self) -> bool:
           # 检查工具是否已安装
           pass
       
       def install(self) -> bool:
           # 执行安装逻辑
           pass
       
       def post_install(self) -> bool:
           # 安装后配置
           pass
   ```

### 平台支持

系统支持以下平台标识：

- `linux_ubuntu` - Ubuntu Linux
- `linux_centos` - CentOS Linux  
- `linux_arch` - Arch Linux
- `darwin` - macOS
- `windows` - Windows

## 📋 常见问题

### Q: 安装失败怎么办？

A: 请检查：
1. 查看 `install.log` 日志文件了解详细错误信息
2. 确认网络连接正常
3. 确认具有足够的系统权限
4. 对于Linux系统，某些工具需要sudo权限

### Q: 如何设置镜像源？

A: 编辑 `config.yaml` 文件中的 `mirrors` 部分，或者在工具配置文件中设置特定的镜像源。

### Q: 支持离线安装吗？

A: 目前不支持完全离线安装，因为大部分工具需要从网络下载。但可以通过配置本地镜像源来加速安装。

### Q: Windows系统需要特殊配置吗？

A: Windows系统建议：
1. 以管理员权限运行
2. 预先安装Chocolatey包管理器
3. 某些工具可能需要手动安装（如小皮面板）

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢所有开源工具的开发者
- 感谢社区提供的安装脚本和最佳实践
- 特别感谢fishros.com提供的镜像源支持

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看 [Issues](../../issues) 了解已知问题
2. 创建新的 [Issue](../../issues/new) 报告问题
3. 查看日志文件 `install.log` 获取详细信息

---

**注意**: 本工具会修改系统环境和安装软件包，使用前请确保了解相关风险。建议在测试环境中先行验证。
