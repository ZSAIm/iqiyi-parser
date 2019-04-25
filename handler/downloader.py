

import os, threading
import nbdler
import gui
import CommonVar as cv

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
        self._filenum = 0
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

    def prepare(self, res):
        self.filepath = cv.FILEPATH
        self.max_task = cv.MAX_TASK
        self.max_conn = cv.MAX_CONN

        self.video_urls = res.getVideoUrls()
        self.audio_urls = res.getAudioUrls()
        self._title = res.getVideoTitle()
        self._filenum = len(self.video_urls)
        self._ext = res.getFileFormat()
        self._range_format = res.getRangeFormat()
        self._headers = res.getReqHeaders()

    def run(self):
        self._thr = threading.Thread(target=self.__run__)
        self._thr.start()

    def shutdown(self):
        self.dlm.shutdown()

    def __run__(self):
        self.dlm.config(max_task=self.max_task)

        self.generate_name()
        path = os.path.join(self.filepath, self._title)
        for i, j in enumerate(self.video_filenames):
            filepath = os.path.join(self.filepath, self._title, j)
            if os.path.exists(filepath + '.nbdler') or not os.path.exists(filepath):
                kwargs = {
                    'filename': j,
                    'filepath': path,
                    'max_conn': self.max_conn,
                    'urls': [*list(self.video_urls[i])] if isinstance(self.video_urls[i], list) or isinstance(
                        self.video_urls[i], tuple) else [self.video_urls[i]],
                    'range_formats': [self._range_format],
                    'headers': [self._headers]
                }
                dl = nbdler.open(**kwargs)

                self.dlm.addHandler(dl, name=i)
            else:
                gui.frame_main.updateBlock(i, gui.COLOR_OK)
                self._inc_progress += os.path.getsize(filepath)

        for i, j in enumerate(self.audio_filenames):
            filepath = os.path.join(self.filepath, self._title, j)
            if os.path.exists(filepath + '.nbdler') or not os.path.exists(filepath):
                kwargs = {
                    'filename': j,
                    'filepath': path,
                    'max_conn': self.max_conn,
                    'urls': [*list(self.audio_urls[i])] if isinstance(self.audio_urls[i], list) or isinstance(
                        self.audio_urls[i], tuple) else [self.audio_urls[i]],
                    'range_formats': [self._range_format],
                    'headers': [self._headers]
                }
                dl = nbdler.open(**kwargs)

                self.dlm.addHandler(dl, name=i)
            else:
                gui.frame_main.updateBlock(len(self.video_filenames) + i, gui.COLOR_OK)
                self._inc_progress += os.path.getsize(filepath)

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
        for i in range(len(self.audio_urls)):
            self.audio_filenames.append('[audio]%04d-%s.%s' % (i, self._title, self._ext))

        self.video_filenames = []
        if self.audio_filenames:
            for i in range(self._filenum):
                self.video_filenames.append('[video]%04d-%s.%s' % (i, self._title, self._ext))
        else:
            for i in range(self._filenum):
                self.video_filenames.append('%04d-%s.%s' % (i, self._title, self._ext))


    def is_all_files_done(self):
        for i in self.video_filenames:
            if not os.path.exists(os.path.join(self.filepath, self._title, i)) or \
                    os.path.exists(os.path.join(self.filepath, self._title, i + '.nbdler')):
                break
        else:
            return True

        return False

    def insert_new_item(self, run_queue):
        new = list(filter(lambda x: self.dlm.getNameFromId(x) not in gui.frame_main.getItemsDict(),
                          run_queue))

        for i in new:
            dl = self.dlm.getHandler(id=i)
            size = dl.getFileSize()
            gui.frame_main.insertItem(self.dlm.getNameFromId(i), size)
            gui.frame_main.updateBlock(self.dlm.getNameFromId(i), gui.COLOR_RUN)

    def delete_end_item(self, done_queue):
        end = list(filter(lambda x: self.dlm.getIdFromName(x) in done_queue,
                          gui.frame_main.getItemsDict()))

        for i in end:
            dl = self.dlm.getHandler(name=i)
            size = dl.getFileSize()
            item = gui.frame_main.getItem(i)
            item.update(size, dl.getInsSpeed(), size)
            gui.frame_main.deleteItem(i, True if len(gui.frame_main.getItemsDict()) > self.max_task else False)
            gui.frame_main.updateBlock(i, gui.COLOR_OK)

    def update_item(self, run_queue):
        for i in run_queue:
            dl = self.dlm.getHandler(id=i)
            inc_byte = dl.getIncByte()
            size = dl.getFileSize()
            item = gui.frame_main.getItem(self.dlm.getNameFromId(i))
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

        gui.frame_main.updateTotal(cur_inc + self._inc_progress, self.dlm.getInsSpeed())

    def process_event(self, event):
        done_queue = self.dlm.getDoneQueue()
        run_queue = self.dlm.getRunQueue()

        self.insert_new_item(run_queue)
        self.delete_end_item(done_queue)

        self.update_item(run_queue)

        self.update_total(run_queue, done_queue)

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

