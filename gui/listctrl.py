# -*- coding: utf-8 -*-

import wx


ODD_BGCOLOR = wx.Colour(240, 240, 240, 255)
EVEN_BGCOLOR = wx.Colour(255, 255, 255, 255)

class ListCtrl_Parser(wx.ListCtrl):
    def __init__(self, *args):
        wx.ListCtrl.__init__(self, *args)

        self.initColumn()

    def initColumn(self):
        self.AppendColumn('bid', format=wx.LIST_FORMAT_LEFT, width=50)
        self.AppendColumn('分辨率', format=wx.LIST_FORMAT_LEFT, width=80)
        self.AppendColumn('文件数', format=wx.LIST_FORMAT_LEFT, width=50)
        self.AppendColumn('大小', width=100, format=wx.LIST_FORMAT_RIGHT)
        self.AppendColumn('格式', width=50, format=wx.LIST_FORMAT_LEFT)
        self.AppendColumn('M3U8', width=50, format=wx.LIST_FORMAT_CENTER)


    def Append(self, entry, fgcolor=None):
        wx.ListCtrl.Append(self, entry)
        item_count = self.GetItemCount()
        if not item_count % 2:
            self.SetItemBackgroundColour(item_count - 1, ODD_BGCOLOR)

        if fgcolor:
            self.SetItemTextColour(item_count-1, wx.Colour(fgcolor))




    def DeleteItem(self, item):
        wx.ListCtrl.DeleteItem(self, item)
        item_count = self.GetItemCount()
        odd = True if item % 2 else False

        for i in range(item_count - item):

            self.SetItemBackgroundColour(i + item, ODD_BGCOLOR if odd else EVEN_BGCOLOR)

            odd = not odd

