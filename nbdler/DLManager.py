

from .packer import Packer
import time, threading
from .DLError import DLUrlError
from .DLThreadPool import ThreadPool
import queue
from . import DLCommon as cv

from .DLProgress import TimeStatus

class Manager(Packer, object):
    def __init__(self, daemon=False, max_task=2):

        self.threads = ThreadPool(daemon)

        self.tasks = {}

        self._mapid = []
        self._nameid = {}

        self.max_task = max_task

        self._queue = TaskQueue()

        self._insp_thr = None

        self._queue_lock = threading.RLock()
        self._done_buff = []

        self._trap_thrs = {}
        self._url_excepts = queue.Queue()

        self.status = TimeStatus()



    def _inspector_thread(self):

        while True:
            if self.status.pausing() or self.status.isEnd():
                self.checkRunQueue()
                break
            self.checkRunQueue()

            self.run()

            time.sleep(0.01)

    def checkRunQueue(self):
        with self._queue_lock:
            for i in list(self._queue.run):
                if self.tasks[i].isEnd():
                    self.tasks[i].close()
                    self._queue.run.remove(i)
                    self._queue.done.append(i)
                    self._done_buff.append(i)
                elif self.tasks[i].isCritical():
                    self._queue.run.remove(i)
                    self._queue.critical.append(i)
            if not self._queue.run and not self._queue.undone:
                self.status.endGo()
                self.status.endDone()

    def getExcept(self):
        return list(self._url_excepts.queue)


    def get(self, name=None, id=None):
        if name is None and id is None:
            return None
        if id is not None:
            return self.tasks[id]

        if name is not None:
            return self.tasks[self.getIdByName(name)]


    def getAll(self):
        return self.tasks

    def getRunQueue(self):
        return self._queue.run

    def getPauseQueue(self):
        return self._queue.pause

    def getDoneQueue(self):
        return self._queue.done

    def getUndoneQueue(self):
        return self._queue.undone

    def getCriticalQueue(self):
        return self._queue.critical

    def getIdByName(self, name):
        return self._nameid[name]


    def getNameById(self, id):
        for i, j in self._nameid.items():
            if id == j:
                return i

    def addHandler(self, Handler, name=None):
        with self._queue_lock:
            id = self.newId()

            name = id if not name else name

            self.tasks[id] = Handler
            self._nameid[name] = id

            self._mapid[id] = True
            self._queue.undone.append(id)

        return id

    def newId(self):
        for i, j in enumerate(self._mapid):
            if not j:
                return i
        else:
            self._mapid.append(False)
            return len(self._mapid) - 1

    def remove(self, id):
        with self._queue_lock:
            del self.tasks[id]
            self._mapid[id] = False
            del self._nameid[self.getIdByName(id)]

    def run(self, id=None):
        with self._queue_lock:
            if not self._insp_thr or self._insp_thr.isStoped():
                self._insp_thr = self.threads.Thread(target=self._inspector_thread,
                                                     name=cv.MANAGER)
                self._insp_thr.start()
            if id is not None:
                if len(self._queue.run) < self.max_task:
                    self.tasks[id].run()
                    self._queue.run.append(id)
            else:
                if not self.status.isStarted():
                    self.status.startGo()
                for i in list(self._queue.undone):

                    self.status.startGo()
                    if len(self._queue.run) < self.max_task:
                        self.tasks[i].run()
                        self._queue.run.append(i)
                        # self._queue.pause.remove(i)
                        self._queue.undone.remove(i)
                    else:
                        break

    def pause(self, id=None):
        self._done_buff = []
        if id is not None:
            self.tasks[id].pause()
            with self._queue_lock:
                if id in self._queue.run:
                    self._queue.run.remove(id)
                if id not in self._queue.pause:
                    self._queue.pause.append(id)
        else:
            self.status.startPause()

            self._insp_thr.join()

            for i in self._queue.run:
                self.threads.Thread(target=self._pause, name='Nb-Manager-Pause', args=(i,)).start()

            self.status.endPause()

    shutdown = pause

    def isPaused(self):
        return self.status.isPaused()

    isShutdown = isPaused

    def _pause(self, id):
        self.tasks[id].pause()
        with self._queue_lock:
            if id in self._queue.run:
                self._queue.run.remove(id)
            if id not in self._queue.pause:
                self._queue.pause.append(id)
        self.checkRunQueue()


    def close(self):
        pass

    def join(self):
        if self._insp_thr:
            if not self._insp_thr:
                raise RuntimeError('cannot join thread before it is started')
            self._insp_thr.join()
            for i, j in list(self.tasks.items()):
                self.tasks[i].join()




    def _trap_run(self):
        for i in list(self._queue.run):
            dl = self.tasks[i]
            if id(dl) not in self._trap_thrs:
                if not dl.isEnd():
                    thr = self.threads.Thread(target=self._trap, args=(dl,))
                    self._trap_thrs[id(dl)] = thr
                    thr.start()

    def trap(self):
        if not self._insp_thr:

            raise RuntimeError('cannot join thread before it is started')
        self._trap_run()

        while self._trap_thrs or not self._url_excepts.empty():
            self._trap_run()
            if not self._url_excepts.empty():
                _except = self._url_excepts.get(timeout=1)
                raise _except
            time.sleep(0.01)
        self._insp_thr.join()

    def _trap(self, task):

        try:
            task.trap()
        except DLUrlError as e:
            self._url_excepts.put(e)

        del self._trap_thrs[id(task)]

    def getAvgSpeed(self, id=None):
        if id is not None:
            return self.tasks[id].getAvgSpeed()

        speed = 0
        for i in self._queue.run:
            if not self.tasks[i].isEnd():
                speed += self.tasks[i].getAvgSpeed()

        return speed

    def getInsSpeed(self, id=None):
        if id is not None:
            return self.tasks[id].getInsSpeed()

        speed = 0
        for i in self._queue.run:
            speed += self.tasks[i].getInsSpeed()

        for i in list(self._done_buff):
            tmp = self.tasks[i].getInsSpeed()
            speed += tmp
            if tmp < 100:
                self._done_buff.remove(i)
            # self._done_buff = []
        return speed

    def getIncByte(self, id=None):
        if id is not None:
            return self.tasks[id].getIncByte()

        inc = 0
        for i in self._queue.done:
            inc += self.tasks[i].getFileSize()
        for i in self._queue.run:
            dl = self.tasks[i]
            inc += dl.getFileSize() - dl.getLeft()

        return inc

    def getFileSize(self, id=None):
        if id is not None:
            return self.tasks[id].getFileSize()

        return self.getTotalSize()

    def getTotalSize(self):
        size = 0
        for i, j in self.tasks.items():
            size += j.getFileSize()

        return size

    def getLeft(self, id=None):
        if id is not None:
            return self.tasks[id].getLeft()

        left = 0
        for i in self._queue.run:
            if not self.tasks[i].isEnd():
                left += self.tasks[i].getLeft()
        for i in self._queue.undone:
            left += self.tasks[i].getLeft()
        return left


    def isEnd(self, id=None):
        if id is not None:
            return self.tasks[id].isEnd()
        else:
            return self.status.isEnd()


    def config(self, **kwargs):
        for i, j in self.__config_params__():
            if i in kwargs:
                setattr(self, j, kwargs[i])

    def __config_params__(self):
        return [('max_task', 'max_task')]


    def __packet_params__(self):
        return ['tasks', 'max_task']


    def unpack(self, packet):
        Packer.unpack(self, packet)


class TaskQueue(object):
    def __init__(self):
        self.run = []
        self.pause = []
        self.undone = []
        self.done = []
        self.ready = []
        self.critical = []

