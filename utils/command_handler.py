#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import shlex
from utils.input_handler import normalize_path


def create_argument_parser():
    """
    Create and configure the argument parser for upload commands.
    
    Returns:
        argparse.ArgumentParser: Configured parser for upload commands
    """
    parser = argparse.ArgumentParser(
        description="123Pan Uploader CLI",
        add_help=False  # Disable default help to avoid exit
    )
    
    parser.add_argument("path", nargs="?", help="Path to file or directory to upload")
    parser.add_argument("-d", "--dest", help="Destination name (default: same as source)")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files (delete and re-upload)")
    parser.add_argument("-k", "--keep", action="store_true", help="Keep both files on conflict")
    parser.add_argument("--no-skip", action="store_true", help="Don't skip existing files with same MD5")
    
    return parser


def parse_upload_command(user_input, default_sure_option, default_skip_existing):
    """
    Parse user input for upload command and extract parameters.
    
    Args:
        user_input: Raw user input string
        default_sure_option: Default conflict resolution option
        default_skip_existing: Default skip existing files setting
        
    Returns:
        dict: Parsed command with keys:
            - path: Path to upload (str)
            - dest_name: Destination name (str or None)
            - sure_option: Conflict resolution option (str)
            - skip_existing: Whether to skip existing files (bool)
            - error: Error message if parsing failed (str or None)
    """
    result = {
        'path': None,
        'dest_name': None,
        'sure_option': default_sure_option,
        'skip_existing': default_skip_existing,
        'error': None
    }
    
    # Check if command has parameters
    if " -" in user_input:
        try:
            parser = create_argument_parser()
            
            # On Windows, use posix=False to handle backslashes correctly
            if sys.platform == "win32":
                parsed_input = shlex.split(user_input, posix=False)
            else:
                parsed_input = shlex.split(user_input)
            
            # Parse arguments, catching SystemExit from argparse
            try:
                parsed_args = parser.parse_args(parsed_input)
            except SystemExit:
                result['error'] = "Invalid command format. Use: <path> [-d dest] [-f | -k] [--no-skip]"
                return result
            
            if not parsed_args or not parsed_args.path:
                result['error'] = "Invalid command format. Path is required."
                return result
            
            # Extract and normalize parameters
            result['path'] = normalize_path(parsed_args.path)
            result['dest_name'] = normalize_path(parsed_args.dest) if parsed_args.dest else None
            
            # Determine conflict handling option
            if parsed_args.force:
                result['sure_option'] = "2"  # Overwrite
            elif parsed_args.keep:
                result['sure_option'] = "1"  # Keep both
            
            # Skip existing setting
            result['skip_existing'] = not parsed_args.no_skip
            
        except (ValueError, Exception) as e:
            result['error'] = f"Invalid command format: {str(e)}"
            return result
    else:
        # Simple path mode - handle quoted paths properly
        result['path'] = normalize_path(user_input)
    
    return result


def handle_mget_command(user_input):
    """
    Handle mget (download) command processing.
    
    Args:
        user_input: Raw command input starting with 'mget'
    
    Usage:
        mget <url> [-o output_file] [-t threads] [-s]
    """
    import shlex
    import argparse
    from utils.mget import MGet
    
    # Parse mget command arguments
    try:
        # Split command properly
        if sys.platform == "win32":
            parts = shlex.split(user_input, posix=False)
        else:
            parts = shlex.split(user_input)
        
        # Remove 'mget' from the beginning
        args = parts[1:] if len(parts) > 1 else []
        
        if not args:
            print("Usage: mget <url> [-o output_file] [-t threads] [-s]")
            print("  -o: Output filename (default: 'downloaded_file')")
            print("  -t: Number of threads (default: 8)")
            print("  -s: Use single-threaded download")
            return
        
        # Create parser for mget arguments
        parser = argparse.ArgumentParser(
            description="File Downloader",
            add_help=False
        )
        parser.add_argument("url", help="URL of the file to download")
        parser.add_argument("-o", "--output", help="Output file path", default="downloaded_file")
        parser.add_argument("-t", "--threads", type=int, help="Number of threads", default=8)
        parser.add_argument("-s", "--single", action="store_true", help="Use single-threaded download")
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            print("Invalid mget command format")
            return
        
        url = parsed_args.url
        output = normalize_path(parsed_args.output)
        threads = parsed_args.threads
        single_thread = parsed_args.single
        
        print(f"Starting download: {url}")
        print(f"Saving to: {output}")
        print(f"Threads: {'1 (single)' if single_thread else threads}")
        
        # Start download
        downloader = MGet(default_threads=threads)
        downloader.download(url, output, threads, force_single=single_thread)
        
        # Show completion message
        if os.path.exists(output):
            file_size = os.path.getsize(output)
            print(f"Download complete! File size: {file_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"Download failed: {str(e)}")


def execute_upload(mpush, path, sure_option, dest_name, skip_existing):
    """
    Execute the upload operation for a file or directory.
    
    Args:
        mpush: MPush instance for uploading
        path: Path to file or directory to upload
        sure_option: Conflict resolution option ("1" or "2")
        dest_name: Destination name (None to keep original)
        skip_existing: Whether to skip files with matching MD5
    """
    if os.path.isdir(path):
        # Upload directory
        print(f"Preparing to upload directory: {os.path.basename(path)}")
        if dest_name:
            mpush.upload_directory_concurrent(
                path, sure=sure_option, custom_dirname=dest_name, skip_existing=skip_existing
            )
        else:
            mpush.upload_directory_concurrent(path, sure=sure_option, skip_existing=skip_existing)
        mpush.pan.cd("/")  # Reset to root directory after directory upload
    elif os.path.isfile(path):
        # Upload single file
        if dest_name:
            # Create custom directory for single file upload
            folder_id = mpush.pan.mkdir(dest_name, remake=False)
            if folder_id:
                mpush.upload_file(path, parent_id=folder_id, sure=sure_option, skip_existing=skip_existing)
                mpush.pan.cd("/")  # Return to root directory after operation
            else:
                print(f"Error: Failed to create directory '{dest_name}'")
        else:
            mpush.upload_file(path, sure=sure_option, skip_existing=skip_existing)
    else:
        print(f"Error: {path} is neither a file nor a directory")


def validate_upload_path(path):
    """
    Validate that the upload path exists.
    
    Args:
        path: Path to validate
        
    Returns:
        bool: True if path exists, False otherwise
    """
    if not os.path.exists(path):
        print(f"Error: Path {path} does not exist")
        return False
    return True


def format_upload_mode(sure_option, skip_existing):
    """
    Format upload mode string for display.
    
    Args:
        sure_option: Conflict resolution option
        skip_existing: Whether to skip existing files
        
    Returns:
        str: Formatted mode description
    """
    mode = 'Overwrite' if sure_option == '2' else 'Keep both'
    return f"Upload mode: {mode}, Skip existing: {skip_existing}"
