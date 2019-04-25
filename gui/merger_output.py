# -*- coding: utf-8 -*-

import wx

EVT_OUTPUT_APPEND = wx.NewId()

class MergerOutput(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u'FFMPEG 输出窗口', pos=wx.DefaultPosition,
                           size=wx.Size(427, 381), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.Size(427, 381), wx.DefaultSize)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.output = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(427, 381),
                                  wx.TE_AUTO_URL | wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB)

        self.output.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "宋体"))

        sizer.Add(self.output, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Layout()

        self.Centre(wx.BOTH)

        self.output.Connect(-1, -1, EVT_OUTPUT_APPEND, self.AppendText)

        self.Bind(wx.EVT_CLOSE, self.onClose)

    def __del__(self):
        pass

    def AppendText(self, event):
        self.output.AppendText(event.text)

    def Clear(self):
        self.output.Clear()

    def onClose(self, event):
        self.Hide()


class MergerOutputAppendEvent(wx.PyEvent):
    def __init__(self, text):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_OUTPUT_APPEND)
        self.text = text

