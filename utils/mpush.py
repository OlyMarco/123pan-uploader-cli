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
        if parent_id is not None and self.pan.parentFileId != parent_id:
            self.pan.cdById(parent_id)
        
        # Refresh directory listing
        self.pan.get_dir()
        
        for file_info in self.pan.list:
            if file_info["FileName"] == file_name and file_info["Type"] == 0:
                # Found file with same name, compare MD5 (Etag is the MD5)
                remote_md5 = file_info.get("Etag", "").lower()
                if remote_md5 == local_md5.lower():
                    return True
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

        # Check if file already exists with same MD5 (skip duplicate)
        if skip_existing:
            if self.check_file_exists_with_md5(file_name, md5, parent_id):
                tqdm.write(f"Skipped (same MD5 exists): {file_name}")
                result['success'] = True
                result['skipped'] = True
                return result

        # First check if file with same name exists and handle accordingly
        if sure == "2":  # If overwrite is pre-selected
            # Get current directory files
            self.pan.get_dir()
            # Find file with same name and delete it
            for i, file_info in enumerate(self.pan.list):
                if file_info["FileName"] == file_name and file_info["Type"] == 0:
                    tqdm.write(f"Deleting existing file: {file_name}")
                    # Use file index to delete (by_num=True)
                    self.pan.delete_file(i, by_num=True, operation=True)
                    # Refresh directory listing
                    self.pan.get_dir()
                    break

        # Prepare upload request payload
        list_up_request = {
            "driveId": 0,
            "etag": md5,
            "fileName": file_name,
            "parentFileId": parent_id,
            "size": file_size,
            "type": 0,
            "duplicate": 0,
        }

        # Sign and send upload request
        sign = getSign("/b/api/file/upload_request")
        up_res = requests.post(
            "https://www.123pan.com/b/api/file/upload_request",
            headers=self.pan.headerLogined,
            params={sign[0]: sign[1]},
            data=json.dumps(list_up_request),
        )

        up_res_json = up_res.json()
        code = up_res_json.get("code")

        # Handle duplicate file detection (code 5060)
        if code == 5060:
            tqdm.write("Duplicate file detected")
            if sure not in ["1", "2"]:
                sure = input(
                    "Duplicate file detected. Enter 1 to keep both, 2 to overwrite, 0 to cancel: "
                )

            if sure == "1":
                list_up_request["duplicate"] = 1
            elif sure == "2":
                # Delete the existing file and retry
                self.pan.get_dir()
                for i, file_info in enumerate(self.pan.list):
                    if file_info["FileName"] == file_name and file_info["Type"] == 0:
                        tqdm.write(f"Deleting existing file: {file_name}")
                        self.pan.delete_file(i, by_num=True, operation=True)
                        # Refresh directory listing after deletion
                        self.pan.get_dir()
                        break

                # Now overwrite by setting duplicate=2
                list_up_request["duplicate"] = 2
            else:
                tqdm.write("Upload cancelled")
                return result

            sign = getSign("/b/api/file/upload_request")
            up_res = requests.post(
                "https://www.123pan.com/b/api/file/upload_request",
                headers=self.pan.headerLogined,
                params={sign[0]: sign[1]},
                data=json.dumps(list_up_request),
            )
            up_res_json = up_res.json()
            code = up_res_json.get("code")

        # Check upload request response
        if code == 0:
            reuse = up_res_json["data"].get("Reuse")
            if reuse:
                tqdm.write(f"Upload successful, file MD5 reused: {file_name}")
                result['success'] = True
                return result
        else:
            tqdm.write(f"Upload request failed: {up_res_json}")
            return result

        # Extract upload parameters from response
        bucket = up_res_json["data"]["Bucket"]
        storage_node = up_res_json["data"]["StorageNode"]
        upload_key = up_res_json["data"]["Key"]
        upload_id = up_res_json["data"]["UploadId"]
        up_file_id = up_res_json["data"]["FileId"]

        # Initialize multipart upload session
        start_data = {
            "bucket": bucket,
            "key": upload_key,
            "uploadId": upload_id,
            "storageNode": storage_node,
        }

        start_res = requests.post(
            "https://www.123pan.com/b/api/file/s3_list_upload_parts",
            headers=self.pan.headerLogined,
            data=json.dumps(start_data),
        )

        start_res_json = start_res.json()
        if start_res_json["code"] != 0:
            tqdm.write(f"Failed to get transfer list: {start_res_json}")
            return result

        # Upload file in chunks (5MB per chunk)
        block_size = 5242880  # 5MB
        part_number_start = 1

        with open(file_path, "rb") as f, tqdm(
            total=file_size, unit="B", unit_scale=True, desc=file_name, position=1, leave=False
        ) as pbar:
            while True:
                data = f.read(block_size)
                if not data:
                    break

                # Request presigned URL for this chunk
                get_link_data = {
                    "bucket": bucket,
                    "key": upload_key,
                    "partNumberEnd": part_number_start + 1,
                    "partNumberStart": part_number_start,
                    "uploadId": upload_id,
                    "StorageNode": storage_node,
                }

                get_link_res = requests.post(
                    "https://www.123pan.com/b/api/file/s3_repare_upload_parts_batch",
                    headers=self.pan.headerLogined,
                    data=json.dumps(get_link_data),
                )

                get_link_res_json = get_link_res.json()
                if get_link_res_json["code"] != 0:
                    tqdm.write(f"Failed to get upload link: {get_link_res_json}")
                    return result

                # Upload chunk to presigned URL
                upload_url = get_link_res_json["data"]["presignedUrls"][
                    str(part_number_start)
                ]
                requests.put(upload_url, data=data)

                pbar.update(len(data))
                part_number_start += 1

        tqdm.write("Chunk upload complete, finalizing...")

        # Finalize multipart upload
        uploaded_list_url = "https://www.123pan.com/b/api/file/s3_list_upload_parts"
        uploaded_comp_data = {
            "bucket": bucket,
            "key": upload_key,
            "uploadId": upload_id,
            "storageNode": storage_node,
        }

        requests.post(
            uploaded_list_url,
            headers=self.pan.headerLogined,
            data=json.dumps(uploaded_comp_data),
        )

        # Complete multipart upload
        comp_multipart_up_url = (
            "https://www.123pan.com/b/api/file/s3_complete_multipart_upload"
        )
        requests.post(
            comp_multipart_up_url,
            headers=self.pan.headerLogined,
            data=json.dumps(uploaded_comp_data),
        )

        # Wait for large files to be processed
        if file_size > 64 * 1024 * 1024:
            time.sleep(3)

        # Close upload session
        close_up_session_url = "https://www.123pan.com/b/api/file/upload_complete"
        close_up_session_data = {"fileId": up_file_id}

        close_up_session_res = requests.post(
            close_up_session_url,
            headers=self.pan.headerLogined,
            data=json.dumps(close_up_session_data),
        )

        close_res_json = close_up_session_res.json()
        if close_res_json["code"] == 0:
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

        # Create root directory in 123Pan
        folder_id = self.pan.mkdir(dir_name, parent_id, remake=False)
        if not folder_id:
            print(f"Failed to create directory {dir_name}")
            return False

        print(f"Directory created: {dir_name}, ID: {folder_id}")

        # Directory ID mapping (local path -> remote folder ID)
        mkdir_list = {dir_path: folder_id}

        # Directories to skip during traversal
        skip_dirs = ["venv", ".idea", "__pycache__", ".git", "node_modules"]

        # Collect all files to upload for progress tracking
        files_to_upload = []
        
        # First pass: create directory structure and collect files
        for filepath, dirnames, filenames in os.walk(dir_path):
            # Skip specific directories
            if any(skip_dir in filepath for skip_dir in skip_dirs):
                continue

            # Create remote folders for subdirectories
            parent_path = os.path.dirname(filepath)
            if parent_path in mkdir_list and filepath != dir_path:
                sub_dir_name = os.path.basename(filepath)
                parent_folder_id = mkdir_list[parent_path]
                sub_folder_id = self.pan.mkdir(sub_dir_name, parent_folder_id, remake=False)
                time.sleep(0.2)  # Rate limiting to avoid API throttling
                mkdir_list[filepath] = sub_folder_id
                tqdm.write(f"Created directory: {sub_dir_name}, ID: {sub_folder_id}")

            # Collect files for upload
            if filepath in mkdir_list:
                current_folder_id = mkdir_list[filepath]
                for filename in filenames:
                    # Filter by file type if specified
                    if file_types:
                        if not any(filename.endswith(ft) for ft in file_types):
                            continue
                    file_path = os.path.join(filepath, filename)
                    files_to_upload.append((file_path, current_folder_id))

        # Statistics tracking
        total_files = len(files_to_upload)
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0

        # Upload files with overall progress bar
        with tqdm(total=total_files, desc="Overall Progress", position=0, unit="file") as overall_pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all upload tasks
                future_to_file = {
                    executor.submit(
                        self.upload_file, file_path, folder_id, sure, skip_existing
                    ): file_path
                    for file_path, folder_id in files_to_upload
                }
                
                # Process completed uploads
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
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
                        tqdm.write(f"Error uploading {file_path}: {str(e)}")
                        failed_count += 1
                    
                    overall_pbar.update(1)
                    overall_pbar.set_postfix(
                        uploaded=uploaded_count, 
                        skipped=skipped_count, 
                        failed=failed_count
                    )

        # Print summary
        print(f"\nDirectory upload completed")
        print(f"  Total files: {total_files}")
        print(f"  Uploaded: {uploaded_count}")
        print(f"  Skipped (same MD5): {skipped_count}")
        print(f"  Failed: {failed_count}")
        
        return failed_count == 0
