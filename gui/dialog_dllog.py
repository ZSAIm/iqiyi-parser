import wx
# import wx.xrc
from gui.listctrl import ListCtrl_DLLog
import threading, time
# import io

EVT_DLLOG_APPEND = wx.NewId()


class DialogDLLog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"下载器日志", pos=wx.DefaultPosition, size=wx.Size(500, 500),
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sizer_global = wx.BoxSizer(wx.VERTICAL)

        self.listctrl_log = ListCtrl_DLLog(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT)
        sizer_global.Add(self.listctrl_log, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer_global)
        self.Layout()

        self.Centre(wx.BOTH)
        self.Bind(wx.EVT_CLOSE, self.onClose)


    def __del__(self):
        pass

    def onClose(self, event):
        self.Hide()

    def start_logger(self, stdout):
        threading.Thread(target=self._stdout_thread, name='log_stdout_read_thread', daemon=True, args=(stdout,)).start()

    def _stdout_thread(self, stdout):
        while True:
            time.sleep(0.1)
            line_text = stdout.readline()
            while line_text:
                self.listctrl_log.Append((line_text,))

    def append_log(self, event):
        self.listctrl_log.Append(event.data)





class DialogDLLogAppendEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DLLOG_APPEND)
        self.data = data


# app = wx.App()
# # # frame_main = FrameParser(None)
# # #
# DialogCopyLink(None).Show()
# # # frame_main.Show()
# app.MainLoop()
