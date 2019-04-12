# -*- coding: utf-8 -*-
import wx
import gui
import socket
import iqiyi_parse as iqiyi
import pyperclip


global_url = None

THREAD_PARSE = None
THREAD_COPYURL = None
THREAD_GODOWNLOAD = None

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
        from main import dlm
        dlm.shutdown()
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


import threading, urllib2, ssl

def __parse__():
    url = gui.frame_parse.textctrl_url.GetLineText(0)
    bid = []

    for i in range(1, 7):
        if getattr(gui.frame_parse, 'checkbox_%d' % (i * 100)).IsChecked():
            bid.append(i * 100)
    try:
        res = iqiyi.parse(url, bid)
    except (socket.timeout, urllib2.URLError, ssl.SSLError):
        dlg = wx.MessageDialog(gui.frame_parse, u'请求超时,请重试！', u'错误', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
    else:
        gui.frame_parse.listctrl_parse.DeleteAllItems()
        try:
            for i in res:
                data = (i.getSelBid(), i.getScreenSize(), i.getTotal(),
                        gui.format_byte(i.getTotalFileSize(), '%.1f%s'),
                        i.getFileFormat(), u'√' if i.getM3U8() else u'×')

                gui.frame_parse.listctrl_parse.Append(data)
        except:
            dlg = wx.MessageDialog(gui.frame_parse, u'Msg：\"%s\"' % res[0].getBossMsg(), u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()

        gui.frame_parse.SetTitle(res[0].getVideoTitle())
    finally:
        gui.frame_parse.button_parse.Enable(True)




class FrameParse_Button_Handler:
    @staticmethod
    def bindEvent():
        items = ('parse', 'path', 'godownload', 'copyurl')
        bindButtonEvent(FrameParse_Button_Handler, gui.frame_parse, items)


    @staticmethod
    def parse(event):
        global THREAD_PARSE, global_url

        global_url = gui.frame_parse.textctrl_url.GetLineText(0)
        # main.set_global_url(gui.frame_parse.textctrl_url.GetLineText(0))

        gui.frame_parse.button_parse.Enable(False)
        THREAD_PARSE = threading.Thread(target=__parse__)
        THREAD_PARSE.setDaemon(1)
        THREAD_PARSE.start()


    @staticmethod
    def path(event):
        dlg = wx.DirDialog(gui.frame_parse, style=wx.FD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            gui.frame_parse.textctrl_path.SetValue(dlg.GetPath())

    @staticmethod
    def godownload(event):
        def _():
            gui.frame_parse.button_godownload.Enable(False)
            index = gui.frame_parse.listctrl_parse.GetFirstSelected()
            if index != -1:
                sel_res = iqiyi.getLastRespond()[index]
                try:
                    sel_res.getVideosFullUrl()
                    gui.frame_parse.EndModal(wx.OK)
                except:

                    dlg = wx.MessageDialog(gui.frame_parse, u'Msg：\"请求被服务器中止或网络超时。\"', u'错误', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()

                    gui.frame_parse.button_godownload.Enable(True)
        global THREAD_GODOWNLOAD
        THREAD_GODOWNLOAD = threading.Thread(target=_)
        THREAD_GODOWNLOAD.start()


    @staticmethod
    def copyurl(event):
        def _():
            gui.frame_parse.button_copyurl.Enable(False)
            index = int(gui.frame_parse.listctrl_parse.GetFirstSelected())
            if index != -1:
                res = iqiyi.getLastRespond()

                sel_res = res[index]
                try:
                    if sel_res.getM3U8():
                        dlg = wx.MessageDialog(gui.frame_parse,
                                               u'该视频提供了M3U8，是否复制M3U8到剪切板？\n选【No】将复制所有片段的下载地址。', u'提示',
                                               wx.YES_NO | wx.ICON_QUESTION)
                        msg = dlg.ShowModal()
                        if msg == wx.ID_YES:
                            cpy_url = str(sel_res.getM3U8())
                        else:
                            cpy_url = str('\n'.join(sel_res.getVideosFullUrl()))
                    else:
                        cpy_url = str('\n'.join(sel_res.getVideosFullUrl()))
                except:
                    dlg = wx.MessageDialog(gui.frame_parse, u'Msg：\"请求被服务器中止或网络超时。。\"', u'错误', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                else:
                    pyperclip.copy(cpy_url)

                    dlg = wx.MessageDialog(gui.frame_parse, u'写入到剪切板成功！', u'完成', wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
            gui.frame_parse.button_copyurl.Enable(True)

        global THREAD_COPYURL
        THREAD_COPYURL = threading.Thread(target=_)
        THREAD_COPYURL.setDaemon(1)
        THREAD_COPYURL.start()


