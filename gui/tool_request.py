


import wx


class DialogToolReq(wx.Dialog):
    def __init__(self, parent, title, total_byte, dlm):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=wx.DefaultPosition, size=wx.DefaultSize,
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.global_sizer = wx.BoxSizer(wx.VERTICAL)

        self.gauge_progress = wx.Gauge(self, wx.ID_ANY, 10000, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.gauge_progress.SetValue(524)
        self.global_sizer.Add(self.gauge_progress, 0, wx.ALL | wx.EXPAND, 5)

        sizer_info = wx.BoxSizer(wx.HORIZONTAL)

        self.text_percent = wx.StaticText(self, wx.ID_ANY, u"0.0%", wx.DefaultPosition, wx.DefaultSize,
                                            wx.ALIGN_LEFT)
        self.text_percent.Wrap(-1)

        sizer_info.Add(self.text_percent, 1, wx.ALL, 5)

        self.total_byte = total_byte
        self.format_int = '%0' + str(len(str(self.total_byte))) + 'd/%0' + str(len(str(self.total_byte))) + 'd'

        self.text_progress = wx.StaticText(self, wx.ID_ANY, self.format_int % (0, self.total_byte), wx.DefaultPosition, wx.DefaultSize,
                                            wx.ALIGN_RIGHT)
        self.text_progress.Wrap(-1)

        sizer_info.Add(self.text_progress, 1, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.global_sizer.Add(sizer_info, 1, wx.EXPAND, 5)

        self.SetSizer(self.global_sizer)
        self.Layout()
        self.global_sizer.Fit(self)

        self.Centre(wx.BOTH)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.timer = wx.Timer()

        self.timer.SetOwner(self, wx.ID_ANY)
        self.dlm = dlm

    def update(self, cur_byte, total_bytes=0):
        if total_bytes:
            self.total_byte = total_bytes
        percent = cur_byte * 100.0 / self.total_byte if self.total_byte else 0
        text_percent = str(round(percent, 1)) + '%'
        text_progress = self.format_int % (cur_byte, self.total_byte)
        if text_percent != self.text_percent.GetLabelText():
            self.text_percent.SetLabelText(text_percent)
        if text_progress != self.text_progress.GetLabelText():
            self.text_progress.SetLabelText(text_progress)

        self.gauge_progress.SetValue(int(percent*100))
        self.global_sizer.Layout()

    def onClose(self, event):
        dlg = wx.MessageDialog(self, u'你确定要中止下载吗？', u'提示', style=wx.YES_NO | wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES:
            self.EndModal(wx.ID_ABORT)

