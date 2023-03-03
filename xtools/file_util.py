# -*- coding: utf-8 -*-

import os


# import setting


# import sys


# curPath = os.path.abspath(os.path.dirname(__file__))
# rootPath = os.path.split(curPath)[0]
# sys.path.append(rootPath)


# 读取文件内容
def read_file(file_path, mode='r'):
    with open(file_path, mode) as f:
        return f.read()


# 写入文件
def write_file(file_path, content, mode='w'):
    path = os.path.split(file_path)[0]
    if path and (not os.path.exists(path)):
        os.makedirs(path)
    with open(file_path, mode) as f:
        f.write(content)

# if __name__ == "__main__":
#     pass
