
# import logging
from DLInfos import *
from DLProgress import *
from packer import Packer
import time, os


LOG_FORMAT = "%(asctime)s,%(msecs)03d - %(levelname)s - %(threadName)-12s - (%(progress)s)[%(urlid)s] - %(message)s"

logging.basicConfig(format=LOG_FORMAT, datefmt="%m/%d/%Y %H:%M:%S", level=logging.CRITICAL)

logger = logging.getLogger('nbdler')


__URL_NODE_PARAMS__ = {
    'urls': 'url',
    'cookies': 'cookie',
    'hosts': 'host',
    'ports': 'port',
    'paths': 'path',
    'headers': 'headers',
    'max_threads': 'max_thread'
}

class Handler(Packer, object):

    def __init__(self):
        self.url = UrlPool()
        self.file = File()
        self.__auto_global__ = GlobalProgress(self, AUTO)

        self.__manual_global__ = GlobalProgress(self, MANUAL)

        self.__new_project__ = True

        self.globalprog = self.__auto_global__

    def uninstall(self):
        pass


    def install(self, GlobalProgress):
        self.globalprog = GlobalProgress

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
                        raise Exception('IterLenError')

            pack_yield.append(node)

        for iter_kw in pack_yield:
            self.addNode(**iter_kw)


    def addNode(self, *args, **kwargs):
        self.url.addNode(*args, **kwargs)

        if self.file.size == -1:
            self.file.size = self.url.getFileSize()
        if not self.file.name:
            self.file.name = self.url.getFileName()

            if not self.file.name:

                self.file = File(name=self.file.name, path=self.file.path,
                                 size=self.url.getFileSize(), block_size=self.file.BLOCK_SIZE)

    def delete(self, url=None, urlid=None):
        if urlid:
            self.url.delete(urlid)
        elif url:
            for i in self.url.dict.values():
                if i.url == url:
                    self.url.delete(i.id)

    def insert(self, begin, end, thread_num=1):
        self.globalprog = self.__manual_global__

        put_urlid = self.globalprog.allotter.assignUrl()
        if put_urlid != -1:

            self.file.fp.insert(begin, end)

            for i in self.globalprog.allotter.splitRange((begin, end), thread_num):
                self.globalprog.insert(put_urlid, i[0], i[1])

    def manualRun(self):
        if not self.globalprog.progresses:
            raise Exception('EmptyEqueue')

        self.globalprog = self.__manual_global__

        self.globalprog.run()




    def getFileName(self):
        return self.file.name if self.file.name else None

    def getFileSize(self):
        return self.url.getFileSize()

    def getUrls(self):
        return self.url.dict

    def getInsSpeed(self):
        return self.globalprog.getInsSpeed()

    def getAvgSpeed(self):
        return self.globalprog.getAvgSpeed()

    def getLeft(self):
        return self.globalprog.getLeft()

    def getOnlines(self):
        return self.globalprog.getOnlines()

    def getConnections(self):
        return self.globalprog.getConnections()

    def getBlockMap(self):
        return self.globalprog.getMap()


    def getSegsValue(self):
        return self.file.fp.getvalue()

    def getSegsSize(self):
        return self.file.fp.getStorageSize()


    def getUrlsThread(self):
        return self.globalprog.allotter.getUrlsThread()

    def __config_params__(self):
        return {'filename': 'file.name',
                'filepath': 'file.path',
                'block_size': 'file.BLOCK_SIZE',
                'max_conn': 'url.max_conn',
                'buffer_size': 'file.buffer_size',
                'max_speed': 'url.max_speed',
        }

    def config(self, **kwargs):

        for i, j in self.__config_params__().items():
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
        if not self.globalprog.isEnd():
            raise Exception('DownloadNotComplete')
        if os.path.isfile(os.path.join(self.file.path, self.file.name + '.nbdler')):
            os.remove(os.path.join(self.file.path, self.file.name + '.nbdler'))

    def fileVerify(self, sample_size=1024):
        if sample_size > self.file.BLOCK_SIZE:
            raise Exception('ParamsError')

        for i, j in self.globalprog.progresses.items():
            Range = segToRange(i)
            self.insert(Range[1] - sample_size, Range[1], 1)

        self.manualRun()

        while not self.globalprog.isEnd():
            time.sleep(0.1)

        all_value = self.file.fp.getvalue()

        damage = []

        with open(os.path.join(self.file.path, self.file.name), 'rb') as f:
            for i, j in all_value.items():
                Range = segToRange(i)
                f.seek(Range[0])
                if f.read(sample_size) != j:
                    damage.append(i)

        return damage


    def fix(self, segs):
        self.fix(segs)

    def sampleDetect(self):
        pass


    def run(self):
        # self.__mode__ = AUTO
        self.globalprog = self.__auto_global__
        if self.__new_project__:
            self.file.makeFile()
            self.globalprog.allotter.makeBaseConn()
            self.globalprog.save()

        self.globalprog.run()

    def pause(self):
        self.globalprog.pause()

    def isEnd(self):
        return self.globalprog.isEnd()

    def unpack(self, packet):
        Packer.unpack(self, packet)
        self.__new_project__ = False


    def __packet_params__(self):
        return ['url', 'file', '__auto_global__']


