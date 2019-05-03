# -*- coding: utf-8 -*-

import wx


ODD_BGCOLOR = wx.Colour(240, 240, 240, 255)
EVEN_BGCOLOR = wx.Colour(255, 255, 255, 255)

class ListCtrl_Parser(wx.ListCtrl):
    def __init__(self, *args):
        wx.ListCtrl.__init__(self, *args)
        self.initColumn()

        self.menu = Menu_Parser()
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)

    def initColumn(self):
        self.AppendColumn('Q', format=wx.LIST_FORMAT_RIGHT, width=50)
        self.AppendColumn('分辨率', format=wx.LIST_FORMAT_CENTER, width=80)
        self.AppendColumn('N', format=wx.LIST_FORMAT_RIGHT, width=40)
        self.AppendColumn('视频大小', width=80, format=wx.LIST_FORMAT_RIGHT)
        self.AppendColumn('音频', width=50, format=wx.LIST_FORMAT_CENTER)
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

    def OnContextMenu(self, event):
        if self.GetFirstSelected() != -1:
            self.PopupMenu(self.menu, event.GetPosition())


class Menu_Parser(wx.Menu):
    def __init__(self, *args):
        wx.Menu.__init__(self, *args)
        self.godownload = None
        self.copylinks = None

        self.initItems()

    def initItems(self):
        self.godownload = wx.MenuItem(self, wx.ID_ANY, u'下载所选项', wx.EmptyString, wx.ITEM_NORMAL)
        self.Append(self.godownload)

        self.AppendSeparator()

        self.copylinks = wx.MenuItem(self, wx.ID_ANY, u'复制下载链接', wx.EmptyString, wx.ITEM_NORMAL)
        self.Append(self.copylinks)

        # self.copylinks.Enable(False)



class ListCtrl_CopyLink(wx.ListCtrl):
    def __init__(self, *args):
        wx.ListCtrl.__init__(self, *args)
        self.initColumn()

        self.menu = Menu_CopyLink()
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)

    def initColumn(self):
        self.AppendColumn('N', format=wx.LIST_FORMAT_RIGHT, width=50)
        self.AppendColumn('链接', format=wx.LIST_FORMAT_CENTER, width=40)
        self.AppendColumn('内容', format=wx.LIST_FORMAT_CENTER, width=40)
        self.AppendColumn('类型', format=wx.LIST_FORMAT_CENTER, width=40)
        # self.AppendColumn('音频', format=wx.LIST_FORMAT_CENTER, width=40)
        self.AppendColumn('预览', width=260, format=wx.LIST_FORMAT_LEFT)
        # self.AppendColumn('音频', width=50, format=wx.LIST_FORMAT_CENTER)
        # self.AppendColumn('格式', width=50, format=wx.LIST_FORMAT_LEFT)
        # self.AppendColumn('M3U8', width=50, format=wx.LIST_FORMAT_CENTER)

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

    def OnContextMenu(self, event):
        if self.GetFirstSelected() != -1:
            self.PopupMenu(self.menu, event.GetPosition())


class Menu_CopyLink(wx.Menu):
    def __init__(self, *args):
        wx.Menu.__init__(self, *args)
        # self.godownload = None
        self.copysel = None
        self.copygroup = None

        self.initItems()

    def initItems(self):

        self.copysel = wx.MenuItem(self, wx.ID_ANY, u'复制所选项', wx.EmptyString, wx.ITEM_NORMAL)
        self.Append(self.copysel)

        self.AppendSeparator()

        self.copygroup = wx.MenuItem(self, wx.ID_ANY, u'复制所在组所有链接', wx.EmptyString, wx.ITEM_NORMAL)
        self.Append(self.copygroup)

