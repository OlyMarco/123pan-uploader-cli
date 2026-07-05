#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logging System for 123Pan Uploader CLI

Provides three types of logs stored in the `logs/` directory:
  - logs/commands/  — Command logs: user input commands and parsed results
  - logs/runtime/   — Runtime logs: program startup, login, upload, download events
  - logs/errors/    — Error logs: login failures, exceptions, crash exits

All logs are written with timestamps and also printed to terminal (stdout).
Error logs are printed to stderr in addition to the log file.
"""

import os
import sys
import logging
from datetime import datetime


# ─── Log directory structure ───
_LOG_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_DIR_COMMANDS = os.path.join(_LOG_ROOT, "commands")
LOG_DIR_RUNTIME = os.path.join(_LOG_ROOT, "runtime")
LOG_DIR_ERRORS = os.path.join(_LOG_ROOT, "errors")

# Ensure directories exist
for _d in (LOG_DIR_COMMANDS, LOG_DIR_RUNTIME, LOG_DIR_ERRORS):
    os.makedirs(_d, exist_ok=True)


def _get_log_filename(prefix):
    """Generate a log filename with today's date.

    Args:
        prefix: Log type prefix (e.g., 'command', 'runtime', 'error')

    Returns:
        str: Full path to the log file
    """
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(_LOG_ROOT, {
        'command': LOG_DIR_COMMANDS,
        'runtime': LOG_DIR_RUNTIME,
        'error': LOG_DIR_ERRORS,
    }.get(prefix, LOG_DIR_RUNTIME), f"{prefix}_{today}.log")


def _log(filepath, level, message):
    """Write a log entry to file and print to terminal.

    Args:
        filepath: Path to the log file
        level: Log level string (INFO, WARNING, ERROR, etc.)
        message: Log message content
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [{level}] {message}"

    # Write to file
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass  # Don't let logging failures crash the program

    # Print to terminal
    if level == 'ERROR':
        print(line, file=sys.stderr)
    else:
        print(line)


def log_command(message):
    """Log a user command or command parsing result.

    Args:
        message: Command description or parsed result string
    """
    _log(_get_log_filename('command'), 'COMMAND', message)


def log_runtime(message):
    """Log a runtime event (startup, login, upload, download, etc.).

    Args:
        message: Event description string
    """
    _log(_get_log_filename('runtime'), 'INFO', message)


def log_error(message):
    """Log an error event (login failure, exception, crash exit).

    The error is written to the error log file and printed to stderr.

    Args:
        message: Error description string
    """
    _log(_get_log_filename('error'), 'ERROR', message)


def log_exit(reason, exit_code=1):
    """Log a program exit event and save to error log before exiting.

    This is the primary function to call when the program must exit
    due to a critical failure (e.g., login failure, token invalid).

    Args:
        reason: Human-readable reason for exiting
        exit_code: Process exit code (default: 1)
    """
    log_error(f"PROGRAM EXIT (code={exit_code}): {reason}")
    sys.exit(exit_code)


def get_log_dirs():
    """Return the three log directory paths for external reference.

    Returns:
        dict: {'commands': str, 'runtime': str, 'errors': str}
    """
    return {
        'commands': LOG_DIR_COMMANDS,
        'runtime': LOG_DIR_RUNTIME,
        'errors': LOG_DIR_ERRORS,
    }
