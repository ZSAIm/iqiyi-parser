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
from core.common import BasicUrlGroup
import traceback
# import io, importlib
from hashlib import md5
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from core.common import raw_decompress
import gzip, json
import io, sys, time
import platform

TOOL_REQ_URL = {
    'ffmpeg': 'https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-3.2-win64-static.zip',
    'node': 'https://npm.taobao.org/mirrors/node/v10.15.3/win-x64/node.exe',

}



HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
}


class Entry:
    """Flow Entry"""
    @staticmethod
    def handle():
        settings.loadConfig()
        if GetTool.handle():
            LoadParserCore.handle()
            UndoneJob.handle()
        else:
            ShutDown.handle()



class LoadParserCore:
    @staticmethod
    def handle():
        try:
            err_msg = parser.init()
            if err_msg:
                dlg = wx.MessageDialog(gui.frame_parse, '\n'.join(err_msg), u'核心加载错误信息', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        except:
            err_msg = traceback.format_exc()
            dlg = wx.MessageDialog(gui.frame_parse, err_msg, u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

class GetTool:
    @staticmethod
    def handle():
        if not GetTool.checkNode():
            return False

        if not GetTool.checkFfmpeg():
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
        if (platform.system()!='Windows'):
            print('非windows系统请自行安装ffmpeg')
            return True
        if (not os.path.exists('ffmpeg.exe') or os.path.exists('ffmpeg.exe.nbdler')) and not os.path.exists(cv.FFMPEG_PATH):
            dlg = wx.MessageDialog(None, u'该程序需要ffmpeg.exe才能完成工作，是否要下载？', u'提示', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() != wx.ID_YES:
                return False

            dl = nbdler.open(urls=[TOOL_REQ_URL['ffmpeg']],
                             max_conn=16, filename='ffmpeg.zip')
            dlm.addHandler(dl)
            dlg = gui.DialogGetTool(gui.frame_downloader, u'正在下载 Ffmpeg 3.2.zip', dl.getFileSize(), dlm)

            dlg.Bind(wx.EVT_TIMER, GetTool._process, dlg.timer)
            dlg.timer.Start(50, oneShot=False)
            dlm.run()
            msg = dlg.ShowModal()
            if not dlm.isEnd():
                dlm.shutdown()
                dlg.Destroy()
                return False
            GetTool.unzip_ffmpeg('ffmpeg.zip')
            if msg == wx.ID_OK:
                return True
            else:
                return False
        else:
            return True

    @staticmethod
    def checkNode():
        dlm = nbdler.Manager()
        if (platform.system()!='Windows'):
            print('非windows系统请自行安装node')
            return True
        if not os.path.exists('node.exe') or os.path.exists('node.exe.nbdler'):
            dlg = wx.MessageDialog(None, u'该程序需要Nodejs.exe才能完成工作，是否要下载？', u'提示', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() != wx.ID_YES:
                return False
            dl = nbdler.open(urls=[TOOL_REQ_URL['node']],
                             max_conn=16, filename='node.exe')
            dlm.addHandler(dl)
            dlg = gui.DialogGetTool(gui.frame_downloader, u'正在下载 Nodejs v10.15.3', dl.getFileSize(), dlm)

            dlg.Bind(wx.EVT_TIMER, GetTool._process, dlg.timer)
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
            dl = dlm.get(id=runs[0])
            dlg.update(dl.getIncByte(), dl.getFileSize())
        if dlm.isEnd():
            dones = dlm.getDoneQueue()
            if dones:
                dl = dlm.get(id=dones[0])
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
                dlg = wx.MessageDialog(None, u'没有解析到匹配的资源。', '错误', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
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
            if not sel_res:
                wx.CallAfter(UndoneJob.empty)
            else:
                cv.SEL_RES = sel_res
                wx.CallAfter(__, sel_res)

    @staticmethod
    def empty():
        dlg = wx.MessageDialog(gui.frame_parse, u'数据返回为空。', u'错误', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()


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
        def exception(msg):
            wx.MessageDialog(gui.frame_parse, msg, u'解析异常', wx.OK | wx.ICON_ERROR).ShowModal()


        @staticmethod
        def _parse(url, qualitys):
            try:
                res = parser.parse(url, qualitys)
            except (socket.timeout, URLError, SSLError):
                wx.CallAfter(FrameParser.ButtonParse.timeout)
            except Exception as e:
                msg = traceback.format_exc()
                # print(traceback.format_exc())
                wx.CallAfter(FrameParser.ButtonParse.exception, msg)

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



    class MenuCopyLink:
        """Frame Parser Button-[Copy] Handler"""
        @staticmethod
        def handle():
            index = gui.frame_parse.listctrl_parse.GetFirstSelected()
            if index != -1:
                # dlg = gui.DialogCopyLink(gui.frame_parse)
                gui.dialog_copylink.listctrl_links.DeleteAllItems()
                wx.CallAfter(gui.dialog_copylink.ShowModal)
                sel_res = parser.getRespond()[index]
                threading.Thread(target=FrameParser.MenuCopyLink._getinfo, args=(sel_res,)).start()

        @staticmethod
        def _getinfo(sel_res):
            cv.CPYLINK_SEL_ITEMS = {}
            cv.LISTCTRL_ITEMS = []
            if sel_res.getM3U8():
                data = ('', u'', u'√', 'V', u'以下是M3U8内容')
                cv.LISTCTRL_ITEMS.append(data)
                wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data, wx.Colour(255, 0, 0))

                data = ('0', u'', u'√', 'V', sel_res.getM3U8())
                cv.CPYLINK_SEL_ITEMS['video_m3u8'] = [data]
                cv.LISTCTRL_ITEMS.append(data)
                wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)

            if sel_res.getM3U8Urls():
                data = ('', u'√', u'', 'V', u'以下是M3U8链接')
                cv.LISTCTRL_ITEMS.append(data)
                wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data, wx.Colour(255, 0, 0))
            tmp = []
            for i, j in enumerate(sel_res.getM3U8Urls()):
                data = (str(i), u'√', u'', 'V', str(j))
                tmp.append(data)
                wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
            cv.CPYLINK_SEL_ITEMS['video_m3u8'] = tmp
            cv.LISTCTRL_ITEMS.extend(tmp)

            if sel_res.getVideoUrls():
                data = ('', u'√', u'', 'V', u'以下是目标视频下载链接')
                cv.LISTCTRL_ITEMS.append(data)
                wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data, wx.Colour(0, 0, 255))
            tmp = []
            for m, i in enumerate(sel_res.getVideoUrls()):
                if isinstance(i, BasicUrlGroup):
                    for n, j in enumerate(i):
                        if isinstance(j, list) or isinstance(j, tuple):
                            preview = j[0]
                        elif isinstance(j, str):
                            preview = j
                        else:
                            raise TypeError()
                        data = ('%d(%03d)' % (m, n), u'√', u'', 'V', preview)
                        tmp.append(data)
                        wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
                elif isinstance(i, list) or isinstance(i, tuple):
                    data = (str(m), u'√', u'', 'V', i[0])
                    tmp.append(data)
                    wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
                elif isinstance(i, str):
                    data = (str(m), u'√', u'', 'V', i)
                    tmp.append(data)
                    wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
                else:
                    raise TypeError()
            cv.CPYLINK_SEL_ITEMS['video_links'] = tmp
            cv.LISTCTRL_ITEMS.extend(tmp)

            if sel_res.getAudioUrls():
                data = ('', u'√', u'', 'A', u'以下是目标音频下载链接')
                cv.LISTCTRL_ITEMS.append(data)
                wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data, wx.Colour(0, 0, 255))
            tmp = []
            for m, i in enumerate(sel_res.getAudioUrls()):
                if isinstance(i, BasicUrlGroup):
                    for n, j in enumerate(i):
                        if isinstance(j, list) or isinstance(j, tuple):
                            preview = j[0]
                        elif isinstance(j, str):
                            preview = j
                        else:
                            raise TypeError()
                        data = ('%d(%03d)' % (m, n), u'√', u'', 'A', preview)
                        tmp.append(data)
                        wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
                elif isinstance(i, list) or isinstance(i, tuple):
                    data = (str(m), u'√', u'', 'A', i[0])
                    tmp.append(data)
                    wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
                elif isinstance(i, str):
                    data = (str(m), u'√', u'', 'A', i)
                    tmp.append(data)
                    wx.CallAfter(gui.dialog_copylink.listctrl_links.Append, data)
                else:
                    raise TypeError()
            cv.CPYLINK_SEL_ITEMS['audio_links'] = tmp
            cv.LISTCTRL_ITEMS.extend(tmp)

        @staticmethod
        def timeout():
            dlg = wx.MessageDialog(gui.dialog_copylink, u'请求超时,请重试！', u'错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    class UpdateParser:
        @staticmethod
        def handle():
            parser_info = FrameParser.UpdateParser.prepare()
            if parser_info:
                FrameParser.UpdateParser.do(parser_info)
            else:
                dlg = wx.MessageDialog(gui.frame_downloader, '解析核心已经是最新了！', '提示', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

        @staticmethod
        def prepare():
            req = Request(urljoin(cv.REPO, 'repo'), headers=HEADERS)
            res = urlopen(req)
            text = raw_decompress(res.read(), res.info())
            parser_info = eval(text)

            for i, j in list(parser_info.items()):
                if os.path.exists(os.path.join(cv.PARSER_PATH, i)):
                    with open(os.path.join(cv.PARSER_PATH, i), 'rb') as f:
                        _md5 = md5()
                        _md5.update(f.read())
                        if _md5.hexdigest() == j:
                            del parser_info[i]

            return parser_info

        @staticmethod
        def do(parser_info):
            avl = list(parser_info.keys())
            dlg = wx.MultiChoiceDialog(gui.frame_parse, u'以下核心可以更新', u'更新核心', avl)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return False
            sel = dlg.GetSelections()
            for i in sel:

                # for i, j in parser_info.items():
                dlm = nbdler.Manager()
                dl = nbdler.open(urls=[urljoin(cv.REPO, avl[i])], max_conn=3, filename=avl[i] + '.gzip', block_size=1,
                                 filepath=cv.PARSER_PATH)
                dlm.addHandler(dl)
                dlg = gui.DialogGetTool(gui.frame_parse, u'正在下载 %s.gzip' % avl[i], dl.getFileSize(), dlm)

                dlg.Bind(wx.EVT_TIMER, GetTool._process, dlg.timer)
                dlg.timer.Start(50, oneShot=False)
                dlm.run()
                msg = dlg.ShowModal()
                if msg != wx.ID_OK:
                    return False
                else:
                    try:
                        with open(os.path.join(cv.PARSER_PATH, avl[i]), 'w') as f:
                            f.write(gzip.open(os.path.join(cv.PARSER_PATH, avl[i] + '.gzip')).read().decode('utf-8'))
                        os.remove(os.path.join(cv.PARSER_PATH, avl[i] + '.gzip'))
                    except:
                        dlg = wx.MessageDialog(gui.frame_parse, traceback.format_exc(), avl[i], wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()

            dlg.Destroy()
            dlg = wx.MessageDialog(gui.frame_parse, '核心更新完成！', '提示', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

            LoadParserCore.handle()


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
                else:
                    gui.frame_parse.listctrl_parse.menu.godownload.Enable(True)

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
        # io
        # gui.dialog_dllog.start_logger()
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
            gui.runTimer(500, False)
            gui.frame_downloader.Show(True)

        @staticmethod
        def _download_insp():
            time.sleep(0.1)
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
            if len(video_src) == 1 and cv.TARGET_FORMAT == '':
                shutil.move(video_src[0], video_dst)
            else:
                # mer = merger.make(video_dst, video_src, method=merger.MET_CONCAT, merger=cv.SEL_RES.getConcatMerger())
                mer = merger.make(video_dst, video_src, cv.SEL_RES.getConcatMethod())
                mer.start()
                mer.join()

        if audio_src:
            if len(audio_src) == 1 and cv.TARGET_FORMAT == '':
                shutil.move(audio_src[0], audio_dst)
            else:
                # mer = merger.make(audio_dst, audio_src, method=merger.MET_CONCAT, merger=cv.SEL_RES.getConcatMerger())
                mer = merger.make(audio_dst, audio_src, cv.MER_CONCAT_DEMUXER)
                mer.start()
                mer.join()

        if video_src and audio_src:
            src = [video_dst + cv.TARGET_FORMAT, audio_dst+ cv.TARGET_FORMAT]
            dst = downloader.getDstFilePath()
            mer = merger.make(dst, src, cv.MER_VIDEO_AUDIO)

            mer.start()
            mer.join()

        dst = downloader.getDstFilePath() + cv.TARGET_FORMAT
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
        gui.dialog_dllog.Show()
        threading.Thread(target=ShutDown._do).start()

    @staticmethod
    def _do():
        thr = threading.Thread(target=ShutDown._shutdown)
        thr.start()
        thr.join()
        with io.open('console.log', 'w') as f:
            f.write(sys.stdout._buff)
            f.write('\n')
            f.write(sys.stderr._buff)
        wx.CallAfter(ShutDown.destroy_frame)

    @staticmethod
    def destroy_frame():
        gui.dialog_dllog.Destroy()
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


class CopyLink:
    @staticmethod
    def handle():
        pass

    @staticmethod
    def copysel():
        cpy_list = []
        next_index = gui.dialog_copylink.listctrl_links.GetFirstSelected()
        while next_index != -1:

            data = cv.LISTCTRL_ITEMS[next_index][4]
            cpy_list.append(data)
            next_index = gui.dialog_copylink.listctrl_links.GetNextSelected(next_index)

        pyperclip.copy('\n'.join(cpy_list))
        CopyLink.success()

    @staticmethod
    def copygroup():
        sel_index = gui.dialog_copylink.listctrl_links.GetFirstSelected()
        sel_key = ''

        link_text = gui.dialog_copylink.listctrl_links.GetItemText(sel_index, 1)
        type_text = gui.dialog_copylink.listctrl_links.GetItemText(sel_index, 3)
        if link_text == u'√' and type_text == 'V':
            sel_key = 'video_links'
        elif link_text != u'√' and type_text == 'V':
            sel_key = 'video_m3u8'
        elif link_text == u'√' and type_text == 'A':
            sel_key = 'audio_links'


        if sel_key:
            content_list = [i[4] for i in cv.CPYLINK_SEL_ITEMS[sel_key]]
            pyperclip.copy('\n'.join(content_list))
            CopyLink.success()


    @staticmethod
    def success():
        dlg = wx.MessageDialog(gui.dialog_copylink, u'写入到剪切板成功！', u'完成')
        dlg.ShowModal()
        dlg.Destroy()
