#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import shlex
from utils.input_handler import normalize_path
from utils.mget import MGet, _validate_output_path
from utils.logger import log_command, log_runtime, log_error


def create_argument_parser():
    """Create and configure the argument parser for upload commands.
    
    Supported arguments:
        path:           Path to file or directory to upload (optional)
        -d, --dest:     Destination directory name
        -f, --force:    Force overwrite existing files
        -k, --keep:     Keep both files on conflict
        --no-skip:      Disable MD5 duplicate check
        --qr, --qrcode: Force QR code login (scan with WeChat)
    
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
    parser.add_argument("--qr", "--qrcode", dest="qrcode", action="store_true", help="Force QR code login (scan with WeChat or 123Pan app)")
    
    return parser


def _is_flag(token):
    """Check if token is a flag argument. Returns (is_flag, flag_name)."""
    if not token.startswith('-'):
        return False, None

    # Standalone "-" is not a valid flag, treat as path part
    if token == '-':
        return False, None

    # Single letter flags: -d, -f, -k (must be ASCII letter)
    if len(token) == 2 and token[1].isascii() and token[1].isalpha():
        return True, token

    # Long flags: --dest, --force, --no-skip
    if token.startswith('--'):
        return True, token

    # On Windows, paths can contain segments starting with "-" followed by
    # non-ASCII characters (e.g., "- 副本", "-中文"). Treat these as path parts.
    # Also treat "-X" where X is non-ASCII/non-letter as path part.
    if len(token) >= 2 and not (token[1].isascii() and token[1].isalpha()):
        return False, None

    return True, token


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

    user_input = user_input.strip()
    if not user_input:
        result['error'] = "Empty input"
        return result

    try:
        parts = shlex.split(user_input, posix=False)
    except ValueError as e:
        result['error'] = f"Invalid command format: {e}"
        return result

    if not parts:
        result['error'] = "Empty input"
        return result

    # Detect unquoted paths with spaces - shlex splits on them, which breaks
    # paths like "C:\path\to file". Detect by checking if any non-flag segment
    # (that doesn't start with quotes) contains spaces.
    unquoted_path_with_spaces = False
    for i, part in enumerate(parts):
        if not part.startswith('-') and ' ' in part and not part.startswith('"') and not part.startswith("'"):
            unquoted_path_with_spaces = True
            break

    # Flags that take a value (must be followed by a non-flag argument)
    flags_with_value = {'-d', '--dest'}
    # Boolean flags (don't consume additional values)
    bool_flags = {'-f', '--force', '-k', '--keep', '--no-skip', '--qr', '--qrcode'}

    path_parts = []
    i = 0

    while i < len(parts):
        token = parts[i]
        is_flag, _ = _is_flag(token)

        # Non-flag token: part of the path
        if not is_flag:
            path_parts.append(token)
            i += 1
            # All subsequent non-flag tokens are also part of the path
            while i < len(parts):
                next_token = parts[i]
                next_is_flag, _ = _is_flag(next_token)
                if not next_is_flag:
                    path_parts.append(next_token)
                    i += 1
                else:
                    break
            continue

        # It's a flag
        if token in bool_flags:
            i += 1
        elif token in flags_with_value:
            # -d takes a value (next token, unless it's another flag)
            if i + 1 < len(parts):
                next_token = parts[i + 1]
                next_is_flag, _ = _is_flag(next_token)
                if not next_is_flag:
                    i += 2  # consume flag + value
                else:
                    result['error'] = f"Flag {token} requires a value"
                    return result
            else:
                result['error'] = f"Flag {token} requires a value"
                return result
        else:
            result['error'] = f"Unknown flag: {token}"
            return result

    # Reconstruct path from collected parts
    raw_path = ' '.join(path_parts).strip().strip('"\'')
    if not raw_path:
        result['error'] = "Path is required"
        return result

    # If path contains spaces but wasn't quoted, suggest quoting
    if unquoted_path_with_spaces and ' ' in raw_path:
        result['error'] = (f'Path "{raw_path}" contains spaces. '
                           'Please quote the path: "{raw_path}"')
        return result

    # Now parse the actual flags using argparse
    try:
        parser = create_argument_parser()
        parsed_args = parser.parse_args(parts[len(path_parts):])
    except SystemExit:
        result['error'] = "Invalid flags. Use: <path> [-d dest] [-f | -k] [--no-skip]"
        return result

    result['path'] = normalize_path(raw_path)
    result['dest_name'] = normalize_path(parsed_args.dest) if parsed_args.dest else None

    if parsed_args.force:
        result['sure_option'] = "2"
    elif parsed_args.keep:
        result['sure_option'] = "1"

    result['skip_existing'] = not parsed_args.no_skip
    return result


def handle_mget_command(user_input):
    """Handle mget (download) command processing.

    Parses the mget command, validates arguments, and executes the download.
    Logs the command to the command log and runtime log.

    Args:
        user_input: Raw command input starting with 'mget'

    Usage:
        mget <url> [-o output_file] [-t threads] [-s]
    """
    import shlex
    import argparse

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

        # Validate output path before download
        try:
            validated_output = _validate_output_path(output)
        except ValueError as e:
            print(f"Output path error: {e}")
            return

        print(f"Starting download: {url}")
        print(f"Saving to: {validated_output}")
        print(f"Threads: {'1 (single)' if single_thread else threads}")

        downloader = MGet(default_threads=threads)
        # Pass validated path directly; MGet.download skips its own validation
        result = downloader._download_raw(url, validated_output, threads, force_single=single_thread)
        
        # Show completion message
        if result is not None and os.path.exists(validated_output):
            file_size = os.path.getsize(validated_output)
            print(f"Download complete! File size: {file_size / 1024 / 1024:.2f} MB")
        elif result is None:
            print("Download failed.")
        
    except Exception as e:
        print(f"Download failed: {str(e)}")


def execute_upload(mpush, path, sure_option, dest_name, skip_existing):
    """Execute the upload operation for a file or directory.
    
    Logs the upload start and completion to the runtime log.
    
    Args:
        mpush: MPush instance for uploading
        path: Path to file or directory to upload
        sure_option: Conflict resolution option ("1" for keep both, "2" for overwrite)
        dest_name: Destination name (None to keep original)
        skip_existing: Whether to skip files with matching MD5
    """
    log_runtime(f"Upload started: path='{path}', mode={sure_option}, dest='{dest_name}', skip={skip_existing}")
    
    if os.path.isdir(path):
        # Upload directory
        print(f"Preparing to upload directory: {os.path.basename(path)}")
        if dest_name:
            mpush.upload_directory_concurrent(
                path, sure=sure_option, custom_dirname=dest_name, skip_existing=skip_existing
            )
        else:
            mpush.upload_directory_concurrent(path, sure=sure_option, skip_existing=skip_existing)
        mpush.pan.parentFileId = 0
        mpush.pan.parentFileList = [0]
    elif os.path.isfile(path):
        # Upload single file
        if dest_name:
            # Create custom directory for single file upload
            folder_id = mpush.pan.mkdir(dest_name, remake=False)
            if folder_id:
                mpush.upload_file(path, parent_id=folder_id, sure=sure_option, skip_existing=skip_existing)
                mpush.pan.parentFileId = 0
                mpush.pan.parentFileList = [0]
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
