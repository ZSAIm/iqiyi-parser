# -*- coding: UTF-8 -*-

from nbdler import Manager, Request
from worker import Worker


class DownloadWorker(Worker):
    def __init__(self):
        pass

    def getresponse(self):
        """ 返回下载响应。"""




mgr = Manager(maxsize=5, subprocess=True)

task_map = {

}









# def putrequest(request):
#     """ 将下载请求添加入下载管理器，并返回该任务的ID号。"""
#     return mgr.putrequest(request)





def request(*args, **kwargs):
    """ 创建下载请求。"""
    tid = mgr.putrequest(Request(*args, **kwargs))
    return


def response():
    """ """


# def


def create_download_group():
    """ 创建下载组。"""


# def create_downloader()