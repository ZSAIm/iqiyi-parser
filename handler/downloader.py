

import os, threading
import nbdler
import gui
import CommonVar as cv
from core.common import BasicUrlGroup

SHUTDOWN = False
HANDLER = None






class Handler:
    def __init__(self):
        self.dlm = nbdler.Manager()

        self.filepath = ''

        self.max_task = 5
        self.max_conn = 3

        self.video_urls = []
        self.audio_urls = []

        self._res = None
        self._title = None
        # self._filenum = 0
        self._ext = ''
        self.video_filenames = []
        self.audio_filenames = []
        self._inc_progress = 0

        self._range_format = 'Range: bytes=%d-%d'
        self._headers = {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

        self._thr = None

        self.wait_for_run = False

        self._undone_list = []


    def prepare(self, res):
        self.filepath = cv.FILEPATH
        self.max_task = cv.MAX_TASK
        self.max_conn = cv.MAX_CONN

        self.video_urls = res.getVideoUrls()
        self.audio_urls = res.getAudioUrls()
        self._title = res.getVideoLegalTitle()
        # self._filenum = len(self.video_urls)
        self._ext = res.getFileFormat()
        self._range_format = res.getRangeFormat()
        self._headers = res.getReqHeaders()

    def run(self):
        self._thr = threading.Thread(target=self.__run__)
        self._thr.start()

    def shutdown(self):
        self.dlm.shutdown()
        self.dlm.join()

    def add_handler(self, dlm, urls, path, name, dlm_name=None):
        group_done_flag = True
        filepath = os.path.join(path, name)
        if os.path.exists(filepath + '.nbdler') and os.path.exists(filepath):

            group_done_flag = False
            dl = nbdler.open(filepath, wait_for_run=self.wait_for_run)
            kwargs = {
                'urls': [*list(urls)] if isinstance(urls, list) or isinstance(
                    urls, tuple) else [urls],
                'range_formats': [self._range_format],
                'headers': [self._headers],
            }
            dl.batchAdd(wait_for_run=self.wait_for_run, **kwargs)
            # dlm.addHandler(dl, name=index)
            dlm.addHandler(dl)

        elif not os.path.exists(filepath):
            group_done_flag = False
            # for mul_url in self.video_urls:

            kwargs = {
                'filename': name,
                'filepath': path,
                'max_conn': self.max_conn,
                'urls': [*list(urls)] if isinstance(urls, list) or isinstance(
                    urls, tuple) else [urls],
                'range_formats': [self._range_format],
                'headers': [self._headers],
                'buffer_size': cv.BUFFER_SIZE * 1024 * 1024,
                'block_size': cv.BLOCK_SIZE * 1024
            }
            dl = nbdler.open(wait_for_run=self.wait_for_run, **kwargs)
            # dlm.addHandler(dl, name=index)
            if dlm_name is not None:
                dlm.addHandler(dl, name=dlm_name)
            else:
                dlm.addHandler(dl)
        else:
            self._inc_progress += os.path.getsize(filepath)

        return group_done_flag

    def __run__(self):
        self.dlm.config(max_task=self.max_task)

        self.generate_name()
        self._undone_list = self.video_filenames[:]
        if len(self.video_filenames) + len(self.audio_filenames) > 100:
            self.wait_for_run = True
        path = os.path.join(self.filepath, self._title)

        ######################## video
        file_counter = 0
        for i, j in enumerate(self.video_urls):

            if isinstance(j, BasicUrlGroup):
                group_done_flag = True
                group_dlm = nbdler.Manager()
                group_dlm.config(max_task=cv.MAX_TASK)
                for index, cur_urls in enumerate(j):

                    if not self.add_handler(group_dlm, cur_urls, path, self.video_filenames[file_counter]):
                        group_done_flag = False
                    file_counter += 1

                self.dlm.addHandler(group_dlm, name=i)
            elif isinstance(j, list) or isinstance(j, tuple):
                group_done_flag = self.add_handler(self.dlm, list(j), path, self.video_filenames[file_counter], i)
                file_counter += 1
            elif isinstance(j, str):
                group_done_flag = self.add_handler(self.dlm, [j], path, self.video_filenames[file_counter], i)
                file_counter += 1
            else:
                raise TypeError('downloader got an unsupported type %s , should be list or tuple' % str(type(j)))

            if group_done_flag:
                gui.frame_downloader.updateBlock(i, gui.COLOR_OK)


        ######################## audio

        file_counter = 0
        for i, j in enumerate(self.audio_urls):

            if isinstance(j, BasicUrlGroup):
                group_done_flag = True
                group_dlm = nbdler.Manager()
                group_dlm.config(max_task=cv.MAX_TASK)
                for index, cur_urls in enumerate(j):

                    if not self.add_handler(group_dlm, cur_urls, path, self.audio_filenames[file_counter]):
                        group_done_flag = False
                    file_counter += 1

                if group_done_flag:
                    gui.frame_downloader.updateBlock(i, gui.COLOR_OK)

                self.dlm.addHandler(group_dlm, name=i)
            elif isinstance(j, list) or isinstance(j, tuple):

                self.add_handler(self.dlm, list(j), path, self.audio_filenames[file_counter], i)
                file_counter += 1
            elif isinstance(j, str):
                self.add_handler(self.dlm, [j], path, self.audio_filenames[file_counter], i)
                file_counter += 1
            else:
                raise TypeError('downloader got an unsupported type %s , should be list or tuple' % str(type(j)))

        self.dlm.run()

    def join(self):
        if not self._thr:
            raise RuntimeError('cannot join thread before it is started')
        self._thr.join()
        self.dlm.join()

    def getAllVideoFilePath(self):
        return [os.path.join(self.filepath, self._title, i) for i in self.video_filenames]

    def getAllAudioFilePath(self):
        return [os.path.join(self.filepath, self._title, i) for i in self.audio_filenames]

    def getDstVideoFilePath(self):
        if self.audio_filenames:
            return os.path.join(self.filepath, '[video]%s.%s' % (self._title, self._ext))
        else:
            return os.path.join(self.filepath, '%s.%s' % (self._title, self._ext))

    def getDstAudioFilePath(self):
        return os.path.join(self.filepath, '[audio]%s.%s' % (self._title, self._ext))


    def getDstFilePath(self):
        return os.path.join(self.filepath, '%s.%s' % (self._title, self._ext))


    def generate_name(self):
        self.audio_filenames = []
        for i, j in enumerate(self.audio_urls):
            # tmp_names = []
            if isinstance(j, BasicUrlGroup):
                for n in range(len(j)):
                    self.audio_filenames.append('[audio]%03d-(%04d)%s.%s' % (i, n, self._title, self._ext))
            else:
                self.audio_filenames.append('[audio]%03d-%s.%s' % (i, self._title, self._ext))
            # self.audio_filenames.append(tmp_names)

        self.video_filenames = []
        if self.audio_filenames:
            for i, j in enumerate(self.video_urls):
                # tmp_names = []
                if isinstance(j, BasicUrlGroup):
                    for n in range(len(j)):
                        self.video_filenames.append('[video]%03d-(%04d)%s.%s' % (i, n, self._title, self._ext))
                else:
                    self.video_filenames.append('[video]%03d-%s.%s' % (i, self._title, self._ext))
                # self.video_filenames.append(tmp_names)
        else:
            for i, j in enumerate(self.video_urls):
                # tmp_names = []
                if isinstance(j, BasicUrlGroup):
                    for n in range(len(j)):
                        self.video_filenames.append('%03d-(%04d)%s.%s' % (i, n, self._title, self._ext))
                else:
                    self.video_filenames.append('%03d-%s.%s' % (i, self._title, self._ext))
                # self.video_filenames.append(tmp_names)

    def is_all_files_done(self):
        for i in list(self._undone_list):
            if not os.path.exists(os.path.join(self.filepath, self._title, i)) or \
                    os.path.exists(os.path.join(self.filepath, self._title, i + '.nbdler')):
                break
            else:
                if i in self._undone_list:
                    self._undone_list.remove(i)
        else:
            return True

        return False

    def insert_new_item(self, run_queue):
        new = list(filter(lambda x: self.dlm.getNameFromId(x) not in gui.frame_downloader.getItemsDict(),
                          run_queue))

        for i in new:
            dl = self.dlm.getHandler(id=i)
            size = dl.getFileSize()
            cur_name = self.dlm.getNameFromId(i)
            gui.frame_downloader.insertItem(cur_name, size)
            gui.frame_downloader.updateBlock(cur_name, gui.COLOR_RUN)

        if new:
            gui.frame_downloader.Layout()
            # gui.frame_main.sizer_items.Layout()

    def delete_end_item(self, done_queue):
        end = list(filter(lambda x: self.dlm.getIdFromName(x) in done_queue,
                          gui.frame_downloader.getItemsDict()))

        for i in end:
            dl = self.dlm.getHandler(name=i)
            size = dl.getFileSize()
            item = gui.frame_downloader.getItem(i)
            item.update(size, dl.getInsSpeed(), size)
            gui.frame_downloader.deleteItem(i, True if len(gui.frame_downloader.getItemsDict()) > self.max_task else False)
            gui.frame_downloader.updateBlock(i, gui.COLOR_OK)

        if end:
            gui.frame_downloader.Layout()
            # gui.frame_main.sizer_items.Layout()

    def update_item(self, run_queue):
        for i in run_queue:
            dl = self.dlm.getHandler(id=i)
            inc_byte = dl.getIncByte()
            size = dl.getFileSize()
            item = gui.frame_downloader.getItem(self.dlm.getNameFromId(i))
            if item:
                item.update(inc_byte, dl.getInsSpeed(), size)

    def update_total(self, run_queue, done_queue):
        cur_inc = 0
        for i in done_queue:
            dl = self.dlm.getHandler(id=i)
            cur_inc += dl.getFileSize()
        for i in run_queue:
            dl = self.dlm.getHandler(id=i)
            cur_inc += dl.getIncByte()

        gui.frame_downloader.updateTotal(cur_inc + self._inc_progress, self.dlm.getInsSpeed(), self.dlm.getTotalSize() + self._inc_progress)

    def process_event(self, event):
        done_queue = self.dlm.getDoneQueue()
        run_queue = self.dlm.getRunQueue()

        self.insert_new_item(run_queue)
        self.delete_end_item(done_queue)

        self.update_item(run_queue)

        self.update_total(run_queue, done_queue)

        # gui.frame_main.Layout()

        if not run_queue:
            if self.is_all_files_done():
                gui.stopTimer()
            return


def init():
    global HANDLER
    HANDLER = Handler()


def prepare(res):
    global HANDLER
    HANDLER.prepare(res)


def run():
    global HANDLER
    HANDLER.run()


def join():
    global HANDLER
    if HANDLER:
        HANDLER.join()


def isAllDone():
    global HANDLER
    return HANDLER.is_all_files_done()


def shutdown():
    global HANDLER, SHUTDOWN
    SHUTDOWN = True
    if HANDLER:
        HANDLER.shutdown()


def getProcessEvent():
    global HANDLER
    return HANDLER.process_event


def getAllVideoFilePath():
    global HANDLER
    return HANDLER.getAllVideoFilePath()

def getAllAudioFilePath():
    global HANDLER
    return HANDLER.getAllAudioFilePath()


def getDstVideoFilePath():
    global HANDLER
    return HANDLER.getDstVideoFilePath()

def getDstFilePath():
    global HANDLER
    return HANDLER.getDstFilePath()


def getDstAudioFilePath():
    global HANDLER
    return HANDLER.getDstAudioFilePath()

