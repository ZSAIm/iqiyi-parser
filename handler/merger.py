# -*- coding: utf-8 -*-
import threading, io, os, time
import gui
import CommonVar as cv
import subprocess
import re
import wx
from gui.frame_merger import MergerOutputAppendEvent, MergerOutputUpdateEvent



SHUTDOWN = False




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

        self.proc = None

    def run(self):
        method_map = {
            cv.MER_VIDEO_AUDIO: self.MergeVideoAudio,
            cv.MER_CONCAT_PROTOCAL: self.ConcatProtocal,
            cv.MER_CONCAT_DEMUXER: self.ConcatDemuxer

        }

        method_map[self.method]()

    def customMethod(self):
        cmdline = self.method.getCMDLine()

        self.pipe_open(cmdline)


    # def convert_mp4(self):
        # cmdline = '"{ffmpeg_path}" -i "{src}" -i "{audio}" -vcodec copy -acodec copy "{output}"'
        # cmdline = '"ffmpeg.exe" -i "out.mp4" -c:v libx264 "out1.mp4"'
        # self.pipe_open(cmdline)


    def handle_output(self, _buff, _thread):
        rex_prog = re.compile(
            'frame=\s*\s*(.*?)\s*\s*'
            'fps=\s*\s*(.*?)\s*\s*'
            'q=\s*\s*(.*?)\s*'
            'size=\s*(.*?)\s*'
            'time=\s*(.*?)\s*'
            'bitrate=\s*(.*?)\s*'
            'speed=\s*(.*)')
        rex_done = re.compile(
            'video:\s*\s*(.*?)\s*\s*'
            'audio:\s*\s*(.*?)\s*\s*'
            'subtitle:\s*\s*(.*?)\s*'
            'other streams:\s*(.*?)\s*'
            'global headers:\s*(.*?)\s*'
            'muxing overhead:\s*(.*)')

        total_len = cv.SEL_RES.getVideoTimeLength()
        start_time = time.time()
        # last_len = 0
        next_cur = 0
        non_monotonous_counter = 0
        while True:
            if cv.SHUTDOWN:
                break
            if len(_buff) > next_cur:
                text_line = _buff[next_cur]
                if 'Non-monotonous DTS in output stream' in text_line:
                    non_monotonous_counter += 1
                    if non_monotonous_counter <= 1:
                        wx.PostEvent(gui.frame_merger.textctrl_output, MergerOutputAppendEvent(text_line))

                else:
                    if non_monotonous_counter > 1:
                        msg = '*** 以上忽略(%d)条连续Non-monotonous信息, 视频可能存在不完整错误！ ***\n' % (non_monotonous_counter - 1)
                        wx.PostEvent(gui.frame_merger.textctrl_output, MergerOutputAppendEvent(msg))
                    non_monotonous_counter = 0
                    wx.PostEvent(gui.frame_merger.textctrl_output, MergerOutputAppendEvent(text_line))
                    time.sleep(0.01)

                res = rex_prog.search(text_line)
                if res:

                    tm = time.strptime(res.group(5), '%H:%M:%S.%y')
                    cur_len = (tm.tm_hour * 60 * 60 + tm.tm_min * 60 + tm.tm_sec) * 1000 + int(str(tm.tm_year)[2:]) * 10

                    cur_byte_str = res.group(4)
                    remain = (total_len - cur_len) / (cur_len / (time.time() - start_time))
                    hour = int(remain / 60 / 60)
                    minute = int((remain % (60*60)) / 60)
                    second = int(remain % 60)
                    remain_time_str = '%02d:%02d:%02d' % (hour, minute, second)
                    wx.PostEvent(gui.frame_merger.gauge_progress,
                                 MergerOutputUpdateEvent(cur_len=cur_len, total_len=total_len,
                                                         cur_byte_str=cur_byte_str, remain_time_str=remain_time_str))

                else:
                    res = rex_done.search(text_line)
                    if res:
                        wx.PostEvent(gui.frame_merger.gauge_progress,
                                     MergerOutputUpdateEvent(cur_len=total_len, total_len=total_len, cur_byte_str=str(
                                         round(os.path.getsize(self.dst + cv.TARGET_FORMAT) / 1024)) + 'kb',
                                                             remain_time_str='00:00:00'))

                next_cur += 1
            else:
                if not _thread.isAlive():
                    break
                time.sleep(0.01)

        pass

    def pipe_open(self, cmdline):
        self.proc = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                stderr=subprocess.PIPE)

        self.proc.stdin.close()

        self.stdout = io.TextIOWrapper(
            self.proc.stdout,
            encoding='utf-8'
        )

        self.stderr = io.TextIOWrapper(
            self.proc.stderr,
            encoding='utf-8'
        )

        self._stdout_buff = []
        stdout_thr = threading.Thread(target=self._readerthread, args=(self.stdout, self._stdout_buff), daemon=True)
        stdout_thr.start()

        self._stderr_buff = []
        stderr_thr = threading.Thread(target=self._readerthread, args=(self.stderr, self._stderr_buff), daemon=True)
        stderr_thr.start()

        self.handle_output(self._stderr_buff, stderr_thr)

    def MergeVideoAudio(self):
        cmdline = '"{ffmpeg_path}" -i "{video}" -i "{audio}" -vcodec copy -acodec copy "{output}{ext}"'
        cmdline = cmdline.format(video=self.src[0], audio=self.src[1], output=self.dst, ffmpeg_path=cv.FFMPEG_PATH, ext=cv.TARGET_FORMAT)
        self.pipe_open(cmdline)

    def ConcatProtocal(self):
        videos = '|'.join([i for i in self.src])
        cmdline = '"{ffmpeg_path}" -i concat:"{videos}" -c copy "{output}{ext}"'
        cmdline = cmdline.format(videos=videos, output=self.dst, ffmpeg_path=cv.FFMPEG_PATH, ext=cv.TARGET_FORMAT)
        self.pipe_open(cmdline)

    def ConcatDemuxer(self):
        concat_files = ["file '%s'" % i for i in self.src]
        concat_files_str = '\n'.join(concat_files)
        with open('concat_demuxer.txt', 'w') as f:
            f.write(concat_files_str)

        cmdline = '"{ffmpeg_path}" -f concat -safe 0 -i concat_demuxer.txt -c copy "{output}{ext}"'
        cmdline = cmdline.format(ffmpeg_path=cv.FFMPEG_PATH, output=self.dst, ext=cv.TARGET_FORMAT)
        self.pipe_open(cmdline)


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

    def shutdown(self):
        cmdline = 'taskkill /pid {pid} -t -f'.format(pid=self.proc.pid)
        proc = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                     stderr=subprocess.PIPE)
        a = proc.communicate()

        self.proc.kill()
        self.proc.terminate()



MER_TASK = []




def make(dst, src, method):
    global MER_TASK

    task = Ffmpeg(dst, src, method)

    MER_TASK.append(task)
    return task


def shutdown():
    global SHUTDOWN
    SHUTDOWN = True
    for i in MER_TASK:
        i.shutdown()
    join()

def isClosed():
    global SHUTDOWN
    return SHUTDOWN


def del_src_files():
    for i in MER_TASK:
        for j in i.getSource():
            os.remove(os.path.join(cv.FILEPATH, j).lstrip('/').lstrip('\\'))

    os.removedirs(os.path.join(cv.FILEPATH, cv.SEL_RES.getVideoLegalTitle()))


def join():
    global MER_TASK
    if MER_TASK:
        for i in MER_TASK:
            i.join()

