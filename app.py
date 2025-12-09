#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import hashlib
import json
import argparse
import shlex
import signal
import atexit

# Setup readline for bash-style line editing (history, arrow keys, etc.)
try:
    import readline
    _readline_available = True
except ImportError:
    try:
        import pyreadline3 as readline
        _readline_available = True
    except ImportError:
        readline = None
        _readline_available = False

# Configure readline if available
HISTORY_FILE = os.path.expanduser("~/.123pan_history")

def setup_readline():
    """Configure readline for bash-style input experience"""
    if not _readline_available or readline is None:
        return
    
    # Set history file length
    readline.set_history_length(1000)
    
    # Load history file if exists
    try:
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
    except (IOError, OSError):
        pass
    
    # Save history on exit
    atexit.register(save_history)
    
    # Enable tab completion for file paths
    if hasattr(readline, 'set_completer'):
        readline.set_completer(path_completer)
        # Set completion delimiters
        readline.set_completer_delims(' \t\n;')
        # Enable tab completion
        readline.parse_and_bind('tab: complete')
    
    # Set editing mode to emacs (bash-like)
    try:
        readline.parse_and_bind('set editing-mode emacs')
    except:
        pass

def save_history():
    """Save command history to file"""
    if _readline_available and readline is not None:
        try:
            readline.write_history_file(HISTORY_FILE)
        except (IOError, OSError):
            pass

def path_completer(text, state):
    """Tab completion for file paths"""
    try:
        # Expand user home directory
        if text.startswith('~'):
            text = os.path.expanduser(text)
        
        # Get directory and partial filename
        if os.path.isdir(text):
            directory = text
            partial = ''
        else:
            directory = os.path.dirname(text) or '.'
            partial = os.path.basename(text)
        
        # List matching files/directories
        try:
            entries = os.listdir(directory)
        except OSError:
            return None
        
        # Filter entries that match the partial name
        matches = []
        for entry in entries:
            if entry.startswith(partial):
                full_path = os.path.join(directory, entry)
                if os.path.isdir(full_path):
                    matches.append(full_path + os.sep)
                else:
                    matches.append(full_path)
        
        if state < len(matches):
            return matches[state]
        return None
    except:
        return None

import requests
from tqdm import tqdm

from tosasitill_123pan.class123 import Pan123
from tosasitill_123pan.sign_get import getSign  
from utils.mget import MGet
from utils.mpush import MPush, format_size

# Global variable for tracking Ctrl+C presses
_ctrl_c_count = 0
_last_ctrl_c_time = 0


def parse_mget_command(cmd_args):
    """Parse command line arguments for file download"""
    parser = argparse.ArgumentParser(description="File Downloader")
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

    try:
        args = parser.parse_args(cmd_args)
        return args
    except SystemExit:
        return None


def handle_mget_command(cmd):
    """Process file download request"""
    args = shlex.split(cmd)[1:]

    if not args:
        print(
            "Error: Missing download URL. Usage: mget <url> [-o output_filename] [-t thread_count] [-s]"
        )
        return

    parsed_args = parse_mget_command(args)
    if not parsed_args:
        return

    url = parsed_args.url
    output = parsed_args.output
    threads = parsed_args.threads
    single_thread = parsed_args.single

    print(f"Starting download: {url}")
    print(f"Saving to: {output}")

    try:
        downloader = MGet(default_threads=threads)
        start_time = time.time()
        downloader.download(url, output, threads, force_single=single_thread)
        elapsed_time = time.time() - start_time
        file_size = os.path.getsize(output)

        print(f"Download complete! File size: {format_size(file_size)}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
    except Exception as e:
        print(f"Download failed: {str(e)}")


def _mpush(mpush, path, sure_option=None, dest_name=None, skip_existing=True):
    """Upload a file or directory to 123Pan Cloud

    Args:
        mpush: MPush instance for handling uploads
        path: Local path to file or directory to upload
        sure_option: Duplicate handling strategy - "1":keep both, "2":overwrite
        dest_name: Custom name for the destination directory in 123Pan
        skip_existing: If True, skip files that already exist with same MD5 (default: True)
    """
    if os.path.isfile(path):
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
    elif os.path.isdir(path):
        if dest_name:
            mpush.upload_directory_concurrent(
                path, sure=sure_option, custom_dirname=dest_name, skip_existing=skip_existing
            )
        else:
            mpush.upload_directory_concurrent(path, sure=sure_option, skip_existing=skip_existing)
        mpush.pan.cd("/")  # Reset to root directory after directory upload
    else:
        print(f"Error: {path} is not a valid file or directory")


def handle_ctrl_c(signum, frame):
    """Handle Ctrl+C signal for graceful exit
    
    Press Ctrl+C twice within 2 seconds to exit the program.
    Single Ctrl+C will only interrupt the current operation.
    """
    global _ctrl_c_count, _last_ctrl_c_time
    current_time = time.time()
    
    if current_time - _last_ctrl_c_time < 2:
        _ctrl_c_count += 1
    else:
        _ctrl_c_count = 1
    
    _last_ctrl_c_time = current_time
    
    if _ctrl_c_count >= 2:
        print("\n\nDouble Ctrl+C detected. Exiting program...")
        sys.exit(0)
    else:
        print("\nPress Ctrl+C again within 2 seconds to exit, or continue with input.")
        raise KeyboardInterrupt()


def main():
    """Main entry point for 123Pan Cloud Upload CLI Tool
    
    Supports both command-line mode and interactive mode.
    - Command-line: python app.py <path> [-f] [-k] [-d dest] [--no-skip]
    - Interactive: python app.py (then enter commands)
    
    Exit methods:
    - Enter '0' to exit
    - Press Ctrl+C twice within 2 seconds to exit
    """
    global _ctrl_c_count, _last_ctrl_c_time
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_ctrl_c)
    
    # Initialize readline for bash-style input
    setup_readline()
    
    parser = argparse.ArgumentParser(description="123Pan Cloud Upload Tool")
    parser.add_argument("path", nargs="?", help="Path to file or directory to upload")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite files with the same name"
    )
    parser.add_argument(
        "-k", "--keep", action="store_true", help="Keep both files when names conflict"
    )
    parser.add_argument(
        "-d", "--dest", help="Specify a custom directory name in 123Pan"
    )
    parser.add_argument(
        "--no-skip", action="store_true", help="Disable skipping files that already exist with same MD5"
    )

    args = parser.parse_args()

    # Set conflict handling strategy
    if args.force:
        sure_option = "2"  # Overwrite
    else:
        sure_option = "1"  # Default to keep both (even if -k is not specified)
    
    # Set skip_existing based on --no-skip flag
    skip_existing = not args.no_skip

    print("Logging in to 123Pan Cloud...")
    try:
        pan = Pan123(readfile=True, input_pwd=True)
        mpush = MPush(pan)
        print("Login successful!")

        # Handle command line mode (non-interactive)
        if args.path:
            path = args.path.strip("\"'")
            if os.path.exists(path):
                _mpush(mpush, path, sure_option, args.dest, skip_existing)
                return
            else:
                print(f"Error: Path {path} does not exist")
                return

        # Interactive mode instructions
        print("\n" + "="*60)
        print("Interactive Mode - Commands:")
        print("  <path>                    Upload file or directory")
        print('  <path> -d "name"          Upload with custom directory name')
        print("  <path> -f                 Force overwrite existing files")
        print("  <path> --no-skip          Disable MD5 duplicate check")
        print("  mget <url> [-o out] [-t n] Download file")
        print("  0                         Exit program")
        print("  Ctrl+C twice              Exit program")
        print("="*60 + "\n")
    except Exception as e:
        print(f"Login failed: {str(e)}")
        sys.exit(1)

    # Interactive mode loop
    while True:
        try:
            user_input = input("\033[91m >\033[0m ")
            
            # Reset Ctrl+C counter only after successful input
            _ctrl_c_count = 0
            
            # Strip whitespace
            user_input = user_input.strip()
            
            if not user_input:
                continue

            if user_input == "0":
                print("Exiting program")
                break

            if user_input.startswith("mget "):
                handle_mget_command(user_input)
                continue

            # Parse command with parameters if present
            if " -" in user_input:
                try:
                    parsed_args = parser.parse_args(shlex.split(user_input))
                except SystemExit:
                    print("Invalid command format. Try again.")
                    continue
                
                if not parsed_args or not parsed_args.path:
                    print("Invalid command format. Try again.")
                    continue

                path = parsed_args.path.strip("\"'")

                # Determine conflict handling option
                cmd_sure_option = sure_option
                if parsed_args.force:
                    cmd_sure_option = "2"  # Overwrite
                elif parsed_args.keep:
                    cmd_sure_option = "1"  # Keep both

                dest_name = parsed_args.dest
                cmd_skip_existing = not parsed_args.no_skip
            else:
                # Simple path mode - use bash-style parsing for quoted paths
                try:
                    parsed_path = shlex.split(user_input)
                    path = parsed_path[0] if parsed_path else user_input
                except ValueError:
                    path = user_input.strip("\"'")
                
                cmd_sure_option = sure_option
                dest_name = None
                cmd_skip_existing = skip_existing

            if not os.path.exists(path):
                print(f"Error: Path {path} does not exist")
                continue

            print(f"Upload mode: {'Overwrite' if cmd_sure_option == '2' else 'Keep both'}, Skip existing: {cmd_skip_existing}")
            _mpush(mpush, path, cmd_sure_option, dest_name, cmd_skip_existing)

        except KeyboardInterrupt:
            print("\nOperation interrupted. Press Ctrl+C again to exit.")
            continue
        except EOFError:
            print("\nExiting program")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            continue


if __name__ == "__main__":
    main()
