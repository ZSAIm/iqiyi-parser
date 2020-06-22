# -*- coding: UTF-8 -*-
import wx
import wx.adv

class DialogAbout(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"About", pos=wx.DefaultPosition,
                           size=wx.Size(350, 400), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        global_sizer = wx.BoxSizer(wx.VERTICAL)
        global_sizer.SetMinSize(wx.Size(350, 350))

        global_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                 wx.BORDER_RAISED | wx.TAB_TRAVERSAL)

        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_panel.Add((0, 20), 0, wx.EXPAND, 5)

        # **************************************  title

        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        text_title = wx.StaticText(global_panel, wx.ID_ANY, u"视频解析下载器v1.7", wx.DefaultPosition,
                                            wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        text_title.Wrap(-1)
        text_title.SetFont(
            wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        sizer_title.Add(text_title, 1, wx.ALIGN_CENTER | wx.ALL, 5)

        # **************************************  Supported Sites

        sizer_support = wx.BoxSizer(wx.VERTICAL)
        text_support = wx.StaticText(global_panel, wx.ID_ANY, u"Supported Sites", wx.DefaultPosition,
                                             wx.DefaultSize, 0)
        text_support.Wrap(-1)
        text_support.SetFont(
            wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))


        text_sites = wx.StaticText(global_panel, wx.ID_ANY, u"爱奇艺、哔哩哔哩、腾讯视频", wx.DefaultPosition,
                                             wx.DefaultSize, 0)
        text_sites.Wrap(-1)

        text_sites.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        sizer_support.Add(text_support, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer_support.Add(text_sites, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # **************************************  Developed by
        sizer_develop = wx.BoxSizer(wx.VERTICAL)

        text_develop = wx.StaticText(global_panel, wx.ID_ANY, u"Developed by:", wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        text_develop.Wrap(-1)

        text_develop.SetFont(
            wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

        text_developed_by = wx.StaticText(global_panel, wx.ID_ANY, u"ZSAIm", wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        text_developed_by.Wrap(-1)

        text_developed_by.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        sizer_develop.Add(text_develop, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer_develop.Add(text_developed_by, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # **************************************  Github links
        sizer_github = wx.BoxSizer(wx.VERTICAL)

        text_github = wx.StaticText(global_panel, wx.ID_ANY, u"Github:", wx.DefaultPosition,
                                               wx.DefaultSize, 0)
        text_github.Wrap(-1)

        text_github.SetFont(
            wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

        sizer_github.Add(text_github, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        link_github = wx.adv.HyperlinkCtrl(global_panel, wx.ID_ANY, u"https://github.com/ZSAIm/iqiyi-parser",
                                                 u"https://github.com/ZSAIm/iqiyi-parser", wx.DefaultPosition,
                                                 wx.DefaultSize, wx.adv.HL_DEFAULT_STYLE)
        sizer_github.Add(link_github, 0, wx.ALIGN_CENTER | wx.ALL, 5)


        sizer_panel.Add(sizer_title, 1, wx.EXPAND, 5)
        sizer_panel.Add((0, 20), 0, wx.EXPAND, 5)
        sizer_panel.Add(sizer_support, 1, wx.EXPAND, 5)
        sizer_panel.Add((0, 20), 0, wx.EXPAND, 5)
        sizer_panel.Add(sizer_develop, 1, wx.EXPAND, 5)
        sizer_panel.Add(sizer_github, 1, wx.EXPAND, 5)
        sizer_panel.Add((0, 20), 1, wx.EXPAND, 5)

        global_panel.SetSizer(sizer_panel)
        global_panel.Layout()
        sizer_panel.Fit(global_panel)
        global_sizer.Add(global_panel, 1, wx.EXPAND | wx.ALL, 5)

        button_ok = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        global_sizer.Add(button_ok, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(global_sizer)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.button_close, button_ok)

        self.Centre(wx.BOTH)

    def button_close(self, event):
        self.Destroy()


    def __del__(self):
        pass


# app = wx.App()
# About_Dialog(None).ShowModal()

