# -*- coding: utf-8 -*-
"""

author: ZSAIm

github: https://github.com/ZSAIm/iqiyi-parser

"""


import gui
import wx, time, sys
import GUIEventBinder
import socket
import threading
import flow
import handler
from handler.logs import StdoutPipe

socket.setdefaulttimeout(3)


def main():
    threading.Thread(target=__main__).start()

def __main__():
    wx.CallAfter(flow.Entry.handle)

def wait_thread():
    """can't run while debugging"""
    main_thread = threading.main_thread()
    for i in threading.enumerate():
        if i != main_thread:
            i.join()


if __name__ == '__main__':
    # with open('error.log', 'a+') as ferr:
    #     ferr.write('------------------------\n')
    #     ferr.write('%s\n' % time.asctime(time.localtime(time.time())))
    #     ferr.write('------------------------\n')
    #     sys.stderr = ferr

        gui.init()
        GUIEventBinder.init()

        sys.stdout = StdoutPipe()
        main()
        gui.MainLoop()

        handler.downloader.join()

        # wait_thread()

        pass
