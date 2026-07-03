# 123Pan Uploader CLI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.6+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/OlyMarco/123pan-uploader-cli?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/OlyMarco/123pan-uploader-cli?style=for-the-badge)

**🚀 A high-performance CLI tool for 123Pan Cloud Storage**

[Features](#-features) • [Quick Start](#-quick-start) • [Usage](#-usage-guide) • [Architecture](#-architecture) • [Changelog](#-changelog)

</div>

---

## 📖 Overview

A practical server-side file uploading tool that supports:
- Fast uploading of large files to 123Pan Cloud
- Multi-threaded downloading for direct links
- **Bash-style input** with Tab completion and command history
- **Smart duplicate detection** - skip files with same MD5
- **Flexible upload modes** - skip, overwrite, or keep both on conflict

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
| 🔧 **Flexible Modes** | `-f` overwrite, `-k` keep both, `--no-skip` force upload | 多种冲突处理模式 |
| 🧩 **Resumable Uploads** | S3 multipart upload for large files (5MB chunks) | S3分片上传，支持大文件断点续传 |

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
| `-k` | Keep both files on conflict (default) | 冲突时保留两者（默认行为） |

### Interactive Mode | 交互模式

```bash
# Basic upload | 基本上传
> /path/to/file

# Upload with custom directory name | 指定远程目录名
> /path/to/dir -d "My_Backup"

# Force overwrite | 强制覆盖
> /path/to/file -f

# Keep both on conflict | 冲突时保留两者
> /path/to/file -k

# Disable MD5 skip, re-upload all | 禁用MD5检查，全部重传
> /path/to/file --no-skip

# Combine flags (order doesn't matter) | 组合使用（顺序无关）
> /path/to/file -f -d "Backup" --no-skip
> /path/to/file -d "Backup" -f
```

> 💡 **Tip**: For paths with spaces, use quotes: `"C:\path with spaces\file"`

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

## 🏗 Architecture | 项目架构

```
123pan-uploader-cli/
├── app.py                          # 主入口 — CLI解析 + 交互模式
├── tosasitill_123pan/
│   ├── class123.py                 # API客户端 — 登录/文件列表/上传/下载/分享
│   └── config.py                   # 配置中心 — API端点URL + 超时/分片参数
├── utils/
│   ├── mpush.py                    # 上传引擎 — MD5去重 + S3分片上传 + 并发
│   ├── mget.py                     # 下载引擎 — 多线程分块下载
│   ├── command_handler.py          # 命令解析 — 路径/标志分离 + argparse集成
│   ├── input_handler.py            # 输入处理 — readline配置 + 路径补全
│   └── get-token.py                # Token工具 — 独立获取并保存登录凭据
├── requirements.txt
└── 123pan.txt                      # 凭据文件（自动生成，勿提交）
```

### API Authentication | API 鉴权流程

```
用户名/密码 → POST user.123pan.cn/api/user/sign_in (JSON)
                    ↓
             返回 Bearer Token
                    ↓
      保存至 123pan.txt + 后续请求 Authorization 头
```

> **Note**: 2026-07-03 起，123云盘已废弃旧的请求签名（`getSign`）机制，所有 API 调用仅需 Bearer Token 鉴权。

## 🙏 Credits | 致谢

Based on [tosasitill/123pan](https://github.com/tosasitill/123pan) - Provides core authentication and API functionality.

基于 [tosasitill/123pan](https://github.com/tosasitill/123pan) - 提供核心认证和API功能。

---

## 📋 Changelog | 更新日志

### [2026-07-03] — API Migration & Login Fix | API 迁移与登录修复

> 123云盘于 6 月 30 日更新了接口和认证体系（[公告](https://yun.123pan.cn/Notice/240156)），旧版本完全无法登录。此版本完整适配了全新的 API 架构。

#### 🔧 Breaking Changes | 重大变更
- **Login endpoint migrated** — 登录接口从 `www.123pan.com/b/api/user/sign_in` 迁移至 `user.123pan.cn/api/user/sign_in`，旧端点返回 404
- **Base domain migrated** — 主域名从 `www.123pan.com` 切换至 `www.123pan.cn`，Web 端已统一跳转至 `yun.123pan.cn`
- **Signature mechanism removed** — 彻底移除 `getSign` 签名机制及 `sign_get.py` 模块，新 API 仅需 Bearer Token 鉴权，不再要求请求签名参数
- **Login request format** — 登录请求从 `form-data` 改为 `application/json`，与官方 Web 端保持一致

#### 🐛 Bug Fixes | Bug 修复
- **Fixed login failure** — 修复因 123pan 接口迁移导致的登录 404 问题
- **Fixed file list retrieval** — 修复 `get_dir()` 因签名参数被拒绝的问题
- **Fixed upload request** — 修复 `upload_request` / `mkdir` / `download_info` 等接口因携带废弃签名参数导致的调用失败
- **Fixed token tool** — 更新 `get-token.py` 请求头以匹配新 API 要求

#### ⬆️ Upgrades | 升级适配
- Updated request headers: `App-Version` → `3`，`Origin`/`Referer` → `yun.123pan.cn`
- Unified `Content-Type: application/json` for all authenticated API calls
- Consolidated duplicate `URL_SIGN_IN` / `URL_123PAN_SIGN_IN` into single `URL_SIGN_IN`
- Improved login error handling with `ValueError` catch for JSON parse failures
- Deleted `sign_get.py` — dead code, no longer referenced by any module

#### ✅ Verified | 验证通过
- Login with phone number + password ✅
- File list / directory navigation ✅
- Single file upload (MD5 dedup + chunk upload + complete) ✅
- `app.py <path>` CLI mode ✅
- `app.py <path> --no-skip` force upload ✅

---

### [Unreleased] - Latest

#### ✨ New Features | 新功能
- **Enhanced command parsing** - Improved flag handling for better compatibility with Windows paths containing special characters (e.g., `中文文件夹`)
- **Flexible flag ordering** - Flags can now be specified in any order: `-f -d dest` and `-d dest -f` both work correctly
- **Path with spaces support** - Added helpful error message when paths contain spaces, guiding users to use quotes

#### 🐛 Bug Fixes | Bug 修复
- Fixed incorrect flag parsing when `-f` appeared before `-d`
- Fixed path recognition for Windows folder names starting with `-` or containing Chinese characters
- Improved error messages for invalid command formats

#### 📖 Documentation | 文档更新
- Added Changelog section
- Enhanced Usage Guide with more examples
- Added badges for last commit and issues

---

## ⚠️ Disclaimer | 免责声明

**This project is for personal use only and is not affiliated with 123Pan Cloud. Please comply with 123Pan Cloud's terms of service.**

**本项目仅供个人使用，与123云盘官方无关。请遵守123云盘的服务条款。**

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

</div>
