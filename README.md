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
- **Three login methods**: Account/Password, QR Code (WeChat scan), Saved Token
- **Auto token recovery**: re-login with saved password if token expires
- **Comprehensive logging**: command, runtime, and error logs saved locally
- **Bash-style input** with Tab completion and command history
- **Smart duplicate detection** - skip files with same MD5
- **Flexible upload modes** - skip, overwrite, or keep both on conflict

一个实用的服务器端文件上传工具，支持123云盘大文件快速上传、多线程下载、三种登录方式（账密/扫码/Token自动恢复）、完整日志系统、Bash风格输入（Tab补全和历史记录）、智能MD5去重。

> 🤗 Managing checkpoint files across multiple servers requires speed and rapid distribution. 123Pan's unlimited uploads and high-speed downloads perfectly match my requirements.

## ✨ Features | 功能特性

| Feature | Description | 说明 |
|---------|-------------|------|
| 🚀 **Fast Upload** | Concurrent multi-file uploads with progress bar | 并发多文件上传，带进度条 |
| 📥 **Multi-threaded Download** | Configurable threads (default: 8) | 可配置线程数（默认8线程） |
| 🔄 **Smart Deduplication** | Skip files with same name and MD5 hash | 智能去重，跳过同名同MD5文件 |
| ⌨️ **Bash-style Input** | Tab completion, command history, arrow keys | Tab补全、历史记录、方向键 |
| 📊 **Progress Tracking** | Real-time progress bar with upload statistics | 实时进度条和上传统计 |
| 🔐 **Multi-Login Support** | Account/Password, QR Code (WeChat), Token persistence | 账密登录、微信扫码登录、Token持久化 |
| 🔑 **Auto Token Recovery** | Re-login with saved password if token expires | Token过期自动用账密重登 |
| 📝 **Comprehensive Logging** | Command, runtime, and error logs in `logs/` | 命令日志、运行日志、错误日志 |
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
qrcode>=7.3.1
pyreadline3>=3.1.0  # Optional: For bash-style input on Windows
```

> **Note | 注意**: Linux/macOS 系统自带 readline。Windows 用户需安装 `pyreadline3` 以获得完整的 Bash 风格体验。QR Code 登录需要 `qrcode` 库。

## 🚀 Quick Start | 快速开始

```bash
# Interactive mode (account/password or QR code login) | 交互模式
python app.py

# Force QR code login | 强制扫码登录
python app.py --qr

# Direct upload | 直接上传
python app.py /path/to/file_or_directory

# Upload with options | 带参数上传
python app.py /path/to/file -d "Remote_Folder" -f
```

First run will prompt for login method (account/password or QR code). Credentials are auto-saved to `123pan.txt`.

首次运行会提示选择登录方式（账密或扫码）。凭据自动保存到 `123pan.txt`。

## 🔐 Login Methods | 登录方式

### 1. QR Code Login (WeChat Scan) | 微信扫码登录

```bash
python app.py --qr
```

- Generates a QR code saved to `qrcode.txt` and `qrcode.png`
- Scan with WeChat or 123Pan app
- Click "微信授权登录" (WeChat Authorize) in the scan page
- Token is automatically obtained and saved
- **No username/password required** — QR login saves empty credentials

> ⚠️ QR code expires in ~60 seconds. Scan quickly and authorize immediately!

### 2. Account & Password Login | 账号密码登录

First run without `123pan.txt` will prompt for credentials:

```
No saved credentials found. Please choose a login method:
  1. Account & Password login
  2. QR Code login (scan with WeChat or 123Pan app)
Enter choice (1 or 2): 1
Please enter username: <your_phone_number>
Please enter password: <your_password>
```

### 3. Saved Token (Auto-Verify) | 已保存Token自动验证

If `123pan.txt` exists, the saved token is loaded and verified:

- **Token valid** → proceed directly (no login needed)
- **Token invalid + password saved** → auto re-login with saved credentials (try once)
- **Token invalid + no password (QR login)** → program exits with error message
- **Token invalid + re-login fails** → program exits with error message

### Token Recovery Flow | Token恢复流程

```
123pan.txt exists
    ↓
Load token → get_dir() verify
    ↓
Token valid? ── YES ──→ Continue
    │
    NO
    ↓
Has userName + passWord? ── YES ──→ Re-login (try once)
    │                                    │
    NO                                   ├─ Success → Continue
    ↓                                    └─ Fail → Exit (code=1)
Exit (code=1)
"Please re-run with --qr"
```

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
| `--qr, --qrcode` | **Force QR code login** (scan with WeChat) | **强制扫码登录**（微信扫码） |

```bash
python app.py /path/to/directory                    # 默认: 智能跳过
python app.py /path/to/directory -f                 # 强制覆盖
python app.py /path/to/directory --no-skip          # 全部重传
python app.py /path/to/directory -d "Backup" -f     # 自定义目录 + 覆盖
python app.py --qr                                  # 强制扫码登录
python app.py --qr /path/to/file                    # 扫码登录 + 直接上传
```

## 📝 Logging System | 日志系统

All program activities are logged to three directories under `logs/`:

| Directory | Content | 内容 |
|-----------|---------|------|
| `logs/commands/` | User input commands and parsed results | 用户输入命令和解析结果 |
| `logs/runtime/` | Program events (startup, login, upload, download) | 程序事件（启动、登录、上传、下载） |
| `logs/errors/` | Error events and program exits | 错误事件和程序退出 |

Log files are named by date: `command_2026-07-05.log`, `runtime_2026-07-05.log`, `error_2026-07-05.log`

## 🏗 Architecture | 项目架构

```
123pan-uploader-cli/
├── app.py                          # 主入口 — CLI解析 + 交互模式 + 登录管理
├── tosasitill_123pan/
│   ├── class123.py                 # API客户端 — 登录/Token验证/文件列表/上传/下载
│   └── config.py                   # 配置中心 — API端点URL + 超时/分片/日志参数
├── utils/
│   ├── mpush.py                    # 上传引擎 — MD5去重 + S3分片上传 + 并发
│   ├── mget.py                     # 下载引擎 — 多线程分块下载
│   ├── command_handler.py          # 命令解析 — 路径/标志分离 + argparse集成
│   ├── input_handler.py            # 输入处理 — readline配置 + 路径补全
│   ├── qr_login.py                 # 扫码登录 — QR生成 + 轮询 + Token获取
│   ├── logger.py                   # 日志系统 — 命令/运行/错误三类日志
│   └── get-token.py                # Token工具 — 独立获取并保存登录凭据
├── logs/                           # 日志目录（自动生成）
│   ├── commands/                   # 命令日志
│   ├── runtime/                    # 运行日志
│   └── errors/                     # 错误日志
├── requirements.txt
├── 123pan.txt                      # 凭据文件（自动生成，勿提交）
├── qrcode.txt                      # 二维码文件（扫码登录时生成）
└── qrcode.png                      # 二维码图片（扫码登录时生成）
```

### API Authentication | API 鉴权流程

```
方式1: 账号/密码 → POST user.123pan.cn/api/user/sign_in (JSON)
                        ↓
                 返回 Bearer Token (code=200)
                        ↓
              保存至 123pan.txt + 后续请求 Authorization 头

方式2: 微信扫码 → GET /api/user/qr-code/generate → 生成二维码
                        ↓
              用户微信扫码 + 授权 → POST /api/user/qr-code/wx_code
                        ↓
              获取 wechat_code → POST /api/user/sign_in (type=4)
                        ↓
              返回 Bearer Token (code=200) → 保存至 123pan.txt
```

> **Note**: 2026-07-03 起，123云盘已废弃旧的请求签名（`getSign`）机制，所有 API 调用仅需 Bearer Token 鉴权。

## 🙏 Credits | 致谢

Based on [tosasitill/123pan](https://github.com/tosasitill/123pan) - Provides core authentication and API functionality.

基于 [tosasitill/123pan](https://github.com/tosasitill/123pan) - 提供核心认证和API功能。

---

## 📋 Changelog | 更新日志

### [2026-07-05] — QR Code Login & Logging System | 扫码登录与日志系统

> **重大更新**: 新增微信扫码登录功能，无需账号密码即可通过微信扫码获取 Token。同时新增完整的日志系统和 Token 自动恢复机制。

#### ✨ New Features | 新功能

##### 🔐 QR Code Login | 扫码登录
- **WeChat QR scan login** — 使用微信或123云盘App扫码登录，无需输入账号密码
  - `--qr` / `--qrcode` 命令行参数强制使用扫码登录
  - 二维码自动保存到 `qrcode.txt`（ASCII码）和 `qrcode.png`（图片）
  - 终端实时显示扫码状态（等待/已扫码/已确认/过期）
  - 扫码后 0.5s 高频轮询获取 `wechat_code`，防止二维码过期
  - QR URL 包含 `env=production` 参数，确保微信页面正确调用扫码API
- **No-credentials login prompt** — 首次运行无 `123pan.txt` 时提示选择登录方式（账密/扫码）

##### 🔑 Token Auto-Recovery | Token自动恢复
- **Smart token verification** — 程序启动时自动验证已保存的 Token
- **Password re-login** — Token 过期时，如保存了账号密码则自动重新登录（尝试一次）
- **Graceful exit on failure** — Token 无效且无账密（扫码登录）或重登失败时，打印日志并退出程序

##### 📝 Logging System | 日志系统
- **Three log types** — 命令日志、运行日志、错误日志分别保存在 `logs/` 下的三个子目录
  - `logs/commands/` — 用户输入的每条命令及解析结果
  - `logs/runtime/` — 程序启动、登录、上传、下载等运行事件
  - `logs/errors/` — 登录失败、异常崩溃等错误事件和程序退出
- 日志文件按日期命名，带时间戳，同时输出到终端

#### 🔧 Technical Details | 技术细节
- QR code login flow reverse-engineered from 123Pan web client (`wx-app-login.html`)
- `envConfig` in `v2-pay.js` maps `env=production` to `https://api.123278.com/api/` API host
- Scan notification via `POST /user/qr-code/scan` (called by WeChat page, not by CLI)
- `wechat_code` obtained via `POST /api/user/qr-code/wx_code`, used for `POST /api/user/sign_in` with `type=4`
- Fast polling (0.5s) after scan detection to prevent QR expiry before `wechat_code` is available
- `login_with_wechat_code` accepts both `code=0` and `code=200` for compatibility

#### 📖 Documentation | 文档更新
- README 新增「登录方式」章节，详细说明三种登录方法和 Token 恢复流程
- README 新增「日志系统」章节
- README 命令行参数表新增 `--qr` / `--qrcode`
- 架构图新增 `qr_login.py`、`logger.py`、`logs/` 目录
- 所有脚本签名和注释全面更新

---

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

## ⚠️ Disclaimer | 免责声明

**This project is for personal use only and is not affiliated with 123Pan Cloud. Please comply with 123Pan Cloud's terms of service.**

**本项目仅供个人使用，与123云盘官方无关。请遵守123云盘的服务条款。**

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

</div>
