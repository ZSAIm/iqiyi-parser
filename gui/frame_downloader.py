# -*- coding: utf-8 -*-

import wx
from gui.item_sizer import ItemBoxSizer, format_byte
import time
import CommonVar as cv

COLOR_OK = 1

COLOR_NORMAL = 2
COLOR_ERROR = 3
COLOR_RUN = 4


class FrameMain(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='视频下载器', pos=wx.DefaultPosition,
                          size=wx.Size(-1, 420), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.SetMinSize(wx.Size(390, 420))
        self.SetMaxSize(wx.Size(390, 420))
        self.global_sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer_items = wx.BoxSizer(wx.VERTICAL)
        self.sizer_blocks = wx.WrapSizer(wx.HORIZONTAL)
        self.sizer_total = wx.BoxSizer(wx.HORIZONTAL)

        self.text_name = None
        self.gauge_total = None
        self.text_speed = None
        self.text_percent = None
        self.total = None
        self.text_progress = wx.StaticText(self, wx.ID_ANY, '', wx.DefaultPosition,
                                          wx.DefaultSize, wx.ALIGN_RIGHT)

        self.text_title = wx.StaticText(self, wx.ID_ANY, '', wx.DefaultPosition,
                                          wx.Size(150, -1), wx.ALIGN_LEFT)

        staticline1 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        staticline2 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        staticline3 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)

        self.sizer_top = wx.BoxSizer(wx.HORIZONTAL)

        # self.global_sizer.Add(self.text_title, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer_top.Add(self.text_title, 2, wx.EXPAND | wx.ALL, 5)
        self.sizer_top.Add(self.text_progress, 1, wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, 5)

        self.global_sizer.Add(self.sizer_top, 0, wx.EXPAND | wx.ALL, 5)

        self.global_sizer.Add(staticline1, 0, wx.EXPAND | wx.ALL, 5)
        self.global_sizer.Add(self.sizer_items, 1, wx.ALL | wx.EXPAND, 3)
        self.global_sizer.Add(staticline2, 0, wx.EXPAND | wx.ALL, 5)
        self.global_sizer.Add(self.sizer_blocks, 0, wx.ALL | wx.EXPAND, 5)
        self.global_sizer.Add(staticline3, 0, wx.EXPAND | wx.ALL, 5)
        self.global_sizer.Add(self.sizer_total, 0, wx.ALL | wx.EXPAND, 5)

        self.menu_bar = MainMenuBar(0)
        self.SetMenuBar(self.menu_bar)

        self.SetSizer(self.global_sizer)
        self.Layout()
        self.Center(wx.BOTH)

        self.items_list = []
        self.items_dict = {}
        self.block_list = []

        self.timer = wx.Timer()

        self.timer.SetOwner(self, wx.ID_ANY)



    def initTotal(self, total):
        self.total = total if total > 0 else 0
        self.gauge_total = wx.Gauge(self, wx.ID_ANY, 10000, wx.DefaultPosition, wx.DefaultSize,
                                       wx.GA_HORIZONTAL)
        self.gauge_total.SetValue(0)
        self.text_percent = wx.StaticText(self, wx.ID_ANY, '0%', wx.DefaultPosition,
                                          wx.Size(42, -1), wx.ALIGN_RIGHT)
        self.text_speed = wx.StaticText(self, wx.ID_ANY, '0B/s', wx.DefaultPosition, wx.Size(65, -1),
                                        wx.ALIGN_RIGHT)

        self.text_percent.Wrap(-1)
        self.text_speed.Wrap(-1)

        self.sizer_total.Add(self.text_percent, 0, wx.ALL, 5)
        self.sizer_total.Add(self.gauge_total, 5, wx.ALL | wx.EXPAND, 5)
        self.sizer_total.Add(self.text_speed, 0, wx.ALL, 5)

    def updateTotal(self, current_byte, speed_byte, total_byte=None):
        if total_byte:
            self.total = total_byte
        percent = current_byte * 100.0 / self.total
        progress = '[ %s/%s ]' % (format_byte(current_byte if current_byte > 0 else 0, '%.1f%s'), format_byte(self.total, '%.1f%s'))
        speed = format_byte(speed_byte if speed_byte > 0 else 0, '%.1f%s/s')
        self.text_percent.SetLabelText(str(round(percent, 1)) + '%')
        self.text_speed.SetLabelText(speed)

        self.gauge_total.SetValue(int(percent*100))

        self.text_progress.SetLabelText(progress)
        # self.sizer_total.Layout()
        # self.sizer_top.Layout()

    def initTotal_Merge(self, total):
        self.total = total
        self.text_percent.SetLabelText('0%')
        self.gauge_total.SetValue(0)
        self.text_speed.SetLabelText('0/0')
        # self.sizer_total.Layout()
        # self.sizer_top.Layout()

    def updateMerge(self, cur_index):
        progress = '%d/%d' % (cur_index, self.total)
        percent = cur_index * 100.0 / self.total

        text_percent = str(round(percent, 1)) + '%'

        if text_percent != self.text_percent.GetLabelText():
            self.text_percent.SetLabelText(text_percent)

        self.gauge_total.SetValue(int(percent*100))
        if progress != self.text_speed.GetLabelText():
            self.text_speed.SetLabelText(progress)
        # self.sizer_total.Layout()

    def insertItem(self, id, total_byte, cur_byte=0, speed_byte=0):
        item = ItemBoxSizer(self, cur_byte, total_byte, name=str(id), speed=speed_byte)
        self.items_list.append(item)
        self.items_dict[id] = item

        self.sizer_items.Add(item, 1, wx.ALL | wx.EXPAND, 1)

        # self.sizer_items.Layout()

    def getItem(self, id):
        return self.items_dict.get(id, None)

    def getItemsDict(self):
        return self.items_dict

    def insertBlock(self, id):

        block = wx.StaticText(self, wx.ID_ANY, str(id), wx.DefaultPosition, wx.Size(20, 20),
                              wx.ALIGN_CENTER)
        block.SetBackgroundColour(wx.Colour(144, 144, 144, 255))
        block.SetForegroundColour(wx.Colour(255, 255, 255, 255))
        self.block_list.append(block)
        self.sizer_blocks.Add(block, 0, wx.ALL, 5)
        # self.sizer_items.Layout()
        # self.Layout()


    def updateBlock(self, id, type):
        if type == COLOR_NORMAL:
            self.block_list[id].SetBackgroundColour(wx.Colour(144, 144, 144, 255))
        elif type == COLOR_OK:
            self.block_list[id].SetBackgroundColour(wx.Colour(0, 128, 0, 255))
        elif type == COLOR_RUN:
            self.block_list[id].SetBackgroundColour(wx.Colour(0, 0, 255, 255))
        else:
            self.block_list[id].SetBackgroundColour(wx.Colour(255, 0, 0, 255))

        # self.Layout()

    def deleteItem(self, id, clear_widget=True):
        if self.items_list:
            item = self.items_dict[id]
            self.items_list.remove(item)
            del self.items_dict[id]
            if clear_widget:
                item.Clear(True)
                self.sizer_items.Remove(item)
                # self.Layout()

    def setTitleName(self, text):
        self.text_title.SetLabelText(text)




class MainMenuBar(wx.MenuBar):
    def __init__(self, style):
        wx.MenuBar.__init__(self, style)

        self.file = Menu_File()
        self.help = Menu_Help()

        self.Append(self.file, 'File')
        self.Append(self.help, 'Help')


class Menu_File(wx.Menu):
    def __init__(self, *args):
        wx.Menu.__init__(self, *args)

        self.logs = None
        self.settings = None
        self.exit = None

        self.initMenuItems()

    def initMenuItems(self):
        self.logs = wx.MenuItem(self, wx.ID_ANY, 'Logs', wx.EmptyString, wx.ITEM_NORMAL)
        # self.parse.Enable(False)
        self.settings = wx.MenuItem(self, wx.ID_ANY, 'Settings', wx.EmptyString, wx.ITEM_NORMAL)
        # self.settings.Enable(False)
        self.exit = wx.MenuItem(self, wx.ID_ANY, 'Exit', wx.EmptyString, wx.ITEM_NORMAL)

        self.Append(self.logs)
        self.AppendSeparator()
        self.Append(self.settings)
        self.AppendSeparator()

        self.Append(self.exit)


class Menu_Help(wx.Menu):
    def __init__(self, *args):
        wx.Menu.__init__(self, *args)

        self.about = None

        self.initMenuItems()

    def initMenuItems(self):
        self.about = wx.MenuItem(self, wx.ID_ANY, '&About\tF1', wx.EmptyString, wx.ITEM_NORMAL)
        self.Append(self.about)