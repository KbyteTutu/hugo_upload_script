#!/usr/bin/python
# -*- coding: utf-8 -*-
# @ 南无阿弥陀佛，不要有太多bug……
# @ Author: tukechao
# @ Date: 2022-07-20 21:21:49
# @ LastEditors: tukechao
# @ LastEditTime: 2022-07-21 00:28:54
# @ FilePath: \hugo_upload_script\hugo_upload.py
# @ Description:hugo上传脚本，目标服务器是远程机，本脚本用来将指定目录内的文件遍历并上传到content目录

from config import REMOTE_HUGO_PATH, LOCAL_CONTENT_PATH, HOST, USER, PWD, PORT, SITE_URL
import os
import paramiko
import time
import urllib
from urllib import parse


class HugoUpload():

    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=HOST, port=PORT, username=USER, password=PWD)
        tran = self.ssh.get_transport()
        self.sftp = paramiko.SFTPClient.from_transport(tran)

    def hugo_create(self, path, origin):
        p = REMOTE_HUGO_PATH + "/content" + path
        q = p + ".bak"
        self.ssh.exec_command(f"rm -rf {p}")
        self.ssh.exec_command(f"rm -rf {q}")
        self.sftp.put(origin, q)
        self.ssh.exec_command("cd {} ;hugo new {}".format(
            REMOTE_HUGO_PATH, path.lstrip('/')))
        time.sleep(1)
        self.ssh.exec_command(f"cat {q}>>{p}")
        time.sleep(1)
        self.ssh.exec_command("cd {} ;hugo".format(REMOTE_HUGO_PATH))
        time.sleep(1)

    def prefix_assets(self, file, predir):
        predir = predir.replace('\\', '/') + '/'
        name_asset = os.path.basename(file).replace(".md", ".assets")
        en_name_asset = urllib.parse.quote(name_asset)
        # rewrite piclink for my site
        with open(file, 'r', encoding='utf-8') as f:
            data = f.readlines()

        new = []
        for line in data:
            if en_name_asset in line:
                x = line.replace(en_name_asset, SITE_URL + predir + name_asset)
                new.append(x)
            else:
                new.append(line)

        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(new)

    def hugo_upload_assets(self, file, relative_path):
        name = os.path.basename(file)
        r = REMOTE_HUGO_PATH + '/content' + relative_path.replace('\\',
                                                                  "/") + "/"
        k = r + name
        self.ssh.exec_command(f"mkdir '{r}'")
        time.sleep(1)
        self.sftp.put(os.path.join(file), k)

    def handle_local_file(self):
        for dirpath, _, filenames in os.walk(LOCAL_CONTENT_PATH):
            relative_path = dirpath.replace(LOCAL_CONTENT_PATH, "")

            for name in filenames:
                if name.endswith('.md'):
                    self.prefix_assets(os.path.join(dirpath, name),
                                       relative_path)
                    to_create = os.path.join(relative_path,
                                             name).replace("\\", "/")
                    self.hugo_create(to_create, os.path.join(dirpath, name))
                # according to Typora local pic rules. All files in assets folder need to upload.
                if '.assets' in dirpath:
                    self.hugo_upload_assets(os.path.join(dirpath, name),
                                            relative_path)

        self.ssh.close()


if __name__ == '__main__':
    ins = HugoUpload()
    ins.handle_local_file()
