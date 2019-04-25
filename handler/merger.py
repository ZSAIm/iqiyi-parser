# -*- coding: utf-8 -*-
import threading, io, os, time
import gui
import CommonVar as cv
import subprocess
import re
import wx
from gui.merger_output import MergerOutputAppendEvent

MERGER_SIMPLE = 'simple'
MERGER_FFMPEG = 'ffmpeg'

MET_MERGE_VIDEO_AUDIO = object()

MET_CONCAT = object()

MET_CONVERT_MP4 = object()
MET_CONVERT_FLV = object()
MET_CONVERT_MKV = object()


SHUTDOWN = False

class SimpleBinMerger(threading.Thread):
    def __init__(self, dst, src):
        threading.Thread.__init__(self)
        self.dst = dst
        self.src = src
        self.total = len(self.src)
        self.current = 0

    def run(self):
        threading.Thread(target=self._progressthread).start()
        with open(self.dst, 'wb') as df:
            for path in self.src:
                self.current += 1
                with open(path, 'rb') as sf:
                    df.write(sf.read())
        self.current = len(self.src)

    def getSource(self):
        return self.src

    def getDest(self):
        return self.dst

    def _progressthread(self):
        global SHUTDOWN
        while True:
            gui.frame_main.updateMerge(self.current)
            time.sleep(0.05)
            if self.current == self.total:
                gui.frame_main.updateMerge(self.current)
                break
            if SHUTDOWN:
                break


class CustomMethod:
    def __init__(self, method, format_set):
        self.method = method
        self.format_set = format_set

    def getCMDLine(self):
        return self.method.format(**self.format_set)




class Ffmpeg(threading.Thread):
    def __init__(self, dst, src, method):
        threading.Thread.__init__(self)
        self.dst = dst
        self.src = src

        self.method = method

        self._stdout_buff = []
        self._stderr_buff = []

        self.stdout = None
        self.stderr = None

    def run(self):
        if self.method == MET_MERGE_VIDEO_AUDIO:
            self.make_video_audio_merge()
        else:
            self.convert_mp4()

    def customMethod(self):
        cmdline = self.method.getCMDLine()

        proc = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                stderr=subprocess.PIPE)
        proc.stdin.close()

        self.stdout = io.TextIOWrapper(
            proc.stdout,
            encoding='utf-8'
        )
        # somehow message comes out from stderr while not stdout

        self.stderr = io.TextIOWrapper(
            proc.stderr,
            encoding='utf-8'
        )


    def convert_mp4(self):
        cmdline = '"ffmpeg.exe" -i "out.mp4" -c:v libx264 "out1.mp4"'
        proc = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                stderr=subprocess.PIPE)

        self.stdout = io.TextIOWrapper(
            proc.stdout,
            encoding='utf-8'
        )

        self.stderr = io.TextIOWrapper(
            proc.stderr,
            encoding='utf-8'
        )

        proc.stdin.close()
        self._stdout_buff = []
        stdout_thr = threading.Thread(target=self._readerthread, args=(self.stdout, self._stdout_buff), daemon=True)
        stdout_thr.start()

        self._stderr_buff = []
        stderr_thr = threading.Thread(target=self._readerthread, args=(self.stderr, self._stderr_buff), daemon=True)
        stderr_thr.start()

        self.handle_output(self._stderr_buff, stderr_thr)


    def handle_output(self, _buff, _thread):
        # rex = re.compile(
        #     'frame=\s*\s*(.*?)\s*\s*fps=\s*\s*(.*?)\s*\s*q=\s*\s*(.*?)\s*size=\s*(.*?)\s*time=\s*(.*?)\s*bitrate=\s*(.*?)\s*speed=\s*(.*)')

        next_cur = 0
        while True:
            if len(_buff) > next_cur:
                text_line = _buff[next_cur]
                wx.PostEvent(gui.frame_merger.output, MergerOutputAppendEvent(text_line))
                next_cur += 1
            else:
                if not _thread.isAlive():
                    break
            time.sleep(0.01)

    def make_video_audio_merge(self):
        cmdline = '"{ffmpeg_path}" -i "{video}" -i "{audio}" -vcodec copy -acodec copy "{output}"'
        cmdline = cmdline.format(video=self.src[0], audio=self.src[1], output=self.dst, ffmpeg_path=cv.FFMPEG_PATH)
        proc = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                stderr=subprocess.PIPE)

        proc.stdin.close()

        self.stdout = io.TextIOWrapper(
            proc.stdout,
            encoding='utf-8'
        )

        self.stderr = io.TextIOWrapper(
            proc.stderr,
            encoding='utf-8'
        )

        self._stdout_buff = []
        stdout_thr = threading.Thread(target=self._readerthread, args=(self.stdout, self._stdout_buff), daemon=True)
        stdout_thr.start()

        self._stderr_buff = []
        stderr_thr = threading.Thread(target=self._readerthread, args=(self.stderr, self._stderr_buff), daemon=True)
        stderr_thr.start()

        self.handle_output(self._stderr_buff, stderr_thr)

    def getSource(self):
        return self.src

    def getDest(self):
        return self.dst

    def _readerthread(self, fh, buffer):
        while True:
            out = fh.readline()
            if out == '':
                break
            buffer.append(out)
        fh.close()


MERGER = {
    'ffmpeg': Ffmpeg,
    'simple': SimpleBinMerger,
}


MER_TASK = []




def make(dst, src, method):
    global MER_TASK
    if method == MET_CONCAT:
        sel_merger = MERGER['simple']
        task = sel_merger(dst, src)

        wx.CallAfter(gui.frame_main.initTotal_Merge, len(src))

        threading.Thread(target=task._progressthread).start()
    elif method == MET_MERGE_VIDEO_AUDIO:
        sel_merger = MERGER['ffmpeg']
        task = sel_merger(dst, src, MET_MERGE_VIDEO_AUDIO)
    else:
        sel_merger = MERGER['ffmpeg']
        task = sel_merger(dst, src, method)
    MER_TASK.append(task)

    return task


def shutdown():
    global SHUTDOWN
    join()
    SHUTDOWN = True

def isClosed():
    global SHUTDOWN
    return SHUTDOWN


def del_src_files():
    for i in MER_TASK:
        for j in i.getSource():
            os.remove(os.path.join(cv.FILEPATH, j).lstrip('/').lstrip('\\'))

    os.removedirs(os.path.join(cv.FILEPATH, cv.SEL_RES.getVideoTitle()))


def join():
    global MER_TASK
    if MER_TASK:
        for i in MER_TASK:
            i.join()

