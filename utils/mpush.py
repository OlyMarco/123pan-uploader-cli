#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import hashlib
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from tosasitill_123pan.sign_get import getSign
from tosasitill_123pan import config


def format_size(size_bytes):
    """Convert bytes to human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Human-readable size string (e.g., '1.50 MB')
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"


class MPush:
    """Upload handler for 123Pan Cloud Storage

    This class provides methods to upload files and directories to 123Pan Cloud.
    Features:
    - Single file upload with progress bar
    - Directory upload with concurrent threads
    - MD5-based duplicate detection and skip
    - Resumable chunk uploads for large files
    """

    def __init__(self, pan):
        """Initialize MPush with an authenticated Pan123 instance

        Args:
            pan: Authenticated Pan123 instance for API calls
        """
        self.pan = pan

    @staticmethod
    def compute_file_md5(file_path):
        """Calculate MD5 hash of a file using chunked reading

        Args:
            file_path: Path to the file to hash

        Returns:
            str: Hexadecimal MD5 hash string
        """
        with open(file_path, "rb") as f:
            md5 = hashlib.md5()
            for chunk in iter(lambda: f.read(64 * 1024), b""):
                md5.update(chunk)
            return md5.hexdigest()

    def check_file_exists_with_md5(self, file_name, local_md5, parent_id=None):
        """Check if a file with same name and MD5 already exists in the target directory

        Args:
            file_name: Name of the file to check
            local_md5: MD5 hash of the local file
            parent_id: Parent folder ID to check in (None for current directory)

        Returns:
            bool: True if file exists with same MD5, False otherwise
        """
        try:
            if parent_id is not None and self.pan.parentFileId != parent_id:
                self.pan.cdById(parent_id)

            if self.pan.list is None:
                return False

            for file_info in self.pan.list:
                if file_info["FileName"] == file_name and file_info["Type"] == 0:
                    remote_md5 = file_info.get("Etag", "").lower()
                    if remote_md5 and remote_md5 == local_md5.lower():
                        return True
            return False
        except Exception as e:
            tqdm.write(f"Warning: Could not check for existing file: {e}")
            return False

    def upload_file(self, file_path, parent_id=None, sure=None, skip_existing=True):
        """Upload a single file to 123Pan Cloud

        Args:
            file_path: Path to the file to upload
            parent_id: Parent folder ID (None for current directory)
            sure: Duplicate handling strategy - "1":keep both, "2":overwrite
            skip_existing: If True, skip files that already exist with same MD5 (default: True)

        Returns:
            dict: Upload result with 'success', 'skipped', 'file_name' keys
        """
        result = {'success': False, 'skipped': False, 'file_name': ''}

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            tqdm.write(f"Error: {file_path} is not a valid file")
            return result

        file_path = file_path.replace('"', "").replace("\\", "/")
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        result['file_name'] = file_name

        tqdm.write(f"Preparing to upload: {file_name} ({format_size(file_size)})")

        tqdm.write("Calculating file MD5...")
        md5 = self.compute_file_md5(file_path)

        if parent_id is None:
            parent_id = self.pan.parentFileId

        if skip_existing:
            if self.check_file_exists_with_md5(file_name, md5, parent_id):
                tqdm.write(f"Skipped (same MD5 exists): {file_name}")
                result['success'] = True
                result['skipped'] = True
                return result

        if sure == "2":
            self.pan.get_dir()
            for i, file_info in enumerate(self.pan.list):
                if file_info["FileName"] == file_name and file_info["Type"] == 0:
                    tqdm.write(f"Deleting existing file: {file_name}")
                    self.pan.delete_file(i, by_num=True, operation=True)
                    self.pan.get_dir()
                    break

        list_up_request = {
            "driveId": 0,
            "etag": md5,
            "fileName": file_name,
            "parentFileId": parent_id,
            "size": file_size,
            "type": 0,
            "duplicate": 0,
        }

        sign = getSign("/b/api/file/upload_request")
        try:
            up_res = requests.post(
                config.URL_UPLOAD_REQUEST,
                headers=self.pan.headerLogined,
                params={sign[0]: sign[1]},
                json=list_up_request,
                timeout=config.TIMEOUT_MEDIUM
            )
            up_res_json = up_res.json()
        except requests.exceptions.RequestException as e:
            tqdm.write(f"Upload request failed: {e}")
            return result
        except ValueError as e:
            tqdm.write(f"Upload request parse failed: {e}")
            return result

        code = up_res_json.get("code")

        if code == 5060:
            tqdm.write("Duplicate file detected")
            if sure not in ["1", "2"]:
                sure = input(
                    "Duplicate file detected. Enter 1 to keep both, 2 to overwrite, 0 to cancel: "
                )

            if sure == "1":
                list_up_request["duplicate"] = 1
            elif sure == "2":
                self.pan.get_dir()
                for i, file_info in enumerate(self.pan.list):
                    if file_info["FileName"] == file_name and file_info["Type"] == 0:
                        tqdm.write(f"Deleting existing file: {file_name}")
                        self.pan.delete_file(i, by_num=True, operation=True)
                        self.pan.get_dir()
                        break
                list_up_request["duplicate"] = 2
            else:
                tqdm.write("Upload cancelled")
                return result

            sign = getSign("/b/api/file/upload_request")
            try:
                up_res = requests.post(
                    config.URL_UPLOAD_REQUEST,
                    headers=self.pan.headerLogined,
                    params={sign[0]: sign[1]},
                    json=list_up_request,
                    timeout=config.TIMEOUT_MEDIUM
                )
                up_res_json = up_res.json()
            except requests.exceptions.RequestException as e:
                tqdm.write(f"Upload request failed after duplicate handling: {e}")
                return result
            except ValueError as e:
                tqdm.write(f"Upload request parse failed: {e}")
                return result
            code = up_res_json.get("code")

        if code == 0:
            reuse = up_res_json["data"].get("Reuse")
            if reuse:
                tqdm.write(f"Upload successful, file MD5 reused: {file_name}")
                result['success'] = True
                return result
        else:
            tqdm.write(f"Upload request failed: {up_res_json}")
            return result

        bucket = up_res_json["data"]["Bucket"]
        storage_node = up_res_json["data"]["StorageNode"]
        upload_key = up_res_json["data"]["Key"]
        upload_id = up_res_json["data"]["UploadId"]
        up_file_id = up_res_json["data"]["FileId"]

        start_data = {
            "bucket": bucket,
            "key": upload_key,
            "uploadId": upload_id,
            "storageNode": storage_node,
        }

        try:
            start_res = requests.post(
                config.URL_S3_LIST_PARTS,
                headers=self.pan.headerLogined,
                json=start_data,
                timeout=config.TIMEOUT_MEDIUM
            )
            start_res_json = start_res.json()
        except requests.exceptions.RequestException as e:
            tqdm.write(f"Failed to get transfer list: {e}")
            return result
        except ValueError as e:
            tqdm.write(f"Failed to parse transfer list response: {e}")
            return result

        if start_res_json.get("code") != 0:
            tqdm.write(f"Failed to get transfer list: {start_res_json}")
            return result

        block_size = config.DEFAULT_BLOCK_SIZE
        part_number_start = 1

        with open(file_path, "rb") as f, tqdm(
            total=file_size, unit="B", unit_scale=True, desc=file_name, position=1, leave=False
        ) as pbar:
            while True:
                data = f.read(block_size)
                if not data:
                    break

                get_link_data = {
                    "bucket": bucket,
                    "key": upload_key,
                    "partNumberEnd": part_number_start + 1,
                    "partNumberStart": part_number_start,
                    "uploadId": upload_id,
                    "StorageNode": storage_node,
                }

                try:
                    get_link_res = requests.post(
                        config.URL_S3_PREPARE_PARTS,
                        headers=self.pan.headerLogined,
                        json=get_link_data,
                        timeout=config.TIMEOUT_MEDIUM
                    )
                    get_link_res_json = get_link_res.json()
                except requests.exceptions.RequestException as e:
                    tqdm.write(f"Failed to get upload link: {e}")
                    return result
                except ValueError as e:
                    tqdm.write(f"Failed to parse upload link response: {e}")
                    return result

                if get_link_res_json.get("code") != 0:
                    tqdm.write(f"Failed to get upload link: {get_link_res_json}")
                    return result

                upload_url = get_link_res_json["data"]["presignedUrls"][
                    str(part_number_start)
                ]
                try:
                    put_res = requests.put(upload_url, data=data, timeout=config.TIMEOUT_UPLOAD_PART)
                    put_res.raise_for_status()
                except requests.exceptions.RequestException as e:
                    tqdm.write(f"Chunk upload failed: {e}")
                    return result

                pbar.update(len(data))
                part_number_start += 1

        tqdm.write("Chunk upload complete, finalizing...")

        uploaded_comp_data = {
            "bucket": bucket,
            "key": upload_key,
            "uploadId": upload_id,
            "storageNode": storage_node,
        }

        try:
            list_parts_res = requests.post(
                config.URL_S3_LIST_PARTS,
                headers=self.pan.headerLogined,
                json=uploaded_comp_data,
                timeout=config.TIMEOUT_MEDIUM
            )
            list_parts_json = list_parts_res.json()
        except requests.exceptions.RequestException as e:
            tqdm.write(f"Failed to list uploaded parts: {e}")
            return result
        except ValueError as e:
            tqdm.write(f"Failed to parse parts list response: {e}")
            return result

        if list_parts_json.get("code") != 0:
            tqdm.write(f"s3_list_upload_parts failed: {list_parts_json}")
            return result

        try:
            comp_res = requests.post(
                config.URL_S3_COMPLETE_MULTIPART,
                headers=self.pan.headerLogined,
                json=uploaded_comp_data,
                timeout=config.TIMEOUT_LONG
            )
            comp_json = comp_res.json()
        except requests.exceptions.RequestException as e:
            tqdm.write(f"Failed to complete multipart upload: {e}")
            return result
        except ValueError as e:
            tqdm.write(f"Failed to parse complete response: {e}")
            return result

        if comp_json.get("code") != 0:
            tqdm.write(f"s3_complete_multipart_upload failed: {comp_json}")
            return result

        if file_size > 64 * 1024 * 1024:
            time.sleep(3)

        close_up_session_data = {"fileId": up_file_id}

        try:
            close_up_session_res = requests.post(
                config.URL_UPLOAD_COMPLETE,
                headers=self.pan.headerLogined,
                json=close_up_session_data,
                timeout=config.TIMEOUT_MEDIUM
            )
            close_res_json = close_up_session_res.json()
        except requests.exceptions.RequestException as e:
            tqdm.write(f"Upload complete request failed: {e}")
            return result
        except ValueError as e:
            tqdm.write(f"Upload complete parse failed: {e}")
            return result

        if close_res_json.get("code") == 0:
            tqdm.write(f"Upload successful: {file_name}")
            result['success'] = True
            return result
        else:
            tqdm.write(f"Upload failed: {close_res_json}")
            return result

    def upload_directory_concurrent(
        self,
        dir_path,
        parent_id=None,
        max_workers=5,
        file_types=None,
        sure=None,
        custom_dirname=None,
        skip_existing=True,
    ):
        """Upload a directory to 123Pan Cloud using concurrent threads

        This method uploads an entire directory structure to 123Pan Cloud.
        It first creates the remote directory structure, then uploads files
        concurrently using a thread pool. Displays overall progress with tqdm.

        Args:
            dir_path: Local path to the directory to upload
            parent_id: Parent folder ID in 123Pan (None for current directory)
            max_workers: Maximum number of concurrent upload threads (default: 5)
            file_types: List of file extensions to include (e.g., ['.jpg', '.png'])
            sure: Duplicate handling strategy - "1":keep both, "2":overwrite
            custom_dirname: Custom name for the remote directory (default: use local name)
            skip_existing: If True, skip files that already exist with same MD5 (default: True)

        Returns:
            bool: True if upload successful, False otherwise
        """
        if not os.path.isdir(dir_path):
            print(f"Error: {dir_path} is not a valid directory")
            return False

        dir_path = dir_path.replace('"', "").replace("\\", "/")
        dir_name = custom_dirname if custom_dirname else os.path.basename(dir_path)

        print(f"Preparing to upload directory: {dir_name}")

        if parent_id is None:
            parent_id = self.pan.parentFileId

        folder_id = self.pan.mkdir(dir_name, parent_id, remake=False)
        if not folder_id:
            print(f"Failed to create directory {dir_name}")
            return False

        print(f"Directory created: {dir_name}, ID: {folder_id}")

        mkdir_list = {dir_path: folder_id}
        skip_dirs = ["venv", ".idea", "__pycache__", ".git", "node_modules"]

        files_to_upload = []

        for filepath, dirnames, filenames in os.walk(dir_path):
            if any(skip_dir in filepath for skip_dir in skip_dirs):
                continue

            parent_path = os.path.dirname(filepath)
            if parent_path in mkdir_list and filepath != dir_path:
                sub_dir_name = os.path.basename(filepath)
                parent_folder_id = mkdir_list[parent_path]
                sub_folder_id = self.pan.mkdir(sub_dir_name, parent_folder_id, remake=False)
                time.sleep(0.2)
                if sub_folder_id:
                    mkdir_list[filepath] = sub_folder_id
                    tqdm.write(f"Created directory: {sub_dir_name}, ID: {sub_folder_id}")

            if filepath in mkdir_list:
                current_folder_id = mkdir_list[filepath]
                for filename in filenames:
                    if file_types:
                        if not any(filename.endswith(ft) for ft in file_types):
                            continue
                    file_path = os.path.join(filepath, filename)
                    files_to_upload.append((file_path, current_folder_id))

        total_files = len(files_to_upload)
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0

        with tqdm(total=total_files, desc="Overall Progress", position=0, unit="file") as overall_pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for file_path, target_folder_id in files_to_upload:
                    # Capture target_folder_id at submission time (not late binding)
                    future = executor.submit(
                        self.upload_file, file_path, target_folder_id, sure, skip_existing
                    )
                    futures[future] = file_path

                for future in as_completed(futures):
                    file_path = futures[future]
                    try:
                        result = future.result()
                        if result.get('success'):
                            if result.get('skipped'):
                                skipped_count += 1
                            else:
                                uploaded_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        tqdm.write(f"Error uploading {file_path}: {e}")
                        failed_count += 1

                    overall_pbar.update(1)
                    overall_pbar.set_postfix(
                        uploaded=uploaded_count,
                        skipped=skipped_count,
                        failed=failed_count
                    )

        print(f"\nDirectory upload completed")
        print(f"  Total files: {total_files}")
        print(f"  Uploaded: {uploaded_count}")
        print(f"  Skipped (same MD5): {skipped_count}")
        print(f"  Failed: {failed_count}")

        return failed_count == 0
