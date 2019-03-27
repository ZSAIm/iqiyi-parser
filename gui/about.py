# -*- coding: utf-8 -*-

import wx
import wx.adv

class About_Dialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"About", pos=wx.DefaultPosition, size=wx.Size(348, 385),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        bSizer9 = wx.BoxSizer(wx.VERTICAL)

        panel3 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                 wx.BORDER_RAISED | wx.TAB_TRAVERSAL)
        panel3.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        bSizer10 = wx.BoxSizer(wx.VERTICAL)

        staticText181 = wx.StaticText(panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                             wx.DefaultSize, 0)
        staticText181.Wrap(-1)

        bSizer10.Add(staticText181, 0, wx.ALL, 5)

        staticText17 = wx.StaticText(panel3, wx.ID_ANY, u"爱奇艺解析下载器", wx.DefaultPosition,
                                            wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        staticText17.Wrap(-1)

        staticText17.SetFont(
            wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

        bSizer10.Add(staticText17, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        staticText18 = wx.StaticText(panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        staticText18.Wrap(-1)

        bSizer10.Add(staticText18, 0, wx.ALL, 5)

        staticText10 = wx.StaticText(panel3, wx.ID_ANY, u"Developed by:", wx.DefaultPosition,
                                            wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        staticText10.Wrap(-1)

        staticText10.SetFont(
            wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

        bSizer10.Add(staticText10, 0, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 5)

        staticText101 = wx.StaticText(panel3, wx.ID_ANY, u"ZSAIm", wx.DefaultPosition, wx.DefaultSize,
                                             wx.ALIGN_CENTER_HORIZONTAL)
        staticText101.Wrap(-1)

        staticText101.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        bSizer10.Add(staticText101, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        staticText19 = wx.StaticText(panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        staticText19.Wrap(-1)

        bSizer10.Add(staticText19, 0, wx.ALL, 5)

        staticText102 = wx.StaticText(panel3, wx.ID_ANY, u"Github:", wx.DefaultPosition, wx.DefaultSize,
                                             wx.ALIGN_CENTER_HORIZONTAL)
        staticText102.Wrap(-1)

        staticText102.SetFont(
            wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

        bSizer10.Add(staticText102, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        hyperlink1 = wx.adv.HyperlinkCtrl(panel3, wx.ID_ANY,
                                                 u"https://github.com/ZSAIm/iqiyi-parser",
                                                 u"https://github.com/ZSAIm/iqiyi-parser", wx.DefaultPosition,
                                                 wx.DefaultSize, wx.adv.HL_ALIGN_CENTRE | wx.adv.HL_DEFAULT_STYLE)
        hyperlink1.SetFont(
            wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                    False, wx.EmptyString))
        hyperlink1.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        bSizer10.Add(hyperlink1, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        staticText21 = wx.StaticText(panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        staticText21.Wrap(-1)

        bSizer10.Add(staticText21, 0, wx.ALL, 5)

        panel3.SetSizer(bSizer10)
        panel3.Layout()
        bSizer10.Fit(panel3)
        bSizer9.Add(panel3, 1, wx.EXPAND | wx.ALL, 10)

        button7 = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer9.Add(button7, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.close, button7)

        self.SetSizer(bSizer9)
        self.Layout()

        self.Centre(wx.BOTH)

    def close(self, event):
        self.Destroy()

    def __del__(self):
        pass


