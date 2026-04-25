#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import getpass
from tosasitill_123pan import config


def get_token(passport=None, password=None, remember=True):
    """
    Get login token for 123pan cloud service

    Args:
        passport: Username/phone number
        password: Login password
        remember: Whether to remember login state

    Returns:
        Dictionary with credentials and token, or None if login fails
    """
    url = config.URL_SIGN_IN

    if not passport:
        passport = input("Enter 123pan username/phone: ")
    if not password:
        password = getpass.getpass("Enter password: ")

    payload = {"passport": passport, "password": password, "remember": remember}

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=config.TIMEOUT_SHORT)
        result = response.json()

        if result.get("code") == 200:
            token = result.get("data", {}).get("token")
            if token:
                print("Login successful, token acquired")
                return {
                    "userName": passport,
                    "passWord": password,
                    "authorization": f"Bearer {token}",
                }
            else:
                print("Login successful, but failed to get token")
                return None
        else:
            print(f"Login failed: {result.get('message', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"Request error: {str(e)}")
        return None


def save_token_to_file(credentials, filename="123pan.txt"):
    """Save credentials to file"""
    try:
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        with open(filename, "w") as f:
            json.dump(credentials, f)

        print(f"Credentials saved to {filename}")
        return True
    except Exception as e:
        print(f"Failed to save credentials: {str(e)}")
        return False


def main():
    """Main function"""
    print("123pan Token Tool")
    print("-" * 30)

    if len(sys.argv) >= 3:
        passport = sys.argv[1]
        password = sys.argv[2]
    else:
        passport = None
        password = None

    credentials = get_token(passport, password)

    if credentials:
        filepath = os.path.join("123pan.txt")
        save_token_to_file(credentials, filepath)

        token = credentials["authorization"].replace("Bearer ", "")
        print(f"Token preview: {token[:20]}...")


if __name__ == "__main__":
    main()
