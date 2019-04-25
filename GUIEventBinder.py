# -*- coding: utf-8 -*-
import wx
import gui
import threading
import handler
import CommonVar as cv
import flow

def init():
    FrameMain_Menu_File_Handler.bindEvent()
    FrameParse_Button_Handler.bindEvent()
    FrameMain_Menu_Help_Handler.bindEvent()
    FrameMain_Close_Handler.bindEvent()
    # Message_Dialog_Handler.bindEvent()

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
        pass

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
        flow.FrameParser.ButtonParse.handle()

    @staticmethod
    def path(event):
        flow.FrameParser.ButtonPath.handle()

    @staticmethod
    def godownload(event):
        flow.FrameParser.ButtonGoDownload.handle()


    @staticmethod
    def copyurl(event):
        flow.FrameParser.ButtonCopy.handle()





class FrameMain_Close_Handler:
    @staticmethod
    def bindEvent():
        gui.frame_main.Bind(wx.EVT_CLOSE, FrameMain_Close_Handler.close)

    @staticmethod
    def close(event):
        def _():
            cv.SHUTDOWN = True
            handler.merger.shutdown()
            handler.downloader.shutdown()

        gui.frame_main.Hide()
        threading.Thread(target=_).start()
        event.Skip()


