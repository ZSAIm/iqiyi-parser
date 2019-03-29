# -*- coding: utf-8 -*-
import wx
import gui
import socket
import iqiyi_parse as iqiyi
import pyperclip

def init():
    FrameMain_Menu_File_Handler.bindEvent()
    FrameParse_Button_Handler.bindEvent()
    FrameMain_Menu_Help_Handler.bindEvent()


def bindMenuItems(handler_parent, source_parent, items_name):
    for i in items_name:
        gui.frame_main.Bind(wx.EVT_MENU, getattr(handler_parent, i), getattr(source_parent, i))



class FrameMain_Menu_File_Handler:
    @staticmethod
    def bindEvent():
        items = ('parse', 'settings', 'exit')
        bindMenuItems(FrameMain_Menu_File_Handler, gui.frame_main.menu_bar.file, items)


    @staticmethod
    def parse(event):
        pass


    @staticmethod
    def settings(event):
        pass


    @staticmethod
    def exit(event):
        exit(0)

class FrameMain_Menu_Help_Handler:
    @staticmethod
    def bindEvent():
        items = ('about', )
        bindMenuItems(FrameMain_Menu_Help_Handler, gui.frame_main.menu_bar.help, items)


    @staticmethod
    def about(event):
        dlg = gui.About_Dialog(gui.frame_main)
        dlg.ShowModal()
        dlg.Destroy()


def bindButtonEvent(handler_parent, source_parent, items_name):
    for i in items_name:
        gui.frame_parse.Bind(wx.EVT_BUTTON, getattr(handler_parent, i), getattr(source_parent, 'button_' + i))



class FrameParse_Button_Handler:
    @staticmethod
    def bindEvent():
        items = ('parse', 'path', 'godownload', 'copyurl')
        bindButtonEvent(FrameParse_Button_Handler, gui.frame_parse, items)


    @staticmethod
    def parse(event):
        url = gui.frame_parse.textctrl_url.GetLineText(0)
        bid = []
        for i in range(1, 7):
            if getattr(gui.frame_parse, 'checkbox_%d' % (i * 100)).IsChecked():
                bid.append(i*100)
        try:
            videoname, res = iqiyi.parse(url, bid)
        except socket.timeout as e:
            dlg = wx.MessageDialog(gui.frame_parse, u'网络超时,请重试！', u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
        else:
            gui.frame_parse.listctrl_parse.DeleteAllItems()
            for i, j in res.items():

                data = (i, j['scrsz'], str(len(j['fs'])), gui.format_byte(j['vsize'], '%.1f%s'), j['ff'])
                gui.frame_parse.listctrl_parse.Append(data)

            gui.frame_parse.SetTitle(videoname)



    @staticmethod
    def path(event):
        dlg = wx.DirDialog(gui.frame_parse, style=wx.FD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            gui.frame_parse.textctrl_path.SetValue(dlg.GetPath())

    @staticmethod
    def godownload(event):
        index = gui.frame_parse.listctrl_parse.GetFirstSelected()
        if index != -1:
            gui.frame_parse.EndModal(wx.OK)

    @staticmethod
    def copyurl(event):
        sel_bid = int(gui.frame_parse.listctrl_parse.GetItemText(gui.frame_parse.listctrl_parse.GetFirstSelected(), 0))
        _, res = iqiyi.getLastRes()
        urls = []
        for i in res[sel_bid]['fs']:
            _url, _ = iqiyi.activatePath(i['l'])
            urls.append(_url)

        text = str('\n'.join(urls))
        # print(text)
        pyperclip.copy(text)

        dlg = wx.MessageDialog(gui.frame_parse, u'下载地址已写入到剪切板！', u'完成', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()


