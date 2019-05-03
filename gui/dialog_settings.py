# -*- coding: utf-8 -*-

import wx
import CommonVar as cv
from handler import settings

class DialogSettings(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u'设置', pos=wx.DefaultPosition,
                           size=wx.Size(390, 435), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        global_sizer = wx.BoxSizer(wx.VERTICAL)

        # global_sizer.SetMinSize(wx.Size(400, 400))


        # ****************** downloader settings

        sizer_download = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"下载器设置"), wx.VERTICAL)

        sizer_max_conn = wx.BoxSizer(wx.HORIZONTAL)

        text_max_conn = wx.StaticText(sizer_download.GetStaticBox(), wx.ID_ANY, u"最大连接数：", wx.DefaultPosition,
                                            wx.DefaultSize, wx.ALIGN_LEFT)
        text_max_conn.Wrap(-1)

        self.slider_max_conn = wx.Slider(sizer_download.GetStaticBox(), wx.ID_ANY, cv.MAX_CONN, 0, 10, wx.DefaultPosition, wx.Size(-1, -1),
                                   wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_SELRANGE)

        sizer_max_conn.Add(text_max_conn, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer_max_conn.Add(self.slider_max_conn, 2, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 5)

        sizer_max_task = wx.BoxSizer(wx.HORIZONTAL)

        text_max_task = wx.StaticText(sizer_download.GetStaticBox(), wx.ID_ANY, u"最大任务数：", wx.DefaultPosition,
                                              wx.DefaultSize, wx.ALIGN_LEFT)
        text_max_task.Wrap(-1)

        self.slider_max_task = wx.Slider(sizer_download.GetStaticBox(), wx.ID_ANY, cv.MAX_TASK, 0, 5, wx.DefaultPosition, wx.DefaultSize,
                                      wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_SELRANGE)

        sizer_max_task.Add(text_max_task, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer_max_task.Add(self.slider_max_task, 2, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 5)


        sizer_buffsize = wx.BoxSizer(wx.HORIZONTAL)

        text_buffsize = wx.StaticText(sizer_download.GetStaticBox(), wx.ID_ANY, u"缓冲器大小(MB)：", wx.DefaultPosition,
                                             wx.DefaultSize, wx.ALIGN_LEFT)
        text_buffsize.Wrap(-1)

        self.slider_buffsize = wx.Slider(sizer_download.GetStaticBox(), wx.ID_ANY, cv.BUFFER_SIZE, 10, 50, wx.DefaultPosition, wx.DefaultSize,
                                     wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_SELRANGE | wx.SL_VALUE_LABEL)

        sizer_buffsize.Add(text_buffsize, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer_buffsize.Add(self.slider_buffsize, 2, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 5)

        sizer_blocksize = wx.BoxSizer(wx.HORIZONTAL)

        text_blocksize = wx.StaticText(sizer_download.GetStaticBox(), wx.ID_ANY, u"块大小(KB)：", wx.DefaultPosition,
                                      wx.DefaultSize, wx.ALIGN_LEFT)
        text_blocksize.Wrap(-1)

        self.slider_blocksize = wx.Slider(sizer_download.GetStaticBox(), wx.ID_ANY, cv.BLOCK_SIZE, 1, 1024,
                                         wx.DefaultPosition, wx.DefaultSize,
                                         wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_SELRANGE | wx.SL_VALUE_LABEL)

        sizer_blocksize.Add(text_blocksize, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer_blocksize.Add(self.slider_blocksize, 2, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 5)

        # sizer_format = wx.BoxSizer(wx.HORIZONTAL)
        #
        # text_format = wx.StaticText(sizer_download.GetStaticBox(), wx.ID_ANY, u"目标视频格式：", wx.DefaultPosition,
        #                             wx.DefaultSize, wx.ALIGN_LEFT)
        # text_format.Wrap(-1)
        #
        # choice_format_list = ['原格式', 'mp4', 'avi', 'wmv', 'flv', 'ts']
        # self.choice_format = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choice_format_list, 0)
        # self.choice_format.SetSelection(0)
        #
        # sizer_format.Add(text_format, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)
        # sizer_format.Add(self.choice_format, 2, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 2)

        sizer_download.Add(sizer_max_conn, 1, wx.EXPAND, 5)
        sizer_download.Add(sizer_max_task, 1, wx.EXPAND, 5)
        sizer_download.Add(sizer_buffsize, 1, wx.EXPAND, 5)
        sizer_download.Add(sizer_blocksize, 1, wx.EXPAND, 5)
        # sizer_download.Add(sizer_format, 1, wx.EXPAND, 5)

        # ****************** merger settings

        sizer_merger = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"合并器设置"), wx.VERTICAL)

        sizer_format = wx.BoxSizer(wx.HORIZONTAL)

        text_format = wx.StaticText(sizer_merger.GetStaticBox(), wx.ID_ANY, u"目标视频格式：", wx.DefaultPosition,
                                      wx.DefaultSize, wx.ALIGN_LEFT)
        text_format.Wrap(-1)

        # choice_format_list = ['原格式', 'MP4', 'AVI', 'WMV', 'FLV', 'TS']
        choice_format_list = ['原格式', 'MP4', 'FLV', 'TS']
        self.choice_format = wx.Choice(sizer_merger.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choice_format_list, 0)
        if cv.TARGET_FORMAT == '':
            self.choice_format.SetSelection(0)
        else:
            self.choice_format.SetSelection(choice_format_list.index(cv.TARGET_FORMAT.upper()[1:]))
        # self.choice_format.SetSelection(0)


        sizer_format.Add(text_format, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, 2)
        sizer_format.Add(self.choice_format, 2, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 2)

        sizer_merger.Add(sizer_format, 1, wx.EXPAND, 5)


        # self.textctrl_path = wx.TextCtrl(sizer_merger.GetStaticBox(), wx.ID_ANY, cv.FILEPATH, wx.DefaultPosition,
        #                                  wx.DefaultSize, 0)
        #
        # self.button_path = wx.Button(sizer_merger.GetStaticBox(), wx.ID_ANY, u"选择", wx.DefaultPosition, wx.Size(60, -1),
        #                              0)
        # self.button_path.SetMinSize(wx.Size(60, -1))
        # self.button_path.SetMaxSize(wx.Size(60, -1))



        sizer_path = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"文件存放路径"), wx.HORIZONTAL)

        self.textctrl_path = wx.TextCtrl(sizer_path.GetStaticBox(), wx.ID_ANY, cv.FILEPATH, wx.DefaultPosition,
                                       wx.DefaultSize, 0)

        self.button_path = wx.Button(sizer_path.GetStaticBox(), wx.ID_ANY, u"选择", wx.DefaultPosition, wx.Size(60, -1), 0)
        self.button_path.SetMinSize(wx.Size(60, -1))
        self.button_path.SetMaxSize(wx.Size(60, -1))

        sizer_path.Add(self.textctrl_path, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer_path.Add(self.button_path, 0, wx.ALIGN_CENTER | wx.ALL, 5)



        sizer_save = wx.BoxSizer(wx.HORIZONTAL)

        self.buttom_save = wx.Button(self, wx.ID_ANY, u"保存设置", wx.DefaultPosition, wx.DefaultSize, 0)

        sizer_save.Add((0, 0), 1, wx.EXPAND, 5)
        sizer_save.Add(self.buttom_save, 0, wx.ALL, 5)


        global_sizer.Add(sizer_download, 1, wx.EXPAND, 5)
        global_sizer.Add(sizer_merger, 0, wx.EXPAND| wx.ALL, 5)
        global_sizer.Add(sizer_path, 0, wx.EXPAND, 5)
        global_sizer.Add(sizer_save, 0, wx.EXPAND, 5)


        self.SetSizer(global_sizer)
        self.Layout()

        self.Centre(wx.BOTH)
        self.bindEvent()


    def bindEvent(self):
        self.Bind(wx.EVT_BUTTON, self.event_button_path, self.button_path)
        self.Bind(wx.EVT_BUTTON, self.event_button_save, self.buttom_save)

    def event_button_path(self, event):
        dlg = wx.DirDialog(self, style=wx.FD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.textctrl_path.SetValue(dlg.GetPath())


    def event_button_save(self, event):
        cv.FILEPATH = self.textctrl_path.GetValue().strip()
        cv.MAX_CONN = self.slider_max_conn.GetValue()
        cv.MAX_TASK = self.slider_max_task.GetValue()
        cv.BUFFER_SIZE = self.slider_buffsize.GetValue()
        cv.BLOCK_SIZE = self.slider_blocksize.GetValue()

        video_format = self.choice_format.GetStringSelection()
        if video_format == '原格式':
            cv.TARGET_FORMAT = ''
        else:
            cv.TARGET_FORMAT = '.%s' % video_format.lower()
        settings.saveConfig()
        dlg = wx.MessageDialog(self, u'设置保存成功！', u'成功', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        self.Destroy()


    def __del__(self):
        pass







# app = wx.App()
# # # frame_main = FrameParser(None)

# DialogSettings(None).ShowModal()
# # # frame_main.Show()
# app.MainLoop()
