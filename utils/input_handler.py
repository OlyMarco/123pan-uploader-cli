#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
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

# History file configuration
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
    except Exception:
        return None


def normalize_path(path_str):
    """
    Normalize a path string by removing quotes and expanding special characters.
    Handles Windows and Unix paths consistently.
    
    Args:
        path_str: Path string that may contain quotes or special characters
        
    Returns:
        Normalized absolute path
    """
    # Remove leading/trailing quotes and whitespace
    path_str = path_str.strip().strip("\"'")
    
    # Expand user home directory (~)
    path_str = os.path.expanduser(path_str)
    
    # Normalize path separators
    path_str = os.path.normpath(path_str)
    
    return path_str
