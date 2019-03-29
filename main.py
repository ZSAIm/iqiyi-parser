

import gui
import iqiyi_parse as iqiyi
import json, os, time
import threading
from merger import Merger
import wx
import nbdler
import GUIEventBinder
import socket
socket.setdefaulttimeout(5)

dlm = nbdler.Manager()
total_filesize = 0
max_task = 5
target_path = ''
video_title = ''
resolution = ''
sel_bid = None
all_filename = []

def build_dl(sel_msg):
    global dlm, video_title, all_filename
    for i, j in enumerate(all_filename):
        _url, _ = iqiyi.activatePath(sel_msg['fs'][i]['l'])
        filepath = os.path.join(target_path, video_title)
        if os.path.exists(os.path.join(filepath, j + u'.nbdler')) or not os.path.exists(
                os.path.join(filepath, j)):
            dl = nbdler.open(filename=j, filepath=filepath, max_conn=3, urls=[_url], wait=False)
            dlm.addHandler(dl, name=i)
        else:
            gui.frame_main.updateBlock(i, gui.COLOR_OK)

    return dlm

def generate_names(filename, msg):
    global all_filename
    all_filename = []
    for i, j in enumerate(msg['fs']):
        name = '%04d-%s.%s' % (i, filename, msg['ff'])
        all_filename.append(name)


def merge_videos():
    _, res = iqiyi.getLastRes()
    path_name_seg = []
    for i in all_filename:
        path_name_seg.append(os.path.join(target_path, video_title, i))
    mer = Merger(unicode(os.path.join(target_path, video_title + '.' + res[sel_bid]['ff'])), path_name_seg)
    gui.frame_main.initTotal_Merge(len(all_filename))
    mer.start()
    while True:
        gui.frame_main.updateMerge(mer.now)
        time.sleep(0.01)
        if mer.now == mer.sum:
            gui.frame_main.updateMerge(mer.now)
            break

    del_seg_video()

def del_seg_video():
    time.sleep(2)
    for i in all_filename:
        os.remove(os.path.join(target_path, video_title, i))

    os.removedirs(os.path.join(target_path, video_title))


def dl_process(event):
    global dlm, max_task

    run_queue = dlm.getRunQueue()
    if not run_queue:
        gui.stopTimer()
        threading.Timer(0.1, merge_videos).start()

    new = list(filter(lambda x: x not in gui.frame_main.getItemsDict(), run_queue))

    for i in new:
        dl = dlm.getHandler(id=i)
        filesize = dl.getFileSize()
        gui.frame_main.insertItem(i, filesize, filesize - dl.getLeft(), dl.getInsSpeed(False))
        gui.frame_main.updateBlock(dlm.getNameFromId(id=i), gui.COLOR_RUN)

    redundancy = list(filter(lambda x: x not in run_queue, gui.frame_main.getItemsDict()))

    for i in redundancy:
        dl = dlm.getHandler(id=i)
        filesize = dl.getFileSize()
        gui.frame_main.getItem(i).update(filesize, dl.getInsSpeed(False), filesize)
        gui.frame_main.deleteItem(i, True if len(gui.frame_main.getItemsDict()) > max_task else False)

        gui.frame_main.updateBlock(dlm.getNameFromId(id=i), gui.COLOR_OK)

    run_queue = dlm.getRunQueue()
    for i in run_queue:
        dl = dlm.getHandler(id=i)
        filesize = dl.getFileSize()
        item = gui.frame_main.getItem(i)
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

    gui.frame_main.updateTotal(cur_inc, dlm.getInsSpeed())


def collectInfo():
    global target_path, sel_bid
    target_path = gui.frame_parse.textctrl_path.GetLineText(0)

    sel_bid = int(gui.frame_parse.listctrl_parse.GetItemText(gui.frame_parse.listctrl_parse.GetFirstSelected(), 0))



def main():
    global video_title

    iqiyi.init()
    GUIEventBinder.init()

    res = gui.frame_parse.ShowModal()
    if res == wx.OK:
        gui.frame_parse.Destroy()
        collectInfo()
        video_title, res = iqiyi.getLastRes()
        runDownloader(video_title, res[sel_bid])

    else:
        exit(0)


def runDownloader(video_title, sel_res):
    global dlm

    if sel_res:
        id_couter = 0
        total_filesize = sel_res['vsize']
        gui.frame_main.setTitleName(video_title)
        gui.frame_main.initTotal(total_filesize)
        for i in sel_res['fs']:
            gui.frame_main.insertBlock(id_couter)
            id_couter += 1

        generate_names(video_title, sel_res)

        gui.frame_main.Show(True)
        dlm = build_dl(sel_res)
        dlm.config(max_task=5)
        dlm.run()
        gui.setTimerHandler(dl_process)
        gui.runTimer(500, False)


if __name__ == '__main__':
    gui.init()
    main()
    gui.MainLoop()
    dlm.shutdown()
