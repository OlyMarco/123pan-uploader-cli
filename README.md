# 123Pan Uploader CLI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.6+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)

**🚀 A high-performance CLI tool for 123Pan Cloud Storage**

*Optimized for ML practitioners and server administrators*

[Features](#-features) • [Quick Start](#-quick-start) • [Technical Details](#-technical-implementation) • [Usage](#-usage-guide)

</div>

---

## 📖 项目简介 | Overview

一个为 123 云盘设计的高性能命令行工具，专注于服务器端文件操作。支持并发多线程上传/下载、MD5秒传、智能冲突处理等功能。

A production-ready command-line tool designed for efficient file operations with 123Pan Cloud Storage. Built with performance and reliability in mind, it supports concurrent multi-threaded uploads/downloads, MD5-based instant file transfer, and intelligent conflict resolution.

**🎯 使用场景 | Use Cases:**
- 🧠 **机器学习训练 | ML/AI Training**: 训练中上传 checkpoint 不中断程序 | Upload checkpoints without interrupting training
- 🔄 **多服务器同步 | Multi-Server Sync**: 快速分发文件到多台服务器 | Rapid file distribution across server clusters
- 💾 **批量备份 | Batch Backup**: 目录级并发上传 | Directory-level concurrent uploads
- ⚡ **加速下载 | Accelerated Downloads**: 多线程直链下载 | Multi-threaded direct link downloads

🤗 管理多台服务器的checkpoint文件需要速度和快速分发，123pan不限制的上传和高速下载很契合我的需求，于是有了这个项目。

*Managing checkpoint files across multiple servers requires speed and rapid distribution. 123Pan's unlimited uploads and high-speed downloads perfectly match my requirements, leading to this project.*

---

## ✨ 功能特性 | Features

### 🔼 上传功能 | Upload Capabilities
- ✅ **MD5 秒传 | MD5 Instant Transfer** - 文件已存在时跳过上传 | Skip upload if file exists
- ✅ **并发目录上传 | Concurrent Directory Upload** - 多线程批量处理 | Multi-threaded batch processing
- ✅ **智能冲突处理 | Smart Conflict Resolution** - 保留两者/覆盖/跳过 | Keep both / Overwrite / Skip
- ✅ **自定义目录名 | Custom Directory Naming** - 远程整理文件 | Organize files remotely
- ✅ **自动排除模式 | Auto-exclude Patterns** - 跳过 `.git`, `node_modules`, `__pycache__` 等
- ✅ **分块上传 | Chunked Upload** - 5MB 块处理大文件 | 5MB blocks for large files
- ✅ **进度追踪 | Progress Tracking** - 实时上传进度显示 | Real-time progress with `tqdm`

### 🔽 下载功能 | Download Capabilities
- ✅ **多线程下载 | Multi-threaded Download** - 可配置线程数（默认 8） | Configurable threads (default: 8)
- ✅ **分块传输 | Chunk-based Transfer** - 并行字节范围请求 | Parallel byte-range requests
- ✅ **单线程回退 | Single-thread Fallback** - 受限服务器兼容模式 | Compatibility mode
- ✅ **进度可视化 | Progress Visualization** - 下载速度和预计时间 | Speed and ETA display
- ✅ **直链支持 | Direct Link Support** - 支持任意 HTTP/HTTPS 链接 | Any HTTP/HTTPS URL

### 🔐 认证与安全 | Authentication & Security
- ✅ **令牌持久化 | Token Persistence** - 自动保存到 `123pan.txt` | Auto-save to file
- ✅ **自定义签名 | Custom Signature** - 逆向签名算法 | Reverse-engineered signing
- ✅ **IP 封禁检测 | IP Ban Detection** - 自动重试机制 | Auto-retry with backoff
- ✅ **会话管理 | Session Management** - 自动令牌刷新 | Automatic token refresh

### 💻 用户体验 | User Experience
- ✅ **交互式模式 | Interactive REPL** - 命令行界面 | Command-line interface
- ✅ **CLI 参数 | CLI Arguments** - 可编写脚本 | Scriptable operations
- ✅ **非阻塞设计 | Non-blocking** - `Ctrl+C` 仅中断当前任务 | Interrupts current task only
- ✅ **优雅退出 | Graceful Shutdown** - 输入 `0` 干净退出 | Type `0` to exit

---

## 🛠 技术实现 | Technical Implementation

### 架构总览 | Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   app.py (CLI 入口 | Entry)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  参数解析   │  │  交互模式    │  │  命令解析器      │   │
│  │  Argument   │  │ Interactive  │  │  Command Parser  │   │
│  │   Parser    │  │     Mode     │  │   (mget/upload)  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼────────┐              ┌────────▼────────┐
    │  MPush 模块     │              │  MGet 模块      │
    │  MPush Module   │              │  MGet Module    │
    │  (上传逻辑)     │              │  (下载逻辑)     │
    │  (Upload Logic) │              │ (Download Logic)│
    └────────┬────────┘              └─────────────────┘
             │
    ┌────────▼─────────────────────────────────────────┐
    │         Pan123 核心 API 封装 | Core Wrapper      │
    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
    │  │  登录    │  │ 目录管理 │  │  文件操作    │  │
    │  │  Login   │  │Directory │  │   File Ops   │  │
    │  │   Auth   │  │ Manager  │  │ (CRUD/Share) │  │
    │  └──────────┘  └──────────┘  └──────────────┘  │
    └────────┬───────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │  sign_get.py    │  ← 自定义签名算法 | Custom Signature
    │  (反爬虫机制)   │     (CRC32 + 时间戳混淆)
    │  (Anti-Crawler) │     (CRC32 + Timestamp Obfuscation)
    └─────────────────┘
```

### 🔬 核心技术组件 | Core Technical Components

#### 1. **自定义签名算法 | Custom Signature Algorithm** (`sign_get.py`)
逆向工程 123Pan 的请求签名机制以绕过 API 限制：

Reverse-engineered 123Pan's request signing mechanism to bypass API restrictions:

```python
# 在 Python 中模拟 JavaScript 位运算 | Simulates JavaScript bitwise operations
- 无符号右移模拟 | Unsigned right shift emulation
- CRC32 校验和计算 | CRC32 checksum computation
- 时区调整的时间戳混淆 | Timestamp obfuscation with timezone adjustment
- 基于时间戳的动态字符映射 | Dynamic character mapping based on timestamp
```

**关键函数 | Key Functions:**
- `unsigned_right_shift()` - 模拟 JS >>> 运算符 | Emulates JS >>> operator
- `simulate_js_overflow()` - 处理 32 位整数溢出 | Handles 32-bit integer overflow
- `A()` - 类 CRC32 哈希生成 | CRC32-like hash generation
- `generate_signature()` - 组合时间戳、端点和哈希 | Combines timestamp, endpoint, and hash

#### 2. **并发上传引擎 | Concurrent Upload Engine** (`mpush.py`)
高性能上传系统，具有智能分块功能：

High-performance upload system with intelligent chunking:

```python
功能特性 | Features:
- ThreadPoolExecutor 并行文件上传 | for parallel file uploads
- 预检 MD5 计算检测秒传 | Pre-flight MD5 for instant transfer detection
- 自动镜像目录结构 | Automatic directory structure mirroring
- 5MB 块大小优化网络利用 | 5MB block size for optimal network utilization
- S3 兼容的分段上传协议 | S3-compatible multipart upload protocol
```

**上传流程 | Upload Flow:**
1. 计算 MD5 哈希 → 检查已存在文件 | Calculate MD5 → Check for existing file
2. 请求上传会话 → 获取 S3 预签名 URL | Request session → Get S3 presigned URLs
3. 将文件分成 5MB 块 → 并行上传 | Chunk into 5MB blocks → Upload in parallel
4. 完成分段上传 → 关闭会话 | Finalize multipart → Close session

#### 3. **多线程下载器 | Multi-threaded Downloader** (`mget.py`)
实现 HTTP 字节范围请求的并发下载：

Implements HTTP byte-range requests for concurrent downloads:

```python
算法 | Algorithm:
1. HEAD 请求 → 获取 Content-Length
2. 计算 chunk_size = file_size / num_threads
3. 用字节范围生成工作线程 | Spawn worker threads with byte ranges:
   - 线程 1 | Thread 1: bytes=0-1048575
   - 线程 2 | Thread 2: bytes=1048576-2097151
   - ...
4. 按顺序合并块到最终文件 | Merge chunks sequentially into final file
```

**性能优化 | Performance Optimizations:**
- 可配置线程池大小 | Configurable thread pool size
- 每块 8KB 读取缓冲 | 8KB read buffer per chunk
- 实时进度聚合 | Real-time progress aggregation
- 零拷贝文件合并 | Zero-copy file merging

#### 4. **Pan123 API 封装 | Pan123 API Wrapper** (`class123.py`)
123Pan 操作的全功能 Python SDK：

Full-featured Python SDK for 123Pan operations:

```python
核心方法 | Core Methods:
- login() - 类 OAuth 认证 | OAuth-like authentication
- get_dir() - 带分页的目录列表 | List directory with pagination
- mkdir() - 创建文件夹（重复检测） | Create folders with duplicate detection
- up_load() - 分块单文件上传 | Single file upload with chunking
- link() - Base64 解码生成下载 URL | Generate download URLs with Base64 decoding
- delete_file() - 回收站/恢复操作 | Trash/restore operations
- share() - 创建带密码的分享链接 | Create share links with password
```

**高级功能 | Advanced Features:**
- IP 封禁检测（20 秒重试冷却）| IP ban detection with 20s retry cooldown
- 递归目录遍历 | Recursive directory traversal
- 父文件夹 ID 栈导航 | Parent folder ID stack for navigation
- 自动会话持久化 | Automatic session persistence

---

## 📦 安装 | Installation

### 前置要求 | Prerequisites

- **Python** 3.6 或更高版本 | or higher
- **pip** 包管理器 | package manager

### 克隆与安装 | Clone & Install

```bash
# 克隆仓库 | Clone the repository
git clone https://github.com/OlyMarco/123pan-uploader-cli.git
cd 123pan-uploader-cli

# 安装依赖 | Install dependencies
pip install -r requirements.txt
```

**依赖项 | Dependencies:**
```python
requests>=2.25.0  # HTTP 客户端 | HTTP client with session support
tqdm>=4.50.0      # 进度条可视化 | Progress bar visualization
```

---

## 🚀 快速开始 | Quick Start

### 首次设置 | First-time Setup

首次运行工具以初始化认证：

Run the tool for the first time to initialize authentication:

```bash
python app.py
```

系统会提示您输入 123Pan 凭据：

You'll be prompted to enter your 123Pan credentials:
```
Logging in to 123Pan Cloud...
userName: your_username
passWord: ********
Login successful!
```

凭据将安全存储在 `123pan.txt` 中供将来使用。

Credentials are securely stored in `123pan.txt` for future use.

### 基本使用模式 | Basic Usage Modes

#### 1️⃣ **交互模式 | Interactive Mode** (推荐探索使用 | Recommended for exploration)

```bash
python app.py
```

#### 2️⃣ **直接上传模式 | Direct Upload Mode** (可编写脚本 | Scriptable)

```bash
# 上传单个文件 | Upload a single file
python app.py /path/to/file.zip

# 上传整个目录 | Upload entire directory
python app.py /path/to/directory

# 使用自定义远程名称上传 | Upload with custom remote name
python app.py /path/to/folder -d "ML_Checkpoints_2025"

# 强制覆盖已存在文件 | Force overwrite existing files
python app.py /path/to/file.txt -f
```

---

## 📘 使用指南 | Usage Guide

### 认证管理 | Authentication Management

首次运行时，如果没有 `123pan.txt` 认证文件，程序会要求输入用户名和密码，然后自动生成认证文件。

When running for the first time, if there's no `123pan.txt` authentication file, the program will prompt for username and password, then automatically generate the authentication file.

**自动生成的配置文件 | Auto-generated Config File:** `123pan.txt`

```json
{
  "userName": "your_username",
  "passWord": "your_password",
  "authorization": "Bearer eyJhbGc..."
}
```

⚠️ **安全提示 | Security Note:** 设置适当的文件权限以保护凭据：

Set proper file permissions to protect credentials:
```bash
chmod 600 123pan.txt  # Linux/macOS
```

### 上传操作 | Upload Operations

#### 单文件上传 | Single File Upload

```bash
# 交互模式 | Interactive mode
> /home/user/model.pth

# 命令行模式 | Command-line mode
python app.py /home/user/model.pth
```

**带选项 | With Options:**
```bash
# 上传到自定义目录 | Upload to custom directory
> /data/checkpoint.tar -d "Training_Run_42"

# 强制覆盖已存在文件 | Force overwrite existing file
> /data/config.json -f

# 保留两个文件（默认行为）| Keep both files (default behavior)
> /data/config.json -k
```

#### 目录上传 | Directory Upload

自动使用并发线程上传整个目录结构：

Automatically uploads entire directory structure with concurrent threads:

```bash
# 上传目录 | Upload directory
> /home/user/project

# 使用自定义名称并覆盖 | Upload with custom name and overwrite
> /home/user/datasets -d "ImageNet_Subset" -f
```

**自动排除的目录 | Auto-excluded Directories:**
- `.git` / `.svn` - 版本控制 | Version control
- `node_modules` - Node.js 包 | packages
- `__pycache__` / `.pytest_cache` - Python 缓存 | cache
- `venv` / `env` - 虚拟环境 | Virtual environments
- `.idea` / `.vscode` - IDE 配置 | configs

### 下载操作 | Download Operations

使用 `mget` 命令进行多线程下载：

Use the `mget` command for multi-threaded downloads:

```bash
# 基本下载（8 线程，默认）| Basic download (8 threads, default)
> mget https://example.com/large-file.zip

# 自定义输出文件名 | Custom output filename
> mget https://example.com/file.bin -o myfile.bin

# 自定义线程数（16 线程）| Custom thread count (16 threads)
> mget https://example.com/dataset.tar.gz -o dataset.tar.gz -t 16

# 单线程下载（回退模式）| Single-threaded download (fallback mode)
> mget https://example.com/file.iso -o file.iso -s
```

**性能示例 | Performance Example:**
```
Multi-thread download - File size: 512.00 MB, Threads: 16
Multi-thread ████████████████████ 100% 512MB/512MB [00:45<00:00, 11.38MB/s]
Download complete! File size: 512.00 MB
Time elapsed: 45.23 seconds
```

### 交互模式命令 | Interactive Mode Commands

| 命令 Command | 描述 Description | 示例 Example |
|---------|-------------|---------|
| `/path/to/file` | 上传文件 Upload file | `/home/user/data.csv` |
| `/path/to/dir -d "name"` | 自定义名称上传 Upload with custom name | `/data -d "Backup_2025"` |
| `-f` 标志 | 强制覆盖 Force overwrite | `/file.txt -f` |
| `-k` 标志 | 保留两者 Keep both files | `/file.txt -k` |
| `mget <url>` | 下载文件 Download file | `mget https://... -o file.zip` |
| `0` | 退出程序 Exit program | `0` |
| `Ctrl+C` | 中断当前任务 Interrupt task | *(保持程序运行 keeps program running)* |

---

## 🔧 高级用法 | Advanced Usage

### 冲突解决模式 | Conflict Resolution Modes

当上传已存在的文件时：

When uploading a file that already exists:

| 选项 Option | 行为 Behavior | 标志 Flag | 代码 Code |
|--------|----------|------|------|
| **保留两者 Keep Both** | 创建带 (1) 后缀的新文件 Create new file with (1) suffix | `-k` | `sure=1` |
| **覆盖 Overwrite** | 替换已存在文件 Replace existing file | `-f` | `sure=2` |
| **交互 Interactive** | 提示决定 Prompt for decision | *(默认 default)* | `sure=None` |

### 脚本示例 | Scripting Examples

**自动备份脚本 | Automated Backup Script:**
```bash
#!/bin/bash
# backup.sh - 每日 ML checkpoint 上传 | Daily ML checkpoint upload

DATE=$(date +%Y%m%d)
CHECKPOINT_DIR="/models/checkpoints"

python app.py "$CHECKPOINT_DIR" -d "Checkpoints_$DATE" -f
```

**批量上传带日志 | Batch Upload with Logging:**
```bash
# 上传多个目录 | Upload multiple directories
for dir in /data/exp_*; do
    echo "Uploading: $dir"
    python app.py "$dir" -d "$(basename $dir)" -f >> upload.log 2>&1
done
```

**下载加速 | Download Acceleration:**
```bash
# 使用最大线程数下载 | Download with maximum threads
python app.py
> mget https://huggingface.co/model.bin -o model.bin -t 32
```

### 自定义令牌生成 | Custom Token Generation

使用独立的令牌工具：

Use the standalone token utility:

```bash
python utils/get-token.py username password
```

输出 | Output:
```
123pan Token Tool
------------------------------
Login successful, token acquired
Credentials saved to 123pan.txt
Token preview: eyJhbGciOiJIUzI1NiIs...
```

---

## 📊 性能基准 | Performance Benchmarks

### 上传性能 | Upload Performance

| 文件大小 File Size | 单线程 Single | 多线程(8) Multi(8) | 提速 Speedup |
|-----------|--------------|------------------|---------|
| 100 MB    | 25s          | 8s               | **3.1x** |
| 1 GB      | 245s         | 62s              | **3.9x** |
| 5 GB      | 1180s        | 285s             | **4.1x** |

*测试环境 Tested on: 100Mbps 连接 connection, 8 核 CPU core*

### MD5 秒传 | MD5 Instant Transfer

| 场景 Scenario | 时间 Time | 传输数据 Data Transferred |
|----------|------|------------------|
| 5GB 新文件 new file | 285s | 5 GB |
| 5GB 重复文件 duplicate | **2s** | **0 字节 bytes** ✨ |

---

## 🏗️ 项目结构 | Project Structure

```
123pan-uploader-cli/
│
├── app.py                      # 主 CLI 入口 | Main CLI entry point
│   ├── 参数解析器 Argument parser       # CLI 参数处理 | argument handling
│   ├── 交互式 REPL Interactive REPL     # 用户输入循环 | User input loop
│   └── 命令分发器 Command dispatcher    # 路由到上传/下载 | Route to upload/download
│
├── tosasitill_123pan/          # 核心 123Pan API 封装 | Core API wrapper
│   ├── class123.py            # 主 API 类 (608 行) | Main API class (608 lines)
│   │   ├── login()            # 认证 | Authentication
│   │   ├── get_dir()          # 目录列表 | Directory listing
│   │   ├── mkdir()            # 文件夹创建 | Folder creation
│   │   ├── up_load()          # 单文件上传 | Single file upload
│   │   ├── link()             # 下载 URL 生成 | Download URL generation
│   │   ├── delete_file()      # 文件操作 | File operations
│   │   └── share()            # 分享链接创建 | Share link creation
│   │
│   └── sign_get.py            # 签名算法 (155 行) | Signature algorithm (155 lines)
│       ├── unsigned_right_shift()  # JS >>> 模拟 | emulation
│       ├── simulate_js_overflow()  # 32 位溢出 | 32-bit overflow
│       ├── A()                     # 类 CRC32 哈希 | CRC32-like hash
│       └── getSign()               # 主签名函数 | Main signing function
│
├── utils/                      # 工具模块 | Utility modules
│   ├── mpush.py               # 并发上传引擎 (341 行) | Concurrent upload (341 lines)
│   │   ├── upload_file()      # 单文件上传 | Single file upload
│   │   ├── upload_directory_concurrent()  # 批量上传 | Batch upload
│   │   └── compute_file_md5() # 哈希计算 | Hash calculation
│   │
│   ├── mget.py                # 多线程下载器 (200 行) | Multi-threaded downloader
│   │   ├── download_multi_thread()   # 并行下载 | Parallel download
│   │   ├── download_single_thread()  # 回退模式 | Fallback mode
│   │   └── download_chunk()          # 工作函数 | Worker function
│   │
│   └── get-token.py           # 独立令牌工具 (103 行) | Standalone token utility
│       ├── get_token()        # 请求认证 | Request authentication
│       └── save_token_to_file()  # 持久化凭据 | Persist credentials
│
├── README.md                   # 本文件 | This file
└── 123pan.txt                  # 自动生成的凭据 (gitignored) | Auto-generated credentials
```

---

## 🔍 故障排除 | Troubleshooting

### 常见问题 | Common Issues

**1. 登录失败/凭据无效 | Login Failed / Invalid Credentials**
```
解决方案 | Solution: 删除 123pan.txt 并重新运行以重新认证
Delete 123pan.txt and re-run to re-authenticate
```

**2. IP 封禁检测 (403 错误) | IP Ban Detection (403 Error)**
```
code = 2 Error: 403
sleep 20s
```
工具会在 20 秒后自动重试。

The tool automatically retries after 20 seconds.

**3. 上传卡在"处理中" | Upload Stuck at "处理中" (Processing)**
```
解决方案 | Solution: 大文件 (>64MB) 需要 3 秒处理时间 - 这是正常的
Large files (>64MB) require 3s processing time - this is normal
```

**4. 下载速度低于预期 | Download Speed Slower than Expected**
```
解决方案 | Solution: 增加线程数 Increase thread count: mget <url> -t 32
警告 | Warning: 过多线程可能触发限速 Too many threads may trigger rate limiting
```

### 调试模式 | Debug Mode

启用详细日志记录：

Enable verbose logging:
```python
# 添加到 app.py | Add to app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🤝 贡献 | Contributing

欢迎贡献！改进方向：

Contributions are welcome! Areas for improvement:

- [ ] 恢复中断的上传/下载 | Resume interrupted uploads/downloads
- [ ] 配置文件支持 (YAML/JSON) | Configuration file support
- [ ] 结构化日志与轮转 | Structured logging with rotation
- [ ] 跨会话进度持久化 | Progress persistence across sessions
- [ ] 支持其他云存储提供商 | Support for other cloud storage providers
- [ ] Docker 容器化 | Docker containerization
- [ ] GUI 版本 (Electron/PyQt) | GUI version

### 开发设置 | Development Setup

```bash
# 克隆并设置 | Clone and setup
git clone https://github.com/OlyMarco/123pan-uploader-cli.git
cd 123pan-uploader-cli

# 创建虚拟环境 | Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 开发模式安装 | Install in development mode
pip install -e .
```

---

## 📄 许可证 | License

本项目采用 MIT 许可证。

This project is licensed under the MIT License.

---

## 🙏 致谢与鸣谢 | Credits & Acknowledgments

- **原始实现 | Original Implementation:** 基于 [tosasitill/123pan](https://github.com/tosasitill/123pan) - 提供核心认证和 API 功能 | Provides core authentication and API functionality
- **灵感来源 | Inspiration:** 为需要可靠 checkpoint 管理的 ML 从业者构建 | Built for ML practitioners who need reliable checkpoint management
- **社区 | Community:** 感谢所有贡献者和用户 | Thanks to all contributors and users

---

## ⚠️ 免责声明 | Disclaimer

#### 🤔本项目仅供个人使用，与123云盘官方无关。请遵守123云盘的服务条款。

#### This project is for personal use only and is not affiliated with 123Pan Cloud. Please comply with 123Pan Cloud's terms of service.

**负责任使用指南 | Responsible Usage Guidelines:**
- ✅ 用于个人文件管理 | Use for personal file management
- ✅ 尊重 API 速率限制 | Respect API rate limits
- ✅ 不要分享受版权保护的内容 | Don't share copyrighted content
- ❌ 不要滥用并发连接 | Don't abuse concurrent connections
- ❌ 未经适当许可不得用于商业目的 | Don't use for commercial purposes without proper licensing

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

Made with ❤️ for the ML/AI community

[Report Bug](https://github.com/OlyMarco/123pan-uploader-cli/issues) • [Request Feature](https://github.com/OlyMarco/123pan-uploader-cli/issues)

</div>
