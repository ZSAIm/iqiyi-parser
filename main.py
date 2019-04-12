# -*- coding: utf-8 -*-

import gui
import iqiyi_parse as iqiyi
import json, os, time
import threading
from merger import Merger
import wx
import nbdler
import GUIEventBinder
import socket
import ConfigParser
import urllib2


socket.setdefaulttimeout(3)

dlm = None
mer = None
max_task = 5
target_path = ''
sel_res = None
all_filename = []
glb_undone_job = None

inc_filesize = 0



def save_configure(undone_job=''):
    global max_task, target_path

    config = ConfigParser.SafeConfigParser()
    config.add_section('Settings')

    config.set('Settings', 'MaxTaskNum', str(max_task))
    config.set('Settings', 'LastSavePath', str(target_path))
    config.set('Settings', 'UndoneJob', str(undone_job))
    with open('config.ini', 'wb') as f:
        config.write(f)


def load_config():
    global max_task, target_path
    if os.path.exists('config.ini') is False:
        return False

    config = ConfigParser.SafeConfigParser()

    config.read('config.ini')
    max_task = int(config.get('Settings', 'MaxTaskNum'))

    target_path = config.get('Settings', 'LastSavePath')
    undone_job = config.get('Settings', 'UndoneJob')
    eval_dict = ''
    try:
        eval_dict = eval(undone_job)
    except:
        pass
    return eval_dict

def build_dl():
    global all_filename, sel_res, inc_filesize

    tmp_dlm = nbdler.Manager()
    all_urls = sel_res.getVideosFullUrl()
    video_title = sel_res.getVideoTitle()
    for i, j in enumerate(all_filename):
        filepath = os.path.join(target_path, video_title)
        if os.path.exists(os.path.join(filepath, j + u'.nbdler')) or not os.path.exists(
                os.path.join(filepath, j)):
            dl = nbdler.open(filename=j, filepath=filepath, max_conn=3,urls=[all_urls[i]])
            tmp_dlm.addHandler(dl, name=i)
        else:
            gui.frame_main.updateBlock(i, gui.COLOR_OK)
            inc_filesize += os.path.getsize(os.path.join(filepath, j))

    return tmp_dlm

def generate_names():
    global all_filename, sel_res
    filename = sel_res.getVideoTitle()
    all_filename = []
    for i in range(sel_res.getTotal()):
        name = '%04d-%s.%s' % (i, filename, sel_res.getFileFormat())
        all_filename.append(name)


def merge_videos():
    global mer

    path_name_seg = []
    for i in all_filename:
        path_name_seg.append(os.path.join(target_path, sel_res.getVideoTitle(), i))
    mer = Merger(unicode(os.path.join(target_path, sel_res.getVideoTitle() + '.' + sel_res.getFileFormat())),
                 path_name_seg)
    gui.frame_main.initTotal_Merge(len(all_filename))
    mer.start()

    while True:
        gui.frame_main.updateMerge(mer.now)
        time.sleep(0.05)
        if mer.now == mer.sum:
            gui.frame_main.updateMerge(mer.now)
            break

    with open('config.ini', 'wb') as f:
        save_configure()

    dlg = wx.MessageDialog(gui.frame_main, u'视频已经合并完成，是否删除分段文件？', u'提示', wx.YES_NO | wx.ICON_QUESTION)
    if dlg.ShowModal() == wx.ID_YES:
        del_seg_video()
    dlg = wx.MessageDialog(gui.frame_main, u'分段文件删除完成。', u'提示', wx.OK | wx.ICON_QUESTION)
    dlg.ShowModal()


def del_seg_video():
    time.sleep(2)
    for i in all_filename:
        os.remove(os.path.join(target_path, sel_res.getVideoTitle(), i))

    os.removedirs(os.path.join(target_path, sel_res.getVideoTitle()))


def check_all_files():
    title = sel_res.getVideoTitle()

    for i in all_filename:
        if not os.path.exists(os.path.join(target_path, title, i)) or \
                os.path.exists(os.path.join(target_path, title, i + '.nbdler')):
            break
    else:
        return True
    return False

def dl_process(event):
    global dlm, max_task, inc_filesize, mer
    if not dlm:
        return
    if not dlm.getRunQueue():
        if check_all_files():
            gui.stopTimer()

            threading.Timer(0.1, merge_videos).start()
        else:
            return



    run_queue = dlm.getRunQueue()

    new = list(filter(lambda x: dlm.getNameFromId(x) not in gui.frame_main.getItemsDict(), run_queue))

    for i in new:
        dl = dlm.getHandler(id=i)
        filesize = dl.getFileSize()
        gui.frame_main.insertItem(dlm.getNameFromId(i), filesize, filesize - dl.getLeft(), dl.getInsSpeed(False))
        gui.frame_main.updateBlock(dlm.getNameFromId(i), gui.COLOR_RUN)

    redundancy = list(filter(lambda x: dlm.getIdFromName(x) not in run_queue, gui.frame_main.getItemsDict()))

    for i in redundancy:
        dl = dlm.getHandler(name=i)
        filesize = dl.getFileSize()
        gui.frame_main.getItem(i).update(filesize, dl.getInsSpeed(False), filesize)
        gui.frame_main.deleteItem(i, True if len(gui.frame_main.getItemsDict()) > max_task else False)

        gui.frame_main.updateBlock(i, gui.COLOR_OK)

    run_queue = dlm.getRunQueue()
    for i in run_queue:
        dl = dlm.getHandler(id=i)
        filesize = dl.getFileSize()
        item = gui.frame_main.getItem(dlm.getNameFromId(i))
        if item:
            item.update(filesize-dl.getLeft(), dl.getInsSpeed(False), filesize)

    cur_inc = 0
    done_queue = dlm.getDoneQueue()
    for i in done_queue:
        dl = dlm.getHandler(id=i)
        cur_inc += dl.getFileSize()
    for i in run_queue:
        dl = dlm.getHandler(id=i)
        cur_inc += dl.getFileSize() - dl.getLeft()

    gui.frame_main.updateTotal(cur_inc + inc_filesize, dlm.getInsSpeed())


def collectInfo():
    global target_path, sel_res
    target_path = gui.frame_parse.textctrl_path.GetLineText(0)

    sel_bid = int(gui.frame_parse.listctrl_parse.GetItemText(gui.frame_parse.listctrl_parse.GetFirstSelected(), 0))
    for i in iqiyi.getLastRespond():
        if i.getSelBid() == sel_bid:
            sel_res = i
            break
    else:
        sel_res = None

def initSettings():
    if os.path.exists('Cookie.txt'):
        with open('Cookie.txt', 'r') as f:
            cookie = f.read().strip()

        if cookie:
            iqiyi.loadCookie(cookie)
    else:
        with open('Cookie.txt', 'w') as f:
            pass


def _parse_undone(undone_job):
    global sel_res
    if not isinstance(undone_job, dict):
        return False
    while True:
        try:
            res = iqiyi.parse(undone_job['url'], [undone_job['bid']])
        except (socket.timeout, urllib2.URLError):
            dlg = wx.MessageDialog(gui.frame_parse, u'请求超时,是否重试！', u'提示', wx.YES_NO | wx.ICON_ERROR)
            msg = dlg.ShowModal()
            if msg == wx.NO:
                return False
            else:
                continue
        sel_res = res[0]
        return True


def handler_frame_main():
    global glb_undone_job

    gui.setTimerHandler(dl_process)
    gui.runTimer(500, False)

    initDownloader()
    gui.MainLoop()
    global mer, dlm, global_url
    if dlm.getRunQueue() or dlm.getUndoneQueue() or (mer and mer.isAlive()):
        undone_job = {
            'url': GUIEventBinder.global_url if GUIEventBinder.global_url else glb_undone_job.get('url', ''),
            'bid': sel_res.getSelBid(),
            'title': sel_res.getVideoTitle()
        }
        save_configure(undone_job)
    else:
        save_configure('')


def show_parser_handler():
    msg = gui.frame_parse.ShowModal()
    if msg == wx.OK:
        gui.frame_parse.Destroy()
        collectInfo()
        handler_frame_main()



def main():
    global glb_undone_job, target_path

    iqiyi.init()
    GUIEventBinder.init()
    initSettings()

    undone_job = load_config()
    gui.frame_parse.textctrl_path.SetValue(target_path)
    if undone_job:
        try:
            dlg = wx.MessageDialog(None,
                                   '[Url]:    %s\n[Title]:  %s\n[Bid]:   %s\n上一次任务尚未完成，是否继续任务？' % (
                                   undone_job['url'].encode('utf-8'), undone_job['title'].encode('utf-8'), undone_job['bid']),
                                   '提示', wx.YES_NO | wx.ICON_QUESTION)
        except:
            dlg = wx.MessageDialog(gui.frame_parse, 'config.ini文件错误。', '错误', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            show_parser_handler()
        else:
            res = dlg.ShowModal()
            if res == wx.ID_YES:
                glb_undone_job = undone_job
                if _parse_undone(undone_job):
                    handler_frame_main()
                else:
                    with open('config.ini', 'wb') as f:
                        save_configure()

                    dlg = wx.MessageDialog(gui.frame_parse, 'config.ini文件错误。', '错误', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()

                    show_parser_handler()

            elif res == wx.ID_NO:
                show_parser_handler()
            else:
                return
    else:
        show_parser_handler()



def initDownloader():

    if sel_res:

        gui.frame_main.setTitleName(sel_res.getVideoTitle())
        gui.frame_main.initTotal(sel_res.getTotalFileSize())

        generate_names()

        gui.frame_main.Show(True)

        for i in range(sel_res.getTotal()):
            gui.frame_main.insertBlock(i)

        threading.Thread(target=runDownloader).start()


def runDownloader():
    global dlm, max_task
    dlm = build_dl()
    dlm.config(max_task=max_task)
    dlm.run()


if __name__ == '__main__':
    gui.init()
    main()

    if dlm:
        dlm.pause()
        dlm.shutdown()
