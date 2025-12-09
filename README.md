# 123Pan Uploader CLI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.6+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)

**🚀 A high-performance CLI tool for 123Pan Cloud Storage**

[Features](#-features) • [Quick Start](#-quick-start) • [Usage](#-usage-guide)

</div>

## 📖 Overview

A practical server-side file uploading tool that supports:
- Fast uploading of large files to 123Pan Cloud
- Multi-threaded downloading for direct links
- **Bash-style input** with Tab completion and command history
- **Smart duplicate detection** - skip files with same MD5

一个实用的服务器端文件上传工具，支持123云盘大文件快速上传、多线程下载、Bash风格输入（Tab补全和历史记录）、智能MD5去重。

> 🤗 Managing checkpoint files across multiple servers requires speed and rapid distribution. 123Pan's unlimited uploads and high-speed downloads perfectly match my requirements.

## ✨ Features | 功能特性

| Feature | Description | 说明 |
|---------|-------------|------|
| 🚀 **Fast Upload** | Concurrent multi-file uploads with progress bar | 并发多文件上传，带进度条 |
| 📥 **Multi-threaded Download** | Configurable threads (default: 8) | 可配置线程数（默认8线程） |
| 🔄 **Smart Deduplication** | Skip files with same name and MD5 hash | 智能去重，跳过同名同MD5文件 |
| ⌨️ **Bash-style Input** | Tab completion, command history, arrow keys | Tab补全、历史记录、方向键 |
| 📊 **Progress Tracking** | Real-time progress bar with upload statistics | 实时进度条和上传统计 |
| 🔐 **Auto Authentication** | Token persistence to `123pan.txt` | 自动保存登录凭据 |

## 📦 Installation | 安装

```bash
git clone https://github.com/OlyMarco/123pan-uploader-cli.git
cd 123pan-uploader-cli
pip install -r requirements.txt
```

**Dependencies | 依赖:**
```
requests>=2.25.0
tqdm>=4.50.0
pyreadline3>=3.1.0  # Optional: For bash-style input on Windows
```

> **Note | 注意**: Linux/macOS 系统自带 readline。Windows 用户需安装 `pyreadline3` 以获得完整的 Bash 风格体验。

## 🚀 Quick Start | 快速开始

```bash
# Interactive mode | 交互模式
python app.py

# Direct upload | 直接上传
python app.py /path/to/file_or_directory

# Upload with options | 带参数上传
python app.py /path/to/file -d "Remote_Folder" -f
```

First run will prompt for 123Pan credentials (auto-saved to `123pan.txt`).

首次运行会提示输入123云盘账号密码（自动保存到 `123pan.txt`）。

## 📘 Usage Guide | 使用指南

### Bash-style Input Features | Bash风格输入

| Feature | Key/Action | 说明 |
|---------|------------|------|
| **Tab Completion** | `Tab` | 自动补全文件路径 |
| **Command History** | `↑`/`↓` | 浏览历史命令 |
| **Line Editing** | `Ctrl+A`/`Ctrl+E`/`Ctrl+U` | 行首/行尾/清空行 |

### Upload Mode Options | 上传模式选项

| Option | Behavior | 说明 |
|--------|----------|------|
| *(默认)* | Skip if same filename **AND** same MD5 exist | 文件名和MD5都相同则跳过 |
| `--no-skip` | Re-upload all, keep both if name conflicts | 全部重传，同名文件保留两者 |
| `-f` | Delete existing and re-upload (overwrite) | 删除已存在文件后重新上传（覆盖） |

```bash
# Default: Skip if same name AND MD5
> /path/to/file

# --no-skip: Always upload, keep both on conflict
> /path/to/file --no-skip

# -f: Force overwrite existing file
> /path/to/file -f

# Upload to custom directory
> /path/to/dir -d "My_Backup" -f
```

### Download Command | 下载命令

```bash
> mget <url> [-o output_file] [-t threads] [-s]

# Examples | 示例
> mget https://example.com/file.zip -o file.zip -t 16  # 16线程下载
> mget https://example.com/file.zip -s                 # 单线程下载
```

### Exit Program | 退出程序

```bash
> 0                    # 方法1: 输入 '0'
> Ctrl+C twice         # 方法2: 2秒内连按两次 Ctrl+C
```

## 🔧 Command Line Arguments | 命令行参数

| Argument | Description | 说明 |
|----------|-------------|------|
| `-f, --force` | Force overwrite existing files | 强制覆盖已存在的文件 |
| `--no-skip` | Disable MD5 check, re-upload all | 禁用MD5检查，全部重传 |
| `-d, --dest` | Specify custom destination directory | 指定远程目录名 |
| `-k, --keep` | Keep both files when names conflict | 同名文件保留两者（默认行为） |

```bash
python app.py /path/to/directory                    # 默认: 智能跳过
python app.py /path/to/directory -f                 # 强制覆盖
python app.py /path/to/directory --no-skip          # 全部重传
python app.py /path/to/directory -d "Backup" -f     # 自定义目录 + 覆盖
```

## 🙏 Credits | 致谢

Based on [tosasitill/123pan](https://github.com/tosasitill/123pan) - Provides core authentication and API functionality.

基于 [tosasitill/123pan](https://github.com/tosasitill/123pan) - 提供核心认证和API功能。


## ⚠️ Disclaimer | 免责声明

**This project is for personal use only and is not affiliated with 123Pan Cloud. Please comply with 123Pan Cloud's terms of service.**

**本项目仅供个人使用，与123云盘官方无关。请遵守123云盘的服务条款。**

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

</div>
