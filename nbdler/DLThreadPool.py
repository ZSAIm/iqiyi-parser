
# import logging
import threading
import time
from . import DLCommon as cv

class ThreadPool:
    def __init__(self, daemon):
        self._daemon = daemon
        self._threads = []
        self._insp_thr_ = None
        self._app_lock = threading.Lock()

    def Thread(self, *args, **kwargs):
        with self._app_lock:
            thr = Thread(*args, daemon=self._daemon, **kwargs)
            self._threads.append(thr)
            if not self._insp_thr_ or self._insp_thr_.isStoped():
                self._insp_thr_ = Thread(target=self.__insp__, name=cv.THREADPOOL, daemon=self._daemon)
                self._insp_thr_.start()

        return thr

    def setDaemon(self, daemonic):
        self._daemon = daemonic

    def __insp__(self):
        while True:
            with self._app_lock:
                for i in list(self._threads):
                    if i._started.is_set() and not i.isAlive():
                        self._threads.remove(i)
                if not self._threads:
                    break
            time.sleep(0.1)

    def isAllDead(self):
        if len(self._threads) == 0:
            return True
        elif len(self._threads) == 1:
            if self._threads[0] is threading.currentThread():
                return True
            else:
                return False
        else:
            return False

    def getPoolThreads(self):
        return self._threads

    def get(self, name):
        for i in self._threads:
            if i.getName() == name:
                return i

    def getAll(self, name):
        threads = []
        for i in list(self._threads):
            if i.getName() == name:
                threads.append(i)

        return threads




class Thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)

    def isStarted(self):
        return self._started.is_set()

    def isRunning(self):
        return self._started.is_set() and self.isAlive()

    def isStoped(self):
        self.is_alive()  # easy way to get ._is_stopped set when appropriate
        return self._is_stopped

    def isInitial(self):
        return not self.isStarted() and not self.isStoped()

