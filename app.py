#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
123Pan Cloud Uploader CLI — Main Entry Point

Supports three login methods:
  1. Saved token (123pan.txt) — auto-verify, re-login with password if invalid
  2. Account & Password — prompt or command-line
  3. QR Code (--qr flag) — scan with WeChat or 123Pan app

Login failure handling:
  - If token is invalid and password credentials exist → try re-login once
  - If re-login fails or no credentials (QR login) → log error and exit(1)
  - All exits are logged to logs/errors/ and printed to terminal

Logging:
  - logs/commands/  — User command inputs and parsed results
  - logs/runtime/   — Program events (startup, login, upload, download)
  - logs/errors/    — Error events and program exits
"""

import os
import sys
import time
import signal
import json
from tosasitill_123pan.class123 import Pan123
from tosasitill_123pan import config
from utils.mpush import MPush
from utils.logger import log_runtime, log_error, log_command, log_exit
from utils.input_handler import setup_readline, normalize_path
from utils.command_handler import (
    create_argument_parser,
    parse_upload_command,
    handle_mget_command,
    execute_upload,
    validate_upload_path,
    format_upload_mode
)

# Global variable for tracking Ctrl+C presses and exit flag
_ctrl_c_count = 0
_last_ctrl_c_time = 0
_should_exit = False


def handle_ctrl_c(signum, frame):
    """Handle Ctrl+C signal for graceful exit.
    
    Press Ctrl+C twice within 2 seconds to exit the program.
    Single Ctrl+C will only interrupt the current operation.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global _ctrl_c_count, _last_ctrl_c_time, _should_exit
    current_time = time.time()
    
    if current_time - _last_ctrl_c_time < 2:
        _ctrl_c_count += 1
    else:
        _ctrl_c_count = 1
    
    _last_ctrl_c_time = current_time
    
    if _ctrl_c_count >= 2:
        log_runtime("Double Ctrl+C detected, exiting program...")
        _should_exit = True
        raise KeyboardInterrupt()
    else:
        print("\nPress Ctrl+C again within 2 seconds to exit, or continue with input.")
        raise KeyboardInterrupt()


def print_interactive_help():
    """Print interactive mode command help"""
    print("\n" + "="*60)
    print("Interactive Mode - Commands:")
    print("  <path>                    Upload file or directory")
    print('  <path> -d "name"          Upload with custom directory name')
    print("  <path> -f                 Force overwrite existing files")
    print("  <path> -k                 Keep both on conflict")
    print("  <path> --no-skip          Disable MD5 duplicate check")
    print("  mget <url> [-o file] [-t n] Download file")
    print("  0                         Exit program")
    print("  Ctrl+C twice              Exit program")
    print("="*60 + "\n")


def run_interactive_mode(mpush, default_sure_option, default_skip_existing):
    """Run the interactive command loop.
    
    Reads user input, logs each command, and executes uploads or downloads.
    Supports Ctrl+C double-press to exit.
    
    Args:
        mpush: MPush instance for uploads
        default_sure_option: Default conflict resolution option ("1" or "2")
        default_skip_existing: Default skip existing files setting (bool)
    """
    global _ctrl_c_count, _should_exit
    
    print_interactive_help()
    
    while True:
        if _should_exit:
            break
            
        try:
            user_input = input("\033[91m >\033[0m ")
            
            _ctrl_c_count = 0
            user_input = user_input.strip()
            
            if not user_input:
                continue

            # Log the command
            log_command(user_input)

            # Exit command
            if user_input == "0":
                log_runtime("User requested exit (input '0')")
                print("Exiting program")
                break

            # Download command
            if user_input.startswith("mget "):
                handle_mget_command(user_input)
                continue

            # Parse upload command
            cmd = parse_upload_command(user_input, default_sure_option, default_skip_existing)
            
            if cmd['error']:
                print(cmd['error'])
                continue
            
            # Validate path
            if not validate_upload_path(cmd['path']):
                continue

            # Display upload mode
            print(format_upload_mode(cmd['sure_option'], cmd['skip_existing']))
            
            # Execute upload
            execute_upload(
                mpush, 
                cmd['path'], 
                cmd['sure_option'], 
                cmd['dest_name'], 
                cmd['skip_existing']
            )

        except KeyboardInterrupt:
            if _should_exit:
                break
            print("\nOperation interrupted. Press Ctrl+C again to exit.")
            continue
        except EOFError:
            log_runtime("EOF received, exiting program")
            print("\nExiting program")
            break
        except Exception as e:
            log_error(f"Interactive mode error: {str(e)}")
            print(f"An error occurred: {str(e)}")
            continue


def main():
    """Main entry point for 123Pan Cloud Upload CLI Tool.
    
    Supports both command-line mode and interactive mode.
    - Command-line: python app.py <path> [-f] [-k] [-d dest] [--no-skip]
    - Interactive: python app.py (then enter commands)
    - QR login: python app.py --qr (force QR code login)
    
    Login flow:
    1. If --qr flag: force QR code login
    2. If 123pan.txt exists: load token, verify, re-login if needed
    3. If no credentials: prompt for account/password or QR code
    
    On login failure, the program logs the error and exits with code 1.
    """
    signal.signal(signal.SIGINT, handle_ctrl_c)
    setup_readline()
    
    parser = create_argument_parser()
    args = parser.parse_args()

    # Set conflict handling strategy
    if args.force:
        sure_option = "2"  # Overwrite
    else:
        sure_option = "1"  # Default to keep both
    
    skip_existing = not args.no_skip

    log_runtime(f"Program started. Path={args.path or 'interactive'}, Force={args.force}, QR={args.qrcode}")
    
    # ─── Login ───
    print("Logging in to 123Pan Cloud...")
    log_runtime("Starting login process...")

    # Check if credentials file exists
    has_credentials = False
    if os.path.exists(config.CREDENTIALS_FILE):
        try:
            with open(config.CREDENTIALS_FILE, "r") as f:
                cred_data = json.loads(f.read())
            if cred_data.get('authorization'):
                has_credentials = True
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    try:
        if args.qrcode:
            # Force QR code login (--qr flag)
            print("\nStarting QR code login (--qr flag)...")
            log_runtime("QR code login forced by --qr flag")
            pan = Pan123(readfile=False, use_qrcode=True)
        elif has_credentials:
            # Use existing credentials — Pan123 will verify token and auto-recover
            log_runtime("Using saved credentials from 123pan.txt")
            pan = Pan123(readfile=True, input_pwd=True)
        else:
            # No credentials found, ask user for login method
            print("\nNo saved credentials found. Please choose a login method:")
            print("  1. Account & Password login")
            print("  2. QR Code login (scan with WeChat or 123Pan app)")
            choice = input("\nEnter choice (1 or 2): ").strip()
            log_command(f"Login method choice: {choice}")

            if choice == "2":
                print("\nStarting QR code login...")
                log_runtime("User chose QR code login")
                pan = Pan123(readfile=False, use_qrcode=True)
            else:
                log_runtime("User chose account/password login")
                pan = Pan123(readfile=False, input_pwd=True)

        mpush = MPush(pan)
        print("Login successful!")
        log_runtime("Login successful, entering main mode")
    except Exception as e:
        log_error(f"Login failed: {str(e)}")
        print(f"\nLogin failed: {str(e)}")
        print(f"Error logged to logs/errors/")
        log_exit(f"Login failure: {str(e)}", exit_code=1)

    # ─── Command-line mode (non-interactive) ───
    if args.path:
        path = normalize_path(args.path)
        log_runtime(f"CLI mode: uploading '{path}'")
        
        if not validate_upload_path(path):
            log_exit("Invalid upload path in CLI mode", exit_code=1)
        
        dest_name = normalize_path(args.dest) if args.dest else None
        
        print(format_upload_mode(sure_option, skip_existing))
        execute_upload(mpush, path, sure_option, dest_name, skip_existing)
        log_runtime("CLI mode upload completed, exiting")
        return

    # ─── Interactive mode ───
    run_interactive_mode(mpush, sure_option, skip_existing)
    log_runtime("Program exited normally")


if __name__ == "__main__":
    main()
