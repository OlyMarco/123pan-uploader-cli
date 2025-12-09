#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


class MGet:
    """Multi-threaded file downloader with single thread fallback option"""

    def __init__(self, default_threads=8):
        """Initialize MGet downloader with configurable thread count"""
        self.default_threads = default_threads

    def get_file_size(self, url):
        """Get file size using HEAD request"""
        response = requests.head(url)
        file_size = int(response.headers.get("content-length", 0))
        return file_size

    def download_single_thread(self, url, output_path):
        """Download file using single thread approach"""
        start_time = time.time()

        response = requests.get(url, stream=True)
        file_size = int(response.headers.get("content-length", 0))

        print(f"Single thread download - File size: {file_size/1024/1024:.2f} MB")

        progress_bar = tqdm(
            total=file_size, unit="B", unit_scale=True, desc="Single thread"
        )

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))

        progress_bar.close()
        elapsed_time = time.time() - start_time
        print(f"Single thread download completed in {elapsed_time:.2f} seconds")
        return elapsed_time

    def download_chunk(self, args):
        """Download specific byte range of a file"""
        url, start, end, output_path, chunk_id = args
        headers = {"Range": f"bytes={start}-{end}"}
        response = requests.get(url, headers=headers, stream=True)

        chunk_path = f"{output_path}.part{chunk_id}"
        with open(chunk_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return chunk_path, chunk_id, end - start + 1

    def download_multi_thread(self, url, output_path, num_threads=None):
        """Download file using multiple parallel threads"""
        if num_threads is None:
            num_threads = self.default_threads

        start_time = time.time()

        file_size = self.get_file_size(url)
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

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            chunk_files = []
            for chunk_path, _, size in executor.map(self.download_chunk, chunks):
                chunk_files.append(chunk_path)
                downloaded += size
                progress_bar.update(size)

        progress_bar.close()

        # Combine chunks into final file
        with open(output_path, "wb") as output_file:
            for i in range(num_threads):
                chunk_path = f"{output_path}.part{i}"
                with open(chunk_path, "rb") as chunk_file:
                    output_file.write(chunk_file.read())
                os.remove(chunk_path)

        elapsed_time = time.time() - start_time
        print(f"Multi-thread download completed in {elapsed_time:.2f} seconds")
        return elapsed_time

    def download(self, url, output_path, num_threads=None, force_single=False):
        """Intelligently select download mode based on parameters"""
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
        print(f"Download complete, elapsed time: {single_time:.2f} seconds")
    else:
        print(f"Using multi-threaded mode (threads: {args.threads})")
        multi_time = downloader.download_multi_thread(
            args.url, args.output, args.threads
        )

        # Optional: Compare with single thread performance
        if args.output.endswith("_multi"):
            single_output = f"{args.output[:-6]}_single"
            print("\nRunning single-thread comparison test...")
            single_time = downloader.download_single_thread(args.url, single_output)

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
