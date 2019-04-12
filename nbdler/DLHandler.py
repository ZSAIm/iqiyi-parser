
import logging
from DLInfos import *
from DLProgress import *
from packer import Packer
import time, os
from DLThreadPool import ThreadPool


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
        self.url = UrlPool(self)
        self.file = File(self)

        self.thrpool = ThreadPool()

        self.__globalprog__ = GlobalProgress(self, AUTO)

        self.__new_project__ = True

        self.globalprog = self.__globalprog__

        self.shutdown_flag = False


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
                        raise Exception('IterLenError')

            pack_yield.append(node)

        self.thrpool.Thread(target=self.__batchAdd__, args=(pack_yield,), name='AddNode').start()


    def addNode(self, *args, **kwargs):
        self.url.addNode(*args, **kwargs)


    def delete(self, url=None, urlid=None):
        if urlid:
            self.url.delete(urlid)
        elif url:
            for i in self.url.dict.values():
                if i.url == url:
                    self.url.delete(i.id)

    def insert(self, begin, end, Urlid=None, thread_num=1):

        put_urlid = self.globalprog.allotter.assignUrlid() if not Urlid else Urlid
        if put_urlid != -1:

            self.globalprog.fs.insert(begin, end)

            for i in self.globalprog.allotter.splitRange((begin, end), thread_num):
                self.globalprog.insert(put_urlid, i[0], i[1])

    def manualRun(self):
        if not self.globalprog.progresses:
            raise Exception('EmptyEqueue')

        self.globalprog.run()


    def join(self):
        while not self.thrpool.isAllDead():
            time.sleep(0.01)

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

    def fileVerify(self, sample_size=4096):
        self.install(GlobalProgress(self, MANUAL))

        if sample_size > self.file.BLOCK_SIZE:
            raise Exception('ParamsError')

        for i, j in self.globalprog.progresses.items():
            Range = segToRange(i)
            self.insert(Range[1] - sample_size, Range[1])

        self.manualRun()

        while not self.globalprog.isEnd():
            time.sleep(0.1)

        all_value = self.globalprog.fs.getvalue()

        damage = []

        with open(os.path.join(self.file.path, self.file.name), 'rb') as f:
            for i, j in all_value.items():
                Range = segToRange(i)
                f.seek(Range[0])
                if f.read(sample_size) != j:
                    damage.append(i)

        self.uninstall()
        return damage


    def fix(self, segs):
        self.fix(segs)

    def sampleUrls(self, sample_size=1024 * 1024):

        import random

        self.url.matchSize()

        if self.file.size < sample_size:
            sample_size = self.file.size

        _begin = random.randint(0, self.file.size - sample_size)
        _end = _begin + sample_size

        global_dict = {}
        for i in self.url.getUrls().keys():
            glob = GlobalProgress(self, MANUAL)
            global_dict[i] = glob
            self.install(glob)
            self.insert(_begin, _end, i)
            self.manualRun()

        while True:
            for i in global_dict.values():
                if not i.isEnd():
                    break
            else:
                break
            time.sleep(0.1)

        samples = {}

        for i, j in global_dict.items():
            i.fs.seek(_begin)
            samples[i] = i.fs.read(sample_size)

        sample_type = []
        sample_type.append([samples.keys()[0]])
        for i, j in samples.items():
            for m in sample_type:
                if i not in m:
                    if samples[i] == samples[m[0]]:
                        m.append(i)
                        break
                else:
                    break
            else:
                sample_type.append([i])

        self.uninstall()

        return sample_type

    def __run__(self):
        if self.__new_project__:
            self.file.makeFile()
            if self.file.size == -1:
                return
            self.globalprog.allotter.makeBaseConn()
            self.globalprog.save()

        self.globalprog.run()

    def run(self):
        self.thrpool.Thread(target=self.__run__).start()

    def pause(self):
        self.globalprog.pause()

    def isEnd(self):
        return self.globalprog.isEnd()

    def unpack(self, packet):
        Packer.unpack(self, packet)
        self.__new_project__ = False

    def shutdown(self):
        if not self.isEnd():
            self.shutdown_flag = True
            self.globalprog.shutdown()
            self.shutdown_flag = False


    def __packet_params__(self):
        return ['url', 'file', '__auto_global__']


    def getFileName(self):
        return self.file.name if self.file.name else None

    def getFileSize(self):
        return self.file.size

    def getUrls(self):
        return self.url.dict

    def getInsSpeed(self, update=True):
        return self.globalprog.getInsSpeed(update)

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

    def getBlockMap(self):
        return self.globalprog.getMap()


    def getSegsValue(self):
        return self.globalprog.fs.getvalue()

    def getSegsSize(self):
        return self.globalprog.fs.getStorageSize()


    def getUrlsThread(self):
        return self.globalprog.allotter.getUrlsThread()
