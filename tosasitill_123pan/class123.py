#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
from .sign_get import getSign
import requests
import hashlib
import os
import json
import base64


# Modified version for easier integration into other projects
# Features:
# 1. mkdir() added parentFileId parameter to specify parent folder, will switch to parent folder first
# 2. mkdir() added remake parameter, if remake=False, will check if folder exists first and return folder id if exists
# 3. Added IP ban detection in get_dir new API, will wait 20s and retry if IP is banned
# 4. up_load() added parentFileId parameter to specify parent folder, will switch to parent folder first


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
        self.headerOnlyUsage = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1474.0',
            "app-version": "2",
            "platform": "web", }
        self.headerLogined = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "App-Version": "3",
            "Authorization": self.authorization,
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
            "sec-ch-ua": "^\\^Microsoft",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "^\\^Windows^^"
        }
        self.parentFileId = 0  # 路径，文件夹的id,0为根目录
        self.parentFileList = [0]
        code = self.get_dir()
        if code != 0:
            self.login()
            self.get_dir()

    def login(self):
        """Authenticate with 123Pan Cloud and obtain bearer token
        
        Returns:
            int: Response code (200 for success, other values for failure)
        """
        data = {"remember": True, "passport": self.userName, "password": self.passWord}
        sign = getSign('/b/api/user/sign_in')
        loginRes = requests.post("https://www.123pan.com/b/api/user/sign_in", headers=self.headerOnlyUsage, data=data,
                                 params={sign[0]: sign[1]})
        res_sign = loginRes.json()
        code = res_sign['code']
        if code != 200:
            print("code = 1 Error:" + str(code))
            print(res_sign['message'])
            return code
        token = res_sign['data']['token']
        self.authorization = 'Bearer ' + token
        headerLogined = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "App-Version": "3",
            "Authorization": self.authorization,
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
            "sec-ch-ua": "^\\^Microsoft",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "^\\^Windows^^"
        }
        self.headerLogined = headerLogined
        # ret['cookie'] = cookie
        self.save_file()
        return code

    def save_file(self):
        """Save credentials and authorization token to 123pan.txt file"""
        with open("123pan.txt", "w") as f:
            saveList = {
                "userName": self.userName,
                "passWord": self.passWord,
                "authorization": self.authorization,
            }

            f.write(json.dumps(saveList))
        print("Saved!")

    def get_dir(self):
        """Fetch file list from current directory
        
        Retrieves paginated file listing from 123Pan Cloud. Handles IP ban
        detection and automatically retries after 20 seconds if banned.
        
        Returns:
            int: Response code (0 for success, other values for failure)
        """
        code = 0
        page = 1
        lists = []
        lenth_now = 0
        total = -1
        while lenth_now < total or total == -1:
            base_url = "https://www.123pan.com/b/api/file/list/new"

            # print(self.headerLogined)
            sign = getSign('/b/api/file/list/new')
            print(sign)
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

            a = requests.get(base_url, headers=self.headerLogined, params=params)
            # print(a.text)
            # print(a.headers)
            text = a.json()
            # print(text)
            code = text['code']
            # code = 403
            if code != 0:
                print(a.text)
                print(a.headers)
                print("code = 2 Error:" + str(code))
                if code == 403 or code == "403":
                    print("sleep 20s")
                    time.sleep(20)
                    return self.get_dir()
                return code
            lists_page = text['data']['InfoList']
            lists += lists_page
            total = text['data']['Total']
            lenth_now += len(lists_page)
            page += 1
        FileNum = 0
        for i in lists:
            i["FileNum"] = FileNum
            FileNum += 1

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
                # File: yellow number, cyan filename
                print("\033[33m" + "Number:", self.list.index(i) + 1, "\033[0m \t\t" + size_print + "\t\t\033[36m",
                      i["FileName"], "\033[0m")
            elif i["Type"] == 1:
                # Folder: magenta number, cyan filename
                print("\033[35m" + "Number:", self.list.index(i) + 1, " \t\t\033[36m",
                      i["FileName"], "\033[0m")

        print("--------------------")

    # fileNumber is 0-indexed, 0 is the first file, subtract 1 when passing!
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
            down_request_url = "https://www.123pan.com/a/api/file/batch_download_info"
            down_request_data = {"fileIdList": [{"fileId": int(fileDetail["FileId"])}]}

        else:
            down_request_url = "https://www.123pan.com/a/api/file/download_info"
            down_request_data = {"driveId": 0, "etag": fileDetail["Etag"], "fileId": fileDetail["FileId"],
                                 "s3keyFlag": fileDetail['S3KeyFlag'], "type": fileDetail['Type'],
                                 "fileName": fileDetail['FileName'], "size": fileDetail['Size']}
        # print(down_request_data)

        sign = getSign("/a/api/file/download_info")

        linkRes = requests.post(down_request_url, headers=self.headerLogined, params={sign[0]: sign[1]},
                                data=down_request_data)
        # print(linkRes.text)
        code = linkRes.json()['code']
        if code != 0:
            print("code = 3 Error:" + str(code))
            # print(linkRes.json())
            return code
        downloadLinkBase64 = linkRes.json()["data"]["DownloadUrl"]
        Base64Url = re.findall("params=(.*)&", downloadLinkBase64)[0]
        # print(Base64Url)
        downLoadUrl = base64.b64decode(Base64Url)
        downLoadUrl = downLoadUrl.decode("utf-8")

        nextToGet = requests.get(downLoadUrl).json()
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
        name = fileDetail['FileName']  # File name
        if os.path.exists(name):
            print("File " + name + " already exists, do you want to overwrite?")
            sure = input("Enter 1 to overwrite, 2 to cancel: ")
            if sure != '1':
                return
        down = requests.get(downLoadUrl, stream=True)

        size = int(down.headers['Content-Length'])  # File size
        content_size = int(size)  # Total file size
        data_count = 0  # Current transferred size
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
                # Real-time progress bar
                now_jd = (data_count / content_size) * 100
                # %% represents %
                # Speed calculation
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
        recycle_id = 0
        url = "https://www.123pan.com/a/api/file/list/new?driveId=0&limit=100&next=0&orderBy=fileId&orderDirection=desc&parentFileId=" + str(
            recycle_id) + "&trashed=true&&Page=1"
        recycleRes = requests.get(url, headers=self.headerLogined)
        jsonRecycle = recycleRes.json()
        RecycleList = jsonRecycle['data']['InfoList']
        self.RecycleList = RecycleList

    # fileNumber is 0-indexed, 0 is the first file, subtract 1 when passing!
    def delete_file(self, file, by_num=True, operation=True):
        """Delete or restore a file
        
        Args:
            file: File number (0-indexed) or file detail object
            by_num: If True, file is a number index; if False, file is the detail object
            operation: True for delete, False for restore
        """
        # operation = 'true' for delete, operation = 'false' for restore
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
        dataDelete = {"driveId": 0,
                      "fileTrashInfoList": file_detail,
                      "operation": operation}
        deleteRes = requests.post("https://www.123pan.com/a/api/file/trash", data=json.dumps(dataDelete),
                                  headers=self.headerLogined)
        DeleJson = deleteRes.json()
        print(DeleJson)
        message = DeleJson['message']
        print(message)

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
            data = {"driveId": 0,
                    "expiration": "2024-02-09T11:42:45+08:00",
                    "fileIdList": fileIdList,
                    "shareName": "我的分享",
                    "sharePwd": sharePwd,

                    }
            shareRes = requests.post("https://www.123pan.com/a/api/share/create", headers=self.headerLogined,
                                     data=json.dumps(data))
            shareResJson = shareRes.json()
            message = shareResJson['message']
            print(message)
            ShareKey = shareResJson['data']['ShareKey']
            share_url = 'https://www.123pan.com/s/' + ShareKey
            print('Share link:\n' + share_url + " Extraction code: " + sharePwd)
        else:
            print("Share cancelled")

    def up_load(self, filePath, parentFileId=None, sure=None):
        """Upload a file to 123Pan Cloud (legacy method)
        
        Args:
            filePath: Path to the file to upload
            parentFileId: Parent folder ID (None for current directory)
            sure: Duplicate handling - "1" for keep both, "2" for overwrite
        """
        if parentFileId is None:
            parentFileId = self.parentFileId
            self.cdById(parentFileId)

        filePath = filePath.replace("\"", "")
        filePath = filePath.replace("\\", "/")
        fileName = filePath.split("/")[-1]
        print("File name:", fileName)
        if not os.path.exists(filePath):
            print("File does not exist, please check the path")
            return
        if os.path.isdir(filePath):
            print("Folder upload not supported in this method")
            return
        fsize = os.path.getsize(filePath)
        with open(filePath, 'rb') as f:
            md5 = hashlib.md5()
            while True:
                data = f.read(64 * 1024)
                if not data:
                    break
                md5.update(data)
            readable_hash = md5.hexdigest()

        listUpRequest = {"driveId": 0, "etag": readable_hash, "fileName": fileName,
                         "parentFileId": parentFileId, "size": fsize, "type": 0, "duplicate": 0}

        sign = getSign("/b/api/file/upload_request")
        upRes = requests.post("https://www.123pan.com/b/api/file/upload_request", headers=self.headerLogined,
                              params={sign[0]: sign[1]},
                              data=listUpRequest)
        upResJson = upRes.json()
        code = upResJson['code']
        if code == 5060:
            print("Duplicate file detected")
            if sure is None:
                sure = input("Duplicate file detected. Enter 1 to overwrite, 2 to keep both, 0 to cancel: ")

            if sure == '1':
                listUpRequest["duplicate"] = 1

            elif sure == '2':
                listUpRequest["duplicate"] = 2
            else:
                print("Upload cancelled")
                return
            sign = getSign("/b/api/file/upload_request")
            upRes = requests.post("https://www.123pan.com/b/api/file/upload_request", headers=self.headerLogined,
                                  params={sign[0]: sign[1]},
                                  data=json.dumps(listUpRequest))
            upResJson = upRes.json()
        code = upResJson['code']
        if code == 0:
            # print(upResJson)
            # print("Upload request successful")
            Reuse = upResJson['data']['Reuse']
            if Reuse:
                print("Upload successful, file MD5 reused")
                return
        else:
            print(upResJson)
            print("Upload request failed")
            return

        bucket = upResJson['data']['Bucket']
        StorageNode = upResJson['data']['StorageNode']
        uploadKey = upResJson['data']['Key']
        uploadId = upResJson['data']['UploadId']
        upFileId = upResJson['data']['FileId']  # FileId for upload completion
        print("Upload file ID:", upFileId)

        # Get already uploaded chunks
        startData = {"bucket": bucket, "key": uploadKey, "uploadId": uploadId, "storageNode": StorageNode}
        startRes = requests.post("https://www.123pan.com/b/api/file/s3_list_upload_parts", headers=self.headerLogined,
                                 data=json.dumps(startData))
        startResJson = startRes.json()
        code = startResJson['code']
        if code == 0:
            # print(startResJson)
            pass
        else:
            print(startData)
            print(startResJson)

            print("Failed to get transfer list")
            return

        # Upload in chunks, get link for each chunk
        block_size = 5242880
        with open(filePath, 'rb') as f:
            partNumberStart = 1
            putSize = 0
            while True:
                data = f.read(block_size)

                precent = round(putSize / fsize, 2)
                print("\r已上传：" + str(precent * 100) + "%", end="")
                putSize = putSize + len(data)

                if not data:
                    break
                getLinkData = {"bucket": bucket, "key": uploadKey,
                               "partNumberEnd": partNumberStart + 1,
                               "partNumberStart": partNumberStart,
                               "uploadId": uploadId,
                               "StorageNode": StorageNode}

                getLinkUrl = "https://www.123pan.com/b/api/file/s3_repare_upload_parts_batch"
                getLinkRes = requests.post(getLinkUrl, headers=self.headerLogined, data=json.dumps(getLinkData))
                getLinkResJson = getLinkRes.json()
                code = getLinkResJson['code']
                if code == 0:
                    # print("Got link successfully")
                    pass
                else:
                    print("Failed to get link")
                    # print(getLinkResJson)
                    return
                # print(getLinkResJson)
                uploadUrl = getLinkResJson['data']['presignedUrls'][str(partNumberStart)]
                # print("上传链接",uploadUrl)
                requests.put(uploadUrl, data=data)
                # print("put")

                partNumberStart = partNumberStart + 1

        print("\nProcessing...")
        # Upload completion flag
        # 1. Get already uploaded chunks
        uploadedListUrl = "https://www.123pan.com/b/api/file/s3_list_upload_parts"
        uploadedCompData = {"bucket": bucket, "key": uploadKey, "uploadId": uploadId, "storageNode": StorageNode}
        # print(uploadedCompData)
        requests.post(uploadedListUrl, headers=self.headerLogined, data=json.dumps(uploadedCompData))
        compmultipartUpUrl = "https://www.123pan.com/b/api/file/s3_complete_multipart_upload"
        requests.post(compmultipartUpUrl, headers=self.headerLogined,
                      data=json.dumps(uploadedCompData))

        # 3. Report upload complete, close upload session
        if fsize > 64 * 1024 * 1024:
            time.sleep(3)
        closeUpSessionUrl = "https://www.123pan.com/b/api/file/upload_complete"
        closeUpSessionData = {"fileId": upFileId}
        # print(closeUpSessionData)
        closeUpSessionRes = requests.post(closeUpSessionUrl, headers=self.headerLogined,
                                          data=json.dumps(closeUpSessionData))
        closeResJson = closeUpSessionRes.json()
        # print(closeResJson)
        code = closeResJson['code']
        if code == 0:
            print("Upload successful")
        else:
            print("Upload failed")
            print(closeResJson)
            return

    # dirId is fileNumber, 0-indexed, subtract 1 when passing! (folders seem to be listed first)
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

    def cdById(self, id):
        """Change current directory by folder ID
        
        Args:
            id: Folder ID to navigate to
        """
        self.parentFileId = id
        self.parentFileList.append(self.parentFileId)
        self.get_dir()
        self.get_dir()
        self.show()

    def read_ini(self, user_name, pass_word, input_pwd, authorization="", ):
        """Read credentials from 123pan.txt configuration file
        
        Args:
            user_name: Default username if file read fails
            pass_word: Default password if file read fails
            input_pwd: If True, prompt for credentials when file not found
            authorization: Default authorization token
        """
        try:
            with open("123pan.txt", "r") as f:
                text = f.read()
            text = json.loads(text)
            user_name = text['userName']
            pass_word = text['passWord']
            authorization = text['authorization']

        except FileNotFoundError or json.decoder.JSONDecodeError:
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
        if parentFileId:
            if self.parentFileId != parentFileId:
                self.cdById(parentFileId)
        if not remake:
            for i in self.list:
                if i['FileName'] == dirname:
                    print("Folder already exists")
                    # print(self.list)
                    # print(i)
                    return i['FileId']

        if parentFileId is None:
            parentFileId = self.parentFileId
        url = "https://www.123pan.com/a/api/file/upload_request"
        dataMk = {"driveId": 0, "etag": "", "fileName": dirname, "parentFileId": parentFileId, "size": 0,
                  "type": 1, "duplicate": 1, "NotReuse": True, "event": "newCreateFolder", "operateType": 1}
        sign = getSign("/a/api/file/upload_request")
        resMk = requests.post(url, headers=self.headerLogined, data=json.dumps(dataMk), params={sign[0]: sign[1]})
        try:
            resJson = resMk.json()
        except json.decoder.JSONDecodeError:
            print("Create failed")
            print(resMk.text)
            return
        code = resJson['code']
        if code == 0:
            print("Created successfully")
            self.get_dir()
            return resJson["data"]["Info"]["FileId"]
        else:
            print("Create failed")
            print(resJson)
            return
