# -*- coding: UTF-8 -*-

"""
Flow:

                                     [load config]
                                           |
                                  [check undone job]
                                     /           \
                                   /              \
                             (do)/                 \(skip)
                    [parse backgound]       [show parser frame]
                           |                           \
                          |        (button_godownload)  \
                    [go download] <------------------- [handle frame parser]
                      /       \
              (done)/          \ (close win)
            [go merge]     [save config] ------> [END]
             /       \
           /          \
         /             \
 (done)/       (done)   \(close win)
[save config] <------- [wait for merge done]
    |
    |
  [END]

"""


from handler import settings, parser, downloader, merger
import wx
import gui
from gui import format_byte
import CommonVar as cv
import socket, os, shutil
from urllib.error import URLError
from ssl import SSLError
import threading
import pyperclip
import nbdler
from zipfile import ZipFile

TOOL_REQ_URL = {
    'ffmpeg': 'https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-3.2-win64-static.zip',
    'node': 'https://npm.taobao.org/mirrors/node/v0.12.18/node.exe'
}



class Entry:
    """Flow Entry"""
    @staticmethod
    def handle():
        settings.loadConfig()
        if ToolReq.handle():
            UndoneJob.handle()
        else:
            ShutDown.handle()

class ToolReq:
    @staticmethod
    def handle():
        if not ToolReq.checkNode():
            return False

        if not ToolReq.checkFfmpeg():
            return False
        return True

    @staticmethod
    def unzip_ffmpeg(zipfile):
        with ZipFile(zipfile, 'r') as f:
            top_path = f.namelist()[0]
            target_path = os.path.join(top_path.rstrip('/').rstrip('\\'), 'bin', 'ffmpeg.exe').replace('\\', '/')
            f.extract(target_path, '.')

        shutil.move(os.path.join(top_path.rstrip('/').rstrip('\\'), 'bin', 'ffmpeg.exe'), 'ffmpeg.exe')
        os.remove(zipfile)
        os.removedirs(os.path.join(top_path.rstrip('/').rstrip('\\'), 'bin'))


    @staticmethod
    def checkFfmpeg():
        dlm = nbdler.Manager()
        if (not os.path.exists('ffmpeg.exe') or os.path.exists('ffmpeg.exe.nbdler')) and not os.path.exists(cv.FFMPEG_PATH):
            dlg = wx.MessageDialog(None, u'该程序需要ffmpeg.exe才能完成工作，是否要下载？', u'提示', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() != wx.ID_YES:
                return False

            dl = nbdler.open(urls=[TOOL_REQ_URL['ffmpeg']],
                             max_conn=16, filename='ffmpeg.zip')
            dlm.addHandler(dl)
            dlg = gui.DialogToolReq(gui.frame_downloader, u'正在下载 Ffmpeg 3.2.zip', dl.getFileSize(), dlm)

            dlg.Bind(wx.EVT_TIMER, ToolReq._process, dlg.timer)
            dlg.timer.Start(50, oneShot=False)
            dlm.run()
            msg = dlg.ShowModal()
            if not dlm.isEnd():
                dlm.shutdown()
                dlg.Destroy()
                return False
            ToolReq.unzip_ffmpeg('ffmpeg.zip')
            if msg == wx.ID_OK:
                return True
            else:
                return False
        else:
            return True

    @staticmethod
    def checkNode():
        dlm = nbdler.Manager()
        if not os.path.exists('node.exe') or os.path.exists('node.exe.nbdler'):
            dlg = wx.MessageDialog(None, u'该程序需要node.exe才能完成工作，是否要下载？', u'提示', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() != wx.ID_YES:
                return False
            dl = nbdler.open(urls=[TOOL_REQ_URL['node']],
                             max_conn=16, filename='node.exe')
            dlm.addHandler(dl)
            dlg = gui.DialogToolReq(gui.frame_downloader, u'正在下载 Nodejs v0.12.18', dl.getFileSize(), dlm)

            dlg.Bind(wx.EVT_TIMER, ToolReq._process, dlg.timer)
            dlg.timer.Start(50, oneShot=False)
            dlm.run()
            msg = dlg.ShowModal()
            dlm.shutdown()
            dlg.Destroy()
            if msg == wx.ID_OK:
                return True
            else:
                return False
        else:
            return True

    @staticmethod
    def _process(event):
        dlg = event.Timer.GetOwner()
        dlm = dlg.dlm
        runs = dlm.getRunQueue()
        if runs:
            dl = dlm.getHandler(id=runs[0])
            dlg.update(dl.getIncByte(), dl.getFileSize())
        if dlm.isEnd():
            dones = dlm.getDoneQueue()
            if dones:
                dl = dlm.getHandler(id=dones[0])
                dlg.update(dl.getFileSize(), dl.getFileSize())
                event.Timer.Stop()
                dlg.EndModal(wx.ID_OK)

class UndoneJob:
    """Undone Job Handler:
            if the window is closed while there was a job running last time.
    """

    @staticmethod
    def handle():
        if cv.UNDONE_JOB:
            if 'url' not in cv.UNDONE_JOB or 'quality' not in cv.UNDONE_JOB or 'features' not in cv.UNDONE_JOB:
                ConfigSettings.fail()
                FrameParser.handle()
            else:
                msg = '[Url]: %s\n[Title]: %s\n[Quality]: %s\n上一次任务尚未完成，是否继续任务？' \
                      % (cv.UNDONE_JOB['url'], cv.UNDONE_JOB.get('title'), cv.UNDONE_JOB['quality'])
                dlg = wx.MessageDialog(None, msg, '提示', wx.YES_NO | wx.ICON_INFORMATION)
                if dlg.ShowModal() == wx.ID_YES:
                    UndoneJob.do()
                else:
                    UndoneJob.skip()
                dlg.Destroy()
        else:
            FrameParser.handle()

    @staticmethod
    def do():
        threading.Thread(target=UndoneJob._do).start()

    @staticmethod
    def _do():
        def __(sel_res):
            if not sel_res:
                ShutDown.handle()
                return
            if FrameParser.MenuGoDownload.handler_audio(sel_res):
                FrameDownload.handle()
            else:
                FrameParser.handle()

        try:
            url = cv.UNDONE_JOB['url']
            quality = cv.UNDONE_JOB['quality']
            features = cv.UNDONE_JOB['features']
            sel_res = parser.matchParse(url, quality, features)
        except (socket.timeout, URLError, SSLError):
            wx.CallAfter(UndoneJob.timeout)
        else:
            cv.SEL_RES = sel_res
            wx.CallAfter(__, sel_res)



    @staticmethod
    def timeout():
        dlg = wx.MessageDialog(gui.frame_parse, u'请求超时,是否重试？', u'错误', wx.YES_NO | wx.ICON_ERROR)
        if dlg.ShowModal() == wx.ID_YES:
            UndoneJob.do()
        else:
            UndoneJob.skip()
        dlg.Destroy()

    @staticmethod
    def skip():
        FrameParser.handle()




class FrameParser:
    """Frame Parser Flow Handler"""

    @staticmethod
    def handle():
        gui.frame_parse.Show()
        # if gui.frame_parse.ShowModal() == cv.ID_PARSER_GODOWNLOAD:
        # FrameDownload.handle()
        # else:
        # ShutDown.handle()



    class ButtonParse:
        """Frame Parser Button-[Parser] Handler"""
        @staticmethod
        def handle():
            gui.frame_parse.button_parse.Enable(False)
            url = gui.frame_parse.textctrl_url.GetLineText(0)
            qualitys = []
            for i in range(1, 7):
                if getattr(gui.frame_parse, 'checkbox_%d' % i).GetValue():
                    qualitys.append(i)

            threading.Thread(target=FrameParser.ButtonParse._parse, args=(url, qualitys,), daemon=True).start()


        @staticmethod
        def timeout():
            dlg = wx.MessageDialog(gui.frame_parse, u'请求超时,请重试！', u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        @staticmethod
        def empty():
            dlg = wx.MessageDialog(gui.frame_parse, u'数据返回为空。', u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        @staticmethod
        def _parse(url, qualitys):
            try:
                res = parser.parse(url, qualitys)
            except (socket.timeout, URLError, SSLError):
                wx.CallAfter(FrameParser.ButtonParse.timeout)
            else:
                if not res:
                    wx.CallAfter(FrameParser.ButtonParse.empty)
                else:
                    wx.CallAfter(FrameParser.ButtonParse.appendItem, res)

            finally:
                wx.CallAfter(gui.frame_parse.button_parse.Enable, True)
                wx.CallAfter(gui.frame_parse.button_parse.SetLabelText, u'解析')

        @staticmethod
        def appendItem(res):
            gui.frame_parse.listctrl_parse.DeleteAllItems()
            # try:
            for i in res:
                audios_info = i.getAllAudioInfo()

                file_num_str = i.getVideoTotal() if not audios_info else '%d+%d' % (i.getVideoTotal(), i.getAudioTotal())
                file_size_str = format_byte(i.getVideoSize(), '%.1f%s' if not audios_info else '%.1f%s+')

                data = (i.getQuality(), i.getScreenSize(), file_num_str, file_size_str,
                        str(len(audios_info)) if audios_info else 0,
                        i.getFileFormat(),
                        u'√' if i.getM3U8() else u'×')

                gui.frame_parse.listctrl_parse.Append(data)

            gui.frame_parse.SetTitle(res[0].getVideoLegalTitle())


    class ButtonPath:
        """Frame Parser Button-[Path] Handler"""
        @staticmethod
        def handle():
            dlg = wx.DirDialog(gui.frame_parse, style=wx.FD_DEFAULT_STYLE)
            if dlg.ShowModal() == wx.ID_OK:
                gui.frame_parse.textctrl_path.SetValue(dlg.GetPath())
                cv.FILEPATH = dlg.GetPath()
            dlg.Destroy()


    class MenuCopyLinks:
        """Frame Parser Button-[Copy] Handler"""
        @staticmethod
        def handle():
            # gui.frame_parse.button_copyurl.Enable(False)
            index = int(gui.frame_parse.listctrl_parse.GetFirstSelected())
            if index != -1:
                sel_res = parser.getRespond()[index]

                if sel_res.getM3U8():
                    dlg = wx.MessageDialog(gui.frame_parse,
                                           u'该视频提供了M3U8，是否复制M3U8到剪切板？\n选【No】将复制所有片段的下载地址。', u'提示',
                                           wx.YES_NO | wx.ICON_INFORMATION)
                    msg = dlg.ShowModal()
                    threading.Thread(target=FrameParser.MenuCopyLinks._copy_fullurl,
                                     args=(sel_res, msg), daemon=True).start()
                    dlg.Destroy()
                else:


                    # for i in sel_res.getVideoUrls():
                    #     for
                    # [ for i in sel_res.getVideoUrls()]
                    cpy_url = str('\n'.join(sel_res.getVideoUrls()))
                    pyperclip.copy(cpy_url)
                    FrameParser.MenuCopyLinks.success()

        @staticmethod
        def success():
            dlg = wx.MessageDialog(gui.frame_parse, u'写入到剪切板成功！', u'完成')
            dlg.ShowModal()
            dlg.Destroy()

        @staticmethod
        def timeout():
            dlg = wx.MessageDialog(gui.frame_parse, u'请求超时,请重试！', u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        @staticmethod
        def _copy_fullurl(sel_res, dlg_msg):
            if dlg_msg == wx.ID_YES:
                cpy_url = str(sel_res.getM3U8())
            else:
                try:
                    cpy_url = str('\n'.join(sel_res.getVideoUrls()))
                except (socket.timeout, URLError, SSLError):
                    wx.CallAfter(FrameParser.MenuCopyLinks.timeout)
                    return

            pyperclip.copy(cpy_url)
            # wx.CallAfter(gui.frame_parse.button_copyurl.Enable, True)
            wx.CallAfter(FrameParser.MenuCopyLinks.success)


    class MenuGoDownload:
        """Frame Parser Button-[GoDownload] Handler"""
        @staticmethod
        def handle():
            gui.frame_parse.listctrl_parse.menu.godownload.Enable(False)
            index = gui.frame_parse.listctrl_parse.GetFirstSelected()
            if index != -1:
                sel_res = parser.getRespond()[index]

                if FrameParser.MenuGoDownload.handler_audio(sel_res):
                    threading.Thread(target=FrameParser.MenuGoDownload._download, args=(sel_res,)).start()

        @staticmethod
        def handler_audio(sel_res):
            audio_info = sel_res.getAllAudioInfo()
            if audio_info:
                dlg = wx.SingleChoiceDialog(gui.frame_parse, u'Pick the AUDIO you prefer', u'Audio Choice', audio_info)
                if dlg.ShowModal() == wx.ID_OK:
                    index = audio_info.index(dlg.GetStringSelection())
                    sel_res.setSelAudio(index)
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return False

            return True


        @staticmethod
        def timeout():
            dlg = wx.MessageDialog(gui.frame_parse, u'Msg：\"请求被服务器中止或网络超时。\"', u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            # gui.frame_parse.button_godownload.Enable(True)

        @staticmethod
        def _download(sel_res):
            try:
                sel_res.getVideoUrls()
            except:
                wx.CallAfter(FrameParser.MenuGoDownload.timeout)
            else:
                cv.SEL_RES = sel_res
                wx.CallAfter(FrameDownload.handle)
            finally:
                gui.frame_parse.listctrl_parse.menu.godownload.Enable(True)



class FrameDownload:
    """Frame Download Handler"""
    @staticmethod
    def handle():
        gui.frame_parse.Hide()
        FrameDownload.Download.handle()

    class Download:
        """Frame Download - [Download] Handler"""
        @staticmethod
        def handle():
            downloader.init()
            FrameDownload.Download.prepare()
            downloader.run()
            threading.Thread(target=FrameDownload.Download._download_insp).start()

        @staticmethod
        def prepare():
            downloader.prepare(cv.SEL_RES)
            gui.frame_downloader.setTitleName(cv.SEL_RES.getVideoLegalTitle())
            gui.frame_downloader.initTotal(cv.SEL_RES.getTotalFileSize())
            for i in range(cv.SEL_RES.getVideoTotal()):
                gui.frame_downloader.insertBlock(i)

            for i in range(cv.SEL_RES.getAudioTotal()):
                gui.frame_downloader.insertBlock(i + cv.SEL_RES.getVideoTotal())

            gui.setTimerHandler(downloader.getProcessEvent())
            gui.runTimer(300, False)
            gui.frame_downloader.Show(True)

        @staticmethod
        def _download_insp():
            downloader.join()

            if cv.SHUTDOWN:
                url = cv.SEL_RES.getBaseUrl()
                quality = cv.SEL_RES.getQuality()
                title = cv.SEL_RES.getVideoLegalTitle()
                settings.setUndoneJob(url, title, quality, cv.SEL_RES.getFeatures())

                settings.saveConfig()
                # wx.CallAfter(ShutDown.handle)
            else:
                wx.CallAfter(Merge.handle)



class Merge:
    """Frame Download Handler"""
    @staticmethod
    def handle():
        if not downloader.isAllDone():
            Merge.fileNotAllFound()
        else:
            Merge.prepare()
            Merge.do()

    @staticmethod
    def prepare():
        gui.frame_downloader.Hide()
        gui.frame_merger.Show()

    @staticmethod
    def do():
        # if downloader.getAllAudioFilePath():
        # wx.CallAfter(gui.frame_merger.Show)

        threading.Thread(target=Merge._do).start()

    @staticmethod
    def _do():
        video_src = downloader.getAllVideoFilePath()
        audio_src = downloader.getAllAudioFilePath()

        video_dst = downloader.getDstVideoFilePath()
        audio_dst = downloader.getDstAudioFilePath()

        if video_src:
            if len(video_src) == 1:
                shutil.move(video_src[0], video_dst)
            else:
                mer = merger.make(video_dst, video_src, method=merger.MET_CONCAT, merger=cv.SEL_RES.getConcatMerger())
                mer.start()
                mer.join()

        if audio_src:
            if len(audio_src) == 1:
                shutil.move(audio_src[0], audio_dst)
            else:
                mer = merger.make(audio_dst, audio_src, method=merger.MET_CONCAT, merger=cv.SEL_RES.getConcatMerger())
                mer.start()
                mer.join()

        if video_src and audio_src:
            src = [video_dst, audio_dst]
            dst = downloader.getDstFilePath()
            mer = merger.make(dst, src, method=merger.MET_MERGE_VIDEO_AUDIO)
            mer.start()
            mer.join()

        dst = downloader.getDstFilePath()
        settings.clearUndoneJob()
        settings.saveConfig()
        if not cv.SHUTDOWN:
            if os.path.exists(dst):
                wx.CallAfter(Merge.success)
            else:
                wx.CallAfter(Merge.fail)

    @staticmethod
    def fail():
        dlg = wx.MessageDialog(gui.frame_downloader, '发生未知错误，无法生成最终视频！', '错误', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()


    @staticmethod
    def fileNotAllFound():
        dlg = wx.MessageDialog(gui.frame_downloader, '未找到所有分段文件，请重启程序重试！', '错误', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()


    @staticmethod
    def success():
        cv.ALLTASKDONE = True
        dlg = wx.MessageDialog(gui.frame_downloader, u'视频已经合并完成，是否删除分段文件？', u'提示', wx.YES_NO | wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES:
            merger.del_src_files()
            dlg = wx.MessageDialog(gui.frame_downloader, u'分段文件删除完成。', u'提示')
            dlg.ShowModal()
        dlg.Destroy()




class ConfigSettings:
    @staticmethod
    def fail():
        settings.initConfig()
        dlg = wx.MessageDialog(gui.frame_parse, 'config.ini文件错误。', '错误', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()



class ShutDown:
    @staticmethod
    def handle():
        thr = threading.Thread(target=ShutDown._shutdown)
        thr.start()
        thr.join()
        ShutDown.destroy_frame()

    @staticmethod
    def destroy_frame():
        gui.frame_parse.Destroy()
        gui.frame_downloader.Destroy()
        gui.frame_merger.Destroy()


    @staticmethod
    def _shutdown():
        cv.SHUTDOWN = True
        merger.shutdown()
        downloader.shutdown()


    @staticmethod
    def frame_parser_close(event):
        if cv.SHUTDOWN:
            event.Skip()
        else:
            gui.frame_parse.Hide()
            ShutDown.handle()

    @staticmethod
    def frame_downloader_close(event):
        if cv.SHUTDOWN:
            event.Skip()
        else:
            dlg = wx.MessageDialog(gui.frame_downloader, u'你确定要中止下载吗？', u'提示', style=wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                gui.frame_downloader.Hide()
                ShutDown.handle()
            dlg.Destroy()


    @staticmethod
    def frame_merger_close(event):
        if cv.SHUTDOWN:
            event.Skip()
        else:
            if not cv.ALLTASKDONE:
                dlg = wx.MessageDialog(gui.frame_merger, u'你确定要中止操作吗？', u'提示', style=wx.YES_NO | wx.ICON_INFORMATION)
                if dlg.ShowModal() == wx.ID_YES:
                    gui.frame_merger.Hide()
                    ShutDown.handle()
                dlg.Destroy()
            else:
                gui.frame_merger.Hide()
                ShutDown.handle()