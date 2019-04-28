# -*- coding: utf-8 -*-

import wx, time

EVT_OUTPUT_APPEND = wx.NewId()
EVT_OUTPUT_UPDATE = wx.NewId()

class FrameMerger(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u'FFMPEG 输出窗口', pos=wx.DefaultPosition,
                           size=wx.Size(427, 450), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.Size(427, 381), wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.textctrl_output = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(427, 381),
                                  wx.TE_AUTO_URL | wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB)

        self.textctrl_output.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "宋体"))

        self.staticline = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)

        self.text_remain = wx.StaticText(self, wx.ID_ANY, u"估计还剩 00:00:00", wx.DefaultPosition, wx.DefaultSize,
                                            wx.ALIGN_RIGHT)
        self.text_remain.Wrap(-1)

        self.gauge_progress = wx.Gauge(self, wx.ID_ANY, 10000, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.gauge_progress.SetValue(0)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.text_percent = wx.StaticText(self, wx.ID_ANY, u"0.0%", wx.DefaultPosition, wx.DefaultSize, 0)
        self.text_percent.Wrap(-1)

        self.text_size = wx.StaticText(self, wx.ID_ANY, u"0kb", wx.DefaultPosition, wx.DefaultSize,
                                            wx.ALIGN_RIGHT)
        self.text_size.Wrap(-1)

        sizer_1.Add(self.text_percent, 1, wx.ALL | wx.EXPAND, 2)
        sizer_1.Add(self.text_size, 1, wx.ALL | wx.EXPAND, 2)

        sizer.Add(self.textctrl_output, 1, wx.ALL | wx.EXPAND, 2)
        sizer.Add(self.staticline, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.text_remain, 0, wx.ALL | wx.EXPAND, 2)
        sizer.Add(self.gauge_progress, 0, wx.ALL | wx.EXPAND, 2)
        sizer.Add(sizer_1, 0, wx.ALL | wx.EXPAND, 3)

        self.menu_bar = MergerMenuBar(0)
        self.SetMenuBar(self.menu_bar)


        self.SetSizer(sizer)
        self.Layout()

        self.Centre(wx.BOTH)

        self.textctrl_output.Connect(-1, -1, EVT_OUTPUT_APPEND, self.AppendText)
        self.gauge_progress.Connect(-1, -1, EVT_OUTPUT_UPDATE, self.update)


    def __del__(self):
        pass

    def AppendText(self, event):
        self.textctrl_output.AppendText(event.text)

    def Clear(self):
        self.textctrl_output.Clear()


    def update(self, event):
        percent = event.cur_len / event.total_len * 100.0

        self.text_percent.SetLabelText('%f%%' % percent)
        self.gauge_progress.SetValue(int(percent*100))

        self.text_remain.SetLabelText('估计还剩 %s' % event.remain_time_str)
        self.text_size.SetLabelText(event.cur_byte_str)
        self.Layout()

class MergerMenuBar(wx.MenuBar):
    def __init__(self, style):
        wx.MenuBar.__init__(self, style)

        self.file = Menu_File()
        self.help = Menu_Help()

        self.Append(self.file, 'File')
        self.Append(self.help, 'Help')


class Menu_File(wx.Menu):
    def __init__(self, *args):
        wx.Menu.__init__(self, *args)

        self.exit = None

        self.initMenuItems()

    def initMenuItems(self):

        self.exit = wx.MenuItem(self, wx.ID_ANY, 'Exit', wx.EmptyString, wx.ITEM_NORMAL)

        self.Append(self.exit)


class Menu_Help(wx.Menu):
    def __init__(self, *args):
        wx.Menu.__init__(self, *args)

        self.about = None

        self.initMenuItems()

    def initMenuItems(self):
        self.about = wx.MenuItem(self, wx.ID_ANY, '&About\tF1', wx.EmptyString, wx.ITEM_NORMAL)
        self.Append(self.about)



class MergerOutputAppendEvent(wx.PyEvent):
    def __init__(self, text):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_OUTPUT_APPEND)
        self.text = text

class MergerOutputUpdateEvent(wx.PyEvent):
    def __init__(self, cur_len, total_len, cur_byte_str, remain_time_str):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_OUTPUT_UPDATE)
        self.cur_len = cur_len
        self.total_len = total_len
        self.cur_byte_str = cur_byte_str
        self.remain_time_str = remain_time_str



# app = wx.App()
# frame_main = FrameMerger(None)
# frame_main.Show()
# dlg.ShowModal()
# app.MainLoop()
