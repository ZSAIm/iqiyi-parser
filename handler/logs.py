
import sys, time
from threading import Thread, Lock
import gui, wx

class StdoutPipe:
    def __init__(self):
        self._buff = []
        self.__console__ = sys.stdout
        self._writhread = Thread(target=self._writethread, daemon=True).start()
        self.list_counter = 0

    def write(self, data):
        self._buff.append(data)
        self.__console__.write(data)


    def _writethread(self):
        while True:
            if self._buff:
                line_text = self._buff.pop(0)
                if line_text.strip():
                    self.list_counter += 1
                    if self.list_counter > 1000:
                        wx.CallAfter(gui.dialog_dllog.listctrl_log.DeleteAllItems)
                        wx.CallAfter(gui.dialog_dllog.listctrl_log.Append, (u'已累计1000条信息，清空缓冲区。',))
                    wx.CallAfter(gui.dialog_dllog.listctrl_log.Append, (str(line_text.strip()),))
            time.sleep(0.1)


    def print_stdconsole(self):
        self.__console__.write()

    def flush(self):
        # self._buff = ''
        pass

    # def

