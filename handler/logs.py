
import sys, time
from threading import Thread, Lock
import gui, wx, io
import CommonVar as cv

class STDRedirect:
    def __init__(self, std):
        self._buff = ''
        self.__console__ = std
        self.list_counter = 0


    def write(self, data):
        self.__console__.write(data)
        if data and not cv.SHUTDOWN:
            self.list_counter += 1
            self._buff += data
            if self.list_counter > 1000:
                wx.CallAfter(gui.dialog_dllog.textctrl_log.Clear)
                wx.CallAfter(gui.dialog_dllog.textctrl_log.AppendText, u'已累计1000条信息，清空缓冲区。\n')
            wx.CallAfter(gui.dialog_dllog.textctrl_log.AppendText, data)


    def flush(self):
        pass
