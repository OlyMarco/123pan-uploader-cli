#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from tosasitill_123pan import config


def _validate_output_path(output_path):
    """Validate and prepare the output path for download.

    Args:
        output_path: Desired output path

    Returns:
        str: Validated output path

    Raises:
        ValueError: If path is invalid or dangerous
    """
    output_path = output_path.strip()

    if not output_path:
        raise ValueError("Output path cannot be empty")

    normalized = os.path.normpath(output_path)

    if os.path.isdir(normalized):
        raise ValueError(f"Output path '{normalized}' is a directory, not a file. Please specify a filename.")

    parent_dir = os.path.dirname(normalized)
    if parent_dir and not os.path.exists(parent_dir):
        raise ValueError(f"Output directory '{parent_dir}' does not exist. Please create it first or use a different path.")

    if os.path.exists(normalized):
        response = input(f"File '{normalized}' already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            raise ValueError("Download cancelled by user")

    abs_path = os.path.abspath(normalized)
    return abs_path


class MGet:
    """Multi-threaded file downloader with single thread fallback option"""

    def __init__(self, default_threads=8):
        """Initialize MGet downloader with configurable thread count"""
        self.default_threads = default_threads

    def get_file_size(self, url):
        """Get file size using HEAD request"""
        try:
            response = requests.head(url, timeout=config.TIMEOUT_SHORT)
            file_size = int(response.headers.get("content-length", 0))
            return file_size
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to get file size: {e}")

    def download_single_thread(self, url, output_path):
        """Download file using single thread approach"""
        start_time = time.time()

        try:
            response = requests.get(url, stream=True, timeout=config.TIMEOUT_LONG)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Single-thread download failed: {e}")
            return None

        file_size = int(response.headers.get("content-length", 0))
        print(f"Single thread download - File size: {file_size/1024/1024:.2f} MB")

        progress_bar = tqdm(
            total=file_size, unit="B", unit_scale=True, desc="Single thread"
        )

        downloaded_size = 0
        try:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
                        downloaded_size += len(chunk)
        except IOError as e:
            progress_bar.close()
            print(f"Write error: {e}")
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            return None

        progress_bar.close()
        elapsed_time = time.time() - start_time
        print(f"Single thread download completed in {elapsed_time:.2f} seconds")
        return elapsed_time

    def download_chunk(self, args):
        """Download specific byte range of a file"""
        url, start, end, output_path, chunk_id = args
        headers = {"Range": f"bytes={start}-{end}"}
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=config.TIMEOUT_LONG)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Chunk {chunk_id} download failed: {e}")

        chunk_path = f"{output_path}.part{chunk_id}"
        try:
            with open(chunk_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except IOError as e:
            if os.path.exists(chunk_path):
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass
            raise IOError(f"Failed to write chunk {chunk_id}: {e}")

        return chunk_path, chunk_id, end - start + 1

    def download_multi_thread(self, url, output_path, num_threads=None):
        """Download file using multiple parallel threads"""
        if num_threads is None:
            num_threads = self.default_threads

        start_time = time.time()
        chunk_files = []

        try:
            file_size = self.get_file_size(url)
        except ConnectionError as e:
            print(f"Multi-thread download failed: {e}")
            return None

        print(
            f"Multi-thread download - File size: {file_size/1024/1024:.2f} MB, Threads: {num_threads}"
        )

        chunk_size = file_size // num_threads
        chunks = []
        for i in range(num_threads):
            start_byte = i * chunk_size
            end_byte = (
                start_byte + chunk_size - 1 if i < num_threads - 1 else file_size - 1
            )
            chunks.append((url, start_byte, end_byte, output_path, i))

        progress_bar = tqdm(
            total=file_size, unit="B", unit_scale=True, desc="Multi-thread"
        )
        downloaded = 0
        failed = False

        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                for chunk_path, _, size in executor.map(self.download_chunk, chunks):
                    chunk_files.append(chunk_path)
                    downloaded += size
                    progress_bar.update(size)
        except (ConnectionError, IOError) as e:
            print(f"\nMulti-thread download failed: {e}")
            failed = True

        progress_bar.close()

        if failed:
            for cf in chunk_files:
                try:
                    os.remove(cf)
                except OSError:
                    pass
            return None

        try:
            with open(output_path, "wb") as output_file:
                for i in range(num_threads):
                    chunk_path = f"{output_path}.part{i}"
                    try:
                        with open(chunk_path, "rb") as chunk_file:
                            output_file.write(chunk_file.read())
                    finally:
                        try:
                            os.remove(chunk_path)
                        except OSError:
                            pass
        except IOError as e:
            print(f"Failed to combine chunks: {e}")
            for cf in chunk_files:
                try:
                    os.remove(cf)
                except OSError:
                    pass
            return None

        elapsed_time = time.time() - start_time
        print(f"Multi-thread download completed in {elapsed_time:.2f} seconds")
        return elapsed_time

    def download(self, url, output_path, num_threads=None, force_single=False):
        """Intelligently select download mode based on parameters (with path validation)"""
        validated_path = _validate_output_path(output_path)
        return self._download_raw(url, validated_path, num_threads, force_single)

    def _download_raw(self, url, output_path, num_threads=None, force_single=False):
        """Internal download logic without path validation (for use when path already validated)"""
        if force_single:
            return self.download_single_thread(url, output_path)
        else:
            if num_threads is None:
                num_threads = self.default_threads
            return self.download_multi_thread(url, output_path, num_threads)


def download_single_thread(url, output_path):
    """Single thread download"""
    downloader = MGet()
    return downloader.download_single_thread(url, output_path)


def download_multi_thread(url, output_path, num_threads=8):
    """Multi-thread download"""
    downloader = MGet()
    return downloader.download_multi_thread(url, output_path, num_threads)


def main():
    """Command line interface for MGet downloader"""
    parser = argparse.ArgumentParser(
        description="File Downloader - Single and Multi-threaded"
    )
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument(
        "-o", "--output", help="Output file path", default="downloaded_file"
    )
    parser.add_argument(
        "-t", "--threads", type=int, help="Number of threads", default=8
    )
    parser.add_argument(
        "-s", "--single", action="store_true", help="Use single-threaded download"
    )
    args = parser.parse_args()

    downloader = MGet(default_threads=args.threads)

    print(f"Starting download: {args.url}")

    if args.single:
        print("Using single-threaded mode")
        single_time = downloader.download_single_thread(args.url, args.output)
        if single_time is not None:
            print(f"Download complete, elapsed time: {single_time:.2f} seconds")
    else:
        print(f"Using multi-threaded mode (threads: {args.threads})")
        multi_time = downloader.download_multi_thread(args.url, args.output, args.threads)

        if multi_time is not None and args.output.endswith("_multi"):
            single_output = f"{args.output[:-6]}_single"
            print("\nRunning single-thread comparison test...")
            single_time = downloader.download_single_thread(args.url, single_output)

            if single_time:
                speedup = single_time / multi_time if multi_time > 0 else 0
                print("\n" + "=" * 50)
                print(f"Performance comparison:")
                print(f"Single-thread: {single_time:.2f} seconds")
                print(f"Multi-thread: {multi_time:.2f} seconds")
                print(f"Speedup: {speedup:.2f}x")
                print("=" * 50)

                single_size = os.path.getsize(single_output)
                multi_size = os.path.getsize(args.output)
                if single_size == multi_size:
                    print(
                        f"File size verification successful: {single_size/1024/1024:.2f} MB"
                    )
                else:
                    print(
                        f"Warning: File size mismatch! Single: {single_size/1024/1024:.2f} MB, Multi: {multi_size/1024/1024:.2f} MB"
                    )


if __name__ == "__main__":
    main()
