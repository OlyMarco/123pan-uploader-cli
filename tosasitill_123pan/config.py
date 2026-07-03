#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Centralized API URL and configuration constants for 123Pan
# Updated: 2026-07-03 — migrated to new API architecture (user.123pan.cn)

# Base URLs
BASE_URL = "https://www.123pan.cn"
LOGIN_URL = "https://user.123pan.cn"

# Auth endpoint (new: user.123pan.cn, JSON body, no signature required)
URL_SIGN_IN = f"{LOGIN_URL}/api/user/sign_in"

# File operation endpoints (Bearer Token auth, no signature required)
URL_FILE_LIST = f"{BASE_URL}/b/api/file/list/new"
URL_UPLOAD_REQUEST = f"{BASE_URL}/b/api/file/upload_request"
URL_S3_PREPARE_PARTS = f"{BASE_URL}/b/api/file/s3_repare_upload_parts_batch"
URL_S3_LIST_PARTS = f"{BASE_URL}/b/api/file/s3_list_upload_parts"
URL_S3_COMPLETE_MULTIPART = f"{BASE_URL}/b/api/file/s3_complete_multipart_upload"
URL_UPLOAD_COMPLETE = f"{BASE_URL}/b/api/file/upload_complete"
URL_BATCH_DOWNLOAD_INFO = f"{BASE_URL}/a/api/file/batch_download_info"
URL_DOWNLOAD_INFO = f"{BASE_URL}/a/api/file/download_info"
URL_FILE_TRASH = f"{BASE_URL}/a/api/file/trash"
URL_SHARE_CREATE = f"{BASE_URL}/a/api/share/create"

# HTTP request timeouts (seconds)
TIMEOUT_SHORT = 10      # Quick API calls (sign-in, mkdir, etc.)
TIMEOUT_MEDIUM = 30      # Normal API calls (file list, upload request, etc.)
TIMEOUT_LONG = 60        # Large file operations (download, multipart finalize, etc.)
TIMEOUT_UPLOAD_PART = 30 # Each upload chunk to presigned URL

# Config file
CREDENTIALS_FILE = "123pan.txt"
HISTORY_FILE = "~/.123pan_history"

# Upload defaults
DEFAULT_BLOCK_SIZE = 5 * 1024 * 1024  # 5MB chunks
DEFAULT_MAX_WORKERS = 5                # Concurrent upload threads

# Download defaults
DEFAULT_DOWNLOAD_THREADS = 8
