#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import os
import json
import base64
import requests
from .sign_get import getSign
from . import config


class Pan123:
    """123Pan Cloud Storage API Client

    This class provides methods to interact with 123Pan Cloud Storage service.
    Features include login, file listing, upload, download, and directory management.

    Args:
        readfile: If True, read credentials from 123pan.txt file (default: True)
        user_name: Username for login (used if readfile=False)
        pass_word: Password for login (used if readfile=False)
        authorization: Bearer token for authentication (optional)
        input_pwd: If True, prompt for credentials when not available (default: True)
    """

    _header_base = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1474.0',
        "app-version": "2",
        "platform": "web",
    }

    _header_authenticated_template = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "App-Version": "3",
        "Authorization": "",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "LoginUuid": "z-uk_yT8HwR4raGX1gqGk",
        "Pragma": "no-cache",
        "Referer": "https://www.123pan.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "platform": "web",
        "sec-ch-ua": "^\"^Microsoft",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "^\"^Windows^^"
    }

    def __init__(self, readfile=True, user_name="", pass_word="", authorization="", input_pwd=True):
        self.RecycleList = None
        self.list = None
        if readfile:
            self.read_ini(user_name, pass_word, input_pwd, authorization)
        else:
            if user_name == "" or pass_word == "":
                print("Read disabled, username or password is empty")
                if input_pwd:
                    user_name = input("Please enter username:")
                    pass_word = input("Please enter password:")
                else:
                    raise Exception("Username or password is empty: When read is disabled, userName and passWord cannot be empty")
            self.userName = user_name
            self.passWord = pass_word
            self.authorization = authorization

        self.headerOnlyUsage = self._header_base.copy()
        self.headerLogined = self._build_auth_header()
        self.parentFileId = 0
        self.parentFileList = [0]
        code = self.get_dir()
        if code != 0:
            self.login()
            self.get_dir()

    def _build_auth_header(self):
        header = self._header_authenticated_template.copy()
        header["Authorization"] = self.authorization
        return header

    def _update_auth_header(self):
        self.authorization = getattr(self, 'authorization', '')
        self.headerLogined = self._build_auth_header()

    def login(self):
        """Authenticate with 123Pan Cloud and obtain bearer token

        Returns:
            int: Response code (200 for success, other values for failure)
        """
        data = {"remember": True, "passport": self.userName, "password": self.passWord}
        sign = getSign('/b/api/user/sign_in')
        try:
            loginRes = requests.post(
                config.URL_123PAN_SIGN_IN,
                headers=self.headerOnlyUsage,
                data=data,
                params={sign[0]: sign[1]},
                timeout=config.TIMEOUT_SHORT
            )
            res_sign = loginRes.json()
        except requests.exceptions.RequestException as e:
            print(f"Login request failed: {e}")
            return -1

        code = res_sign['code']
        if code != 200:
            print(f"code = 1 Error: {code}")
            print(res_sign.get('message', ''))
            return code
        token = res_sign['data']['token']
        self.authorization = 'Bearer ' + token
        self._update_auth_header()
        self.save_file()
        return code

    def save_file(self):
        """Save credentials and authorization token to 123pan.txt file"""
        try:
            with open(config.CREDENTIALS_FILE, "w") as f:
                saveList = {
                    "userName": self.userName,
                    "passWord": self.passWord,
                    "authorization": self.authorization,
                }
                f.write(json.dumps(saveList))
            print("Saved!")
        except OSError as e:
            print(f"Failed to save credentials: {e}")

    def get_dir(self, _recursion_depth=0):
        """Fetch file list from current directory

        Retrieves paginated file listing from 123Pan Cloud. Handles IP ban
        detection and automatically retries after 20 seconds if banned.

        Args:
            _recursion_depth: Internal counter to prevent infinite recursion (max 3 retries)

        Returns:
            int: Response code (0 for success, other values for failure)
        """
        if _recursion_depth >= 3:
            print("get_dir: Max retry count reached, giving up")
            return -1

        code = 0
        page = 1
        lists = []
        lenth_now = 0
        total = -1
        while lenth_now < total or total == -1:
            sign = getSign('/b/api/file/list/new')
            params = {
                sign[0]: sign[1],
                "driveId": 0,
                "limit": 100,
                "next": 0,
                "orderBy": "file_id",
                "orderDirection": "desc",
                "parentFileId": str(self.parentFileId),
                "trashed": False,
                "SearchData": "",
                "Page": str(page),
                "OnlyLookAbnormalFile": 0
            }

            try:
                a = requests.get(config.URL_FILE_LIST, headers=self.headerLogined, params=params, timeout=config.TIMEOUT_MEDIUM)
            except requests.exceptions.RequestException as e:
                print(f"get_dir: Request failed: {e}")
                return -1

            try:
                text = a.json()
            except ValueError as e:
                print(f"get_dir: Failed to parse response: {e}")
                return -1

            code = text['code']
            if code != 0:
                print(f"get_dir: Error code={code}: {a.text}")
                if code == 403:
                    print("get_dir: IP banned, sleeping 20s...")
                    time.sleep(20)
                    return self.get_dir(_recursion_depth=_recursion_depth + 1)
                return code
            lists_page = text['data']['InfoList']
            lists += lists_page
            total = text['data']['Total']
            lenth_now += len(lists_page)
            page += 1

        for i, item in enumerate(lists):
            item["FileNum"] = i

        self.list = lists
        return code

    def show(self):
        """Display current directory listing with file numbers, sizes and names"""
        print("--------------------")
        for i in self.list:
            size = i["Size"]
            if size > 1048576:
                size_print = str(round(size / 1048576, 2)) + "M"
            else:
                size_print = str(round(size / 1024, 2)) + "K"

            if i["Type"] == 0:
                print("\033[33m" + "Number:", self.list.index(i) + 1, "\033[0m \t\t" + size_print + "\t\t\033[36m",
                      i["FileName"], "\033[0m")
            elif i["Type"] == 1:
                print("\033[35m" + "Number:", self.list.index(i) + 1, " \t\t\033[36m",
                      i["FileName"], "\033[0m")

        print("--------------------")

    def link(self, file_number, showlink=True):
        """Get download link for a file

        Args:
            file_number: 0-indexed file number in the current directory listing
            showlink: If True, print the download link (default: True)

        Returns:
            str: Direct download URL, or error code on failure
        """
        fileDetail = self.list[file_number]
        typeDetail = fileDetail['Type']
        if typeDetail == 1:
            down_request_url = config.URL_BATCH_DOWNLOAD_INFO
            down_request_data = {"fileIdList": [{"fileId": int(fileDetail["FileId"])}]}
        else:
            down_request_url = config.URL_DOWNLOAD_INFO
            down_request_data = {
                "driveId": 0, "etag": fileDetail["Etag"], "fileId": fileDetail["FileId"],
                "s3keyFlag": fileDetail['S3KeyFlag'], "type": fileDetail['Type'],
                "fileName": fileDetail['FileName'], "size": fileDetail['Size']
            }

        sign = getSign("/a/api/file/download_info")
        try:
            linkRes = requests.post(
                down_request_url,
                headers=self.headerLogined,
                params={sign[0]: sign[1]},
                json=down_request_data,
                timeout=config.TIMEOUT_MEDIUM
            )
            res_json = linkRes.json()
        except requests.exceptions.RequestException as e:
            print(f"link: Request failed: {e}")
            return -1
        except ValueError as e:
            print(f"link: Failed to parse response: {e}")
            return -1

        code = res_json['code']
        if code != 0:
            print(f"link: Error code={code}")
            return code

        downloadLinkBase64 = res_json["data"]["DownloadUrl"]
        Base64Url = re.findall("params=(.*)&", downloadLinkBase64)[0]
        downLoadUrl = base64.b64decode(Base64Url).decode("utf-8")

        try:
            nextToGet = requests.get(downLoadUrl, timeout=config.TIMEOUT_SHORT).json()
        except requests.exceptions.RequestException as e:
            print(f"link: Failed to get redirect URL: {e}")
            return -1

        redirect_url = nextToGet['data']['redirect_url']
        if showlink:
            print(redirect_url)

        return redirect_url

    def download(self, file_number):
        """Download a file from 123Pan Cloud

        Args:
            file_number: 0-indexed file number in the current directory listing
        """
        fileDetail = self.list[file_number]
        downLoadUrl = self.link(file_number, showlink=False)
        name = fileDetail['FileName']
        if os.path.exists(name):
            print(f"File {name} already exists, do you want to overwrite?")
            sure = input("Enter 1 to overwrite, 2 to cancel: ")
            if sure != '1':
                return
        try:
            down = requests.get(downLoadUrl, stream=True, timeout=config.TIMEOUT_LONG)
        except requests.exceptions.RequestException as e:
            print(f"download: Request failed: {e}")
            return

        size = int(down.headers['content-length'])
        content_size = int(size)
        data_count = 0
        if size > 1048576:
            size_print = str(round(size / 1048576, 2)) + "M"
        else:
            size_print = str(round(size / 1024, 2)) + "K"
        print(name + "    " + size_print)
        time1 = time.time()
        time_temp = time1
        data_count_temp = 0
        with open(name, "wb") as f:
            for i in down.iter_content(1024):
                f.write(i)
                done_block = int((data_count / content_size) * 50)
                data_count = data_count + len(i)
                now_jd = (data_count / content_size) * 100
                time1 = time.time()
                pass_time = time1 - time_temp
                if pass_time > 1:
                    time_temp = time1
                    pass_data = int(data_count) - int(data_count_temp)
                    data_count_temp = data_count
                    speed = pass_data / int(pass_time)
                    speed_M = speed / 1048576
                    if speed_M > 1:
                        speed_print = str(round(speed_M, 2)) + "M/S"
                    else:
                        speed_print = str(round(speed_M * 1024, 2)) + "K/S"
                    print(
                        "\r [%s%s] %d%%  %s" % (done_block * '█', ' ' * (50 - 1 - done_block), now_jd, speed_print),
                        end="")
                elif data_count == content_size:
                    print("\r [%s%s] %d%%  %s" % (50 * '█', '', 100, ""), end="")
        print("\nok")

    def recycle(self):
        """Fetch list of files in the recycle bin"""
        url = f"{config.BASE_URL}/b/api/file/list/new?driveId=0&limit=100&next=0&orderBy=fileId&orderDirection=desc&parentFileId=0&trashed=true&Page=1"
        try:
            recycleRes = requests.get(url, headers=self.headerLogined, timeout=config.TIMEOUT_MEDIUM)
            jsonRecycle = recycleRes.json()
            self.RecycleList = jsonRecycle['data']['InfoList']
        except requests.exceptions.RequestException as e:
            print(f"recycle: Request failed: {e}")
        except (KeyError, ValueError) as e:
            print(f"recycle: Failed to parse response: {e}")

    def delete_file(self, file, by_num=True, operation=True):
        """Delete or restore a file

        Args:
            file: File number (0-indexed) or file detail object
            by_num: If True, file is a number index; if False, file is the detail object
            operation: True for delete, False for restore
        """
        if by_num:
            if not str(file).isdigit():
                print("Please enter a number")
                return -1
            if 0 <= file < len(self.list):
                file_detail = self.list[file]
            else:
                print("Out of valid range")
                return
        else:
            if file in self.list:
                file_detail = file
            else:
                print("File not found")
                return

        dataDelete = {
            "driveId": 0,
            "fileTrashInfoList": file_detail,
            "operation": operation
        }
        try:
            deleteRes = requests.post(
                config.URL_FILE_TRASH,
                headers=self.headerLogined,
                json=dataDelete,
                timeout=config.TIMEOUT_SHORT
            )
            DeleJson = deleteRes.json()
            print(DeleJson)
            print(DeleJson.get('message', ''))
        except requests.exceptions.RequestException as e:
            print(f"delete_file: Request failed: {e}")
        except ValueError as e:
            print(f"delete_file: Failed to parse response: {e}")

    def share(self):
        """Create a share link for selected files"""
        fileIdList = ""
        share_name_list = []
        add = '1'
        while str(add) == '1':
            share_num = input("Enter file number to share: ")
            num_test2 = share_num.isdigit()
            if num_test2:
                share_num = int(share_num)
                if 0 < share_num < len(self.list) + 1:
                    share_id = self.list[int(share_num) - 1]['FileId']
                    share_name = self.list[int(share_num) - 1]['FileName']
                    share_name_list.append(share_name)
                    print(share_name_list)
                    fileIdList = fileIdList + str(share_id) + ","
                    add = input("Enter 1 to add more files, 0 to create share, other to cancel: ")
            else:
                print("Please enter a number")
                add = "1"

        if str(add) == "0":
            sharePwd = input("Extraction code (leave empty for none): ")
            fileIdList = fileIdList.strip(',')
            data = {
                "driveId": 0,
                "expiration": "2030-12-31T23:59:59+08:00",
                "fileIdList": fileIdList,
                "shareName": "My Share",
                "sharePwd": sharePwd,
            }
            try:
                shareRes = requests.post(
                    config.URL_SHARE_CREATE,
                    headers=self.headerLogined,
                    json=data,
                    timeout=config.TIMEOUT_SHORT
                )
                shareResJson = shareRes.json()
                message = shareResJson.get('message', '')
                print(message)
                ShareKey = shareResJson['data']['ShareKey']
                share_url = f"{config.BASE_URL}/s/{ShareKey}"
                print(f"Share link:\n{share_url} Extraction code: {sharePwd}")
            except requests.exceptions.RequestException as e:
                print(f"share: Request failed: {e}")
            except (KeyError, ValueError) as e:
                print(f"share: Failed to parse response: {e}")
        else:
            print("Share cancelled")

    def cd(self, dir_num):
        """Change current directory

        Args:
            dir_num: Directory number (1-indexed), '..' for parent, '/' for root
        """
        if not dir_num.isdigit():
            if dir_num == "..":
                if len(self.parentFileList) > 1:
                    self.parentFileList.pop()
                    self.parentFileId = self.parentFileList[-1]
                    self.get_dir()
                    self.show()
                else:
                    print("Already at root directory")
                return
            elif dir_num == "/":
                self.parentFileId = 0
                self.parentFileList = [0]
                self.get_dir()
                self.show()
                return
            else:
                print("Invalid input")
                return
        dir_num = int(dir_num) - 1
        if dir_num >= (len(self.list) - 1) or dir_num < 0:
            print("Invalid input")
            return
        if self.list[dir_num]['Type'] != 1:
            print("Not a folder")
            return
        self.parentFileId = self.list[dir_num]['FileId']
        self.parentFileList.append(self.parentFileId)
        self.get_dir()
        self.show()

    def cdById(self, id, _recursion_depth=0):
        """Change current directory by folder ID

        Args:
            id: Folder ID to navigate to
            _recursion_depth: Internal counter to prevent infinite recursion from get_dir() retries
        """
        if _recursion_depth >= 3:
            print("cdById: Max retry count reached, giving up")
            return
        self.parentFileId = id
        self.parentFileList.append(self.parentFileId)
        code = self.get_dir(_recursion_depth=_recursion_depth)
        self.show()
        if code != 0:
            print(f"cdById: Warning - get_dir returned code {code}")

    def read_ini(self, user_name, pass_word, input_pwd, authorization=""):
        """Read credentials from 123pan.txt configuration file

        Args:
            user_name: Default username if file read fails
            pass_word: Default password if file read fails
            input_pwd: If True, prompt for credentials when file not found
            authorization: Default authorization token
        """
        try:
            with open(config.CREDENTIALS_FILE, "r") as f:
                text = f.read()
            text = json.loads(text)
            user_name = text['userName']
            pass_word = text['passWord']
            authorization = text['authorization']
        except (FileNotFoundError, json.decoder.JSONDecodeError, KeyError):
            print("Read failed")

            if user_name == "" or pass_word == "":
                if input_pwd:
                    user_name = input("Username:")
                    pass_word = input("Password:")
                    authorization = ""
                else:
                    raise Exception("Input mode disabled, no username or password")

        self.userName = user_name
        self.passWord = pass_word
        self.authorization = authorization

    def mkdir(self, dirname, parentFileId=None, remake=False):
        """Create a directory in 123Pan Cloud

        Args:
            dirname: Name of the directory to create
            parentFileId: Parent folder ID (None for current directory)
            remake: If False, check if folder exists first and return its ID

        Returns:
            int: Folder ID if successful, None otherwise
        """
        target_parent = parentFileId if parentFileId is not None else self.parentFileId

        if target_parent != self.parentFileId:
            self.cdById(target_parent)

        if not remake:
            for i in self.list:
                if i['FileName'] == dirname:
                    print("Folder already exists")
                    return i['FileId']

        if parentFileId is None:
            parentFileId = self.parentFileId

        dataMk = {
            "driveId": 0, "etag": "", "fileName": dirname,
            "parentFileId": parentFileId, "size": 0,
            "type": 1, "duplicate": 1, "NotReuse": True,
            "event": "newCreateFolder", "operateType": 1
        }
        sign = getSign("/a/api/file/upload_request")
        try:
            resMk = requests.post(
                config.URL_UPLOAD_REQUEST,
                headers=self.headerLogined,
                json=dataMk,
                params={sign[0]: sign[1]},
                timeout=config.TIMEOUT_SHORT
            )
            resJson = resMk.json()
        except requests.exceptions.RequestException as e:
            print(f"mkdir: Request failed: {e}")
            return None
        except ValueError:
            print("mkdir: Create failed (invalid JSON response)")
            print(f"mkdir: Response text: {resMk.text}")
            return None

        code = resJson.get('code')
        if code == 0:
            print("Created successfully")
            self.get_dir()
            return resJson["data"]["Info"]["FileId"]
        else:
            print(f"mkdir: Create failed, code={code}")
            print(resJson)
            return None
