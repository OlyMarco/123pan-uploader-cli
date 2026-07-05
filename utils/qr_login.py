#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
123Pan QR Code Login Module

Implements QR code login flow based on API reverse engineering:
1. Visit login page to get necessary cookies (aliyungf_tc)
2. GET /api/user/qr-code/generate to create QR code session and get URL
3. Display QR code (URL: https://yun.123pan.cn/wx-app-login.html?uniID=...)
4. Poll GET /api/user/qr-code/result to check scan status (loginStatus)
5. When scanned (loginStatus != 0), POST /api/user/qr-code/wx_code to get wechat_code
6. POST /api/user/sign_in with wechat_code (type=4) to get token

loginStatus values:
  0 = waiting for scan
  1 = scanned, waiting for confirm
  2 = confirmed
  3 = expired
  4 = no valid session
"""

import os
import uuid
import time
import socket
import hashlib
import platform
import requests
from datetime import datetime
from tosasitill_123pan import config


# Login status constants
LOGIN_STATUS_WAITING = 0
LOGIN_STATUS_SCANNED = 1
LOGIN_STATUS_CONFIRMED = 2
LOGIN_STATUS_EXPIRED = 3
LOGIN_STATUS_NO_SESSION = 4


def _generate_loginuuid():
    """Generate a persistent device fingerprint (64-char hex string).

    Uses machine hostname + username to create a SHA-256 hash,
    making it persistent across sessions on the same machine.

    Returns:
        str: 64-character hex string
    """
    try:
        username = os.getlogin()
    except OSError:
        username = os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
    hostname = socket.gethostname()
    os_name = platform.system()
    raw = f"{hostname}:{username}:{os_name}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _generate_uni_id():
    """Generate a UUID v4 string.

    Returns:
        str: UUID string (e.g., '7e9fd53d-113c-48a6-a97d-0de85de75a8c')
    """
    return str(uuid.uuid4())


def _build_qr_headers(loginuuid):
    """Build request headers for QR code API calls.

    Based on captured traffic from 123pan web login.

    Args:
        loginuuid: Device fingerprint string

    Returns:
        dict: Headers dictionary
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Content-Type': 'application/json',
        'Origin': 'https://user.123pan.cn',
        'Referer': 'https://user.123pan.cn/centerlogin?redirect_url=https%3A%2F%2Fyun.123pan.cn&source_page=website',
        'platform': 'web',
        'app-version': '132',
        'loginuuid': loginuuid,
    }


def _save_qrcode_to_file(qr_url, uni_id, loginuuid):
    """Save QR code to qrcode.txt (with ASCII art) and qrcode.png (image).

    Writes both the QR code URL metadata and a scannable ASCII-art QR code
    into qrcode.txt, so the user can open the file and scan directly.
    Also saves a PNG image as qrcode.png for easier mobile scanning.

    Args:
        qr_url: QR code URL string
        uni_id: The server-generated uniID for this login session
        loginuuid: Device fingerprint
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Build ASCII QR code art
    ascii_qr = ""
    try:
        import io as _io
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        # Capture ASCII output to string
        buf = _io.StringIO()
        qr.print_ascii(invert=True, out=buf)
        ascii_qr = buf.getvalue()
    except ImportError:
        ascii_qr = "(qrcode library not installed, cannot render ASCII QR)\n"

    content = (
        f"{'=' * 60}\n"
        f"[{timestamp}] 123Pan QR Code Login\n"
        f"{'=' * 60}\n"
        f"uniID: {uni_id}\n"
        f"loginuuid: {loginuuid[:16]}...\n"
        f"QR URL: {qr_url}\n"
        f"{'=' * 60}\n"
        f"Scan the QR code below with WeChat or 123Pan app:\n"
        f"{'=' * 60}\n\n"
        f"{ascii_qr}\n"
        f"{'=' * 60}\n"
        f"Or open this URL in browser: {qr_url}\n"
        f"{'=' * 60}\n"
    )
    try:
        with open(config.QRCODE_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [QR code saved to {config.QRCODE_FILE}]")
    except OSError as e:
        print(f"  [Warning: Failed to save QR code to file: {e}]")

    # Also save PNG image
    try:
        import qrcode
        qr_img = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_img.add_data(qr_url)
        qr_img.make(fit=True)
        img = qr_img.make_image(fill_color="black", back_color="white")
        img.save("qrcode.png")
        print(f"  [QR image saved to qrcode.png]")
    except ImportError:
        pass
    except Exception as e:
        print(f"  [Warning: Failed to save QR image: {e}]")


def _display_qr_in_terminal(qr_url):
    """Display QR code in terminal using qrcode library.

    Falls back to printing the URL if qrcode library is not available.

    Args:
        qr_url: URL string to encode as QR code
    """
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        print("\n" + "=" * 50)
        print("  Please scan the QR code with WeChat or 123Pan app")
        print("=" * 50 + "\n")
        qr.print_ascii(invert=True)
        print("\n" + "=" * 50)
        print(f"  Or visit: {qr_url}")
        print("=" * 50 + "\n")
    except ImportError:
        print("\n" + "=" * 50)
        print("  Please scan the QR code with WeChat or 123Pan app")
        print("=" * 50)
        print(f"  QR Code URL: {qr_url}")
        print(f"  (Install 'qrcode' library for terminal QR display)")
        print("=" * 50 + "\n")


def get_qrcode(session, loginuuid):
    """Request QR code from 123Pan API.

    Calls GET /api/user/qr-code/generate to create a QR code session.
    The server returns a new uniID and the base URL for the QR code.
    The full QR code URL is constructed as: {base_url}?uniID={server_uniID}

    Args:
        session: requests.Session with necessary cookies
        loginuuid: Device fingerprint string

    Returns:
        dict: {'success': bool, 'uni_id': str, 'qr_url': str, 'error': str}
    """
    client_uni_id = _generate_uni_id()
    headers = _build_qr_headers(loginuuid)

    try:
        resp = session.get(
            config.URL_QR_CODE_GENERATE,
            params={'uniID': client_uni_id},
            headers=headers,
            timeout=config.TIMEOUT_SHORT
        )
        result = resp.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f"Request failed: {e}"}
    except ValueError as e:
        return {'success': False, 'error': f"Failed to parse response: {e}"}

    code = result.get('code', -1)
    if code != 0:
        return {
            'success': False,
            'error': f"API error code={code}: {result.get('message', 'Unknown error')}"
        }

    data = result.get('data', {})
    server_uni_id = data.get('uniID', '')
    base_url = data.get('url', '')

    if not server_uni_id or not base_url:
        return {
            'success': False,
            'error': f"Missing uniID or url in response: {result}"
        }

    # Construct the full QR code URL
    # env=production is REQUIRED: wx-app-login.html uses envConfig[env] to determine
    # the API host for calling POST /user/qr-code/scan (notifies server of scan).
    # Without env, hostUrl is undefined and the scan is never registered.
    qr_url = f"{base_url}?uniID={server_uni_id}&env=production"

    return {
        'success': True,
        'uni_id': server_uni_id,
        'qr_url': qr_url,
        'error': None
    }


def poll_qrcode_result(session, uni_id, loginuuid, timeout=None):
    """Poll QR code scan status until scanned, confirmed, or timeout.

    Calls GET /api/user/qr-code/result to check if the QR code has been
    scanned and confirmed by the user.

    When loginStatus changes from 0 (waiting), calls POST /api/user/qr-code/wx_code
    to obtain the wechat_code needed for sign_in.

    Args:
        session: requests.Session with necessary cookies
        uni_id: The server-generated uniID from get_qrcode()
        loginuuid: Device fingerprint string
        timeout: Maximum seconds to wait (default: config.QRCODE_TIMEOUT)

    Returns:
        dict: {'success': bool, 'wechat_code': str, 'status': int, 'error': str}
    """
    if timeout is None:
        timeout = config.QRCODE_TIMEOUT

    headers = _build_qr_headers(loginuuid)
    params = {
        'uniID': uni_id,
        'remember': 'true',
        'gray': 'true',
    }

    start_time = time.time()
    poll_count = 0
    last_status = -1
    scanned = False

    while time.time() - start_time < timeout:
        poll_count += 1
        try:
            resp = session.get(
                config.URL_QR_CODE_RESULT,
                headers=headers,
                params=params,
                timeout=config.TIMEOUT_SHORT
            )
            result = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  Poll request failed (retrying): {e}")
            time.sleep(0.5 if scanned else config.QRCODE_POLL_INTERVAL)
            continue
        except ValueError as e:
            print(f"  Failed to parse poll response (retrying): {e}")
            time.sleep(0.5 if scanned else config.QRCODE_POLL_INTERVAL)
            continue

        code = result.get('code', -1)
        if code != 0:
            print(f"  Poll error: code={code}, message={result.get('message', '')}")
            time.sleep(0.5 if scanned else config.QRCODE_POLL_INTERVAL)
            continue

        data = result.get('data', {})
        login_status = data.get('loginStatus', -1)
        scan_platform = data.get('scanPlatform', 0)

        # Print status changes
        if login_status != last_status:
            status_messages = {
                0: "Waiting for scan...",
                1: "Scanned! Waiting for WeChat authorize...",
                2: "Confirmed! Getting wechat_code...",
                3: "QR code expired",
                4: "No valid session",
            }
            msg = status_messages.get(login_status, f"Unknown status: {login_status}")
            print(f"  [{msg}] (platform: {scan_platform})")
            last_status = login_status

        if login_status == LOGIN_STATUS_NO_SESSION:
            return {
                'success': False,
                'wechat_code': None,
                'status': login_status,
                'error': 'No valid session (QR code may have expired)'
            }

        # When scanned or confirmed, aggressively poll wx_code (fast mode)
        if login_status in (LOGIN_STATUS_SCANNED, LOGIN_STATUS_CONFIRMED):
            scanned = True
            wx_result = _get_wx_code(session, uni_id, loginuuid)
            if wx_result['success'] and wx_result['wechat_code']:
                print(f"  [Obtained wechat_code!]")
                return {
                    'success': True,
                    'wechat_code': wx_result['wechat_code'],
                    'status': login_status,
                    'error': None
                }
            # If wx_code not ready yet, continue fast polling

        # Handle expired: try wx_code one last time if we were scanned
        if login_status == LOGIN_STATUS_EXPIRED:
            if scanned:
                print(f"  QR expired but was scanned - last-chance wx_code attempt...")
                wx_result = _get_wx_code(session, uni_id, loginuuid)
                if wx_result['success'] and wx_result['wechat_code']:
                    print(f"  [Obtained wechat_code after expiry!]")
                    return {
                        'success': True,
                        'wechat_code': wx_result['wechat_code'],
                        'status': login_status,
                        'error': None
                    }
            return {
                'success': False,
                'wechat_code': None,
                'status': login_status,
                'error': 'QR code expired'
            }

        # Print periodic update
        if poll_count % 15 == 0 and login_status == LOGIN_STATUS_WAITING:
            elapsed = int(time.time() - start_time)
            remaining = int(timeout - elapsed)
            print(f"  Still waiting... ({elapsed}s elapsed, {remaining}s remaining)")

        # Fast poll (0.5s) when scanned, normal poll (2s) when waiting
        time.sleep(0.5 if scanned else config.QRCODE_POLL_INTERVAL)

    return {
        'success': False,
        'wechat_code': None,
        'status': -1,
        'error': f'QR code scan timeout ({timeout}s)'
    }


def _get_wx_code(session, uni_id, loginuuid):
    """Get wechat_code from the wx_code API endpoint.

    Calls POST /api/user/qr-code/wx_code with the uniID to get the
    wechat_code that's needed for sign_in.

    Args:
        session: requests.Session with necessary cookies
        uni_id: The server-generated uniID
        loginuuid: Device fingerprint string

    Returns:
        dict: {'success': bool, 'wechat_code': str, 'error': str}
    """
    headers = _build_qr_headers(loginuuid)
    payload = {"uniID": uni_id}

    try:
        resp = session.post(
            config.URL_QR_CODE_WX,
            headers=headers,
            json=payload,
            timeout=config.TIMEOUT_SHORT
        )
        result = resp.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'wechat_code': None, 'error': f"Request failed: {e}"}
    except ValueError as e:
        return {'success': False, 'wechat_code': None, 'error': f"Failed to parse response: {e}"}

    code = result.get('code', -1)
    if code != 0:
        return {
            'success': False,
            'wechat_code': None,
            'error': f"API error code={code}: {result.get('message', '')}"
        }

    data = result.get('data', {})
    wechat_code = data.get('wxCode', '') or data.get('wechat_code', '')

    if not wechat_code:
        return {
            'success': False,
            'wechat_code': None,
            'error': 'wxCode is empty (scan may not be complete yet)'
        }

    return {
        'success': True,
        'wechat_code': wechat_code,
        'error': None
    }


def login_with_wechat_code(session, wechat_code, loginuuid):
    """Sign in to 123Pan using the wechat_code obtained from QR scan.

    Calls POST /api/user/sign_in with the wechat_code and type=4 (wechat login).

    Args:
        session: requests.Session with necessary cookies
        wechat_code: The code obtained from QR code scan
        loginuuid: Device fingerprint string

    Returns:
        dict: {'success': bool, 'token': str, 'error': str}
    """
    headers = _build_qr_headers(loginuuid)
    payload = {
        "from": "web",
        "wechat_code": wechat_code,
        "type": 4,
        "remember": True,
        "gray": True,
    }

    try:
        resp = session.post(
            config.URL_SIGN_IN,
            headers=headers,
            json=payload,
            timeout=config.TIMEOUT_MEDIUM
        )
        result = resp.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'token': None, 'error': f"Request failed: {e}"}
    except ValueError as e:
        return {'success': False, 'token': None, 'error': f"Failed to parse response: {e}"}

    code = result.get('code', -1)
    # 123Pan sign_in API returns code=0 for QR login success (code=200 for password login)
    if code not in (0, 200):
        return {
            'success': False,
            'token': None,
            'error': f"Login failed (code={code}): {result.get('message', 'Unknown error')}"
        }

    data = result.get('data', {})

    # Try to get token from JSON response
    token = data.get('token', '')

    # If not in JSON, try to get from cookies
    if not token:
        token = resp.cookies.get('sso-token', '')

    # If still not found, try response headers (set-cookie)
    if not token:
        set_cookie = resp.headers.get('set-cookie', '')
        if 'sso-token=' in set_cookie:
            import re
            match = re.search(r'sso-token=([^;]+)', set_cookie)
            if match:
                token = match.group(1)

    if not token:
        return {
            'success': False,
            'token': None,
            'error': f"No token in login response. Full response: {result}"
        }

    # Clean token (remove 'Bearer ' prefix if present)
    if token.startswith('Bearer '):
        token = token[7:]

    return {
        'success': True,
        'token': token,
        'error': None
    }


def qr_login(timeout=None):
    """Execute the complete QR code login flow.

    This is the main entry point for QR code login. It:
    1. Generates device fingerprint
    2. Visits login page to get necessary cookies
    3. Gets QR code from API (GET /api/user/qr-code/generate)
    4. Saves QR code to qrcode.txt with timestamp
    5. Displays QR code in terminal
    6. Polls for scan status (GET /api/user/qr-code/result)
    7. Gets wechat_code (POST /api/user/qr-code/wx_code)
    8. Signs in with wechat_code (POST /api/user/sign_in)

    Args:
        timeout: Maximum seconds to wait for QR scan (default: config.QRCODE_TIMEOUT)

    Returns:
        dict: {'success': bool, 'token': str, 'loginuuid': str, 'error': str}
    """
    print("\n" + "=" * 60)
    print("  123Pan QR Code Login")
    print("=" * 60)

    # Step 1: Generate device fingerprint
    loginuuid = _generate_loginuuid()
    print(f"  [1/5] Device ID generated: {loginuuid[:16]}...")

    # Step 2: Create session and visit login page to get cookies
    print(f"  [2/5] Initializing session...")
    session = requests.Session()
    try:
        session.get(
            config.LOGIN_PAGE_URL,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            timeout=config.TIMEOUT_SHORT
        )
    except requests.exceptions.RequestException as e:
        print(f"  [Warning: Could not visit login page: {e}]")

    # Step 3: Get QR code
    print(f"  [3/5] Requesting QR code...")
    qr_result = get_qrcode(session, loginuuid)
    if not qr_result['success']:
        print(f"  [Error] Failed to get QR code: {qr_result['error']}")
        return {'success': False, 'token': None, 'loginuuid': loginuuid, 'error': qr_result['error']}

    uni_id = qr_result['uni_id']
    qr_url = qr_result['qr_url']

    # Save QR code to file
    _save_qrcode_to_file(qr_url, uni_id, loginuuid)

    # Display QR code in terminal
    _display_qr_in_terminal(qr_url)

    # Step 4: Poll for scan status
    print(f"  [4/5] Monitoring for scan (timeout: {timeout or config.QRCODE_TIMEOUT}s)...")
    poll_result = poll_qrcode_result(session, uni_id, loginuuid, timeout)
    if not poll_result['success']:
        print(f"  [Error] {poll_result['error']}")
        return {'success': False, 'token': None, 'loginuuid': loginuuid, 'error': poll_result['error']}

    wechat_code = poll_result['wechat_code']

    # Step 5: Sign in with wechat_code
    print(f"  [5/5] Logging in with wechat_code...")
    login_result = login_with_wechat_code(session, wechat_code, loginuuid)
    if not login_result['success']:
        print(f"  [Error] Login failed: {login_result['error']}")
        return {'success': False, 'token': None, 'loginuuid': loginuuid, 'error': login_result['error']}

    token = login_result['token']
    print(f"\n  Login successful! Token: {token[:20]}...")
    print("=" * 60 + "\n")

    return {
        'success': True,
        'token': token,
        'loginuuid': loginuuid,
        'error': None
    }
