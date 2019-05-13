
import logging
from .DLInfos import *
from .DLProgress import *
from .packer import Packer
import time, os
from .DLThreadPool import ThreadPool


# LOG_FORMAT = "%(asctime)s,%(msecs)03d - %(levelname)s - %(threadName)-12s - (%(progress)s)[%(urlid)s] - %(message)s"
#
# logging.basicConfig(format=LOG_FORMAT, datefmt="%m/%d/%Y %H:%M:%S", level=logging.CRITICAL)
#
# logger = logging.getLogger('nbdler')

__URL_NODE_PARAMS__ = {
    'urls': 'url',
    'cookies': 'cookie',
    'hosts': 'host',
    'ports': 'port',
    'paths': 'path',
    'headers': 'headers',
    'max_threads': 'max_thread',
    'range_formats': 'range_format',
    # 'pull_flags': 'pull_flag'
}


__CONFIG__ = {
    'filename': 'file.name',
    'filepath': 'file.path',
    'block_size': 'file.BLOCK_SIZE',
    'max_conn': 'url.max_conn',
    'buffer_size': 'file.buffer_size',
    'max_speed': 'url.max_speed',
    'wait_for_run': '_wait_for_run',
    'daemon': '_daemon',
    'max_retry': 'url.max_retry'
}

class Handler(Packer, object):

    def __init__(self):
        self.url = UrlPool(self)
        self.file = File(self)

        self.threads = ThreadPool(False)

        self.__globalprog__ = GlobalProgress(self, AUTO)
        self.status = self.__globalprog__.status

        self.__new_project__ = True

        self.globalprog = self.__globalprog__

        # self.shutdown_flag = False

        # self._wait_for_run = False
        self._batchnode_bak = None

        self._daemon = False

    def setDaemon(self, daemonic):
        self._daemon = daemonic
        self.threads.setDaemon(daemonic)

    def uninstall(self):
        self.globalprog = self.__globalprog__

    def install(self, GlobalProgress):
        self.globalprog = GlobalProgress

    def __batchAdd__(self, pack_yield):
        for iter_kw in pack_yield:
            self.addNode(**iter_kw)


    def batchAdd(self, **kwargs):
        global __URL_NODE_PARAMS__

        pack_yield = []
        iter_len = len(kwargs.get('urls', []))
        for i in range(iter_len):
            node = {}
            for m, n in __URL_NODE_PARAMS__.items():
                if m in kwargs:
                    if len(kwargs[m]) == 1:
                        node[n] = kwargs[m][0]
                    elif len(kwargs[m]) == iter_len:
                        node[n] = kwargs[m][i]
                    else:
                        raise ValueError('IterLenError')

            pack_yield.append(node)

        self.threads.Thread(target=self.__batchAdd__, args=(pack_yield,), name=cv.ADDNODE).start()
        print(self.file.name)

    def addNode(self, *args, **kwargs):
        self.url.addNode(*args, **kwargs)

    def delete(self, url=None, urlid=None):
        if urlid:
            self.url.delete(urlid)
        elif url:
            for i in self.url._url_box.values():
                if i.url == url:
                    self.url.delete(i.id)

    def insert(self, begin, end, Urlid=None, thread_num=1):

        put_urlid = self.globalprog.allotter.assignUrlid() if not Urlid else Urlid
        if put_urlid != -1:
            print('fs_insert')
            self.globalprog.fs.insert(begin, end)

            for i in self.globalprog.allotter.splitRange((begin, end), thread_num):
                self.globalprog.insert(put_urlid, i[0], i[1])

    def manualRun(self):
        if not self.globalprog.progresses:
            raise Exception('EmptyEqueue')

        self.globalprog.run()

    def trap(self):
        self.globalprog.trap()


    def join(self):
        self.globalprog.join()

    def isCritical(self):
        return self.globalprog.isCritical()


    def config(self, **kwargs):

        for i, j in __CONFIG__.items():
            if i in kwargs:
                objs = j.split('.')
                if len(objs) == 1:
                    setattr(self, objs[0], kwargs[i])
                else:
                    attr = getattr(self, objs[0])
                    for m in objs[1:-1]:
                        attr = getattr(attr, m)
                    setattr(attr, objs[-1], kwargs[i])

    def close(self):
        if not self.status.isEnd():
            raise RuntimeError("download isn't completed.")

        self.join()

        if os.path.isfile(os.path.join(self.file.path, self.file.name + '.nbdler')):
            os.remove(os.path.join(self.file.path, self.file.name + '.nbdler'))


    def __run__(self):
        if self.file.size == -1 and self._batchnode_bak:
            self.batchAdd(**self._batchnode_bak)

        # for i in self.threads.getThreads(cv.ADDNODE):
        while self.file.size == -1:
            if not self.threads.getAll(cv.ADDNODE):
                if self.file.size == -1:
                    return
            time.sleep(0.01)

        if self.__new_project__:
            self.file.makeFile()
            # if self.file.size == -1:
            #     return

            self.globalprog.allotter.makeBaseConn()
            self.globalprog.save()
        self.__new_project__ = False
        self.globalprog.run()


    def run(self):
        self.threads.Thread(target=self.__run__, name=cv.LAUNCHER).start()

    def pause(self):
        self.globalprog.pause()
        print(self.file.name, 'paused')

    shutdown = pause

    # def pausing(self):
    #     return self.globalprog.status.pausing()

    def isEnd(self):
        return self.status.isEnd()

    def unpack(self, packet):
        Packer.unpack(self, packet)
        self.__new_project__ = False

    # def shutdown(self):
    #     # if not self.isEnd():
    #     # self.globalprog.shutdown_flag = True
    #     self.globalprog.shutdown()
    #     # self.globalprog.shutdown_flag = False



    def __packet_params__(self):
        return ['url', 'file', '__globalprog__']


    def getFileName(self):
        return self.file.name if self.file.name else None

    def getFileSize(self):
        return self.file.size

    def getAllUrl(self):
        return self.url._url_box

    def getInsSpeed(self):
        return self.globalprog.getInsSpeed()

    def getAvgSpeed(self):
        return self.globalprog.getAvgSpeed()

    def getLeft(self):
        return self.globalprog.getLeft()

    def getIncByte(self):
        return self.getFileSize() - self.getLeft() if self.getFileSize() != -1 else 0

    def getOnlines(self):
        return self.globalprog.getOnlines()

    def getConnections(self):
        return self.globalprog.getConnections()

    # def getBlockMap(self):
    #     return self.globalprog.getMap()

    def getFileStorage(self):
        return self.globalprog.fs

    # def getSegsValue(self):
    #     return self.globalprog.fs.getvalue()
    #
    # def getSegsSize(self):
    #     return self.globalprog.fs.getStorageSize()


    def getUrlsThread(self):
        return self.globalprog.allotter.getUrlsThread()


    def __repr__(self):
        return '[%s] - %s' % (self.file.size, self.file.name)