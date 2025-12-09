#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
from tosasitill_123pan.class123 import Pan123
from utils.mpush import MPush
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
    """
    Handle Ctrl+C signal for graceful exit.
    
    Press Ctrl+C twice within 2 seconds to exit the program.
    Single Ctrl+C will only interrupt the current operation.
    """
    global _ctrl_c_count, _last_ctrl_c_time, _should_exit
    current_time = time.time()
    
    if current_time - _last_ctrl_c_time < 2:
        _ctrl_c_count += 1
    else:
        _ctrl_c_count = 1
    
    _last_ctrl_c_time = current_time
    
    if _ctrl_c_count >= 2:
        print("\n\nDouble Ctrl+C detected. Exiting program...")
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
    print("  <path> --no-skip          Disable MD5 duplicate check")
    print("  mget <url> [-o output_file] [-t n] Download file")
    print("  0                         Exit program")
    print("  Ctrl+C twice              Exit program")
    print("="*60 + "\n")


def run_interactive_mode(mpush, default_sure_option, default_skip_existing):
    """
    Run the interactive command loop.
    
    Args:
        mpush: MPush instance for uploads
        default_sure_option: Default conflict resolution option
        default_skip_existing: Default skip existing files setting
    """
    global _ctrl_c_count, _should_exit
    
    print_interactive_help()
    
    while True:
        # Check if we should exit after Ctrl+C
        if _should_exit:
            break
            
        try:
            user_input = input("\033[91m >\033[0m ")
            
            # Reset Ctrl+C counter only after successful input
            _ctrl_c_count = 0
            
            # Strip whitespace
            user_input = user_input.strip()
            
            if not user_input:
                continue

            # Exit command
            if user_input == "0":
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
            # Check if double Ctrl+C was pressed
            if _should_exit:
                break
            print("\nOperation interrupted. Press Ctrl+C again to exit.")
            continue
        except EOFError:
            print("\nExiting program")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            continue


def main():
    """
    Main entry point for 123Pan Cloud Upload CLI Tool.
    
    Supports both command-line mode and interactive mode.
    - Command-line: python app.py <path> [-f] [-k] [-d dest] [--no-skip]
    - Interactive: python app.py (then enter commands)
    """
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_ctrl_c)
    
    # Initialize readline for bash-style input
    setup_readline()
    
    # Create argument parser (already includes all arguments)
    parser = create_argument_parser()

    # Parse command line arguments
    args = parser.parse_args()

    # Set conflict handling strategy
    if args.force:
        sure_option = "2"  # Overwrite
    else:
        sure_option = "1"  # Default to keep both
    
    # Set skip_existing based on --no-skip flag
    skip_existing = not args.no_skip

    # Login to 123Pan
    print("Logging in to 123Pan Cloud...")
    try:
        pan = Pan123(readfile=True, input_pwd=True)
        mpush = MPush(pan)
        print("Login successful!")
    except Exception as e:
        print(f"Login failed: {str(e)}")
        sys.exit(1)

    # Handle command line mode (non-interactive)
    if args.path:
        path = normalize_path(args.path)
        
        if not validate_upload_path(path):
            sys.exit(1)
        
        # Normalize dest if provided
        dest_name = normalize_path(args.dest) if args.dest else None
        
        print(format_upload_mode(sure_option, skip_existing))
        execute_upload(mpush, path, sure_option, dest_name, skip_existing)
        return

    # Run interactive mode
    run_interactive_mode(mpush, sure_option, skip_existing)


if __name__ == "__main__":
    main()
