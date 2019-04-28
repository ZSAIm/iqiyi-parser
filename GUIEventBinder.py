# -*- coding: utf-8 -*-
import wx
import gui
import threading
import handler
import CommonVar as cv
import flow

def init():
    FrameMain.bindEvent()
    FrameParser.bindEvent()
    FrameMerger.bindEvent()


class FrameMain:
    @staticmethod
    def bindEvent():
        gui.frame_downloader.Bind(wx.EVT_CLOSE, FrameMain.win_close)
        FrameMain.MenuBar.bindEvent()

    @staticmethod
    def win_close(event):
        flow.ShutDown.frame_downloader_close(event)


    class MenuBar:
        @staticmethod
        def bindEvent():
            FrameMain.MenuBar.File.bineEvent()
            FrameMain.MenuBar.Help.bindEvent()

        class File:
            @staticmethod
            def bineEvent():
                items = ('parse', 'settings', 'exit')
                FrameMain.MenuBar.batchBind(FrameMain.MenuBar.File, gui.frame_downloader.menu_bar.file, items)

            @staticmethod
            def parse(event):
                pass

            @staticmethod
            def settings(event):
                dlg = gui.DialogSettings(gui.frame_parse)
                dlg.ShowModal()

            @staticmethod
            def exit(event):
                pass


        class Help:
            @staticmethod
            def bindEvent():
                items = ('about',)
                FrameMain.MenuBar.batchBind(FrameMain.MenuBar.Help, gui.frame_downloader.menu_bar.help, items)

            @staticmethod
            def about(event):
                dlg = gui.DialogAbout(gui.frame_downloader)
                dlg.ShowModal()
                dlg.Destroy()

        @staticmethod
        def batchBind(handler_parent, source_parent, items_name):
            for i in items_name:
                gui.frame_downloader.Bind(wx.EVT_MENU, getattr(handler_parent, i), getattr(source_parent, i))


class FrameParser:
    @staticmethod
    def bindEvent():
        gui.frame_parse.Bind(wx.EVT_CLOSE, FrameParser.win_close)
        FrameParser.TextCtrl.bindEvent()
        FrameParser.Button.bindEvent()
        FrameParser.MemuBar.bindEvent()

    @staticmethod
    def win_close(event):
        flow.ShutDown.frame_parser_close(event)


    class TextCtrl:
        @staticmethod
        def bindEvent():
            items = ('godownload', 'copylinks')
            FrameParser.MemuBar.batchBind(FrameParser.TextCtrl, gui.frame_parse.listctrl_parse.menu, items)

        @staticmethod
        def godownload(event):
            flow.FrameParser.MenuGoDownload.handle()

        @staticmethod
        def copylinks(event):
            flow.FrameParser.MenuCopyLinks.handle()


    class MemuBar:
        @staticmethod
        def bindEvent():
            FrameParser.MemuBar.File.bindEvent()
            FrameParser.MemuBar.Help.bindEvent()

        class File:
            @staticmethod
            def bindEvent():
                items = ('settings',)
                FrameParser.MemuBar.batchBind(FrameParser.MemuBar.File, gui.frame_parse.menu_bar.file, items)

            @staticmethod
            def settings(event):
                dlg = gui.DialogSettings(gui.frame_parse)
                dlg.ShowModal()

        class Help:
            @staticmethod
            def bindEvent():
                items = ('about',)
                FrameParser.MemuBar.batchBind(FrameParser.MemuBar.Help, gui.frame_parse.menu_bar.help, items)

            @staticmethod
            def about(event):
                dlg = gui.DialogAbout(gui.frame_downloader)
                dlg.ShowModal()
                dlg.Destroy()

        @staticmethod
        def batchBind(handler_parent, source_parent, items_name):
            for i in items_name:
                gui.frame_parse.Bind(wx.EVT_MENU, getattr(handler_parent, i), getattr(source_parent, i))


    class Button:
        @staticmethod
        def bindEvent():
            items = ('parse',)
            FrameParser.Button.batchBind(FrameParser.Button, gui.frame_parse, items)

        @staticmethod
        def parse(event):
            flow.FrameParser.ButtonParse.handle()

        @staticmethod
        def batchBind(handler_parent, source_parent, items_name):
            for i in items_name:
                gui.frame_parse.Bind(wx.EVT_BUTTON, getattr(handler_parent, i), getattr(source_parent, 'button_' + i))



class FrameMerger:
    @staticmethod
    def bindEvent():
        gui.frame_merger.Bind(wx.EVT_CLOSE, FrameMerger.win_close)
        FrameMerger.MenuBar.bindEvent()

    @staticmethod
    def win_close(event):
        flow.ShutDown.frame_merger_close(event)

    class MenuBar:
        @staticmethod
        def bindEvent():
            FrameMerger.MenuBar.File.bineEvent()
            FrameMerger.MenuBar.Help.bindEvent()

        class File:
            @staticmethod
            def bineEvent():
                items = ('exit',)
                FrameMerger.MenuBar.batchBind(FrameMerger.MenuBar.File, gui.frame_merger.menu_bar.file, items)

            @staticmethod
            def settings(event):
                pass

            @staticmethod
            def exit(event):
                flow.ShutDown.handle()


        class Help:
            @staticmethod
            def bindEvent():
                items = ('about',)
                FrameMerger.MenuBar.batchBind(FrameMerger.MenuBar.Help, gui.frame_merger.menu_bar.help, items)

            @staticmethod
            def about(event):
                dlg = gui.DialogAbout(gui.frame_downloader)
                dlg.ShowModal()
                dlg.Destroy()

        @staticmethod
        def batchBind(handler_parent, source_parent, items_name):
            for i in items_name:
                gui.frame_merger.Bind(wx.EVT_MENU, getattr(handler_parent, i), getattr(source_parent, i))

