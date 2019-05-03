import wx
# import wx.xrc
from gui.listctrl import ListCtrl_CopyLink


class DialogCopyLink(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"链接浏览窗口", pos=wx.DefaultPosition, size=wx.Size(500, 500),
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sizer_global = wx.BoxSizer(wx.VERTICAL)

        self.listctrl_links = ListCtrl_CopyLink(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT)
        sizer_global.Add(self.listctrl_links, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer_global)
        self.Layout()

        self.Centre(wx.BOTH)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def __del__(self):
        pass

    def onClose(self, event):
        self.Hide()


# app = wx.App()
# # # frame_main = FrameParser(None)
# # #
# DialogCopyLink(None).Show()
# # # frame_main.Show()
# app.MainLoop()
